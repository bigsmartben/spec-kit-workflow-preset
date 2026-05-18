from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
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
                self.assertEqual("none", item["isolation"]["parallelism"])
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
        self.assertIn("## 1.0.0", changelog)
        self.assertIn("subagent profile matrix", changelog)
        self.assertIn("digest", changelog)


if __name__ == "__main__":
    unittest.main()
