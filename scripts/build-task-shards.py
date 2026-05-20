#!/usr/bin/env python3
"""Build Spec Kit implementation handoff shards.

Builds conservative implementation handoff shards from the active feature's
``tasks.md`` so a workflow can fan out into repeated ``speckit.implement``
handoff-mode calls.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any


_TASK_RE = re.compile(
    r"^\s*-\s+\[(?P<status>[ xX])\]\s+(?P<id>[A-Za-z]+\d{3,})\b(?P<body>.*)$"
)
_HEADING_RE = re.compile(r"^\s{0,3}#{2,6}\s+(?P<title>.+?)\s*$")
_BACKTICK_RE = re.compile(r"`([^`]+)`")
_PATH_TOKEN_RE = re.compile(
    r"(?<![\w./-])([A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)+|[A-Za-z0-9_.-]+\.[A-Za-z0-9_.-]+)(?![\w./-])"
)
_SNIPPET_CONTEXT_LINES = 3

_EXECUTOR_PROFILES = {
    "setup": {
        "id": "setup-worker",
        "purpose": "Prepare project structure, dependencies, configuration, and generated scaffolding.",
    },
    "test": {
        "id": "test-worker",
        "purpose": "Create or update tests, fixtures, and contract checks before implementation.",
    },
    "implementation": {
        "id": "implementation-worker",
        "purpose": "Implement product code for the scoped task paths.",
    },
    "integration": {
        "id": "integration-worker",
        "purpose": "Wire components, APIs, services, events, and external boundaries.",
    },
    "validation": {
        "id": "validation-worker",
        "purpose": "Run and repair validation flows without expanding feature scope.",
    },
    "cleanup": {
        "id": "cleanup-worker",
        "purpose": "Perform documentation, polish, cleanup, and final consistency updates.",
    },
}


@dataclass
class ParsedTask:
    task_id: str
    text: str
    phase: str
    task_type: str
    parallel: bool
    paths: list[str]
    validation_commands: list[str]
    topo_layer: int | None
    completed: bool


@dataclass
class TaskShard:
    shard_id: str
    tasks: list[ParsedTask]

    @property
    def task_ids(self) -> list[str]:
        return [task.task_id for task in self.tasks]

    @property
    def paths(self) -> list[str]:
        seen: dict[str, None] = {}
        for task in self.tasks:
            for path in task.paths:
                seen.setdefault(path, None)
        return list(seen)

    @property
    def validation_commands(self) -> list[str]:
        seen: dict[str, None] = {}
        for task in self.tasks:
            for command in task.validation_commands:
                seen.setdefault(command, None)
        return list(seen)

    @property
    def task_types(self) -> list[str]:
        seen: dict[str, None] = {}
        for task in self.tasks:
            seen.setdefault(task.task_type, None)
        return list(seen)

    @property
    def shard_type(self) -> str:
        task_types = self.task_types
        if len(task_types) == 1:
            return task_types[0]
        return "implementation-batch"

    @property
    def executor_profile(self) -> dict[str, str]:
        if self.shard_type in _EXECUTOR_PROFILES:
            return _EXECUTOR_PROFILES[self.shard_type]
        return {
            "id": "implementation-worker",
            "purpose": "Execute a mixed implementation shard with a fresh process and context.",
        }

    @property
    def safe_parallel(self) -> bool:
        return bool(self.tasks) and all(task.parallel for task in self.tasks)

    @property
    def topo_layers(self) -> list[int]:
        seen: dict[int, None] = {}
        for task in self.tasks:
            if task.topo_layer is not None:
                seen.setdefault(task.topo_layer, None)
        return list(seen)

    @property
    def phases(self) -> list[str]:
        seen: dict[str, None] = {}
        for task in self.tasks:
            seen.setdefault(task.phase, None)
        return list(seen)


class TaskShardBuilder:
    """Generate handoff files from the active feature's ``tasks.md``."""

    @classmethod
    def build(
        cls,
        project_root: Path,
        args: str,
        max_shards: int,
        run_id: str,
    ) -> dict[str, Any]:
        if max_shards < 1:
            raise ValueError("max_shards must be a positive integer.")

        project_root = project_root.resolve()
        feature_dir = cls._resolve_feature_dir(project_root)
        cls._require_feature_files(feature_dir)
        tasks = cls._parse_tasks(feature_dir / "tasks.md")
        cls._apply_manifest_metadata(feature_dir / "tasks.manifest.json", tasks)
        shards = cls._build_shards(tasks, max_shards)
        items = cls._write_handoffs(
            project_root,
            feature_dir,
            tasks,
            shards,
            args,
            run_id,
        )
        return {
            "feature_dir": str(feature_dir),
            "tasks_path": str(feature_dir / "tasks.md"),
            "item_count": len(items),
            "items": items,
        }

    @classmethod
    def _resolve_feature_dir(cls, project_root: Path) -> Path:
        feature_json = project_root / ".specify" / "feature.json"
        if feature_json.is_file():
            try:
                raw = json.loads(feature_json.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as exc:
                raise ValueError(f"Failed to parse .specify/feature.json: {exc}") from exc
            feature_value = raw.get("feature_directory") if isinstance(raw, dict) else None
            if feature_value:
                return cls._normalize_feature_dir(project_root, str(feature_value))

        env_feature = os.environ.get("SPECIFY_FEATURE_DIRECTORY", "").strip()
        if env_feature:
            return cls._normalize_feature_dir(project_root, env_feature)

        branch = cls._current_branch(project_root)
        if not branch:
            raise ValueError(
                "Unable to resolve active feature: no .specify/feature.json, "
                "SPECIFY_FEATURE_DIRECTORY, or git branch is available."
            )
        return cls._find_feature_dir_by_prefix(project_root, branch)

    @staticmethod
    def _normalize_feature_dir(project_root: Path, value: str) -> Path:
        path = Path(value)
        if not path.is_absolute():
            path = project_root / path
        return path.resolve()

    @staticmethod
    def _current_branch(project_root: Path) -> str | None:
        try:
            proc = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=5,
            )
        except (OSError, subprocess.TimeoutExpired):
            return None
        if proc.returncode != 0:
            return None
        branch = proc.stdout.strip()
        if branch == "HEAD":
            return None
        if "/" in branch:
            branch = branch.rsplit("/", 1)[1]
        return branch or None

    @classmethod
    def _find_feature_dir_by_prefix(cls, project_root: Path, branch: str) -> Path:
        specs_dir = project_root / "specs"
        prefix = ""
        timestamp = re.match(r"^(\d{8}-\d{6})-", branch)
        sequential = re.match(r"^(\d{3,})-", branch)
        if timestamp:
            prefix = timestamp.group(1)
        elif sequential:
            prefix = sequential.group(1)
        else:
            feature_date = re.match(r"^feature-(\d{8})-", branch)
            if feature_date:
                prefix = feature_date.group(1)
            else:
                return (specs_dir / branch).resolve()

        matches = sorted(path for path in specs_dir.glob(f"{prefix}-*") if path.is_dir())
        if not matches:
            return (specs_dir / branch).resolve()
        if len(matches) > 1:
            names = ", ".join(path.name for path in matches)
            raise ValueError(
                f"Multiple spec directories found with prefix {prefix!r}: {names}."
            )
        return matches[0].resolve()

    @staticmethod
    def _require_feature_files(feature_dir: Path) -> None:
        if not feature_dir.is_dir():
            raise ValueError(f"Feature directory not found: {feature_dir}")
        missing = [
            name
            for name in ("spec.md", "plan.md", "tasks.md")
            if not (feature_dir / name).is_file()
        ]
        if missing:
            raise ValueError(
                f"Feature directory {feature_dir} is missing required file(s): "
                + ", ".join(missing)
            )

    @classmethod
    def _parse_tasks(cls, tasks_path: Path) -> list[ParsedTask]:
        current_phase = "Tasks"
        tasks: list[ParsedTask] = []
        for line in tasks_path.read_text(encoding="utf-8").splitlines():
            heading = _HEADING_RE.match(line)
            if heading:
                current_phase = heading.group("title").strip()
                continue

            match = _TASK_RE.match(line)
            if not match:
                continue

            task_id = match.group("id")
            text = line.strip()
            body = match.group("body")
            completed = match.group("status").lower() == "x"
            task_type = cls._classify_task(current_phase, body)
            parallel = "[P]" in body
            paths = cls._extract_paths(body)
            if parallel and not paths:
                raise ValueError(
                    f"Parallel task {task_id} must declare at least one explicit path."
                )
            tasks.append(
                ParsedTask(
                    task_id=task_id,
                    text=text,
                    phase=current_phase,
                    task_type=task_type,
                    parallel=parallel,
                    paths=paths,
                    validation_commands=[],
                    topo_layer=None,
                    completed=completed,
                )
            )

        if not tasks:
            raise ValueError(f"No implementation tasks found in {tasks_path}.")
        open_tasks = [task for task in tasks if not task.completed]
        if not open_tasks:
            raise ValueError(f"No incomplete implementation tasks found in {tasks_path}.")
        cls._validate_parallel_conflicts(open_tasks)
        return open_tasks

    @staticmethod
    def _classify_task(phase: str, body: str) -> str:
        text = f"{phase} {body}".lower()
        if any(term in text for term in ("setup", "scaffold", "configure", "bootstrap")):
            return "setup"
        if any(term in text for term in ("test", "contract test", "unit test", "fixture")):
            return "test"
        if any(term in text for term in ("integration", "wire", "api", "service", "event")):
            return "integration"
        if any(term in text for term in ("validation", "validate", "quickstart", "smoke")):
            return "validation"
        if any(term in text for term in ("cleanup", "polish", "docs", "documentation", "readme")):
            return "cleanup"
        return "implementation"

    @classmethod
    def _apply_manifest_metadata(
        cls, manifest_path: Path, tasks: list[ParsedTask]
    ) -> None:
        if not manifest_path.is_file():
            return
        try:
            raw = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return
        manifest_tasks = raw.get("tasks") if isinstance(raw, dict) else None
        if not isinstance(manifest_tasks, list):
            return

        tasks_by_id = {task.task_id: task for task in tasks}
        for entry in manifest_tasks:
            if not isinstance(entry, dict):
                continue
            task = tasks_by_id.get(str(entry.get("task_id", "")))
            if task is None:
                continue

            target_paths = entry.get("target_paths", [])
            if not isinstance(target_paths, list):
                target_paths = []
            paths: dict[str, None] = {}
            commands: dict[str, None] = {}
            for raw_target in target_paths:
                value = str(raw_target).strip()
                if value.startswith("command:"):
                    command = value[len("command:") :].strip()
                    if command:
                        commands.setdefault(command, None)
                    continue
                normalized = cls._normalize_task_path(value)
                if normalized:
                    paths.setdefault(normalized, None)
            if paths or commands:
                task.paths = list(paths)
                task.validation_commands = list(commands)

            topo_layer = entry.get("topo_layer")
            if isinstance(topo_layer, int):
                task.topo_layer = topo_layer

    @classmethod
    def _extract_paths(cls, text: str) -> list[str]:
        candidates: list[str] = []
        for raw in _BACKTICK_RE.findall(text):
            candidates.extend(raw.split())
        candidates.extend(match.group(1) for match in _PATH_TOKEN_RE.finditer(text))

        paths: dict[str, None] = {}
        for candidate in candidates:
            normalized = cls._normalize_task_path(candidate)
            if normalized:
                paths.setdefault(normalized, None)
        return list(paths)

    @staticmethod
    def _normalize_task_path(raw: str) -> str | None:
        value = raw.strip().strip(".,;:()[]{}")
        if not value or value.startswith(("http://", "https://")):
            return None
        value = value.replace("\\", "/")
        if value in {".", ".."} or "/../" in f"/{value}/":
            return None
        if value.startswith("/"):
            value = value.lstrip("/")
        if "{" in value or "}" in value:
            return None
        first_part = PurePosixPath(value).parts[0] if PurePosixPath(value).parts else ""
        if first_part.startswith(
            (
                "BR-",
                "EC-",
                "FR-",
                "INV-",
                "LC-",
                "SC-",
                "SFV-",
                "SIG-",
                "SMK-",
                "SSE-",
                "TC-",
                "TM-",
                "UC-",
                "UIF-",
            )
        ):
            return None
        if not ("/" in value or "." in PurePosixPath(value).name):
            return None
        return str(PurePosixPath(value))

    @classmethod
    def _validate_parallel_conflicts(cls, tasks: list[ParsedTask]) -> None:
        by_phase: dict[str, list[ParsedTask]] = {}
        for task in tasks:
            if task.parallel:
                by_phase.setdefault(task.phase, []).append(task)

        for phase, phase_tasks in by_phase.items():
            for idx, left in enumerate(phase_tasks):
                for right in phase_tasks[idx + 1 :]:
                    overlap = cls._overlap(left.paths, right.paths)
                    if overlap:
                        raise ValueError(
                            f"Parallel tasks {left.task_id} and {right.task_id} in "
                            f"{phase!r} write overlapping path {overlap!r}."
                        )

    @classmethod
    def _build_shards(cls, tasks: list[ParsedTask], max_shards: int) -> list[TaskShard]:
        if any(task.topo_layer is not None for task in tasks):
            return cls._build_manifest_layer_shards(tasks, max_shards)

        groups: list[list[ParsedTask]] = []
        current: list[ParsedTask] = []
        current_type: str | None = None

        for task in tasks:
            task_type = task.task_type
            if task.parallel or (current and current_type != task_type):
                if current:
                    groups.append(current)
                    current = []
                    current_type = None
            if task.parallel:
                groups.append([task])
            else:
                current.append(task)
                current_type = task_type
        if current:
            groups.append(current)

        while len(groups) > max_shards:
            merge_index = cls._find_merge_candidate(groups)
            if merge_index is None:
                raise ValueError(
                    f"Unable to cap handoff shards at {max_shards} without merging "
                    "groups that declare overlapping write paths."
                )
            groups[merge_index] = groups[merge_index] + groups[merge_index + 1]
            del groups[merge_index + 1]

        return [
            TaskShard(f"S{idx + 1:02d}-{cls._group_shard_type(group)}-01", group)
            for idx, group in enumerate(groups)
        ]

    @classmethod
    def _build_manifest_layer_shards(
        cls, tasks: list[ParsedTask], max_shards: int
    ) -> list[TaskShard]:
        grouped: dict[int, list[ParsedTask]] = {}
        fallback_layer = 0
        for task in tasks:
            layer = task.topo_layer
            if layer is None:
                fallback_layer += 1
                layer = fallback_layer
            grouped.setdefault(layer, []).append(task)
        groups = [grouped[layer] for layer in sorted(grouped)]

        while len(groups) > max_shards:
            merge_index = cls._find_merge_candidate(groups)
            if merge_index is None:
                merge_index = len(groups) - 2
            groups[merge_index] = groups[merge_index] + groups[merge_index + 1]
            del groups[merge_index + 1]

        return [
            TaskShard(f"S{idx + 1:02d}-{cls._group_shard_type(group)}-01", group)
            for idx, group in enumerate(groups)
        ]

    @staticmethod
    def _group_shard_type(tasks: list[ParsedTask]) -> str:
        task_types = list(dict.fromkeys(task.task_type for task in tasks))
        if len(task_types) == 1:
            return task_types[0]
        return "implementation-batch"

    @classmethod
    def _find_merge_candidate(cls, groups: list[list[ParsedTask]]) -> int | None:
        for idx in range(len(groups) - 1):
            left_paths = cls._group_paths(groups[idx])
            right_paths = cls._group_paths(groups[idx + 1])
            if not cls._overlap(left_paths, right_paths):
                return idx
        return None

    @staticmethod
    def _group_paths(tasks: list[ParsedTask]) -> list[str]:
        paths: dict[str, None] = {}
        for task in tasks:
            for path in task.paths:
                paths.setdefault(path, None)
        return list(paths)

    @staticmethod
    def _overlap(left_paths: list[str], right_paths: list[str]) -> str | None:
        for left in left_paths:
            left_parts = PurePosixPath(left).parts
            for right in right_paths:
                right_parts = PurePosixPath(right).parts
                if left == right:
                    return left
                min_len = min(len(left_parts), len(right_parts))
                if left_parts[:min_len] == right_parts[:min_len]:
                    return left if len(left_parts) <= len(right_parts) else right
        return None

    @classmethod
    def _write_handoffs(
        cls,
        project_root: Path,
        feature_dir: Path,
        tasks: list[ParsedTask],
        shards: list[TaskShard],
        original_args: str,
        run_id: str,
    ) -> list[dict[str, Any]]:
        handoff_dir = feature_dir / "handoffs" / "implement" / run_id
        handoff_dir.mkdir(parents=True, exist_ok=True)

        context_index = cls._build_context_index(project_root, feature_dir, tasks)
        index_path = handoff_dir / "context-index.json"
        index_path.write_text(
            json.dumps(context_index, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        def write_one(shard: TaskShard) -> dict[str, Any]:
            handoff_path = handoff_dir / f"{shard.shard_id}.json"
            digest_path = handoff_dir / f"{shard.shard_id}.context.md"
            receipt_path = handoff_dir / "results" / f"{shard.shard_id}.json"
            receipt_path.parent.mkdir(parents=True, exist_ok=True)
            digest_text, source_refs, context_gaps, context_notes = cls._context_digest(
                project_root,
                feature_dir,
                shard,
                context_index,
            )
            digest_path.write_text(digest_text, encoding="utf-8")
            payload = cls._handoff_payload(
                project_root,
                feature_dir,
                shard,
                handoff_path,
                index_path,
                digest_path,
                receipt_path,
                source_refs,
                context_gaps,
                context_notes,
            )
            handoff_path.write_text(
                json.dumps(payload, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            shard_args = cls._handoff_args(original_args, handoff_path, shard)
            return {
                "shard_id": shard.shard_id,
                "task_type": payload["task_type"],
                "shard_type": payload["shard_type"],
                "executor_type": payload["executor_type"],
                "executor_profile": payload["executor_profile"],
                "isolation": payload["isolation"],
                "execution_body": payload["execution_body"],
                "lifecycle": payload["lifecycle"],
                "handoff_path": str(handoff_path),
                "context_digest_path": str(digest_path),
                "context_index_path": str(index_path),
                "context_gaps": payload["context_gaps"],
                "allowed_read_paths": payload["allowed_read_paths"],
                "allowed_write_paths": payload["allowed_write_paths"],
                "scope": payload["scope"],
                "task_status_update": payload["task_status_update"],
                "validation_commands": payload["validation_commands"],
                "task_ids": shard.task_ids,
                "task_classification": payload["task_classification"],
                "args": shard_args,
            }

        worker_count = min(len(shards), (os.cpu_count() or 1))
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            return list(executor.map(write_one, shards))

    @classmethod
    def _handoff_payload(
        cls,
        project_root: Path,
        feature_dir: Path,
        shard: TaskShard,
        handoff_path: Path,
        index_path: Path,
        digest_path: Path,
        receipt_path: Path,
        source_refs: list[dict[str, Any]],
        context_gaps: list[str],
        context_notes: list[str],
    ) -> dict[str, Any]:
        feature_ref = cls._display_path(project_root, feature_dir)
        index_ref = cls._display_path(project_root, index_path)
        digest_ref = cls._display_path(project_root, digest_path)
        receipt_ref = cls._display_path(project_root, receipt_path)
        tasks_ref = cls._display_path(project_root, feature_dir / "tasks.md")
        allowed_read_paths = list(
            dict.fromkeys([digest_ref, index_ref, tasks_ref, *shard.paths])
        )
        allowed_write_paths = list(dict.fromkeys([receipt_ref, *shard.paths]))
        executor_profile = shard.executor_profile

        return {
            "contract_type": "speckit.implement.handoff.v2",
            "shard_id": shard.shard_id,
            "task_type": shard.shard_type,
            "shard_type": shard.shard_type,
            "executor_type": executor_profile["id"],
            "executor_profile": executor_profile,
            "task_classification": [
                {
                    "task_id": task.task_id,
                    "task_type": task.task_type,
                    "phase": task.phase,
                    "parallel": task.parallel,
                }
                for task in shard.tasks
            ],
            "isolation": {
                "process": "fresh",
                "context": "fresh",
                "reuse": "never",
                "parallelism": "safe" if shard.safe_parallel else "none",
                "topo_layers": shard.topo_layers,
                "phases": shard.phases,
            },
            "execution_body": {
                "kind": "independent_cli_invocation",
                "command": "speckit.implement",
                "handoff_argument": (
                    f"Use handoff JSON {cls._display_path(project_root, handoff_path)}"
                ),
            },
            "lifecycle": {
                "state": "created",
                "creation": "before_shard_dispatch",
                "reuse": "never",
                "destruction": "after_shard_result",
            },
            "feature_dir": feature_ref,
            "task_ids": shard.task_ids,
            "task_text": [task.text for task in shard.tasks],
            "context_digest_path": digest_ref,
            "context_index_path": index_ref,
            "allowed_read_paths": allowed_read_paths,
            "allowed_write_paths": allowed_write_paths,
            "scope": {
                "read": allowed_read_paths,
                "write": allowed_write_paths,
                "validation": shard.validation_commands,
            },
            "task_status_update": {
                "mode": "receipt",
                "receipt_path": receipt_ref,
                "committer": "orchestrator",
                "contract_type": "speckit.implement.receipt.v1",
                "required_fields": [
                    "contract_type",
                    "shard_id",
                    "task_ids",
                    "completed_task_ids",
                ],
            },
            "required_context_refs": [digest_ref],
            "source_refs": source_refs,
            "context_gaps": context_gaps,
            "context_notes": context_notes,
            "validation_commands": shard.validation_commands,
            "forbidden_actions": [
                "Do not modify tasks.md; write the task_status_update receipt only after validation passes.",
                "Do not modify paths outside allowed_write_paths unless the task explicitly requires a generated adjacent file.",
                "Do not read full spec.md, plan.md, or contracts by default; request a narrower digest when context_gaps are present.",
                "Do not revert user changes or unrelated work.",
            ],
        }

    @classmethod
    def _build_context_index(
        cls,
        project_root: Path,
        feature_dir: Path,
        tasks: list[ParsedTask],
    ) -> dict[str, Any]:
        docs: list[Path] = [feature_dir / name for name in ("spec.md", "plan.md", "tasks.md")]
        for optional_name in (
            "data-model.md",
            "research.md",
            "quickstart.md",
            "class-diagram.md",
            "test-plan.md",
        ):
            optional_path = feature_dir / optional_name
            if optional_path.is_file():
                docs.append(optional_path)
        contracts_dir = feature_dir / "contracts"
        if contracts_dir.is_dir():
            docs.extend(sorted(path for path in contracts_dir.rglob("*") if path.is_file()))

        documents: dict[str, Any] = {}
        for path in docs:
            rel = cls._display_path(project_root, path)
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except OSError:
                lines = []
            documents[rel] = {
                "line_count": len(lines),
                "headings": cls._heading_index(lines),
                "path_mentions": cls._path_mentions(lines),
            }

        return {
            "contract_type": "speckit.implement.context-index.v1",
            "feature_dir": cls._display_path(project_root, feature_dir),
            "documents": documents,
            "tasks": [
                {
                    "task_id": task.task_id,
                    "phase": task.phase,
                    "parallel": task.parallel,
                    "paths": task.paths,
                    "validation_commands": task.validation_commands,
                    "topo_layer": task.topo_layer,
                    "task_type": task.task_type,
                    "text": task.text,
                }
                for task in tasks
            ],
        }

    @staticmethod
    def _heading_index(lines: list[str]) -> list[dict[str, Any]]:
        headings: list[dict[str, Any]] = []
        for idx, line in enumerate(lines, start=1):
            match = re.match(r"^(?P<marks>#{1,6})\s+(?P<title>.+?)\s*$", line)
            if match:
                headings.append(
                    {
                        "line": idx,
                        "level": len(match.group("marks")),
                        "title": match.group("title").strip(),
                    }
                )
        return headings

    @classmethod
    def _path_mentions(cls, lines: list[str]) -> dict[str, list[int]]:
        mentions: dict[str, list[int]] = {}
        for idx, line in enumerate(lines, start=1):
            for path in cls._extract_paths(line):
                mentions.setdefault(path, []).append(idx)
        return mentions

    @classmethod
    def _context_digest(
        cls,
        project_root: Path,
        feature_dir: Path,
        shard: TaskShard,
        context_index: dict[str, Any],
    ) -> tuple[str, list[dict[str, Any]], list[str], list[str]]:
        query_terms = cls._query_terms(shard)
        snippets: list[dict[str, Any]] = []
        required_contexts: list[dict[str, Any]] = []
        source_refs: list[dict[str, Any]] = []
        context_gaps: list[str] = []
        context_notes: list[str] = []
        matched_documents: set[str] = set()
        outlined_documents: set[str] = set()

        documents = context_index.get("documents", {})
        for rel_path in sorted(documents):
            path = project_root / rel_path
            if not path.is_file():
                continue
            lines = path.read_text(encoding="utf-8").splitlines()
            ranges = cls._matching_ranges(lines, query_terms)
            if ranges:
                matched_documents.add(rel_path)
                for start, end in ranges[:3]:
                    text = "\n".join(lines[start - 1 : end])
                    snippets.append({"path": rel_path, "start": start, "end": end, "text": text})
                    source_refs.append({"path": rel_path, "lines": [start, end]})
            elif rel_path.endswith(("class-diagram.md", "contracts/sequences.md", "test-plan.md")):
                required_context = cls._required_context_for_digest(lines)
                if required_context:
                    required_contexts.append(
                        {
                            "path": rel_path,
                            "start": 1,
                            "end": len(lines),
                            "text": required_context,
                        }
                    )
            elif rel_path.endswith(("spec.md", "plan.md")):
                outline = cls._outline_for_digest(documents.get(rel_path, {}))
                if outline:
                    outlined_documents.add(rel_path)
                    snippets.append(
                        {
                            "path": rel_path,
                            "start": 1,
                            "end": 1,
                            "text": outline,
                            "outline_only": True,
                        }
                    )
                required_context = cls._blocking_context_for_digest(lines)
                if required_context:
                    required_contexts.append(
                        {
                            "path": rel_path,
                            "start": 1,
                            "end": len(lines),
                            "text": required_context,
                        }
                    )

        for required_doc in ("spec.md", "plan.md"):
            rel = cls._display_path(project_root, feature_dir / required_doc)
            if rel not in matched_documents and rel not in outlined_documents:
                context_gaps.append(
                    f"No digest context was found in {rel}; request a narrower digest "
                    "instead of reading the full document."
                )
            elif rel in outlined_documents and rel not in matched_documents:
                context_notes.append(
                    f"No task/path-specific snippet was found in {rel}; the digest "
                    "includes outline plus blocking required context when present."
                )

        digest_text = cls._render_digest(
            feature_dir, shard, snippets, required_contexts, context_gaps, context_notes
        )
        return (digest_text, source_refs, context_gaps, context_notes)

    @classmethod
    def _query_terms(cls, shard: TaskShard) -> list[str]:
        terms: dict[str, None] = {}
        for task in shard.tasks:
            for value in (task.task_id, task.phase):
                if value:
                    terms.setdefault(value.lower(), None)
            for path in task.paths:
                terms.setdefault(path.lower(), None)
                name = PurePosixPath(path).name
                if name:
                    terms.setdefault(name.lower(), None)
                stem = PurePosixPath(path).stem
                if stem and len(stem) >= 3:
                    terms.setdefault(stem.lower(), None)
        return [term for term in terms if len(term) >= 3]

    @staticmethod
    def _matching_ranges(lines: list[str], terms: list[str]) -> list[tuple[int, int]]:
        ranges: list[tuple[int, int]] = []
        for idx, line in enumerate(lines, start=1):
            lowered = line.lower()
            if any(term in lowered for term in terms):
                start = max(1, idx - _SNIPPET_CONTEXT_LINES)
                end = min(len(lines), idx + _SNIPPET_CONTEXT_LINES)
                if ranges and start <= ranges[-1][1] + 1:
                    ranges[-1] = (ranges[-1][0], max(ranges[-1][1], end))
                else:
                    ranges.append((start, end))
        return ranges

    @staticmethod
    def _outline_for_digest(document: dict[str, Any]) -> str:
        headings = document.get("headings", [])
        if not headings:
            return ""
        rendered = ["Document outline only:"]
        for heading in headings[:20]:
            rendered.append(
                f"L{heading.get('line')}: {'#' * int(heading.get('level', 1))} {heading.get('title')}"
            )
        return "\n".join(rendered)

    @staticmethod
    def _required_context_for_digest(lines: list[str]) -> str:
        return "\n".join(line.rstrip() for line in lines).strip()

    @classmethod
    def _blocking_context_for_digest(cls, lines: list[str]) -> str:
        ranges = cls._matching_ranges(lines, ["needs clarification"])
        blocks: list[str] = []
        for start, end in ranges[:5]:
            blocks.append("\n".join(lines[start - 1 : end]))
        return "\n\n".join(block.strip() for block in blocks if block.strip())

    @staticmethod
    def _render_digest(
        feature_dir: Path,
        shard: TaskShard,
        snippets: list[dict[str, Any]],
        required_contexts: list[dict[str, Any]],
        context_gaps: list[str],
        context_notes: list[str],
    ) -> str:
        parts = [
            "# Spec Kit Implement Context Digest",
            "",
            f"Feature: {feature_dir}",
            f"Shard: {shard.shard_id}",
            f"Task IDs: {', '.join(shard.task_ids)}",
            "",
            "## Tasks",
            *[f"- {task.text}" for task in shard.tasks],
            "",
            "## Allowed Write Paths",
            *[f"- {path}" for path in shard.paths],
            "",
            "## Validation Commands",
            *[f"- {command}" for command in shard.validation_commands],
            "",
            "## Context Snippets",
        ]
        for snippet in snippets:
            parts.extend(
                [
                    "",
                    f"### {snippet['path']}:{snippet['start']}-{snippet['end']}",
                    "```text",
                    snippet["text"],
                    "```",
                ]
            )
        if required_contexts:
            parts.extend(["", "## Required Context"])
            for item in required_contexts:
                parts.extend(
                    [
                        "",
                        f"### {item['path']}:required",
                        "```text",
                        item["text"],
                        "```",
                    ]
                )
        if context_gaps:
            parts.extend(["", "## Context Gaps", *[f"- {gap}" for gap in context_gaps]])
        if context_notes:
            parts.extend(["", "## Context Notes", *[f"- {note}" for note in context_notes]])
        return "\n".join(parts).rstrip() + "\n"

    @staticmethod
    def _handoff_args(original_args: str, handoff_path: Path, shard: TaskShard) -> str:
        prefix = f"{original_args.strip()} " if original_args.strip() else ""
        task_ids = ", ".join(shard.task_ids)
        return (
            f"{prefix}Use handoff JSON {handoff_path}. "
            f"Execute only task IDs: {task_ids}."
        )

    @staticmethod
    def _display_path(project_root: Path, path: Path) -> str:
        try:
            return str(path.resolve().relative_to(project_root))
        except ValueError:
            return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build Spec Kit implementation handoff shards."
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Spec Kit project root. Defaults to the current directory.",
    )
    parser.add_argument(
        "--args",
        default="",
        help="Original implementation arguments to forward to each shard.",
    )
    parser.add_argument(
        "--max-shards",
        type=int,
        default=8,
        help="Maximum number of handoff shards to generate.",
    )
    parser.add_argument(
        "--run-id",
        default="manual",
        help="Workflow run id used to namespace generated handoff files.",
    )
    parsed = parser.parse_args(argv)

    try:
        output = TaskShardBuilder.build(
            Path(parsed.project_root),
            parsed.args,
            parsed.max_shards,
            parsed.run_id,
        )
    except ValueError as exc:
        print(json.dumps({"error": str(exc), "items": []}), file=sys.stderr)
        return 1

    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
