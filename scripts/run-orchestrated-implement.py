#!/usr/bin/env python3
"""Run orchestrated Spec Kit implementation shards."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


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
    try:
        return path.resolve().relative_to(project_root).as_posix()
    except ValueError:
        return str(path)


def _resolve_scoped_path(project_root: Path, raw_path: str) -> Path | None:
    value = raw_path.strip()
    if not value:
        return None
    path = Path(value)
    if not path.is_absolute():
        path = project_root / path
    resolved = path.resolve()
    try:
        resolved.relative_to(project_root)
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
    ignored_parts = {".git", ".specify"}
    files: list[Path] = []
    for path in project_root.rglob("*"):
        try:
            rel_parts = path.relative_to(project_root).parts
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


def _should_dispatch(item: dict[str, Any]) -> bool:
    return not item.get("context_gaps")


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


def _dispatch_item(
    item: dict[str, Any],
    integration_key: str,
    project_root: Path,
    model: str | None,
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
            if integration_key == "copilot":
                return _dispatch_copilot_fallback(
                    item, project_root, model, import_error
                )
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

    result = impl.dispatch_command(
        "speckit.implement",
        args=str(item.get("args", "")),
        project_root=project_root,
        model=model,
    )
    return {
        "shard_id": item.get("shard_id"),
        "task_type": item.get("task_type"),
        "executor_type": item.get("executor_type"),
        "execution_body": item.get("execution_body"),
        "lifecycle": item.get("lifecycle"),
        "exit_code": result.get("exit_code", 1),
        "stdout": result.get("stdout", ""),
        "stderr": result.get("stderr", ""),
        "dispatch_process": {
            "kind": "subprocess",
            "command": impl.key,
            "agent": "speckit.implement",
            "pid_scope": "independent",
            "integration_source": "specify_cli.integrations",
        },
    }


def _dispatch_copilot_fallback(
    item: dict[str, Any],
    project_root: Path,
    model: str | None,
    import_error: str,
) -> dict[str, Any]:
    copilot = shutil.which("copilot")
    if not copilot:
        return {
            "shard_id": item.get("shard_id"),
            "exit_code": 1,
            "error": "Integration CLI not found on PATH: copilot",
            "fallback_reason": f"specify_cli import failed: {import_error}",
        }

    cli_args = [
        copilot,
        "-p",
        str(item.get("args", "")),
        "--agent",
        "speckit.implement",
    ]
    if _allow_all():
        cli_args.append("--yolo")
    if model:
        cli_args.extend(["--model", model])

    result = subprocess.run(cli_args, text=True, cwd=project_root)
    return {
        "shard_id": item.get("shard_id"),
        "task_type": item.get("task_type"),
        "executor_type": item.get("executor_type"),
        "execution_body": item.get("execution_body"),
        "lifecycle": item.get("lifecycle"),
        "exit_code": result.returncode,
        "stdout": "",
        "stderr": "",
        "dispatch_process": {
            "kind": "subprocess",
            "command": "copilot",
            "agent": "speckit.implement",
            "pid_scope": "independent",
            "fallback_reason": f"specify_cli import failed: {import_error}",
        },
    }


def _allow_all() -> bool:
    return os.environ.get("SPECIFY_YOLO", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    } or os.environ.get("GITHUB_COPILOT_CLI_YOLO", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
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
        for item in output["items"]:
            if not _should_dispatch(item):
                result = {
                    "shard_id": item.get("shard_id"),
                    "exit_code": 1,
                    "error": "Shard has blocking context gaps.",
                    "context_gaps": item.get("context_gaps", []),
                }
                results.append(result)
                output["dispatch_results"] = results
                print(json.dumps(output, indent=2, sort_keys=True))
                print(
                    json.dumps(
                        {
                            "error": "Shard dispatch blocked.",
                            "failed_shard": item.get("shard_id"),
                            "detail": result["error"],
                        },
                        sort_keys=True,
                    ),
                    file=sys.stderr,
                )
                return 1
            before = _capture_workspace_state(project_root, item)
            result = _dispatch_item(
                item,
                parsed.integration,
                project_root,
                parsed.model.strip() or None,
            )
            if result.get("exit_code") == 0:
                verification = _verify_shard_scope(project_root, item, before)
                result["post_dispatch_verification"] = verification
                if verification["exit_code"] != 0:
                    result["exit_code"] = verification["exit_code"]
                    result["error"] = "Shard modified files or task statuses outside its handoff scope."
            results.append(result)
            if result.get("exit_code") != 0:
                output["dispatch_results"] = results
                print(json.dumps(output, indent=2, sort_keys=True))
                print(
                    json.dumps(
                        {
                            "error": "Shard dispatch failed.",
                            "failed_shard": result.get("shard_id"),
                            "detail": result.get("error") or result.get("stderr"),
                        },
                        sort_keys=True,
                    ),
                    file=sys.stderr,
                )
                return int(result.get("exit_code") or 1)

    output["dispatch_results"] = results
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
