from __future__ import annotations

import contextlib
import io
import importlib.util
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
PRESET_PATH = REPO_ROOT / "preset.yml"
README_PATH = REPO_ROOT / "README.md"
CHANGELOG_PATH = REPO_ROOT / "CHANGELOG.md"
PLAN_COMMAND_PATH = REPO_ROOT / "commands" / "speckit.plan.md"
TASKS_COMMAND_PATH = REPO_ROOT / "commands" / "speckit.tasks.md"
IMPLEMENT_COMMAND_PATH = REPO_ROOT / "commands" / "speckit.implement.md"
PLAN_TEMPLATE_PATH = REPO_ROOT / "templates" / "plan-template.md"
REQUIREMENTS_DEV_PATH = REPO_ROOT / "requirements-dev.txt"
WORKFLOW_PATH = (
    REPO_ROOT
    / "workflows"
    / "speckit-orchestrated-implement"
    / "workflow.yml"
)


def load_build_task_shards():
    module_path = REPO_ROOT / "scripts" / "build-task-shards.py"
    spec = importlib.util.spec_from_file_location("build_task_shards", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_orchestrated_implement():
    module_path = REPO_ROOT / "scripts" / "run-orchestrated-implement.py"
    spec = importlib.util.spec_from_file_location("run_orchestrated_implement", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class PresetContractTests(unittest.TestCase):
    def test_preset_manifest_contract(self) -> None:
        data = yaml.safe_load(PRESET_PATH.read_text(encoding="utf-8"))

        self.assertEqual("1.0", data["schema_version"])
        self.assertEqual("workflow-preset", data["preset"]["id"])
        self.assertEqual("Workflow Preset", data["preset"]["name"])
        self.assertEqual("1.0.0", data["preset"]["version"])
        self.assertEqual(
            "Plan design artifacts and orchestrated implementation workflow",
            data["preset"]["description"],
        )
        self.assertEqual("bigsmartben", data["preset"]["author"])
        self.assertEqual(
            "https://github.com/bigsmartben/spec-kit-workflow-preset",
            data["preset"]["repository"],
        )
        self.assertEqual("MIT", data["preset"]["license"])
        self.assertEqual(">=0.8.10.dev0", data["requires"]["speckit_version"])
        self.assertEqual(
            ["planning", "design", "implementation", "orchestration", "workflow", "spec-kit"],
            data["tags"],
        )

        provides = data["provides"]["templates"]
        self.assertEqual(4, len(provides))
        entries = {entry["name"]: entry for entry in provides}

        plan_template = entries["plan-template"]
        self.assertEqual("template", plan_template["type"])
        self.assertEqual("templates/plan-template.md", plan_template["file"])
        self.assertEqual("plan-template", plan_template["replaces"])
        self.assertEqual("wrap", plan_template["strategy"])

        for command_name in ("speckit.plan", "speckit.tasks"):
            command = entries[command_name]
            self.assertEqual("command", command["type"])
            self.assertEqual(f"commands/{command_name}.md", command["file"])
            self.assertEqual(command_name, command["replaces"])
            self.assertEqual("wrap", command["strategy"])

        implement = entries["speckit.implement"]
        self.assertEqual("command", implement["type"])
        self.assertEqual("commands/speckit.implement.md", implement["file"])
        self.assertEqual("speckit.implement", implement["replaces"])
        self.assertEqual("replace", implement["strategy"])
        self.assertEqual(
            [
                "scripts/build-task-shards.py",
                "scripts/run-orchestrated-implement.py",
                "workflows/speckit-orchestrated-implement/workflow.yml",
            ],
            data["provides"]["files"],
        )

        workflows = data["provides"]["workflows"]
        self.assertEqual(1, len(workflows))
        self.assertEqual("speckit-orchestrated-implement", workflows[0]["id"])
        self.assertEqual(
            "workflows/speckit-orchestrated-implement/workflow.yml",
            workflows[0]["file"],
        )

    def test_plan_command_wrapper_contract(self) -> None:
        command = PLAN_COMMAND_PATH.read_text(encoding="utf-8")

        self.assertIn("{CORE_TEMPLATE}", command)
        self.assertIn("class-diagram.md", command)
        self.assertIn("contracts/sequences.md", command)
        self.assertIn("test-plan.md", command)
        self.assertIn("strategy: wrap", command)
        self.assertIn("Generate the three design artifacts only when useful", command)
        self.assertIn("Keep `plan.md` as summary/navigation", command)
        self.assertIn("final report must list generated artifacts", command)
        self.assertNotIn("speckit.tasks", command)
        self.assertNotIn("speckit.implement", command)

    def test_plan_template_navigation_contract(self) -> None:
        template = PLAN_TEMPLATE_PATH.read_text(encoding="utf-8")

        self.assertIn("{CORE_TEMPLATE}", template)
        self.assertIn("## Design Artifacts", template)
        self.assertIn("./class-diagram.md", template)
        self.assertIn("./contracts/sequences.md", template)
        self.assertIn("./test-plan.md", template)
        self.assertIn("./data-model.md", template)
        self.assertIn("./contracts/", template)
        self.assertIn("./quickstart.md", template)

    def test_tasks_command_wrapper_contract(self) -> None:
        tasks = TASKS_COMMAND_PATH.read_text(encoding="utf-8")

        self.assertIn("{CORE_TEMPLATE}", tasks)
        self.assertIn("class-diagram.md", tasks)
        self.assertIn("contracts/sequences.md", tasks)
        self.assertIn("test-plan.md", tasks)
        self.assertIn("strategy: wrap", tasks)
        self.assertIn("implementation, integration, orchestration", tasks)
        self.assertIn("existing checklist format and user-story organization", tasks)

    def test_implement_command_replacement_contract(self) -> None:
        command = IMPLEMENT_COMMAND_PATH.read_text(encoding="utf-8")

        self.assertNotIn("{CORE_TEMPLATE}", command)
        self.assertNotIn("strategy: wrap", command)
        self.assertIn(
            "uv run .specify/presets/workflow-preset/scripts/run-orchestrated-implement.py",
            command,
        )
        self.assertNotIn(
            ".specify/presets/workflow-preset/workflows/speckit-orchestrated-implement/workflow.yml",
            command,
        )
        self.assertIn("Use handoff JSON <path>", command)
        self.assertIn("class-diagram.md", command)
        self.assertIn("contracts/sequences.md", command)
        self.assertIn("test-plan.md", command)
        self.assertIn("Execute exactly one shard", command)
        self.assertIn("Subagent Matrix", command)
        self.assertIn("setup -> setup-worker", command)
        self.assertIn("test -> test-worker", command)
        self.assertIn("implementation -> implementation-worker", command)
        self.assertIn("integration -> integration-worker", command)
        self.assertIn("validation -> validation-worker", command)
        self.assertIn("cleanup -> cleanup-worker", command)
        self.assertIn("fresh process", command)
        self.assertIn("fresh context", command)
        self.assertIn("Do not edit `tasks.md`", command)
        self.assertIn("speckit.implement.receipt.v1", command)
        self.assertIn("isolation.parallelism", command)
        self.assertNotIn("Heartbeat", command)
        self.assertNotIn("300 seconds", command)

    def test_dispatch_uses_script_managed_streaming_without_integration_timeout(self) -> None:
        module = load_orchestrated_implement()

        calls: dict[str, object] = {}

        class FakeIntegration:
            key = Path(sys.executable).name

            def build_command_invocation(self, command_name: str, args: str = "") -> str:
                calls["command_name"] = command_name
                calls["args"] = args
                return f"/{command_name} {args}".strip()

            def build_exec_args(
                self,
                prompt: str,
                *,
                model: str | None = None,
                output_json: bool = True,
            ) -> list[str]:
                calls["prompt"] = prompt
                calls["model"] = model
                calls["output_json"] = output_json
                return [
                    sys.executable,
                    "-c",
                    "print('fake dispatch complete')",
                ]

            def dispatch_command(self, *args: object, **kwargs: object) -> dict[str, object]:
                raise AssertionError("dispatch_command should not be used")

        fake_package = types.ModuleType("specify_cli")
        fake_integrations = types.ModuleType("specify_cli.integrations")
        fake_integrations.get_integration = lambda key: FakeIntegration()
        previous_package = sys.modules.get("specify_cli")
        previous_integrations = sys.modules.get("specify_cli.integrations")
        sys.modules["specify_cli"] = fake_package
        sys.modules["specify_cli.integrations"] = fake_integrations
        try:
            with tempfile.TemporaryDirectory() as tmp:
                result = module._dispatch_item(
                    {"shard_id": "S01-implementation-01", "args": "Use handoff JSON demo.json"},
                    "fake",
                    Path(tmp),
                    "demo-model",
                    Path(tmp) / "logs",
                    heartbeat_interval=60.0,
                )
                self.assertEqual(0, result["exit_code"])
                self.assertNotIn("stdout", result)
                self.assertNotIn("stderr", result)
                self.assertIn("fake dispatch complete", result["stdout_tail"])
                self.assertTrue(Path(result["stdout_log_path"]).is_file())
                self.assertIn("stderr_tail", result)
                self.assertIn("stderr_log_path", result)
                self.assertIn("output_truncated", result)
        finally:
            if previous_package is None:
                sys.modules.pop("specify_cli", None)
            else:
                sys.modules["specify_cli"] = previous_package
            if previous_integrations is None:
                sys.modules.pop("specify_cli.integrations", None)
            else:
                sys.modules["specify_cli.integrations"] = previous_integrations

        self.assertEqual(False, calls["output_json"])
        self.assertEqual("speckit.implement", calls["command_name"])
        self.assertEqual("Use handoff JSON demo.json", calls["args"])
        self.assertEqual("/speckit.implement Use handoff JSON demo.json", calls["prompt"])
        self.assertEqual("none", result["dispatch_process"]["timeout"])

    def test_logged_subprocess_writes_full_output_without_echoing_to_main_stdout(self) -> None:
        module = load_orchestrated_implement()

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            script = tmp_path / "noisy_then_done.py"
            script.write_text(
                "import time\n"
                "print('hidden child output')\n"
                "time.sleep(0.2)\n"
                "print('child complete')\n",
                encoding="utf-8",
            )
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                result = module._run_logged_subprocess(
                    [sys.executable, str(script)],
                    tmp_path,
                    "S01-implementation-01",
                    tmp_path / "logs",
                    heartbeat_interval=0.05,
                )
            self.assertIn(
                "hidden child output",
                Path(result["stdout_log_path"]).read_text(encoding="utf-8"),
            )

        self.assertEqual(0, result["exit_code"])
        self.assertIn("child complete", result["stdout_tail"])
        self.assertNotIn("hidden child output", stdout.getvalue())
        self.assertNotIn("child complete", stdout.getvalue())
        self.assertIn("shard_heartbeat", stdout.getvalue())

    def test_logged_subprocess_starts_child_in_new_session(self) -> None:
        module = load_orchestrated_implement()
        original_popen = module.subprocess.Popen
        calls: dict[str, object] = {}

        def fake_popen(*args: object, **kwargs: object) -> object:
            calls["popen_kwargs"] = kwargs
            raise KeyboardInterrupt

        module.subprocess.Popen = fake_popen
        try:
            result = module._run_logged_subprocess(
                [sys.executable, "-c", "print('x')"],
                Path("/tmp"),
                "S01-implementation-01",
                Path("/tmp/logs"),
                heartbeat_interval=0.01,
            )
        finally:
            module.subprocess.Popen = original_popen

        self.assertEqual(130, result["exit_code"])
        self.assertTrue(calls["popen_kwargs"]["start_new_session"])

    def test_process_group_cleanup_terminates_child_session(self) -> None:
        module = load_orchestrated_implement()
        original_killpg = module.os.killpg
        original_getpgid = module.os.getpgid
        calls: dict[str, object] = {}

        class FakeProcess:
            pid = 4321

            def wait(self, timeout: float | None = None) -> int:
                calls["wait_timeout"] = timeout
                return 0

        def fake_killpg(pgid: int, sig: int) -> None:
            calls["killpg"] = (pgid, sig)

        def fake_getpgid(pid: int) -> int:
            calls["getpgid_pid"] = pid
            return 9876

        module.os.killpg = fake_killpg
        module.os.getpgid = fake_getpgid
        try:
            module._terminate_process_group(FakeProcess())
        finally:
            module.os.killpg = original_killpg
            module.os.getpgid = original_getpgid

        self.assertEqual(4321, calls["getpgid_pid"])
        self.assertIn("killpg", calls)

    def test_dispatch_results_are_compacted_before_main_output(self) -> None:
        module = load_orchestrated_implement()

        compacted = module._compact_dispatch_result(
            {
                "shard_id": "S01-implementation-01",
                "exit_code": 0,
                "stdout_tail": "x" * 10000,
                "stderr_tail": "y" * 10000,
                "stdout_log_path": "logs/S01.stdout.log",
                "stderr_log_path": "logs/S01.stderr.log",
                "output_truncated": True,
                "post_dispatch_verification": {"exit_code": 0},
            }
        )

        self.assertNotIn("stdout_tail", compacted)
        self.assertNotIn("stderr_tail", compacted)
        self.assertEqual("logs/S01.stdout.log", compacted["stdout_log_path"])
        self.assertEqual("logs/S01.stderr.log", compacted["stderr_log_path"])

    def test_failed_dispatch_result_keeps_only_short_error_tail(self) -> None:
        module = load_orchestrated_implement()

        compacted = module._compact_dispatch_result(
            {
                "shard_id": "S02-implementation-01",
                "exit_code": 1,
                "stdout_tail": "x" * 10000,
                "stderr_tail": "error-" + "y" * 10000,
                "stdout_log_path": "logs/S02.stdout.log",
                "stderr_log_path": "logs/S02.stderr.log",
            }
        )

        self.assertNotIn("stdout_tail", compacted)
        self.assertIn("stderr_tail", compacted)
        self.assertLessEqual(len(compacted["stderr_tail"]), 2000)

    def test_build_dispatch_cli_args_uses_integration_framework_for_all_agents(self) -> None:
        module = load_orchestrated_implement()
        calls: dict[str, object] = {}

        class FakeIntegration:
            key = "copilot"

            def build_command_invocation(self, command_name: str, args: str = "") -> str:
                calls["command_name"] = command_name
                calls["args"] = args
                return f"integration-native:{command_name}:{args}"

            def build_exec_args(
                self,
                prompt: str,
                *,
                model: str | None = None,
                output_json: bool = True,
            ) -> list[str]:
                calls["prompt"] = prompt
                calls["model"] = model
                calls["output_json"] = output_json
                return ["copilot", "run", prompt, "--model", model or ""]

        args = module._build_dispatch_cli_args(
            FakeIntegration(),
            "Use handoff JSON demo.json",
            "demo-model",
        )

        self.assertEqual(
            [
                "copilot",
                "run",
                "integration-native:speckit.implement:Use handoff JSON demo.json",
                "--model",
                "demo-model",
            ],
            args,
        )
        self.assertEqual("speckit.implement", calls["command_name"])
        self.assertEqual("Use handoff JSON demo.json", calls["args"])
        self.assertEqual(
            "integration-native:speckit.implement:Use handoff JSON demo.json",
            calls["prompt"],
        )
        self.assertEqual(False, calls["output_json"])

    def test_dispatch_requires_spec_kit_integrations_without_agent_fallback(self) -> None:
        module = load_orchestrated_implement()
        original_add_site_packages = module._add_specify_tool_site_packages

        def fake_add_site_packages() -> bool:
            return False

        module._add_specify_tool_site_packages = fake_add_site_packages
        previous_package = sys.modules.pop("specify_cli", None)
        previous_integrations = sys.modules.pop("specify_cli.integrations", None)
        try:
            with tempfile.TemporaryDirectory() as tmp:
                result = module._dispatch_item(
                    {"shard_id": "S01-implementation-01", "args": "Use handoff JSON demo.json"},
                    "copilot",
                    Path(tmp),
                    "demo-model",
                    Path(tmp) / "logs",
                    heartbeat_interval=60.0,
                )
        finally:
            module._add_specify_tool_site_packages = original_add_site_packages
            if previous_package is not None:
                sys.modules["specify_cli"] = previous_package
            if previous_integrations is not None:
                sys.modules["specify_cli.integrations"] = previous_integrations

        self.assertEqual(1, result["exit_code"])
        self.assertIn("Unable to import Spec Kit integrations", result["error"])

    def test_workflow_uses_workflow_preset_install_path(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn(
            "uv run .specify/presets/workflow-preset/scripts/run-orchestrated-implement.py",
            workflow,
        )
        self.assertIn("run_id:", workflow)
        self.assertIn('--run-id "{{ inputs.run_id }}"', workflow)
        self.assertIn("--dry-run", workflow)
        self.assertIn("--model", workflow)
        self.assertNotIn('{{ run_id }}', workflow)
        self.assertNotIn(".specify/presets/implement/", workflow)

    def test_shard_context_includes_design_artifacts(self) -> None:
        module = load_build_task_shards()

        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp) / "project"
            feature_dir = project_root / "specs" / "001-demo"
            (project_root / ".specify").mkdir(parents=True)
            feature_dir.mkdir(parents=True)
            (feature_dir / "contracts").mkdir()
            (project_root / ".specify" / "feature.json").write_text(
                json.dumps({"feature_directory": "specs/001-demo"}) + "\n",
                encoding="utf-8",
            )
            (feature_dir / "spec.md").write_text("# Spec\n", encoding="utf-8")
            (feature_dir / "plan.md").write_text("# Plan\n", encoding="utf-8")
            (feature_dir / "class-diagram.md").write_text(
                "# Class Diagram\n\nOnboardingService composes ProfileRepository.\n",
                encoding="utf-8",
            )
            (feature_dir / "contracts" / "sequences.md").write_text(
                "# Sequences\n\nClient calls API, then API emits OnboardingCompleted.\n",
                encoding="utf-8",
            )
            (feature_dir / "test-plan.md").write_text(
                "# Test Plan\n\nValidate happy path and retry failure handling.\n",
                encoding="utf-8",
            )
            (feature_dir / "tasks.md").write_text(
                "# Tasks\n\n- [ ] T001 Implement onboarding in `src/onboarding.py`\n",
                encoding="utf-8",
            )

            output = module.TaskShardBuilder.build(project_root, "", 4, "contract")

            item = output["items"][0]
            digest = Path(item["context_digest_path"]).read_text(encoding="utf-8")
            index = json.loads(Path(item["context_index_path"]).read_text(encoding="utf-8"))

            self.assertIn("Class Diagram", digest)
            self.assertIn("OnboardingService", digest)
            self.assertIn("Sequences", digest)
            self.assertIn("OnboardingCompleted", digest)
            self.assertIn("Test Plan", digest)
            self.assertIn("retry failure handling", digest)
            self.assertIn(
                "specs/001-demo/class-diagram.md",
                index["documents"],
            )
            self.assertIn(
                "specs/001-demo/contracts/sequences.md",
                index["documents"],
            )
            self.assertIn("specs/001-demo/test-plan.md", index["documents"])

    def test_shard_handoffs_can_be_written_concurrently(self) -> None:
        module = load_build_task_shards()

        original_context_digest = module.TaskShardBuilder._context_digest
        call_order: list[str] = []

        def fake_context_digest(project_root, feature_dir, shard, context_index):
            call_order.append(shard.shard_id)
            return (
                f"# Digest for {shard.shard_id}\n",
                [],
                [],
                [],
            )

        module.TaskShardBuilder._context_digest = staticmethod(fake_context_digest)
        try:
            with tempfile.TemporaryDirectory() as tmp:
                project_root = Path(tmp) / "project"
                feature_dir = project_root / "specs" / "001-demo"
                (project_root / ".specify").mkdir(parents=True)
                feature_dir.mkdir(parents=True)
                (project_root / ".specify" / "feature.json").write_text(
                    json.dumps({"feature_directory": "specs/001-demo"}) + "\n",
                    encoding="utf-8",
                )
                (feature_dir / "spec.md").write_text("# Spec\n", encoding="utf-8")
                (feature_dir / "plan.md").write_text("# Plan\n", encoding="utf-8")
                (feature_dir / "tasks.md").write_text(
                    "# Tasks\n\n"
                    "## Setup\n"
                    "- [ ] T001 Configure project in `pyproject.toml`\n\n"
                    "## Tests\n"
                    "- [ ] T002 [P] Add contract test in `tests/test_app.py`\n\n"
                    "## Core Implementation\n"
                    "- [ ] T003 Implement app in `src/app.py`\n\n"
                    "## Integration\n"
                    "- [ ] T004 Wire API integration in `src/api.py`\n\n",
                    encoding="utf-8",
                )

                output = module.TaskShardBuilder.build(project_root, "", 8, "run")

            self.assertGreaterEqual(len(call_order), 2)
            self.assertEqual(["setup", "test", "implementation", "integration"], [item["task_type"] for item in output["items"]])
        finally:
            module.TaskShardBuilder._context_digest = original_context_digest

    def test_shard_handoff_writer_submits_one_parallel_job_per_shard(self) -> None:
        module = load_build_task_shards()

        calls: dict[str, object] = {}
        original_executor = module.ThreadPoolExecutor

        class RecordingExecutor:
            def __init__(self, max_workers: int) -> None:
                calls["max_workers"] = max_workers

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb) -> None:
                return None

            def map(self, fn, shards):
                shard_list = list(shards)
                calls["shard_count"] = len(shard_list)
                return [fn(shard) for shard in shard_list]

        module.ThreadPoolExecutor = RecordingExecutor
        try:
            with tempfile.TemporaryDirectory() as tmp:
                project_root = Path(tmp) / "project"
                feature_dir = project_root / "specs" / "001-demo"
                (project_root / ".specify").mkdir(parents=True)
                feature_dir.mkdir(parents=True)
                (project_root / ".specify" / "feature.json").write_text(
                    json.dumps({"feature_directory": "specs/001-demo"}) + "\n",
                    encoding="utf-8",
                )
                (feature_dir / "spec.md").write_text("# Spec\n", encoding="utf-8")
                (feature_dir / "plan.md").write_text("# Plan\n", encoding="utf-8")
                (feature_dir / "tasks.md").write_text(
                    "# Tasks\n\n"
                    "## Setup\n"
                    "- [ ] T001 Configure project in `pyproject.toml`\n\n"
                    "## Tests\n"
                    "- [ ] T002 [P] Add contract test in `tests/test_app.py`\n\n"
                    "## Core Implementation\n"
                    "- [ ] T003 Implement app in `src/app.py`\n",
                    encoding="utf-8",
                )

                output = module.TaskShardBuilder.build(project_root, "", 8, "run")
        finally:
            module.ThreadPoolExecutor = original_executor

        self.assertEqual(output["item_count"], calls["shard_count"])
        self.assertGreaterEqual(calls["max_workers"], 2)

    def test_shard_handoff_uses_receipt_instead_of_tasks_md_write_access(self) -> None:
        module = load_build_task_shards()

        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp) / "project"
            feature_dir = project_root / "specs" / "001-demo"
            (project_root / ".specify").mkdir(parents=True)
            feature_dir.mkdir(parents=True)
            (project_root / ".specify" / "feature.json").write_text(
                json.dumps({"feature_directory": "specs/001-demo"}) + "\n",
                encoding="utf-8",
            )
            (feature_dir / "spec.md").write_text("# Spec\n", encoding="utf-8")
            (feature_dir / "plan.md").write_text("# Plan\n", encoding="utf-8")
            (feature_dir / "tasks.md").write_text(
                "# Tasks\n\n- [ ] T001 Implement demo in `src/demo.py`\n",
                encoding="utf-8",
            )

            output = module.TaskShardBuilder.build(project_root, "", 4, "run")

            item = output["items"][0]
            payload = json.loads(Path(item["handoff_path"]).read_text(encoding="utf-8"))
            self.assertNotIn("specs/001-demo/tasks.md", item["allowed_write_paths"])
            self.assertIn("specs/001-demo/tasks.md", item["allowed_read_paths"])
            self.assertIn("task_status_update", item)
            self.assertEqual("receipt", item["task_status_update"]["mode"])
            self.assertEqual("orchestrator", item["task_status_update"]["committer"])
            self.assertIn(
                item["task_status_update"]["receipt_path"],
                item["allowed_write_paths"],
            )
            self.assertEqual(item["task_status_update"], payload["task_status_update"])

    def test_orchestrator_commits_completed_task_receipt_as_single_tasks_writer(self) -> None:
        module = load_orchestrated_implement()

        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp) / "project"
            feature_dir = project_root / "specs" / "001-demo"
            receipt_path = feature_dir / "handoffs" / "implement" / "run" / "results" / "S01.json"
            feature_dir.mkdir(parents=True)
            receipt_path.parent.mkdir(parents=True)
            tasks_path = feature_dir / "tasks.md"
            tasks_path.write_text(
                "# Tasks\n\n"
                "- [ ] T001 Implement demo in `src/demo.py`\n"
                "- [ ] T002 Implement other in `src/other.py`\n",
                encoding="utf-8",
            )
            receipt_path.write_text(
                json.dumps(
                    {
                        "contract_type": "speckit.implement.receipt.v1",
                        "shard_id": "S01-implementation-01",
                        "task_ids": ["T001"],
                        "completed_task_ids": ["T001"],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            item = {
                "shard_id": "S01-implementation-01",
                "task_ids": ["T001"],
                "task_status_update": {
                    "mode": "receipt",
                    "receipt_path": "specs/001-demo/handoffs/implement/run/results/S01.json",
                    "committer": "orchestrator",
                },
            }

            commit = module._commit_task_receipt(project_root, tasks_path, item)

            self.assertEqual(0, commit["exit_code"])
            self.assertEqual(["T001"], commit["completed_task_ids"])
            updated = tasks_path.read_text(encoding="utf-8")
            self.assertIn("- [x] T001 Implement demo", updated)
            self.assertIn("- [ ] T002 Implement other", updated)

    def test_parallel_scheduler_groups_only_non_overlapping_write_paths(self) -> None:
        module = load_orchestrated_implement()

        items = [
            {
                "shard_id": "S01",
                "allowed_write_paths": ["src/a.py"],
                "isolation": {"parallelism": "safe"},
            },
            {
                "shard_id": "S02",
                "allowed_write_paths": ["src/b.py"],
                "isolation": {"parallelism": "safe"},
            },
            {
                "shard_id": "S03",
                "allowed_write_paths": ["src"],
                "isolation": {"parallelism": "safe"},
            },
            {
                "shard_id": "S04",
                "allowed_write_paths": ["docs/readme.md"],
                "isolation": {"parallelism": "safe"},
            },
        ]

        layers = module._schedule_parallel_layer_ids(Path("/tmp/project"), items)

        self.assertEqual([["S01", "S02", "S04"], ["S03"]], layers)

    def test_parallel_scheduler_does_not_cross_sequential_barriers(self) -> None:
        module = load_orchestrated_implement()

        items = [
            {
                "shard_id": "S01",
                "allowed_write_paths": ["src/a.py"],
                "isolation": {"parallelism": "safe"},
            },
            {
                "shard_id": "S02",
                "allowed_write_paths": ["src/setup.py"],
                "isolation": {"parallelism": "none"},
            },
            {
                "shard_id": "S03",
                "allowed_write_paths": ["src/b.py"],
                "isolation": {"parallelism": "safe"},
            },
        ]

        layers = module._schedule_parallel_layer_ids(Path("/tmp/project"), items)

        self.assertEqual([["S01"], ["S02"], ["S03"]], layers)

    def test_parallel_scheduler_does_not_cross_manifest_topo_layers(self) -> None:
        module = load_orchestrated_implement()

        items = [
            {
                "shard_id": "S01",
                "allowed_write_paths": ["src/a.py"],
                "isolation": {"parallelism": "safe", "topo_layer": 1},
            },
            {
                "shard_id": "S02",
                "allowed_write_paths": ["src/b.py"],
                "isolation": {"parallelism": "safe", "topo_layer": 2},
            },
        ]

        layers = module._schedule_parallel_layer_ids(Path("/tmp/project"), items)

        self.assertEqual([["S01"], ["S02"]], layers)

    def test_layer_scope_ignores_orchestrator_log_files(self) -> None:
        module = load_orchestrated_implement()

        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp) / "project"
            log_dir = (
                project_root
                / "specs"
                / "001-demo"
                / "handoffs"
                / "implement"
                / "run"
                / "logs"
            )
            src_dir = project_root / "src"
            log_dir.mkdir(parents=True)
            src_dir.mkdir(parents=True)

            item = {
                "shard_id": "S01",
                "handoff_path": "specs/001-demo/handoffs/implement/run/S01.json",
                "allowed_write_paths": ["src/a.py"],
            }
            before = module._capture_workspace_state(
                project_root, {"allowed_write_paths": []}
            )

            (src_dir / "a.py").write_text("# changed\n", encoding="utf-8")
            (log_dir / "S01.stdout.log").write_text("hello\n", encoding="utf-8")

            verification = module._verify_layer_scope(project_root, [item], before)

            self.assertEqual(0, verification["exit_code"])
            self.assertEqual([], verification["scope_violations"])

    def test_orchestrator_rejects_receipt_missing_required_task_fields(self) -> None:
        module = load_orchestrated_implement()

        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp) / "project"
            feature_dir = project_root / "specs" / "001-demo"
            receipt_path = (
                feature_dir / "handoffs" / "implement" / "run" / "results" / "S01.json"
            )
            receipt_path.parent.mkdir(parents=True)
            tasks_path = feature_dir / "tasks.md"
            tasks_path.write_text(
                "# Tasks\n\n- [ ] T001 Implement demo in `src/demo.py`\n",
                encoding="utf-8",
            )
            receipt_path.write_text(
                json.dumps(
                    {
                        "contract_type": "speckit.implement.receipt.v1",
                        "shard_id": "S01-implementation-01",
                        "completed_task_ids": ["T001"],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            item = {
                "shard_id": "S01-implementation-01",
                "task_ids": ["T001"],
                "task_status_update": {
                    "mode": "receipt",
                    "receipt_path": "specs/001-demo/handoffs/implement/run/results/S01.json",
                    "committer": "orchestrator",
                },
            }

            commit = module._commit_task_receipt(project_root, tasks_path, item)

            self.assertEqual(1, commit["exit_code"])
            self.assertIn("missing required field", commit["error"])

    def test_shards_classify_tasks_and_executor_profiles(self) -> None:
        module = load_build_task_shards()

        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp) / "project"
            feature_dir = project_root / "specs" / "001-demo"
            (project_root / ".specify").mkdir(parents=True)
            feature_dir.mkdir(parents=True)
            (project_root / ".specify" / "feature.json").write_text(
                json.dumps({"feature_directory": "specs/001-demo"}) + "\n",
                encoding="utf-8",
            )
            (feature_dir / "spec.md").write_text(
                "# Spec\n\n## Demo\n\nUse src/app.py and tests/test_app.py.\n",
                encoding="utf-8",
            )
            (feature_dir / "plan.md").write_text(
                "# Plan\n\n## Demo\n\nUse src/app.py and tests/test_app.py.\n",
                encoding="utf-8",
            )
            (feature_dir / "tasks.md").write_text(
                "# Tasks\n\n"
                "## Setup\n"
                "- [ ] T001 Configure project in `pyproject.toml`\n\n"
                "## Tests\n"
                "- [ ] T002 [P] Add contract test in `tests/test_app.py`\n\n"
                "## Core Implementation\n"
                "- [ ] T003 Implement app in `src/app.py`\n\n"
                "## Integration\n"
                "- [ ] T004 Wire API integration in `src/api.py`\n\n"
                "## Validation\n"
                "- [ ] T005 Run quickstart validation in `quickstart.md`\n\n"
                "## Polish\n"
                "- [ ] T006 Update docs cleanup in `README.md`\n",
                encoding="utf-8",
            )

            output = module.TaskShardBuilder.build(project_root, "", 8, "contract")

            items = output["items"]
            self.assertEqual(6, len(items))
            expected = [
                ("setup", "setup-worker"),
                ("test", "test-worker"),
                ("implementation", "implementation-worker"),
                ("integration", "integration-worker"),
                ("validation", "validation-worker"),
                ("cleanup", "cleanup-worker"),
            ]
            for item, (task_type, executor_profile) in zip(items, expected):
                self.assertEqual(task_type, item["task_type"])
                self.assertEqual(task_type, item["shard_type"])
                self.assertEqual(executor_profile, item["executor_type"])
                self.assertEqual(executor_profile, item["executor_profile"]["id"])
                self.assertEqual("fresh", item["isolation"]["process"])
                self.assertEqual("fresh", item["isolation"]["context"])
                self.assertEqual("never", item["isolation"]["reuse"])
                expected_parallelism = "safe" if task_type == "test" else "none"
                self.assertEqual(expected_parallelism, item["isolation"]["parallelism"])
                self.assertEqual("created", item["lifecycle"]["state"])
                self.assertEqual(
                    task_type,
                    item["task_classification"][0]["task_type"],
                )

    def test_shard_digest_does_not_include_unmatched_full_spec_or_plan(self) -> None:
        module = load_build_task_shards()

        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp) / "project"
            feature_dir = project_root / "specs" / "001-demo"
            (project_root / ".specify").mkdir(parents=True)
            feature_dir.mkdir(parents=True)
            (project_root / ".specify" / "feature.json").write_text(
                json.dumps({"feature_directory": "specs/001-demo"}) + "\n",
                encoding="utf-8",
            )
            (feature_dir / "spec.md").write_text(
                "# Spec\n\n## Requirements\n\n"
                "UNMATCHED-SPEC-CONTENT must stay out of shard digest.\n",
                encoding="utf-8",
            )
            (feature_dir / "plan.md").write_text(
                "# Plan\n\n## Architecture\n\n"
                "UNMATCHED-PLAN-CONTENT must stay out of shard digest.\n",
                encoding="utf-8",
            )
            (feature_dir / "tasks.md").write_text(
                "# Tasks\n\n- [ ] T001 Implement demo in `src/demo.py`\n",
                encoding="utf-8",
            )

            output = module.TaskShardBuilder.build(project_root, "", 4, "contract")

            digest = Path(output["items"][0]["context_digest_path"]).read_text(
                encoding="utf-8"
            )
            self.assertIn("Document outline only:", digest)
            self.assertNotIn("UNMATCHED-SPEC-CONTENT", digest)
            self.assertNotIn("UNMATCHED-PLAN-CONTENT", digest)
            self.assertEqual([], output["items"][0]["context_gaps"])

    def test_directory_allowed_write_paths_allow_descendant_changes_only(self) -> None:
        module = load_orchestrated_implement()

        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp) / "project"
            src_dir = project_root / "src"
            src_dir.mkdir(parents=True)
            (src_dir / "existing.py").write_text("# existing\n", encoding="utf-8")

            item = {
                "shard_id": "S01-implement-01",
                "task_ids": [],
                "allowed_write_paths": ["src"],
            }
            before = module._capture_workspace_state(project_root, item)

            (src_dir / "new_file.py").write_text("# new\n", encoding="utf-8")
            verification = module._verify_shard_scope(project_root, item, before)
            self.assertEqual([], verification["scope_violations"])

            (src_dir / "existing.py").unlink()
            verification = module._verify_shard_scope(project_root, item, before)
            self.assertEqual([], verification["scope_violations"])

            (project_root / "other.py").write_text("# outside\n", encoding="utf-8")
            verification = module._verify_shard_scope(project_root, item, before)
            self.assertEqual(["other.py"], verification["scope_violations"])

    def test_readme_contract(self) -> None:
        readme = README_PATH.read_text(encoding="utf-8")
        changelog = CHANGELOG_PATH.read_text(encoding="utf-8")
        requirements = REQUIREMENTS_DEV_PATH.read_text(encoding="utf-8")

        self.assertIn("specify preset add workflow-preset --from", readme)
        self.assertIn("specify preset add --dev /path/to/workflow-preset", readme)
        self.assertIn("/speckit.plan", readme)
        self.assertIn("/speckit.tasks", readme)
        self.assertIn("/speckit.implement", readme)
        self.assertIn("class-diagram.md", readme)
        self.assertIn("contracts/sequences.md", readme)
        self.assertIn("test-plan.md", readme)
        self.assertIn("handoffs/implement", readme)
        self.assertIn("orchestrated implementation", readme)
        self.assertIn("Spec Kit CLI `>=0.8.10.dev0`", readme)
        self.assertIn("python3 -m pip install -r requirements-dev.txt", readme)
        self.assertIn("GitHub CLI `gh`", readme)
        self.assertIn("PyYAML", requirements)
        self.assertIn("Files Written", readme)
        self.assertIn("Safety Boundaries", readme)
        self.assertIn("Subagent Matrix", readme)
        self.assertIn("fresh process and fresh context", readme)
        self.assertIn("scripts/run-orchestrated-implement.py", readme)
        self.assertIn("--dry-run true --run-id manual", readme)
        self.assertIn("## 1.0.0", changelog)
        self.assertIn("subagent profile matrix", changelog)
        self.assertIn("digest", changelog)


if __name__ == "__main__":
    unittest.main()
