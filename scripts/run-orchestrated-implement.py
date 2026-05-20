#!/usr/bin/env python3
"""Run orchestrated Spec Kit implementation shards."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import selectors
import signal
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

TAIL_BYTES = 32 * 1024
MAIN_OUTPUT_ERROR_TAIL_CHARS = 2000


def _load_builder() -> Any:
    module_path = Path(__file__).with_name("build-task-shards.py")
    spec = importlib.util.spec_from_file_location("build_task_shards", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.TaskShardBuilder


def _add_specify_tool_site_packages() -> bool:
    specify_bin = shutil.which("specify")
    if not specify_bin:
        return False

    try:
        first_line = Path(specify_bin).read_text(encoding="utf-8").splitlines()[0]
    except (IndexError, OSError, UnicodeDecodeError):
        return False
    if not first_line.startswith("#!"):
        return False

    python_path = Path(first_line[2:].strip().split()[0])
    tool_root = python_path.parent.parent
    candidates = sorted(tool_root.glob("lib/python*/site-packages"))
    added = False
    for candidate in candidates:
        if not (candidate / "specify_cli").is_dir():
            continue
        candidate_text = str(candidate)
        if candidate_text not in sys.path:
            sys.path.insert(0, candidate_text)
        added = True
    return added


def _parse_bool(raw: str) -> bool:
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _display_path(project_root: Path, path: Path) -> str:
    resolved_root = project_root.resolve()
    try:
        return path.resolve().relative_to(resolved_root).as_posix()
    except ValueError:
        return str(path)


def _resolve_scoped_path(project_root: Path, raw_path: str) -> Path | None:
    resolved_root = project_root.resolve()
    value = raw_path.strip()
    if not value:
        return None
    path = Path(value)
    if not path.is_absolute():
        path = resolved_root / path
    resolved = path.resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError:
        return None
    return resolved


def _file_digest(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _iter_workspace_files(project_root: Path) -> list[Path]:
    resolved_root = project_root.resolve()
    ignored_parts = {".git", ".specify"}
    files: list[Path] = []
    for path in resolved_root.rglob("*"):
        try:
            rel_parts = path.relative_to(resolved_root).parts
        except ValueError:
            continue
        if any(part in ignored_parts for part in rel_parts):
            continue
        if path.is_file():
            files.append(path)
    return files


def _task_statuses(tasks_path: Path) -> dict[str, str]:
    try:
        lines = tasks_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return {}
    statuses: dict[str, str] = {}
    for line in lines:
        stripped = line.lstrip()
        if not stripped.startswith("- [") or "]" not in stripped:
            continue
        marker = stripped[3:4].lower()
        remainder = stripped.split("]", 1)[1].strip()
        task_id = remainder.split(maxsplit=1)[0] if remainder else ""
        if task_id:
            statuses[task_id] = marker
    return statuses


def _capture_workspace_state(project_root: Path, item: dict[str, Any]) -> dict[str, Any]:
    files = {
        _display_path(project_root, path): _file_digest(path)
        for path in _iter_workspace_files(project_root)
    }
    task_statuses: dict[str, str] = {}
    for raw_path in item.get("allowed_write_paths", []):
        if str(raw_path).endswith("tasks.md"):
            path = _resolve_scoped_path(project_root, str(raw_path))
            if path is not None:
                task_statuses = _task_statuses(path)
                break
    return {"files": files, "task_statuses": task_statuses}


def _allowed_write_paths(project_root: Path, item: dict[str, Any]) -> set[str]:
    allowed: set[str] = set()
    for raw_path in item.get("allowed_write_paths", []):
        path = _resolve_scoped_path(project_root, str(raw_path))
        if path is None:
            continue
        allowed.add(_display_path(project_root, path))
    return allowed


def _path_is_allowed(path: str, allowed_writes: set[str]) -> bool:
    for allowed in allowed_writes:
        if path == allowed or path.startswith(f"{allowed.rstrip('/')}/"):
            return True
    return False


def _paths_overlap(left_paths: set[str], right_paths: set[str]) -> bool:
    for left in left_paths:
        left_value = left.rstrip("/")
        for right in right_paths:
            right_value = right.rstrip("/")
            if (
                left_value == right_value
                or left_value.startswith(f"{right_value}/")
                or right_value.startswith(f"{left_value}/")
            ):
                return True
    return False


def _safe_parallel_writes(project_root: Path, item: dict[str, Any]) -> set[str]:
    writes = _allowed_write_paths(project_root, item)
    task_update = item.get("task_status_update", {})
    if isinstance(task_update, dict):
        receipt_path = str(task_update.get("receipt_path", ""))
        resolved = _resolve_scoped_path(project_root, receipt_path)
        if resolved is not None:
            writes.discard(_display_path(project_root, resolved))
    return writes


def _parallel_group_key(item: dict[str, Any]) -> tuple[Any, ...]:
    isolation = item.get("isolation", {})
    if not isinstance(isolation, dict):
        return ()
    topo_layer = isolation.get("topo_layer")
    topo_layers_value = isolation.get("topo_layers", []) or []
    if topo_layer is not None:
        topo_layers = (topo_layer,)
    else:
        topo_layers = tuple(topo_layers_value)
    phases = tuple(isolation.get("phases", []) or [])
    if topo_layers:
        return ("topo_layers", topo_layers)
    if phases:
        return ("phases", phases)
    return ()


def _schedule_parallel_layers(
    project_root: Path, items: list[dict[str, Any]]
) -> list[list[dict[str, Any]]]:
    layers: list[list[dict[str, Any]]] = []
    current_safe_block: list[dict[str, Any]] = []
    current_group_key: tuple[Any, ...] | None = None

    def flush_safe_block() -> None:
        nonlocal current_safe_block, current_group_key
        if current_safe_block:
            layers.extend(_schedule_safe_block(project_root, current_safe_block))
            current_safe_block = []
            current_group_key = None

    for item in items:
        if item.get("isolation", {}).get("parallelism") != "safe":
            flush_safe_block()
            layers.append([item])
            continue
        group_key = _parallel_group_key(item)
        if current_group_key is None:
            current_group_key = group_key
        elif group_key != current_group_key:
            flush_safe_block()
            current_group_key = group_key
        current_safe_block.append(item)

    flush_safe_block()
    return layers


def _schedule_safe_block(
    project_root: Path, items: list[dict[str, Any]]
) -> list[list[dict[str, Any]]]:
    remaining = list(items)
    layers: list[list[dict[str, Any]]] = []
    while remaining:
        layer: list[dict[str, Any]] = []
        layer_writes: set[str] = set()
        next_remaining: list[dict[str, Any]] = []
        for item in remaining:
            writes = _safe_parallel_writes(project_root, item)
            if _paths_overlap(layer_writes, writes):
                next_remaining.append(item)
                continue
            layer.append(item)
            layer_writes.update(writes)
        layers.append(layer)
        remaining = next_remaining
    return layers


def _schedule_parallel_layer_ids(
    project_root: Path, items: list[dict[str, Any]]
) -> list[list[str]]:
    return [
        [str(item.get("shard_id", "")) for item in layer]
        for layer in _schedule_parallel_layers(project_root, items)
    ]


def _should_dispatch(item: dict[str, Any]) -> bool:
    return not item.get("context_gaps")


def _emit_shard_heartbeat(shard_id: str) -> None:
    print(
        json.dumps(
            {
                "event": "shard_heartbeat",
                "shard_id": shard_id,
                "status": "running",
            },
            sort_keys=True,
        ),
        flush=True,
    )


def _terminate_process_group(process: subprocess.Popen[str]) -> None:
    try:
        pgid = os.getpgid(process.pid)
    except OSError:
        process.terminate()
        return

    try:
        os.killpg(pgid, signal.SIGTERM)
    except OSError:
        process.terminate()


class LogReceiver:
    def __init__(self, log_dir: Path, shard_id: str, tail_bytes: int = TAIL_BYTES):
        self.log_dir = log_dir
        self.shard_id = shard_id
        self.tail_bytes = tail_bytes
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.stdout_log_path = self.log_dir / f"{shard_id}.stdout.log"
        self.stderr_log_path = self.log_dir / f"{shard_id}.stderr.log"
        self._stdout_tail = ""
        self._stderr_tail = ""
        self._output_truncated = False

    def append(self, stream_name: str, line: str) -> None:
        if stream_name == "stdout":
            self._append_to(self.stdout_log_path, line)
            self._stdout_tail = self._trim_tail(self._stdout_tail + line)
        else:
            self._append_to(self.stderr_log_path, line)
            self._stderr_tail = self._trim_tail(self._stderr_tail + line)

    def result_fields(self) -> dict[str, Any]:
        return {
            "stdout_tail": self._stdout_tail,
            "stderr_tail": self._stderr_tail,
            "stdout_log_path": str(self.stdout_log_path),
            "stderr_log_path": str(self.stderr_log_path),
            "output_truncated": self._output_truncated,
        }

    def _append_to(self, path: Path, line: str) -> None:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line)

    def _trim_tail(self, value: str) -> str:
        encoded = value.encode("utf-8")
        if len(encoded) <= self.tail_bytes:
            return value
        self._output_truncated = True
        return encoded[-self.tail_bytes :].decode("utf-8", errors="replace")


def _run_logged_subprocess(
    cli_args: list[str],
    project_root: Path,
    shard_id: str,
    log_dir: Path,
    heartbeat_interval: float,
) -> dict[str, Any]:
    receiver = LogReceiver(log_dir, shard_id)
    selector = selectors.DefaultSelector()
    process: subprocess.Popen[str] | None = None

    try:
        process = subprocess.Popen(
            cli_args,
            cwd=project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            start_new_session=True,
        )
        if process.stdout is not None:
            selector.register(process.stdout, selectors.EVENT_READ, "stdout")
        if process.stderr is not None:
            selector.register(process.stderr, selectors.EVENT_READ, "stderr")

        next_heartbeat = time.monotonic() + heartbeat_interval
        while selector.get_map():
            timeout = max(0.0, next_heartbeat - time.monotonic())
            events = selector.select(timeout)
            if not events:
                _emit_shard_heartbeat(shard_id)
                next_heartbeat = time.monotonic() + heartbeat_interval
                continue

            for key, _ in events:
                stream = key.fileobj
                line = stream.readline()
                if line == "":
                    selector.unregister(stream)
                    stream.close()
                    continue
                if key.data == "stdout":
                    receiver.append("stdout", line)
                else:
                    receiver.append("stderr", line)
                next_heartbeat = time.monotonic() + heartbeat_interval

        exit_code = process.wait()
        if process.stdout is not None and not process.stdout.closed:
            process.stdout.close()
        if process.stderr is not None and not process.stderr.closed:
            process.stderr.close()
    except KeyboardInterrupt:
        if process is not None:
            _terminate_process_group(process)
            process.wait()
            if process.stdout is not None and not process.stdout.closed:
                process.stdout.close()
            if process.stderr is not None and not process.stderr.closed:
                process.stderr.close()
        fields = receiver.result_fields()
        return {
            "exit_code": 130,
            **fields,
            "stderr_tail": fields["stderr_tail"] + "Interrupted by user",
        }
    finally:
        selector.close()

    return {
        "exit_code": exit_code,
        **receiver.result_fields(),
    }


def _build_dispatch_cli_args(
    impl: Any,
    handoff_args: str,
    model: str | None,
) -> list[str] | None:
    prompt = impl.build_command_invocation("speckit.implement", handoff_args)
    return impl.build_exec_args(
        prompt,
        model=model,
        output_json=False,
    )


def _changed_files(project_root: Path, before: dict[str, Any]) -> set[str]:
    previous = before.get("files", {})
    current = {
        _display_path(project_root, path): _file_digest(path)
        for path in _iter_workspace_files(project_root)
    }
    paths = set(previous) | set(current)
    return {path for path in paths if previous.get(path) != current.get(path)}


def _verify_shard_scope(
    project_root: Path, item: dict[str, Any], before: dict[str, Any]
) -> dict[str, Any]:
    allowed_writes = _allowed_write_paths(project_root, item)
    changed = _changed_files(project_root, before)
    scope_violations = sorted(
        path for path in changed if not _path_is_allowed(path, allowed_writes)
    )

    task_violations: list[str] = []
    allowed_task_ids = set(str(task_id) for task_id in item.get("task_ids", []))
    before_statuses = before.get("task_statuses", {})
    if before_statuses:
        for raw_path in item.get("allowed_write_paths", []):
            if not str(raw_path).endswith("tasks.md"):
                continue
            path = _resolve_scoped_path(project_root, str(raw_path))
            if path is None:
                continue
            after_statuses = _task_statuses(path)
            for task_id, before_status in before_statuses.items():
                if task_id in allowed_task_ids:
                    continue
                if after_statuses.get(task_id) != before_status:
                    task_violations.append(
                        f"Task {task_id} status changed outside shard task_ids."
                    )
            break

    exit_code = 1 if scope_violations or task_violations else 0
    return {
        "shard_id": item.get("shard_id"),
        "exit_code": exit_code,
        "scope_violations": scope_violations,
        "task_violations": task_violations,
    }


def _verify_layer_scope(
    project_root: Path, items: list[dict[str, Any]], before: dict[str, Any]
) -> dict[str, Any]:
    allowed_writes: set[str] = set()
    for item in items:
        allowed_writes.update(_allowed_write_paths(project_root, item))
    changed = _changed_files(project_root, before)
    ignored_paths: set[str] = set()
    for item in items:
        handoff_path = _resolve_scoped_path(project_root, str(item.get("handoff_path", "")))
        if handoff_path is None:
            continue
        ignored_paths.add(_display_path(project_root, handoff_path.parent / "logs"))
    scope_violations = sorted(
        path
        for path in changed
        if not _path_is_allowed(path, allowed_writes)
        and not any(path == log_dir or path.startswith(f"{log_dir}/") for log_dir in ignored_paths)
    )
    return {
        "shard_ids": [item.get("shard_id") for item in items],
        "exit_code": 1 if scope_violations else 0,
        "scope_violations": scope_violations,
        "task_violations": [],
    }


def _write_task_statuses(tasks_path: Path, completed_task_ids: set[str]) -> list[str]:
    original = tasks_path.read_text(encoding="utf-8")
    lines = original.splitlines()
    updated: list[str] = []
    marked: list[str] = []
    for line in lines:
        match = re_task_status_line(line)
        if match and match["task_id"] in completed_task_ids:
            updated.append(f"{match['prefix']}- [x] {match['suffix']}")
            marked.append(match["task_id"])
        else:
            updated.append(line)
    trailing_newline = "\n" if original.endswith("\n") else ""
    tasks_path.write_text("\n".join(updated) + trailing_newline, encoding="utf-8")
    return marked


def re_task_status_line(line: str) -> dict[str, str] | None:
    stripped = line.lstrip()
    indent = line[: len(line) - len(stripped)]
    if not stripped.startswith("- [") or "]" not in stripped:
        return None
    suffix = stripped.split("]", 1)[1].strip()
    task_id = suffix.split(maxsplit=1)[0] if suffix else ""
    if not task_id:
        return None
    return {"prefix": indent, "task_id": task_id, "suffix": suffix}


def _commit_task_receipt(
    project_root: Path, tasks_path: Path, item: dict[str, Any]
) -> dict[str, Any]:
    task_update = item.get("task_status_update")
    if not isinstance(task_update, dict) or task_update.get("mode") != "receipt":
        return {
            "exit_code": 1,
            "error": "Shard is missing receipt-based task_status_update.",
        }
    receipt_path = _resolve_scoped_path(project_root, str(task_update.get("receipt_path", "")))
    if receipt_path is None or not receipt_path.is_file():
        return {
            "exit_code": 1,
            "error": "Shard completion receipt was not written.",
            "receipt_path": str(task_update.get("receipt_path", "")),
        }
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return {
            "exit_code": 1,
            "error": f"Failed to read shard completion receipt: {exc}",
            "receipt_path": str(receipt_path),
        }
    if receipt.get("contract_type") != "speckit.implement.receipt.v1":
        return {
            "exit_code": 1,
            "error": "Shard completion receipt has an invalid contract_type.",
            "receipt_path": str(receipt_path),
        }
    required_fields = ("contract_type", "shard_id", "task_ids", "completed_task_ids")
    missing_fields = [field for field in required_fields if field not in receipt]
    if missing_fields:
        return {
            "exit_code": 1,
            "error": "Shard completion receipt is missing required field(s).",
            "missing_fields": missing_fields,
            "receipt_path": str(receipt_path),
        }
    if str(receipt.get("shard_id", "")) != str(item.get("shard_id", "")):
        return {
            "exit_code": 1,
            "error": "Shard completion receipt shard_id does not match handoff.",
            "receipt_path": str(receipt_path),
        }

    receipt_task_ids = [str(task_id) for task_id in receipt.get("task_ids", [])]
    handoff_task_ids = [str(task_id) for task_id in item.get("task_ids", [])]
    if receipt_task_ids != handoff_task_ids:
        return {
            "exit_code": 1,
            "error": "Shard completion receipt task_ids do not match handoff.",
            "receipt_path": str(receipt_path),
        }

    allowed_task_ids = set(handoff_task_ids)
    completed_task_ids = {
        str(task_id) for task_id in receipt.get("completed_task_ids", [])
    }
    invalid_task_ids = sorted(completed_task_ids - allowed_task_ids)
    if invalid_task_ids:
        return {
            "exit_code": 1,
            "error": "Shard completion receipt lists task IDs outside handoff scope.",
            "invalid_task_ids": invalid_task_ids,
            "receipt_path": str(receipt_path),
        }

    marked = _write_task_statuses(tasks_path, completed_task_ids)
    return {
        "exit_code": 0,
        "receipt_path": str(receipt_path),
        "completed_task_ids": marked,
    }


def _compact_dispatch_result(result: dict[str, Any]) -> dict[str, Any]:
    compacted = dict(result)
    compacted.pop("stdout_tail", None)
    stderr_tail = str(compacted.pop("stderr_tail", "") or "")
    if int(compacted.get("exit_code") or 0) != 0 and stderr_tail:
        compacted["stderr_tail"] = stderr_tail[-MAIN_OUTPUT_ERROR_TAIL_CHARS:]
    return compacted


def _compact_dispatch_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [_compact_dispatch_result(result) for result in results]


def _output_with_dispatch_results(
    output: dict[str, Any],
    results: list[dict[str, Any]],
) -> dict[str, Any]:
    compacted = dict(output)
    compacted["dispatch_results"] = _compact_dispatch_results(results)
    return compacted


def _dispatch_item(
    item: dict[str, Any],
    integration_key: str,
    project_root: Path,
    model: str | None,
    log_dir: Path | None = None,
    heartbeat_interval: float = 60.0,
) -> dict[str, Any]:
    try:
        from specify_cli.integrations import get_integration
    except ImportError as exc:
        import_error = str(exc)
        if _add_specify_tool_site_packages():
            try:
                from specify_cli.integrations import get_integration
            except ImportError as retry_exc:
                import_error = f"{import_error}; retry after specify tool path: {retry_exc}"
            else:
                import_error = ""
        if import_error:
            return {
                "shard_id": item.get("shard_id"),
                "exit_code": 1,
                "error": f"Unable to import Spec Kit integrations: {import_error}",
            }

    impl = get_integration(integration_key)
    if impl is None:
        return {
            "shard_id": item.get("shard_id"),
            "exit_code": 1,
            "error": f"Unknown integration: {integration_key}",
        }
    if impl.build_exec_args("test") is None:
        return {
            "shard_id": item.get("shard_id"),
            "exit_code": 1,
            "error": f"Integration does not support CLI dispatch: {integration_key}",
        }
    if not shutil.which(impl.key):
        return {
            "shard_id": item.get("shard_id"),
            "exit_code": 1,
            "error": f"Integration CLI not found on PATH: {impl.key}",
        }

    cli_args = _build_dispatch_cli_args(
        impl,
        str(item.get("args", "")),
        model,
    )
    if cli_args is None:
        return {
            "shard_id": item.get("shard_id"),
            "exit_code": 1,
            "error": f"Integration does not support CLI dispatch: {integration_key}",
        }

    result = _run_logged_subprocess(
        cli_args,
        project_root,
        str(item.get("shard_id", "")),
        log_dir or project_root / ".specify" / "workflow-preset" / "logs",
        heartbeat_interval,
    )
    return {
        "shard_id": item.get("shard_id"),
        "task_type": item.get("task_type"),
        "executor_type": item.get("executor_type"),
        "execution_body": item.get("execution_body"),
        "lifecycle": item.get("lifecycle"),
        "exit_code": result.get("exit_code", 1),
        "stdout_tail": result.get("stdout_tail", ""),
        "stderr_tail": result.get("stderr_tail", ""),
        "stdout_log_path": result.get("stdout_log_path", ""),
        "stderr_log_path": result.get("stderr_log_path", ""),
        "output_truncated": result.get("output_truncated", False),
        "dispatch_process": {
            "kind": "subprocess",
            "command": impl.key,
            "agent": "speckit.implement",
            "pid_scope": "independent",
            "integration_source": "specify_cli.integrations",
            "timeout": "none",
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build and dispatch Spec Kit implementation handoff shards."
    )
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--args", default="")
    parser.add_argument("--max-shards", type=int, default=8)
    parser.add_argument("--run-id", default="manual")
    parser.add_argument("--integration", default="copilot")
    parser.add_argument("--model", default="")
    parser.add_argument(
        "--dry-run",
        default="false",
        help="When true, build shards and report dispatch inputs without running agents.",
    )
    parsed = parser.parse_args(argv)

    project_root = Path(parsed.project_root).resolve()
    try:
        builder = _load_builder()
        output = builder.build(project_root, parsed.args, parsed.max_shards, parsed.run_id)
    except (RuntimeError, ValueError) as exc:
        print(json.dumps({"error": str(exc), "items": []}), file=sys.stderr)
        return 1

    dry_run = _parse_bool(str(parsed.dry_run))
    results: list[dict[str, Any]] = []
    if dry_run:
        for item in output["items"]:
            results.append(
                {
                    "shard_id": item.get("shard_id"),
                    "task_type": item.get("task_type"),
                    "executor_type": item.get("executor_type"),
                    "execution_body": item.get("execution_body"),
                    "lifecycle": item.get("lifecycle"),
                    "args": item.get("args"),
                    "dry_run": True,
                    "exit_code": 0,
                }
            )
    else:
        tasks_path = Path(str(output["tasks_path"]))
        items_by_id = {str(item.get("shard_id")): item for item in output["items"]}
        for layer in _schedule_parallel_layers(project_root, output["items"]):
            blocked = [item for item in layer if not _should_dispatch(item)]
            if blocked:
                result = {
                    "shard_id": blocked[0].get("shard_id"),
                    "exit_code": 1,
                    "error": "Shard has blocking context gaps.",
                    "context_gaps": blocked[0].get("context_gaps", []),
                }
                results.append(result)
                print(
                    json.dumps(
                        _output_with_dispatch_results(output, results),
                        indent=2,
                        sort_keys=True,
                    )
                )
                print(
                    json.dumps(
                        {
                            "error": "Shard dispatch blocked.",
                            "failed_shard": blocked[0].get("shard_id"),
                            "detail": result["error"],
                        },
                        sort_keys=True,
                    ),
                    file=sys.stderr,
                )
                return 1

            before = _capture_workspace_state(project_root, {"allowed_write_paths": []})
            layer_results: dict[str, dict[str, Any]] = {}
            worker_count = len(layer)
            with ThreadPoolExecutor(max_workers=worker_count) as executor:
                futures = {
                    executor.submit(
                        _dispatch_item,
                        item,
                        parsed.integration,
                        project_root,
                        parsed.model.strip() or None,
                        Path(str(item.get("handoff_path", ""))).parent / "logs",
                    ): str(item.get("shard_id"))
                    for item in layer
                }
                for future in as_completed(futures):
                    shard_id = futures[future]
                    layer_results[shard_id] = future.result()

            ordered_layer_results = [
                layer_results[str(item.get("shard_id"))] for item in layer
            ]
            failed = next(
                (result for result in ordered_layer_results if result.get("exit_code") != 0),
                None,
            )

            if failed is None:
                verification = _verify_layer_scope(project_root, layer, before)
                for result in ordered_layer_results:
                    result["post_dispatch_verification"] = verification
                if verification["exit_code"] != 0:
                    failed = ordered_layer_results[0]
                    failed["exit_code"] = verification["exit_code"]
                    failed["error"] = (
                        "Shard layer modified files outside its combined handoff scope."
                    )

            if failed is None:
                for result in ordered_layer_results:
                    item = items_by_id[str(result.get("shard_id"))]
                    commit = _commit_task_receipt(project_root, tasks_path, item)
                    result["task_status_commit"] = commit
                    if commit["exit_code"] != 0:
                        result["exit_code"] = commit["exit_code"]
                        result["error"] = commit["error"]
                        failed = result
                        break

            results.extend(ordered_layer_results)
            if failed is not None:
                print(
                    json.dumps(
                        _output_with_dispatch_results(output, results),
                        indent=2,
                        sort_keys=True,
                    )
                )
                print(
                    json.dumps(
                        {
                            "error": "Shard dispatch failed.",
                            "failed_shard": failed.get("shard_id"),
                            "detail": failed.get("error") or failed.get("stderr_tail"),
                            "stdout_log_path": failed.get("stdout_log_path"),
                            "stderr_log_path": failed.get("stderr_log_path"),
                        },
                        sort_keys=True,
                    ),
                    file=sys.stderr,
                )
                return int(failed.get("exit_code") or 1)

    print(
        json.dumps(
            _output_with_dispatch_results(output, results),
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
