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
PLAN_COMMAND_PATH = REPO_ROOT / "commands" / "speckit.plan.md"
TASKS_COMMAND_PATH = REPO_ROOT / "commands" / "speckit.tasks.md"
IMPLEMENT_COMMAND_PATH = REPO_ROOT / "commands" / "speckit.implement.md"
PLAN_TEMPLATE_PATH = REPO_ROOT / "templates" / "plan-template.md"
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

    def test_readme_contract(self) -> None:
        readme = README_PATH.read_text(encoding="utf-8")

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
        self.assertIn("Files Written", readme)
        self.assertIn("Safety Boundaries", readme)


if __name__ == "__main__":
    unittest.main()
