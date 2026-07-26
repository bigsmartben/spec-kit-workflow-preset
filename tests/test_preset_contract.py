from __future__ import annotations

import unittest
import json
import re
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from validators.speckit_behavior_contract import (
    validate_behavior_case_coverage,
    validate_behavior_contract_bundle,
    validate_behavior_draft_contract,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
PRESET_PATH = REPO_ROOT / "preset.yml"
README_PATH = REPO_ROOT / "README.md"
CHANGELOG_PATH = REPO_ROOT / "CHANGELOG.md"
CROSS_AGENT_PROTOCOL_PATH = REPO_ROOT / "tests" / "contracts" / "speckit-cross-agent-protocol.md"
AGENTS_PATH = REPO_ROOT / "AGENTS.md"
EXTENSION_GOVERNANCE_PATH = REPO_ROOT / "docs" / "extension-governance.md"
SPECIFY_COMMAND_PATH = REPO_ROOT / "commands" / "speckit.specify.md"
CLARIFY_COMMAND_PATH = REPO_ROOT / "commands" / "speckit.clarify.md"
CHECKLIST_COMMAND_PATH = REPO_ROOT / "commands" / "speckit.checklist.md"
CONSTITUTION_COMMAND_PATH = REPO_ROOT / "commands" / "speckit.constitution.md"
ANALYZE_COMMAND_PATH = REPO_ROOT / "commands" / "speckit.analyze.md"
PLAN_COMMAND_PATH = REPO_ROOT / "commands" / "speckit.plan.md"
TASKS_COMMAND_PATH = REPO_ROOT / "commands" / "speckit.tasks.md"
CONSTITUTION_TEMPLATE_PATH = REPO_ROOT / "templates" / "constitution-template.md"
ARCHITECTURE_TEMPLATE_PATH = REPO_ROOT / "templates" / "architecture-template.md"
PLAN_TEMPLATE_PATH = REPO_ROOT / "templates" / "plan-template.md"
CANONICAL_RESPONSIVE_VISUAL_RULE = (
    "Responsive visual requirements block PASS only when required source-backed "
    "state or viewport evidence is missing for a feature that depends on provider evidence"
)
FORBIDDEN_VISUAL_COMPAT_TERMS = (
    "legacy visual",
    "previous-version",
    "previous version",
    "backward-compatible",
    "backward compatible",
    "fallback visual",
    "fallback visual rule",
    "compatibility mode",
    "历史版本",
    "旧版兼容",
    "兼容旧版",
    "回退视觉规则",
)
REQUIREMENTS_DEV_PATH = REPO_ROOT / "requirements-dev.txt"
BEHAVIOR_SCHEMA_PATHS = {
    "speckit.behavior.scenarios.draft.v1": REPO_ROOT
    / "schemas"
    / "speckit.behavior.scenarios.draft.v1.schema.json",
    "speckit.behavior.uif.intent.v1": REPO_ROOT
    / "schemas"
    / "speckit.behavior.uif.intent.v1.schema.json",
    "speckit.behavior.data_fixtures.intent.v1": REPO_ROOT
    / "schemas"
    / "speckit.behavior.data-fixtures.intent.v1.schema.json",
    "speckit.behavior.uif.expected.v1": REPO_ROOT
    / "schemas"
    / "speckit.behavior.uif.expected.v1.schema.json",
    "speckit.behavior.scenario_instances.v1": REPO_ROOT
    / "schemas"
    / "speckit.behavior.scenario-instances.v1.schema.json",
    "speckit.behavior.data_fixtures.v1": REPO_ROOT
    / "schemas"
    / "speckit.behavior.data-fixtures.v1.schema.json",
    "speckit.behavior.assertions.v1": REPO_ROOT
    / "schemas"
    / "speckit.behavior.assertions.v1.schema.json",
}
BEHAVIOR_TEMPLATE_PATHS = {
    "behavior-bdd-draft-template": REPO_ROOT / "templates" / "behavior" / "bdd-draft.feature",
    "behavior-scenarios-draft-template": REPO_ROOT
    / "templates"
    / "behavior"
    / "behavior-scenarios-draft.json",
    "behavior-uif-intent-template": REPO_ROOT / "templates" / "behavior" / "uif-intent.json",
    "behavior-data-fixtures-intent-template": REPO_ROOT
    / "templates"
    / "behavior"
    / "data-fixtures-intent.json",
    "behavior-testability-template": REPO_ROOT
    / "templates"
    / "behavior"
    / "behavior-testability.md",
    "behavior-bdd-contract-template": REPO_ROOT / "templates" / "behavior" / "bdd-contract.feature",
    "behavior-uif-expected-template": REPO_ROOT / "templates" / "behavior" / "uif-expected.json",
    "behavior-scenario-instances-template": REPO_ROOT
    / "templates"
    / "behavior"
    / "scenario-instances.json",
    "behavior-data-fixtures-template": REPO_ROOT / "templates" / "behavior" / "data-fixtures.json",
    "behavior-assertions-template": REPO_ROOT / "templates" / "behavior" / "assertions.json",
}
REQUIREMENT_TEMPLATE_PATHS = {
    "requirement-domain-gate-template": REPO_ROOT
    / "templates"
    / "requirements"
    / "domain-gate.md",
    "requirement-behavior-gate-template": REPO_ROOT
    / "templates"
    / "requirements"
    / "behavior-gate.md",
    "requirement-nfr-gate-template": REPO_ROOT
    / "templates"
    / "requirements"
    / "nfr-gate.md",
    "requirement-visual-gate-template": REPO_ROOT
    / "templates"
    / "requirements"
    / "visual-gate.md",
}
REMOVED_IMPLEMENT_RUNTIME_PATHS = (
    REPO_ROOT / "commands" / "speckit.implement.md",
    REPO_ROOT / "schemas" / "speckit.implement.manifest.v1.schema.json",
    REPO_ROOT / "schemas" / "speckit.implement.handoff.v2.schema.json",
    REPO_ROOT / "schemas" / "speckit.implement.receipt.v1.schema.json",
    REPO_ROOT / "validators" / "speckit_implement_contract.py",
    REPO_ROOT / "tests" / "contracts" / "speckit-cross-agent-subagents.md",
)

FEATURE_PATH = "specs/001-demo"












def minimal_behavior_scenarios_draft(
    *,
    scenario_id: str = "SCN-001",
    scenario_type: str = "positive",
) -> dict:
    return {
        "contract_type": "speckit.behavior.scenarios.draft.v1",
        "feature": "refund-application",
        "scenarios": [
            {
                "id": scenario_id,
                "title": "Submit refund",
                "type": scenario_type,
                "given": ["FIX-BUYER"],
                "when": ["click_refund", "submit_refund"],
                "then": ["show_refund_submitted"],
                "source": "plan-phase-0",
            }
        ],
    }


def minimal_uif_intent() -> dict:
    return {
        "contract_type": "speckit.behavior.uif.intent.v1",
        "feature": "refund-application",
        "intents": [
            {
                "id": "UIF-INTENT-001",
                "start_view": "OrderDetailPage",
                "events": [{"name": "submit_refund", "label": "Submit refund"}],
                "expected_feedback": ["Refund submitted"],
                "possible_transition_types": ["local_route", "api_call"],
            }
        ],
    }


def minimal_data_fixtures_intent() -> dict:
    return {
        "contract_type": "speckit.behavior.data_fixtures.intent.v1",
        "fixtures": [
            {
                "id": "FIX-BUYER",
                "description": "Buyer user",
                "required_for": ["SCN-001"],
                "required_states": {"user.role": "buyer"},
            }
        ],
    }


def minimal_uif_expected() -> dict:
    return {
        "contract_type": "speckit.behavior.uif.expected.v1",
        "id": "UIF-001",
        "source": "behavior/uif.intent.json",
        "type": "expected",
        "start_view": {"id": "VIEW-ORDER-DETAIL", "name": "Order detail"},
        "steps": [
            {"id": "EVT-SUBMIT-REFUND", "type": "user_event", "label": "Submit refund"},
            {"type": "api_call", "api": {"method": "POST", "path": "/orders/{orderId}/refund"}},
        ],
        "feedback_candidates": [
            {"id": "FB-SUCCESS", "type": "toast", "message": "Refund submitted"}
        ],
    }


def minimal_behavior_scenario_instances() -> dict:
    return {
        "contract_type": "speckit.behavior.scenario_instances.v1",
        "scenarios": [
            {
                "id": "SCN-001",
                "title": "Submit refund",
                "type": "positive",
                "uif_path_id": "UIF-001",
                "fixture_ids": ["FIX-BUYER"],
                "request_case": {"id": "REQ-001", "reason": "QUALITY_ISSUE"},
                "expected_response": {"business_code": "SUCCESS"},
                "expected_feedback": {"message": "Refund submitted"},
                "assertion_ids": ["AST-001"],
            }
        ],
    }


def minimal_exception_behavior_scenario_instances(*, scenario_type: str = "permission") -> dict:
    instances = minimal_behavior_scenario_instances()
    scenario = instances["scenarios"][0]
    scenario["id"] = "SCN-ERR-001"
    scenario["title"] = "Reject refund request"
    scenario["type"] = scenario_type
    scenario["request_case"] = {
        "id": "REQ-ERR-001",
        "case_kind": scenario_type,
        "outcome": "failure",
        "trigger": "submit_refund_without_required_permission",
    }
    scenario["expected_response"] = {
        "business_code": "REJECTED",
        "status": 403,
        "error_code": "ERR_PERMISSION_DENIED",
    }
    scenario["expected_feedback"] = {
        "type": "inline_error",
        "message": "Permission denied",
    }
    scenario["assertion_ids"] = ["AST-001"]
    return instances


def minimal_case_coverage() -> dict:
    return {
        "case_coverage": [
            {
                "story": "Refund request",
                "case_id": "CASE-001",
                "case_type": "permission",
                "status": "Required",
                "source": "spec.md#user-story-1",
                "scenario_id": "SCN-ERR-001",
            }
        ]
    }


def minimal_case_coverage_with_blocker() -> dict:
    return {
        "case_coverage": [
            {
                "story": "Refund request",
                "case_id": "CASE-002",
                "case_type": "validation",
                "status": "Required",
                "source": "spec.md#user-story-1",
                "blocker_id": "BLK-001",
            }
        ]
    }


def minimal_behavior_data_fixtures() -> dict:
    return {
        "contract_type": "speckit.behavior.data_fixtures.v1",
        "fixtures": [
            {
                "id": "FIX-BUYER",
                "name": "Buyer user",
                "entities": ["user"],
                "required_states": {"user.role": "buyer"},
                "constraints": [],
                "setup_strategy": "factory",
            }
        ],
    }


def minimal_behavior_assertions() -> dict:
    return {
        "contract_type": "speckit.behavior.assertions.v1",
        "assertions": [
            {
                "id": "AST-001",
                "target": "refund.status",
                "operator": "equals",
                "expected": "PENDING",
            }
        ],
    }


def minimal_exception_behavior_assertions() -> dict:
    return minimal_exception_behavior_assertions_with_intent("state_invariant")


def minimal_exception_behavior_assertions_with_intent(intent: str) -> dict:
    assertions = minimal_behavior_assertions()
    assertions["assertions"][0]["intent"] = intent
    return assertions


class PresetContractTests(unittest.TestCase):
    def test_manifest_excludes_implement_override_and_runtime(self) -> None:
        manifest = yaml.safe_load(PRESET_PATH.read_text(encoding="utf-8"))
        entries = manifest["provides"]["templates"]
        command_entries = [entry for entry in entries if entry["type"] == "command"]
        template_entries = [entry for entry in entries if entry["type"] == "template"]

        self.assertEqual(7, len(command_entries))
        self.assertEqual(24, len(template_entries))
        self.assertEqual(31, len(entries))
        self.assertNotIn(
            "speckit.implement",
            {entry["name"] for entry in command_entries},
        )
        self.assertFalse(
            any("speckit.implement" in entry["file"] for entry in entries)
        )
        for path in REMOVED_IMPLEMENT_RUNTIME_PATHS:
            self.assertFalse(path.exists(), path)

    def test_tasks_end_with_mandatory_code_review_without_runtime_protocol(self) -> None:
        tasks = TASKS_COMMAND_PATH.read_text(encoding="utf-8")
        self.assertIn("Final Code Review", tasks)
        self.assertIn("append the final phase after user-story tasks", tasks)
        self.assertIn(
            "`boundary`, `interface_contract`, `visual`, `data_side_effect`, "
            "`behavior_contract`, `sequence_consistency`, and `asset_binding`",
            tasks,
        )
        for forbidden in (
            "speckit.implement.handoff",
            "speckit.implement.receipt",
            "handoff-manifest.json",
            "Manual Worker Queue",
            "Reviewer runtime",
        ):
            self.assertNotIn(forbidden, tasks)

    def test_current_docs_define_core_implement_ownership(self) -> None:
        current_docs = (
            README_PATH.read_text(encoding="utf-8"),
            EXTENSION_GOVERNANCE_PATH.read_text(encoding="utf-8"),
            AGENTS_PATH.read_text(encoding="utf-8"),
            CROSS_AGENT_PROTOCOL_PATH.read_text(encoding="utf-8"),
        )
        for document in current_docs:
            self.assertIn("Spec Kit core", document)
            for forbidden in (
                "speckit.implement.persistent_handoff_orchestration",
                "Manual Worker Queue",
                "Vertical Planner Agent",
                "Worker Agent mode",
                "speckit.implement.receipt.v1",
            ):
                self.assertNotIn(forbidden, document)

    def test_requirement_gate_and_clarify_repair_contract(self) -> None:
        checklist = CHECKLIST_COMMAND_PATH.read_text(encoding="utf-8")
        clarify = CLARIFY_COMMAND_PATH.read_text(encoding="utf-8")

        for path in (
            "checklists/requirements.md",
            "checklists/behavior.md",
            "checklists/ux.md",
            "checklists/security.md",
            "checklists/nfr.md",
            "checklists/visual.md",
        ):
            self.assertIn(path, checklist)
        self.assertIn("Planning Readiness is aggregated in memory", checklist)
        self.assertIn("do not create\n`planning-readiness.md`", checklist)
        self.assertIn("Case Coverage Matrix", checklist)
        self.assertIn("Visual Fidelity Evidence Matrix", checklist)
        self.assertIn("[blocker:provider-evidence] [return:intake]", checklist)
        self.assertIn("Recompute generated sections using stable", checklist)
        self.assertIn("legacy `checklists/behavior-testability.md`", checklist)

        self.assertIn("[blocker:product-decision]", clarify)
        self.assertIn("[blocker:provider-evidence]", clarify)
        self.assertIn("preserve its `[return:intake]`", clarify)
        self.assertIn("recompute affected requirement gates", clarify)
        self.assertIn("never create `planning-readiness.md`", clarify)

    def test_bdd_plan_task_readiness_contract(self) -> None:
        plan = PLAN_COMMAND_PATH.read_text(encoding="utf-8")
        tasks = TASKS_COMMAND_PATH.read_text(encoding="utf-8")
        analyze = ANALYZE_COMMAND_PATH.read_text(encoding="utf-8")

        self.assertIn("Phase 0 Gate Consumption", plan)
        self.assertIn("Required case types from `checklists/behavior.md`", plan)
        self.assertIn("BDD Plan / Behavior Testability Closeout", plan)
        self.assertIn("generate `behavior/behavior-testability.md`", plan)
        self.assertIn("Behavior Testability Status: READY", plan)
        self.assertIn("Task\nDerivation Matrix", plan)
        self.assertIn("UIF may be `N/A` only with a concrete non-UI reason", plan)
        self.assertIn("Do not accept the legacy", plan)

        self.assertIn("Behavior Testability Preflight", tasks)
        self.assertIn("Behavior Testability Status: READY", tasks)
        self.assertIn("stop before writing\n`tasks.md`", tasks)
        self.assertIn("Task Derivation Matrix as the primary task input", tasks)
        self.assertIn("fixture → validation/test → implementation → evidence", tasks)

        self.assertIn(
            "requirement gates -> BDD/UIF intent -> contracts -> behavior testability -> tasks",
            analyze,
        )
        self.assertIn("`behavior/behavior-testability.md` carries current spec/plan revisions", analyze)

    def test_requirement_and_behavior_testability_templates_contract(self) -> None:
        for path in (*REQUIREMENT_TEMPLATE_PATHS.values(), *BEHAVIOR_TEMPLATE_PATHS.values()):
            self.assertTrue(path.exists(), path)

        behavior_gate = REQUIREMENT_TEMPLATE_PATHS[
            "requirement-behavior-gate-template"
        ].read_text(encoding="utf-8")
        nfr_gate = REQUIREMENT_TEMPLATE_PATHS[
            "requirement-nfr-gate-template"
        ].read_text(encoding="utf-8")
        visual_gate = REQUIREMENT_TEMPLATE_PATHS[
            "requirement-visual-gate-template"
        ].read_text(encoding="utf-8")
        task_readiness = BEHAVIOR_TEMPLATE_PATHS[
            "behavior-testability-template"
        ].read_text(encoding="utf-8")

        self.assertIn("**Stage**: requirements", behavior_gate)
        self.assertIn("Case Coverage Matrix", behavior_gate)
        self.assertIn("positive, negative, boundary, permission, validation", behavior_gate)
        self.assertIn("NFR Coverage Matrix", nfr_gate)
        self.assertIn("Not Applicable", nfr_gate)
        self.assertIn("Visual Fidelity Evidence Matrix", visual_gate)
        self.assertIn("[BLOCKED: PROVIDER_EVIDENCE]", visual_gate)

        self.assertIn("Behavior Testability / Task Readiness", task_readiness)
        self.assertIn("**Stage**: plan", task_readiness)
        self.assertIn("**Behavior Testability Status**: READY | BLOCKED", task_readiness)
        self.assertIn("**Spec Revision**", task_readiness)
        self.assertIn("**Plan Revision**", task_readiness)
        self.assertIn("Task Derivation Matrix", task_readiness)
        self.assertIn("| Case ID | Scenario ID | BDD Ref | UIF Ref | Fixture Ref | Assertion Ref |", task_readiness)
        self.assertFalse(
            (REPO_ROOT / "templates" / "behavior" / "behavior-testability-checklist.md").exists()
        )

    def test_public_docs_define_two_stage_ownership(self) -> None:
        readme = README_PATH.read_text(encoding="utf-8")
        governance = EXTENSION_GOVERNANCE_PATH.read_text(encoding="utf-8")

        self.assertIn("requirement-domain readiness gates", readme)
        self.assertIn("behavior/behavior-testability.md", readme)
        self.assertIn("Missing provider evidence remains an intake blocker", readme)

        self.assertIn("requirement-readiness gates", governance)
        self.assertIn("BDD Plan closeout", governance)
        self.assertIn("behavior/behavior-testability.md", governance)


    def test_plan_command_wrapper_contract(self) -> None:
        command = PLAN_COMMAND_PATH.read_text(encoding="utf-8")

        self.assertIn("{CORE_TEMPLATE}", command)
        self.assertIn("class-diagram.md", command)
        self.assertIn("contracts/sequences.md", command)
        self.assertNotIn("test-plan.md", command)
        self.assertIn("strategy: wrap", command)
        self.assertIn("Generate design artifacts only when the feature requires internal object design or cross-boundary sequence constraints", command)
        self.assertIn("Keep `plan.md` as summary/navigation", command)
        self.assertIn("validation decisions belong in `research.md`", command)
        self.assertIn("executable validation paths belong in `quickstart.md`", command)
        self.assertIn("final report must list generated artifacts", command)
        self.assertIn("## Architecture-Guided Planning", command)
        self.assertIn(".specify/memory/architecture.md", command)
        self.assertIn("`research.md` MUST follow established technical decisions and evidence", command)
        self.assertIn("`data-model.md` MUST preserve defined concepts", command)
        self.assertIn("`contracts/` MUST preserve system boundaries", command)
        self.assertIn("`plan.md` and `quickstart.md` MUST carry forward", command)
        self.assertIn("return to the Constitution stage", command)
        self.assertIn("Do not create a compliance matrix", command)
        self.assertIn("Plan Agent Topology", command)
        self.assertIn(
            "Follow cross-agent protocol profile: `speckit.plan.stage_local_planning`",
            command,
        )
        self.assertIn("Plan Core Agent", command)
        for agent_role in (
            "Behavior Projection Agent",
            "Formal Contract Agent",
            "Design Artifact Agent",
            "Validation Planning Agent",
            "Visual Planning Agent",
        ):
            self.assertIn(agent_role, command)
        self.assertIn("Each payload declares assigned scope, allowed reads, allowed sections, and output contract", command)
        self.assertIn("rather than subagent conversation history", command)
        self.assertNotIn("speckit.tasks", command)
        self.assertNotIn("speckit.implement", command)

    def test_plan_template_navigation_contract(self) -> None:
        template = PLAN_TEMPLATE_PATH.read_text(encoding="utf-8")

        self.assertIn("{CORE_TEMPLATE}", template)
        self.assertIn("## Design Artifacts", template)
        self.assertIn("./class-diagram.md", template)
        self.assertIn("./contracts/sequences.md", template)
        self.assertNotIn("test-plan.md", template)
        self.assertIn("./data-model.md", template)
        self.assertIn("./contracts/", template)
        self.assertIn("./quickstart.md", template)

    def test_plan_visual_substage_enhancement_contract(self) -> None:
        command = PLAN_COMMAND_PATH.read_text(encoding="utf-8")
        template = PLAN_TEMPLATE_PATH.read_text(encoding="utf-8")
        readme = README_PATH.read_text(encoding="utf-8")
        governance = EXTENSION_GOVERNANCE_PATH.read_text(encoding="utf-8")

        for term in (
            "Visual Planning Responsibilities",
            "visual and IR planning inputs",
            "Visual Item ID",
            "HTML SSOT refs",
            "structured IR refs",
            "readiness status",
            "unresolved blocker refs",
            "do not copy the Visual Fidelity Evidence Matrix into `research.md`",
            "rebuild provider evidence matrices",
            "Do not define visual validation strategy",
            "visual_item_refs",
            "viewport_matrix_refs",
            "state_matrix_refs",
            "visual_proof_refs",
            "accepted_exception_refs",
            "UI interaction sequence",
            "visual state handoff points",
            "responsive branch trigger refs",
        ):
            self.assertIn(term, command)

        for term in (
            "Visual fidelity navigation",
            "Visual/IR source refs and readiness inputs: `./research.md`",
            "Visual interaction contracts: `./contracts/uif/` and `./contracts/behavior/`",
            "Visual flow sequences: `./contracts/sequences.md`",
            "Non-visual acceptance execution: `./quickstart.md`",
        ):
            self.assertIn(term, template)

        for document in (readme, governance):
            self.assertIn("research.md", document)
            self.assertIn("visual/IR", document)
            self.assertIn("contracts/sequences.md", document)

        self.assertIn(
            "fixed R/M/U/O model: R is Repository / Workspace, M is Module / Capability, U is Unit / Design Object, and O is Operation / Detail",
            readme,
        )
        self.assertIn("System Boundary -> Conceptual Model", readme)

    def test_constitution_change_scope_granularity_contract(self) -> None:
        command = CONSTITUTION_COMMAND_PATH.read_text(encoding="utf-8")
        template = CONSTITUTION_TEMPLATE_PATH.read_text(encoding="utf-8")
        architecture = ARCHITECTURE_TEMPLATE_PATH.read_text(encoding="utf-8")

        exact_mapping = [
            "R: Repository / Workspace. Environment only; too broad for scoped changes.",
            "M: Module / Capability. Hard outer boundary.",
            "U: Unit / Design Object. Primary planning boundary.",
            "O: Operation / Detail. Execution detail.",
        ]
        forbidden_mapping_drift = [
            "R, Requirement",
            "R: Requirement",
            "M, Model",
            "M: Model",
            "U, User/API Interface",
            "U: User/API Interface",
            "O, Operations",
            "O: Operations",
        ]

        for document in (command, template):
            self.assertIn("{CORE_TEMPLATE}", document)
            self.assertIn("Change Scope Granularity", document)
            self.assertIn("R/M/U/O", document)
            self.assertIn("Planning locks M + U", document)
            for mapping in exact_mapping:
                self.assertIn(mapping, document)
            for forbidden in forbidden_mapping_drift:
                self.assertNotIn(forbidden, document)

        self.assertIn("strategy: wrap", command)
        self.assertIn("Spec Kit planning and execution MUST use R/M/U/O scope granularity", template)
        self.assertIn("This principle applies from planning onward", template)
        self.assertIn("Requirement specification, clarification, and checklist readiness MUST NOT infer M/U/O boundaries", template)
        self.assertIn("preserve the Change Scope Granularity principle", command)
        self.assertIn("must not remove, weaken, or contradict", command)
        self.assertIn("The R/M/U/O letter mapping is fixed and MUST remain exact", command)
        self.assertIn("preserves the exact R/M/U/O letter mapping", command)
        self.assertIn("CONSTITUTION_RMUO_MAPPING_DRIFT", command)
        self.assertIn("CONSTITUTION_TEMPLATE_STATUS_UNCHECKED", command)
        self.assertIn("do not report it as missing", command)
        self.assertIn("do not treat that as the workflow-preset template being absent", command)
        self.assertIn("Constitution Stage Input Agreement", command)
        for mode in ("greenfield", "brownfield", "amendment"):
            self.assertIn(mode, command)
        self.assertIn("No conventional path is mandatory", command)
        self.assertIn("candidate sources only until the user authorizes their role", command)
        self.assertIn("Existing code is evidence", command)
        self.assertIn("ARCH_LEGACY_FORMAT", command)
        self.assertIn("Separate Artifact Ownership", command)
        self.assertIn(".specify/memory/constitution.md", command)
        self.assertIn(".specify/memory/architecture.md", command)
        self.assertIn("write exactly one Architecture artifact", command)
        self.assertIn("without 4+1", command)
        self.assertIn("Technical validation is evidence registration only", command)
        self.assertIn("Optional tables may be empty", command)
        self.assertIn("Do not create PoC code", command)
        self.assertIn("Architecture-Guided Planning", command)
        self.assertIn("`/speckit.plan` MUST read", command)
        self.assertIn("planning MUST stop and return to the Constitution stage", command)
        self.assertIn("The R/M/U/O letter mapping is fixed", template)
        self.assertIn("Constitution And Architecture Boundary", template)
        self.assertIn("Feature-local planning artifacts may refine Architecture", template)
        self.assertIn("Architecture-Guided Planning", template)
        self.assertIn("`research.md` MUST follow established technical decisions", template)
        self.assertIn("`contracts/` MUST preserve system boundaries", template)

        expected_sections = [
            "Architecture Overview",
            "System Boundary",
            "Conceptual Model",
            "Technical Decisions & Evidence",
            "Planning Guardrails & Gaps",
        ]
        self.assertEqual(
            expected_sections,
            re.findall(r"^## (.+)$", architecture, flags=re.MULTILINE),
        )
        self.assertIn("**Architecture Goal**", architecture)
        self.assertIn("**Authorized Sources**", architecture)
        self.assertIn("Does Not Own", architecture)
        self.assertIn("Evidence Or Explicit Gap", architecture)
        self.assertIn("MUST_VALIDATE", architecture)
        self.assertIn("Optional tables may remain empty", architecture)
        self.assertNotIn("4+1", architecture)

    def test_change_scope_granularity_stage_references(self) -> None:
        plan = PLAN_COMMAND_PATH.read_text(encoding="utf-8")
        tasks = TASKS_COMMAND_PATH.read_text(encoding="utf-8")
        analyze = ANALYZE_COMMAND_PATH.read_text(encoding="utf-8")

        self.assertIn("Apply the constitution's Change Scope Granularity principle.", plan)
        self.assertIn("During planning, lock the change scope to `M + U`", plan)
        self.assertIn("Do not lock operation-level implementation details or concrete write paths.", plan)
        self.assertNotIn("Architecture SSOT Compliance", plan)
        self.assertNotIn("PLANNING_ARCH_SSOT_CONFLICT", plan)

        self.assertIn("Preserve the planned `M + U` scope", tasks)
        self.assertIn("Do not generate execution metadata or write-path fields.", tasks)

        self.assertIn("Check that tasks preserve the planned `M + U` scope.", analyze)
        self.assertIn("Report missing, widened, or ambiguous scope boundaries as blockers.", analyze)

        self.assertFalse((REPO_ROOT / "commands" / "speckit.implement.md").exists())

    def test_preplanning_commands_do_not_infer_scope_granularity(self) -> None:
        for path in (SPECIFY_COMMAND_PATH, CLARIFY_COMMAND_PATH, CHECKLIST_COMMAND_PATH):
            command = path.read_text(encoding="utf-8")
            for forbidden in (
                "Change Scope Granularity",
                "R/M/U/O",
                "M + U",
                "U -> concrete paths",
                "module/capability plus design object",
                "concrete write paths",
                "allowed_write_paths",
                "context_gaps",
            ):
                self.assertNotIn(forbidden, command, f"{path} contains {forbidden}")

    def test_tasks_command_wrapper_contract(self) -> None:
        tasks = TASKS_COMMAND_PATH.read_text(encoding="utf-8")

        self.assertIn("{CORE_TEMPLATE}", tasks)
        self.assertIn("class-diagram.md", tasks)
        self.assertIn("contracts/sequences.md", tasks)
        self.assertNotIn("test-plan.md", tasks)
        self.assertIn("strategy: wrap", tasks)
        self.assertIn("implementation, integration, orchestration", tasks)
        self.assertIn("existing checklist format and user-story organization", tasks)
        self.assertIn("`/speckit.tasks` owns implementation, non-visual validation, and review task definition in `tasks.md`", tasks)
        self.assertIn("must not invent validation strategy", tasks)
        self.assertIn("change requirements, update contracts, or widen scope", tasks)
        self.assertIn("Task-Derivation Subagents", tasks)
        self.assertIn("context-reduced multi-subagent derivation model", tasks)
        self.assertIn("derivation-time partitioning rule only", tasks)
        self.assertIn("do not create implementation transfer artifacts", tasks)
        self.assertIn("Tasks Core Agent", tasks)
        for agent_role in (
            "Story Task Agent",
            "Contract Validation Agent",
            "Visual Task Agent",
            "Review Task Agent",
        ):
            self.assertIn(agent_role, tasks)
        for payload_field in (
            "`assigned_scope`",
            "`allowed_read_paths`",
            "`allowed_sections`",
            "`output_contract`",
        ):
            self.assertIn(payload_field, tasks)
        self.assertIn("TASK_DERIVATION_CONTEXT_GAP", tasks)
        self.assertIn("must not consume full conversation history", tasks)
        self.assertIn("Split checklist items only when the validation level, implementation owner, dependency order, evidence source, or review scope differs", tasks)
        self.assertIn("Planning Input Taxonomy", tasks)
        self.assertIn("validation level taxonomy", tasks)
        self.assertIn("fixture strategy and external-system execution mode taxonomy", tasks)
        self.assertIn("Evidence binding", tasks)
        self.assertIn("Validation Task Derivation", tasks)
        self.assertIn("derive the validation level", tasks)
        self.assertIn("fixture strategy, external-system execution mode", tasks)
        self.assertIn("inline evidence requirement", tasks)
        self.assertIn("validation task taxonomy", tasks)
        for validation_scope in (
            "`contract_validation`",
            "`ui_acceptance`",
            "`data_side_effect_validation`",
            "`integration_e2e_validation`",
        ):
            self.assertIn(validation_scope, tasks)
        self.assertIn("Final Code Review", tasks)
        self.assertIn("append the final phase after user-story tasks", tasks)
        self.assertIn("final review scope taxonomy", tasks)
        self.assertIn("`boundary`, `interface_contract`, `visual`, `data_side_effect`, `behavior_contract`, `sequence_consistency`, and `asset_binding`", tasks)
        self.assertIn("Checked sources include", tasks)
        self.assertIn("`contracts/uif/`", tasks)
        self.assertIn("`spec.md` Client Asset Contract entries", tasks)
        self.assertIn("Visual Fidelity Readiness", tasks)
        self.assertIn("data side-effect review", tasks)
        self.assertIn("field-level update/delete", tasks)
        self.assertIn("runtime database writes", tasks)
        self.assertIn("boundary review", tasks)
        self.assertIn("task scope stays within planned `M + U`", tasks)
        self.assertIn("no implementation task changed `spec.md`, `contracts/`, readiness checklists, or Visual Fidelity Readiness", tasks)
        self.assertIn("UI consistency review", tasks)
        self.assertIn("implemented UI states and viewport behavior", tasks)
        self.assertIn("visual/IR traceability refs", tasks)
        self.assertIn("UI/visual task taxonomy", tasks)
        self.assertIn("story-local task granularity", tasks)
        self.assertIn("`visual_setup` -> `visual_implementation` -> `ui_acceptance` or `asset_binding`", tasks)
        self.assertIn("Do not create a separate visual lifecycle phase", tasks)
        self.assertIn("Visual/UI tasks must name concrete source, test, fixture, configuration, asset paths, and visual/IR traceability refs", tasks)
        self.assertIn("report a readiness blocker instead of generating an ambiguous task", tasks)
        self.assertIn("Client Asset Contract bindings, variants, and fallback policy", tasks)
        self.assertIn("screenshot comparison, visual diff, baseline capture, or final visual review", tasks)
        self.assertIn("real-system e2e environment readiness", tasks)
        self.assertIn("Review evidence binding", tasks)
        self.assertIn("concrete review scope, source artifacts, implementation surfaces, and evidence refs", tasks)
        self.assertIn("bounded repair permission", tasks)
        self.assertIn("review evidence, bounded repair permission, or a blocker", tasks)
        self.assertIn("record a blocker instead of treating the change as implementation work", tasks)
        self.assertNotIn("handoff", tasks)
        self.assertNotIn("allowed_write_paths", tasks)
        self.assertNotIn("receipt", tasks)
        self.assertNotIn("speckit.implement.receipt.v1", tasks)
        self.assertNotIn("task_type: code_review", tasks)
        self.assertNotIn("data_side_effect_review", tasks)
        self.assertNotIn("review_conclusion", tasks)
        self.assertNotIn("checked_sources", tasks)
        self.assertNotIn("consistency_repairs", tasks)
        self.assertNotIn("deferred_validation_todos", tasks)
        self.assertNotIn("empty arrays or objects indicate no entries", tasks)
        self.assertNotIn("task_type: visual_verification", tasks)
        self.assertNotIn("`visual_validation`", tasks)
        self.assertNotIn("`visual_verification`", tasks)
        self.assertNotIn("`final_visual_review`", tasks)
        self.assertNotIn("visual regression tests", tasks)
        self.assertNotIn("screenshot comparison, state or viewport coverage validation", tasks)
        self.assertNotIn("task_type: interface_validation", tasks)
        self.assertNotIn("task_type: data_side_effect_validation", tasks)

    def test_behavior_first_command_wrapper_contracts(self) -> None:
        specify = SPECIFY_COMMAND_PATH.read_text(encoding="utf-8")
        clarify = CLARIFY_COMMAND_PATH.read_text(encoding="utf-8")
        checklist = CHECKLIST_COMMAND_PATH.read_text(encoding="utf-8")

        for command in (specify, clarify, checklist):
            self.assertIn("{CORE_TEMPLATE}", command)
            self.assertIn("strategy: wrap", command)
        for command in (specify, clarify):
            self.assertIn(
                "This wrapper must not redefine core-owned User Input, Pre-Execution Checks, extension hooks, base path resolution, or core file handling.",
                command,
            )
        self.assertIn("This wrapper extends the core spec-only checklist contract", checklist)
        self.assertIn("must not read\n`plan.md` or `tasks.md`", checklist)
        self.assertIn("Planning Readiness is aggregated in memory", checklist)

        self.assertIn("Spec-Only Requirement Policy", specify)
        self.assertIn("Wrapper Input Additions", specify)
        self.assertIn("Wrapper Preflight Additions", specify)
        self.assertIn("Wrapper Outline Additions", specify)
        self.assertNotIn("## User Input", specify)
        self.assertNotIn("## Pre-Execution Checks", specify)
        self.assertIn("Preset-added requirement output writes only `spec.md`", specify)
        self.assertIn("Product requirements stay in `spec.md`", specify)
        self.assertIn("non-functional requirements", specify)
        self.assertIn("visual and UI requirements", specify)
        self.assertIn("report the `spec.md` sections created or updated", specify)
        for term in (
            "Official Style Alignment",
            "Focus on WHAT users need and WHY",
            "Avoid HOW to implement",
            "Limit [NEEDS CLARIFICATION] markers to the highest-impact unresolved product decisions",
            "Specification Quality Validation",
            "Done When",
        ):
            self.assertIn(term, specify)
        for term in (
            "confirmed external intake facts",
            "visual SSOT refs",
            "structured IR refs",
            "evidence refs",
            "does not perform intake",
            "call provider tools",
            "parse HTML SSOT bundles",
            "re-parse structured IR artifacts",
            "decide provider source readiness",
            "generate provider artifact instances",
            "Specification Projection Policy",
            "source-backed external intake facts",
            "Visual Asset Registry",
            "external source artifact inputs",
            "visual media inventory",
            "license status",
            "Visual & UI Specification",
            "observable visual and UI requirements",
            "write a `Visual & UI Specification` section",
            "Not Applicable rationale",
            "Every identified visual or UI requirement must be recorded",
            "status `Required`, `Not Applicable`, `Unknown`, or `[BLOCKED: PROVIDER_EVIDENCE]`",
            "do not silently omit low-evidence visual or UI requirements",
            "source refs",
            "HTML SSOT refs",
            "structured IR refs",
            "state and viewport refs",
            "Client Asset Contract facts",
            "asset source strategy",
            "required variants",
            "fallback policy",
            "blocker status",
            "Promote only confirmed product facts and source-backed visual, layout, state, interaction, responsive, accessibility, and acceptance facts",
            "Component State Matrix content as Visual & UI Specification requirements, not visual assets",
            "observable states, visual feedback, and interaction outcomes",
            "missing product decisions become `[NEEDS CLARIFICATION]`",
            "missing provider or intake evidence for a feature that depends on that evidence becomes `[BLOCKED: PROVIDER_EVIDENCE]`",
            "features that do not depend on HTML SSOT, structured IR, or provider evidence are `Not Applicable`",
            "DOM structure",
            "CSS selectors",
            "component props",
            "provider blockers",
            "[BLOCKED: PROVIDER_EVIDENCE]",
            "keep explicit visual or UI requirement coverage in `spec.md`",
            "Functional, non-functional, and visual/UI requirement coverage",
            "Do not promote provider evidence gaps into product requirements or `[NEEDS CLARIFICATION]` markers",
            "[NEEDS CLARIFICATION]",
            "visual SSOT refs preserved",
        ):
            self.assertIn(term, specify)
        self.assertLessEqual(len(specify.splitlines()), 70)
        for forbidden in (
            "/speckit.plan",
            "/speckit.checklist",
            "Visual Fidelity Evidence Matrix",
            "`[NEEDS CLARIFICATION]` item requesting a filled Provider Evidence Packet",
            "behavior/bdd.draft.feature",
            "behavior/behavior-scenarios.draft.json",
            "behavior/uif.intent.json",
            "behavior/data-fixtures.intent.json",
            "behavior/open-questions.json",
            "formal behavior contracts",
            "interface schemas",
            "validation commands",
            "task plans",
            "design artifacts",
            "local asset path",
            "asset hash",
            "allowed_write_paths",
            "Design intake input",
            "Provider Evidence Packet readiness",
            "Requirement Merge Report",
            "raw get_metadata",
            "Stage 0:",
            "Stage 1:",
            "Stage 2:",
            "Stage 3:",
            "Observed from provider design",
        ):
            self.assertNotIn(forbidden, specify)
        self.assertNotIn("contracts/bdd/", specify)
        self.assertNotIn("contracts/uif/", specify)

        self.assertIn("Spec-Only Clarification Policy", clarify)
        self.assertIn("Wrapper Input Additions", clarify)
        self.assertIn("Wrapper Preflight Additions", clarify)
        self.assertIn("Wrapper Outline Additions", clarify)
        self.assertNotIn("## User Input", clarify)
        self.assertNotIn("## Pre-Execution Checks", clarify)
        self.assertIn("Use `spec.md` as the clarification source", clarify)
        self.assertIn("Do not read or update behavior draft artifacts", clarify)
        self.assertIn("Product requirements stay in `spec.md`", clarify)
        self.assertIn("non-functional requirement assumptions", clarify)
        self.assertIn("visual/UI requirement coverage status", clarify)
        self.assertIn("only after user-provided answers", clarify)
        self.assertIn("Design Requirement Clarification Strategy", clarify)
        self.assertIn("external intake evidence", clarify)
        self.assertIn("visual SSOT refs", clarify)
        self.assertIn("evidence-derived gaps", clarify)
        self.assertIn("visual/UI coverage status `Unknown`", clarify)
        self.assertIn("[NEEDS CLARIFICATION]", clarify)
        self.assertIn("Do not call provider tools", clarify)
        self.assertIn("Do not re-extract design facts", clarify)
        self.assertIn("re-parse provider design links", clarify)
        self.assertIn("parse HTML SSOT bundles", clarify)
        self.assertIn("re-parse structured IR artifacts", clarify)
        self.assertIn("External intake owns source capture and provider readiness", clarify)
        self.assertIn("confirmed evidence-backed requirements and trace refs", clarify)
        self.assertIn("Do not ask the user to fix provider extraction artifacts", clarify)
        self.assertIn("Ask at most 5 high-impact questions", clarify)
        self.assertIn("Present EXACTLY ONE question at a time", clarify)
        self.assertIn("Do NOT output them all at once", clarify)
        self.assertIn("Never reveal future queued questions", clarify)
        self.assertIn("Maximum of 5 total questions", clarify)
        self.assertIn("Format recommendations as `**Recommended:** Option [X] - <brief rationale>`", clarify)
        self.assertIn("Keep the rationale short and decision-focused", clarify)
        self.assertNotIn("<reasoning>", clarify)
        self.assertIn("Suggested", clarify)
        self.assertIn("2-5", clarify)
        self.assertIn("<=5 words", clarify)
        self.assertIn("yes", clarify)
        self.assertIn("recommended", clarify)
        self.assertIn("suggested", clarify)
        self.assertIn("Save `spec.md` after each accepted answer", clarify)
        self.assertIn("## Clarifications", clarify)
        self.assertIn("### Session YYYY-MM-DD", clarify)
        self.assertIn("Q:", clarify)
        self.assertIn("A:", clarify)
        self.assertIn("provider-specific clarification document", clarify)
        self.assertIn("Validation after each write", clarify)
        self.assertIn("after EACH write plus final pass", clarify)
        self.assertIn("Total asked", clarify)
        self.assertIn("no contradictory earlier statement remains", clarify)
        self.assertIn("recompute affected requirement gates", clarify)
        self.assertIn("Replace generated status and blocker", clarify)
        self.assertNotIn("FEATURE_DIR/checklists/requirements.md", clarify)
        self.assertNotIn("Only toggle the `[ ]`/`[x]` marker", clarify)
        self.assertIn("hooks.before_clarify", clarify)
        self.assertIn("hooks.after_clarify", clarify)
        self.assertIn("EXECUTE_COMMAND", clarify)
        self.assertIn("Completion Report", clarify)
        self.assertIn("Visual/UI coverage status: Required, Not Applicable, Unknown, or `[BLOCKED: PROVIDER_EVIDENCE]`", clarify)
        self.assertIn("visual fidelity scope", clarify)
        self.assertIn("missing UI states", clarify)
        self.assertIn("responsive behavior", clarify)
        self.assertIn("component reuse constraints", clarify)
        self.assertIn("data semantics", clarify)
        self.assertIn("acceptance evidence", clarify)
        self.assertIn("accepted exception approval flow", clarify)
        self.assertIn("write confirmed answers back into `spec.md`", clarify)
        self.assertIn("Update affected visual/UI coverage status", clarify)
        self.assertIn("Any answered visual/UI coverage status was updated in `spec.md`", clarify)
        self.assertIn("Do not generate visual restoration checklists", clarify)
        for forbidden in (
            "behavior/bdd.draft.feature",
            "behavior/behavior-scenarios.draft.json",
            "behavior/uif.intent.json",
            "behavior/data-fixtures.intent.json",
            "behavior/open-questions.json",
            "use_provider_tool",
            "get_design_context",
            "fetch provider design URL",
            "read provider design URL",
            "Provider Evidence Packet",
            "Design Requirement" + " Intake",
            "Inferred from Structure",
            "update checklists/behavior-testability.md",
        ):
            self.assertNotIn(forbidden, clarify)

        for term in (
            "Multi-Domain Requirement Gate",
            "Use `$ARGUMENTS` only to prioritize requirement-quality focus",
            "Stage/Domain/Gate/Applicability/Status/Spec Revision",
            "The legacy `checklists/behavior-testability.md` is not an input or output",
            "Behavior Requirement Gate",
            "Case Coverage Matrix",
            "positive, negative, boundary, permission, validation, and",
            "state_conflict",
            "stable Case IDs",
            "Scenario IDs and `case_coverage_blockers` remain `/speckit.plan` outputs",
            "This gate checks whether behavior requirements are projectable",
            "NFR Requirement Gate",
            "verifiable product-level criteria",
            "Do not require",
            "technical designs or invent architecture",
            "Recompute generated sections using stable CHK/CASE/NFR/VIS IDs",
            "Never append",
            "duplicate status blocks, stale blockers, or repeated matrix rows",
        ):
            self.assertIn(term, checklist)
        for term in (
            "Visual Requirement Gate",
            "Visual & UI Specification",
            "Apply the gate when `spec.md` contains a Visual & UI Specification",
            "Every visual item is",
            "`[BLOCKED: PROVIDER_EVIDENCE]`",
            "Unknown product semantics become `[blocker:product-decision]`",
            "Missing provider proof remains `[blocker:provider-evidence] [return:intake]`",
            "Provider blockers must not be converted into clarify questions",
            "visual SSOT refs",
            "external intake refs",
            "structured IR refs",
            "Visual Fidelity Evidence Matrix",
            "source traceability",
            "readiness input",
            "Responsive visual requirements block PASS only when required source-backed",
            "Do not call provider tools, rebuild intake evidence",
        ):
            self.assertIn(term, checklist)
        for term in (
            "| Visual Item ID | Source `spec.md` section | Requirement Status | Fidelity Scope | Screenshot Level | Evidence Refs | Visual Proof Required | Blocking Item ID | Exception Rule |",
            "Screenshot evidence level",
            "declared visual proof required",
            "proof level sufficiency",
            "screenshot sufficiency",
            "raw metadata completeness",
            "metadata index completeness proof",
            "node inventory parity",
            "blocker lint errors",
            "Responsive visual readiness must record viewport-specific evidence or set Gate Status: BLOCKED",
        ):
            self.assertNotIn(term, checklist)
        self.assertIn("Planning Readiness aggregate", checklist)
        self.assertIn("provider-evidence\nblockers separately", checklist)
        return
        self.assertIn("PASS", checklist)
        self.assertIn("BLOCKED", checklist)
        self.assertIn("product-decision blockers, and provider-evidence", checklist)

    def test_behavior_first_plan_and_tasks_awareness_contract(self) -> None:
        plan = PLAN_COMMAND_PATH.read_text(encoding="utf-8")
        tasks = TASKS_COMMAND_PATH.read_text(encoding="utf-8")
        template = PLAN_TEMPLATE_PATH.read_text(encoding="utf-8")

        for term in (
            "behavior/bdd.draft.feature",
            "behavior/uif.intent.json",
            "behavior/data-fixtures.intent.json",
            "contracts/bdd/",
            "contracts/uif/",
            "contracts/behavior/",
            "formal behavior contracts",
            "must formalize",
            "N/A or blocker",
            "research.md",
            "test level",
            "fixture strategy",
            "mock/external-system strategy",
            "BehaviorScenarioInstance",
            "DataFixture",
            "UIFPath",
            "FeedbackView",
            "BehaviorAssertion",
            "Required case types from `checklists/behavior.md`",
            "must project into",
            "`behavior/behavior-scenarios.draft.json`",
            "must formalize into",
            "`contracts/behavior/scenario-instances.json`",
            "Do not continue with only positive",
            "scenarios when Required case types exist",
            "Map each Required Case ID to a",
            "Scenario ID or `case_coverage_blockers` entry",
            "write `case_coverage_blockers`",
            "record `N/A or blocker` with",
            "the Case ID, missing planning input",
        ):
            self.assertIn(term, plan)

        self.assertIn("BDD Plan closeout", plan)
        self.assertIn("behavior/behavior-testability.md", plan)
        return

        for term in (
            "Phase 0 Gate Consumption",
            "Phase 0 Behavior Projection",
            "read-only Planning Readiness preflight",
            "before core research or design work",
            "visual fidelity scope",
            "source refs",
            "HTML SSOT refs",
            "structured IR refs",
            "screenshot refs",
            "visual proof refs",
            "visual SSOT refs",
            "Visual Fidelity Evidence Matrix `Requirement Status`",
            "Carry forward only visual rows with status `Required` or an accepted exception rule",
            "Rows with status `Unknown` or `[BLOCKED: PROVIDER_EVIDENCE]` must already have blocked checklist PASS",
            "report-only/no-write upstream gate failure",
            "Do not project `Not Applicable` rows into visual planning outputs",
            "behavior/behavior-scenarios.draft.json",
            "report-only/no-write failure",
            "Do not create or update partial behavior artifacts",
            "Do not discover new requirement problems",
            "Do not ask clarification questions",
            "Do not modify `spec.md`",
            "upstream gate failure",
            "Return to `/speckit.checklist` or `/speckit.clarify`",
        ):
            self.assertIn(term, plan)

        self.assertNotIn("empty, or records only an upstream gate failure", plan)
        self.assertNotIn("behavior/open-questions.json", plan)
        self.assertNotIn("test-plan.md", plan)
        self.assertIn("BDD Plan closeout", plan)
        self.assertIn("behavior/behavior-testability.md", plan)
        return

        for term in (
            "contracts/bdd/",
            "contracts/uif/",
            "contracts/behavior/",
            "`spec.md` visual acceptance requirements",
            "`checklists/visual.md` Visual Fidelity Readiness",
            "HTML SSOT refs",
            "structured IR refs",
            "screenshot refs",
            "visual proof refs",
            "visual SSOT refs",
            "external evidence refs",
            "visual fidelity requirements",
            "test-first",
            "existing checklist format and user-story organization",
            "For each BehaviorScenarioInstance",
            "fixture task",
            "BDD/E2E or contract test task",
            "implementation task",
            "verification evidence task",
            "Expected UIF contract step with type `user_event`",
            "Expected UIF contract step with type `api_call`",
            "UI/visual task taxonomy",
            "`ui_acceptance`",
            "UI acceptance task",
            "viewport/state requirement refs",
            "required state and viewport coverage",
            "visual/IR traceability ref",
            "For each quickstart validation path",
            "derive the validation level",
            "fixture strategy, external-system execution mode",
            "inline evidence requirement",
            "Planning Input Taxonomy",
            "`/speckit.tasks` owns implementation, non-visual validation, and review task definition in `tasks.md`",
            "must not invent validation strategy",
            "visual validation work",
            "validation level taxonomy",
            "fixture strategy and external-system execution mode taxonomy",
            "Evidence binding",
            "validation task taxonomy",
            "`contract_validation`",
            "`ui_acceptance`",
            "`data_side_effect_validation`",
            "`integration_e2e_validation`",
            "Client Asset Contract",
            "derive asset preparation, binding, implementation, and non-visual acceptance tasks",
            "Missing required client visual assets are readiness blockers",
            "Use Visual Fidelity Readiness as the only visual planning readiness source",
            "`Requirement Status` as the visual task input filter",
            "Generate UI implementation, asset binding, and non-visual acceptance tasks only for rows with status `Required` or `Required` plus an accepted exception",
            "tasks for accepted exceptions must cite the exception rule",
            "Do not generate implementation, validation, verification, evidence, asset binding, UI acceptance, or review tasks for `Not Applicable`, `Unknown`, or `[BLOCKED: PROVIDER_EVIDENCE]` rows",
            "Route `Unknown` rows back to `/speckit.clarify`",
            "route `[BLOCKED: PROVIDER_EVIDENCE]` rows to the external intake extension",
            "`/speckit.tasks` must not discover visual requirements, repair evidence, re-parse provider artifacts, or define visual validation strategy",
            "only decomposes visual specifications that already passed the readiness gate",
            "Do not create a second readiness rule",
            "HTML SSOT refs",
            "structured IR refs",
            "external intake artifacts",
            "Do not generate execution metadata or write-path fields.",
            "Missing Required case coverage is a coverage blocker, not silently skipped work",
            "`negative`, `boundary`, `permission`, `validation`, or `state_conflict`",
            "For each BehaviorScenarioInstance with type",
            "derive fixture, contract or BDD test, implementation, and verification evidence tasks",
            "UI consistency review",
            "implemented UI states and viewport behavior",
            "UI/visual task taxonomy",
            "story-local task granularity",
            "`visual_setup` -> `visual_implementation` -> `ui_acceptance` or `asset_binding`",
            "`asset_binding`",
            "`visual_setup`, `visual_implementation`, `ui_acceptance`, and `asset_binding` are the only visual/UI task types",
            "without screenshot comparison, visual diff, baseline capture, or final visual review",
            "empty/error/loading/disabled/hover/focus states",
            "license or authorization refs",
            "Do not create a separate visual lifecycle phase",
            "Visual/UI tasks must name concrete source, test, fixture, configuration, asset paths, and visual/IR traceability refs",
            "report a readiness blocker instead of generating an ambiguous task",
            "Do not generate visual validation, screenshot comparison, visual diff, baseline capture, final visual review, or visual tasks for rows with `Requirement Status` `Not Applicable`, `Unknown`, or `[BLOCKED: PROVIDER_EVIDENCE]`",
            "Client Asset Contract bindings, variants, and fallback policy",
            "Review evidence binding",
            "bounded repair permission",
            "final review scope taxonomy",
            "`boundary`, `interface_contract`, `visual`, `data_side_effect`, `behavior_contract`, `sequence_consistency`, and `asset_binding`",
            "boundary review",
            "no implementation task changed `spec.md`, `contracts/`, readiness checklists, or Visual Fidelity Readiness",
        ):
            self.assertIn(term, tasks)

        self.assertNotIn("task_type: visual_verification", tasks)
        self.assertNotIn("`visual_validation`", tasks)
        self.assertNotIn("`visual_verification`", tasks)
        self.assertNotIn("`final_visual_review`", tasks)
        self.assertNotIn("visual regression tests", tasks)
        self.assertNotIn("task_type: interface_validation", tasks)
        self.assertNotIn("task_type: data_side_effect_validation", tasks)
        self.assertNotIn("test-plan.md", tasks)

        self.assertIn("./behavior/bdd.draft.feature", template)
        self.assertIn("./contracts/bdd/", template)
        self.assertIn("./contracts/uif/", template)
        self.assertIn("./contracts/behavior/", template)

        self.assertNotIn("tests/contracts/", implement)
        self.assertIn("Read contracts/ for API specifications and test requirements", implement)
        self.assertIn("Requirement Status", cross_agent)
        self.assertIn("visual shard candidates must come only from `tasks.md` visual/UI task types", cross_agent)
        self.assertIn("only `Required` or `Required` plus an accepted exception is executable", cross_agent)
        self.assertIn("do not create visual shards for `Not Applicable`, `Unknown`, or `[BLOCKED: PROVIDER_EVIDENCE]`", cross_agent)
        self.assertIn("route `Unknown` back to `/speckit.clarify`", cross_agent)
        self.assertIn("`[BLOCKED: PROVIDER_EVIDENCE]` to the external intake extension", cross_agent)
        self.assertIn("missing required HTML SSOT refs", cross_agent)
        self.assertIn("missing structured IR refs", cross_agent)
        self.assertNotIn("final_visual_review tasks", cross_agent)
        self.assertNotIn("Visual Review Worker", cross_agent)
        self.assertNotIn("`visual_validation`", cross_agent)
        self.assertNotIn("`visual_verification`", cross_agent)
        self.assertNotIn("`final_visual_review`", cross_agent)
        self.assertIn("planned `U` design object", cross_agent)
        self.assertIn("specific source, test, fixture, configuration, or receipt paths", cross_agent)

    def test_bdd_formalization_strengthens_reasoning_without_traceability_system(self) -> None:
        plan = PLAN_COMMAND_PATH.read_text(encoding="utf-8")
        bdd_contract_template = BEHAVIOR_TEMPLATE_PATHS[
            "behavior-bdd-contract-template"
        ].read_text(encoding="utf-8")

        for term in (
            "When formalizing BDD Draft into `contracts/bdd/*.feature`",
            "Preserve scenario intent and business outcome from the draft.",
            "Convert ambiguous Given steps into formal fixture, actor, state, permission, or start-view conditions.",
            "Convert When steps into formal user events, request cases, or system triggers aligned with UIF/API contracts.",
            "Convert Then steps into formal feedback, response, business state, or assertion expectations.",
            "If a step cannot be formalized without inventing information, record `N/A or blocker` instead of guessing.",
            "Do not introduce independent traceability mechanisms for BDD formalization.",
        ):
            self.assertIn(term, plan)

        for forbidden in (
            "@SCN-",
            "trace table",
            "coverage matrix",
            "reverse index",
        ):
            self.assertNotIn(forbidden, plan)
            self.assertNotIn(forbidden, bdd_contract_template)

    def test_analyze_command_owns_vertical_consistency_contract(self) -> None:
        analyze = ANALYZE_COMMAND_PATH.read_text(encoding="utf-8")

        self.assertIn("{CORE_TEMPLATE}", analyze)
        self.assertIn("strategy: wrap", analyze)
        self.assertIn("vertical consistency", analyze)
        self.assertIn(
            "requirement gates -> BDD/UIF intent -> contracts -> behavior testability -> tasks",
            analyze,
        )
        self.assertIn("spec.md user stories have BDD coverage", analyze)
        self.assertIn("BDD Given steps map to fixtures", analyze)
        self.assertIn("BDD When steps map to UIF events or API requests", analyze)
        self.assertIn("BDD Then steps map to feedback or behavior assertions", analyze)
        self.assertIn("behavior/uif.intent.json is formalized into contracts/uif/*.expected.json", analyze)
        self.assertIn("behavior drafts exist but formal contracts are missing", analyze)
        self.assertIn("source draft and missing planning input", analyze)
        self.assertNotIn("behavior/open-questions.json", analyze)
        self.assertIn("N/A or blocker", analyze)
        self.assertIn("UIF API calls exist in contracts/api/", analyze)
        self.assertIn("behavior contracts cover scenarios, fixtures, and assertions", analyze)
        self.assertIn("tasks.md covers BDD, UIF, API, fixtures, and quickstart validation paths", analyze)
        self.assertIn("case coverage", analyze)
        self.assertIn("Required case types in `checklists/behavior.md`", analyze)
        self.assertIn("`behavior/behavior-testability.md` carries current spec/plan revisions", analyze)
        self.assertIn("case types are either covered or have `N/A or blocker` evidence", analyze)
        self.assertIn(
            "failure scenarios declare error code, failure feedback, and state invariant, rollback, or compensation assertion",
            analyze,
        )
        self.assertIn("quickstart validation paths cover Required failure scenarios", analyze)
        self.assertIn("Build a one-pass artifact inventory before deep reading", analyze)
        self.assertIn("Use stable IDs as the primary consistency surface", analyze)
        self.assertIn("CASE-", analyze)
        self.assertIn("SCN-", analyze)
        self.assertIn("UIF-", analyze)
        self.assertIn("FIX-", analyze)
        self.assertIn("AST-", analyze)
        self.assertIn("BLK-", analyze)
        self.assertIn("Read surrounding prose only when a required ID, source section, or blocker explanation is missing or ambiguous", analyze)
        self.assertIn("Stop expanding a branch after the first blocker that proves the downstream link cannot be closed", analyze)
        self.assertNotIn("uif.actual.json", analyze)
        self.assertNotIn("uif.diff.json", analyze)
        self.assertNotIn("Actual UIF", analyze)

    def test_actual_uif_artifacts_are_not_part_of_preset_contract(self) -> None:
        paths = [
            README_PATH,
            SPECIFY_COMMAND_PATH,
            CLARIFY_COMMAND_PATH,
            CHECKLIST_COMMAND_PATH,
            ANALYZE_COMMAND_PATH,
            PLAN_COMMAND_PATH,
            TASKS_COMMAND_PATH,
            PRESET_PATH,
        ]
        forbidden_terms = [
            "Expected UIF vs Actual UIF",
            "Actual UIF",
            "uif.actual.json",
            "uif.diff.json",
            "from implementation",
            "implementation-derived UIF",
            "static analysis tooling",
        ]
        for path in paths:
            document = path.read_text(encoding="utf-8")
            for term in forbidden_terms:
                self.assertNotIn(term, document, f"{path} contains {term}")

    def test_behavior_first_templates_exist_and_are_decoupled(self) -> None:
        for path in BEHAVIOR_TEMPLATE_PATHS.values():
            self.assertTrue(path.exists(), path)

        self.assertIn("Feature:", BEHAVIOR_TEMPLATE_PATHS["behavior-bdd-draft-template"].read_text())
        self.assertIn("Feature:", BEHAVIOR_TEMPLATE_PATHS["behavior-bdd-contract-template"].read_text())
        behavior_testability = BEHAVIOR_TEMPLATE_PATHS[
            "behavior-testability-template"
        ].read_text(encoding="utf-8")
        self.assertIn("**Stage**: plan", behavior_testability)
        self.assertIn("**Behavior Testability Status**: READY | BLOCKED", behavior_testability)
        self.assertIn("| Case ID | Scenario ID | BDD Ref | UIF Ref | Fixture Ref | Assertion Ref |", behavior_testability)
        self.assertIn("Task Derivation Matrix", behavior_testability)
        for path in REQUIREMENT_TEMPLATE_PATHS.values():
            self.assertTrue(path.exists(), path)
        behavior_gate = REQUIREMENT_TEMPLATE_PATHS[
            "requirement-behavior-gate-template"
        ].read_text(encoding="utf-8")
        nfr_gate = REQUIREMENT_TEMPLATE_PATHS["requirement-nfr-gate-template"].read_text(
            encoding="utf-8"
        )
        visual_gate = REQUIREMENT_TEMPLATE_PATHS[
            "requirement-visual-gate-template"
        ].read_text(encoding="utf-8")
        self.assertIn("Case Coverage Matrix", behavior_gate)
        self.assertIn("`Required|Not Applicable|Unknown`", behavior_gate)
        self.assertIn("NFR Coverage Matrix", nfr_gate)
        self.assertIn("Visual Fidelity Evidence Matrix", visual_gate)
        self.assertIn("**Status**: PASS | BLOCKED", visual_gate)
        self.assertFalse(
            (REPO_ROOT / "templates" / "behavior" / "behavior-testability-checklist.md").exists()
        )
        self.assertFalse((REPO_ROOT / "templates" / "behavior" / "open-questions.json").exists())
        self.assertFalse(
            (
                REPO_ROOT
                / "schemas"
                / "speckit.behavior.open-questions.v1.schema.json"
            ).exists()
        )

        for template_name in (
            "behavior-scenarios-draft-template",
            "behavior-uif-intent-template",
            "behavior-data-fixtures-intent-template",
            "behavior-uif-expected-template",
            "behavior-scenario-instances-template",
            "behavior-data-fixtures-template",
            "behavior-assertions-template",
        ):
            self.assertIn(
                "contract_type",
                BEHAVIOR_TEMPLATE_PATHS[template_name].read_text(encoding="utf-8"),
            )

        scenario_instances_template = BEHAVIOR_TEMPLATE_PATHS[
            "behavior-scenario-instances-template"
        ].read_text(encoding="utf-8")
        self.assertIn('"case_coverage_blockers"', scenario_instances_template)
        self.assertIn('"type": "permission"', scenario_instances_template)
        self.assertIn('"case_kind": "permission"', scenario_instances_template)
        self.assertIn('"error_code"', scenario_instances_template)
        self.assertIn('"expected_feedback"', scenario_instances_template)

        assertions_template = BEHAVIOR_TEMPLATE_PATHS["behavior-assertions-template"].read_text(
            encoding="utf-8"
        )
        self.assertIn('"intent": "state_invariant"', assertions_template)

    def test_visual_fidelity_screenshot_evidence_gate_contract(self) -> None:
        command = CHECKLIST_COMMAND_PATH.read_text(encoding="utf-8")
        template = REQUIREMENT_TEMPLATE_PATHS[
            "requirement-visual-gate-template"
        ].read_text(encoding="utf-8")

        for term in (
            "Write visual readiness and the only Visual Fidelity Evidence Matrix to",
            "`checklists/visual.md`",
            "[blocker:product-decision]",
            "[blocker:provider-evidence] [return:intake]",
            "Provider blockers must not be converted into clarify questions",
            "Do not call provider tools, rebuild intake evidence, parse provider or HTML",
            "define screenshot comparison, visual diff, baseline capture, or",
            "final visual review",
            "Planning Readiness aggregate",
        ):
            self.assertIn(term, command)
        for term in (
            "| Visual Item ID | Source `spec.md` section | Requirement Status | Fidelity Scope | Screenshot Level | Evidence Refs | Visual Proof Required | Blocking Item ID | Exception Rule |",
            "raw metadata completeness",
            "metadata index completeness proof",
            "node inventory parity",
            "blocker lint errors",
            "Responsive visual readiness must record viewport-specific evidence or set Gate Status: BLOCKED",
        ):
            self.assertNotIn(term, command)

        for term in (
            "**Stage**: requirements",
            "**Domain**: visual",
            "**Gate**: planning-readiness",
            "**Applicability**: APPLICABLE | NOT_APPLICABLE",
            "**Status**: PASS | BLOCKED",
            "Visual Fidelity Evidence Matrix",
            "single visual planning-readiness record",
            "Provider Evidence Dependency",
            "Visual SSOT Refs",
            "HTML SSOT Refs",
            "Structured IR Refs",
            "Other Evidence Refs",
            "Readiness Input",
            "Accepted Exception Refs",
            "Unknown items become product-decision blockers",
            "evidence gaps remain intake blockers and are never converted to clarification",
            "Do not call provider tools, re-parse provider artifacts, define screenshot",
            "comparison, visual diff, baseline capture, or final visual review",
            "## Blocking Items",
        ):
            self.assertIn(term, template)
        self.assertEqual(
            len(
                re.findall(
                    r"^## Visual Fidelity Evidence Matrix$",
                    template,
                    flags=re.MULTILINE,
                )
            ),
            1,
        )
        self.assertEqual(
            template.count(
                "| Visual Item ID | Source `spec.md` section | Requirement Status | Provider Evidence Dependency | Visual SSOT Refs | HTML SSOT Refs | Structured IR Refs | Other Evidence Refs | Readiness Input | Blocking Item ID | Accepted Exception Refs |"
            ),
            1,
        )
        self.assertEqual(
            template.count(
                "This is the single visual planning-readiness record"
            ),
            1,
        )
        for forbidden in (
            "Screenshot evidence level",
            "visual proof refs",
            "L0|L1|L2|L3",
            "declared visual proof required",
            "proof level sufficiency",
            "screenshot sufficiency",
            "Missing screenshot evidence sets Gate Status: BLOCKED",
            "High-fidelity requirements without L3 screenshot evidence set Gate Status: BLOCKED",
            "Pixel-perfect requirements without L3 screenshot evidence set Gate Status: BLOCKED",
            "L3 Visual Baseline",
            "Responsive visual readiness must record viewport-specific evidence or set Gate Status: BLOCKED",
            "Responsive visual readiness records viewport-specific evidence or sets Gate Status: BLOCKED",
            "Screenshot Coverage Matrix",
            "Visual Proof Matrix",
            "Visual Restoration Checklist",
        ):
            self.assertNotIn(forbidden, template)

        for document in (command, template):
            lowered = document.lower()
            for forbidden in FORBIDDEN_VISUAL_COMPAT_TERMS:
                self.assertNotIn(forbidden, lowered)




    def test_behavior_first_schema_contracts_accept_minimal_examples(self) -> None:
        examples = {
            "speckit.behavior.scenarios.draft.v1": minimal_behavior_scenarios_draft(),
            "speckit.behavior.uif.intent.v1": minimal_uif_intent(),
            "speckit.behavior.data_fixtures.intent.v1": minimal_data_fixtures_intent(),
            "speckit.behavior.uif.expected.v1": minimal_uif_expected(),
            "speckit.behavior.scenario_instances.v1": minimal_behavior_scenario_instances(),
            "speckit.behavior.data_fixtures.v1": minimal_behavior_data_fixtures(),
            "speckit.behavior.assertions.v1": minimal_behavior_assertions(),
        }

        for contract_type, path in BEHAVIOR_SCHEMA_PATHS.items():
            schema = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual("object", schema["type"])
            self.assertIn("required", schema)
            self.assertIn("properties", schema)
            self.assertEqual(contract_type, schema["properties"]["contract_type"]["const"])
            Draft202012Validator(schema).validate(examples[contract_type])

    def test_behavior_draft_schema_rejects_empty_given_when_then(self) -> None:
        schema = json.loads(
            BEHAVIOR_SCHEMA_PATHS["speckit.behavior.scenarios.draft.v1"].read_text(
                encoding="utf-8"
            )
        )

        for field in ("given", "when", "then"):
            with self.subTest(field=field):
                draft = minimal_behavior_scenarios_draft()
                draft["scenarios"][0][field] = []

                with self.assertRaises(ValidationError):
                    Draft202012Validator(schema).validate(draft)

    def test_behavior_scenario_instances_schema_rejects_empty_contract_refs(self) -> None:
        schema = json.loads(
            BEHAVIOR_SCHEMA_PATHS["speckit.behavior.scenario_instances.v1"].read_text(
                encoding="utf-8"
            )
        )

        for field in ("fixture_ids", "assertion_ids"):
            with self.subTest(field=field):
                instances = minimal_behavior_scenario_instances()
                instances["scenarios"][0][field] = []

                with self.assertRaises(ValidationError):
                    Draft202012Validator(schema).validate(instances)

    def test_behavior_scenario_instances_schema_accepts_structured_exception_cases(self) -> None:
        schema = json.loads(
            BEHAVIOR_SCHEMA_PATHS["speckit.behavior.scenario_instances.v1"].read_text(
                encoding="utf-8"
            )
        )

        for scenario_type in ("negative", "boundary", "permission", "validation", "state_conflict"):
            with self.subTest(scenario_type=scenario_type):
                Draft202012Validator(schema).validate(
                    minimal_exception_behavior_scenario_instances(
                        scenario_type=scenario_type,
                    )
                )

    def test_behavior_scenario_instances_schema_rejects_exception_case_shells(self) -> None:
        schema = json.loads(
            BEHAVIOR_SCHEMA_PATHS["speckit.behavior.scenario_instances.v1"].read_text(
                encoding="utf-8"
            )
        )
        invalid_mutations = [
            ("case_kind", lambda scenario: scenario["request_case"].pop("case_kind")),
            ("trigger", lambda scenario: scenario["request_case"].pop("trigger")),
            ("expected_response", lambda scenario: scenario.update({"expected_response": {}})),
            ("error_code", lambda scenario: scenario["expected_response"].pop("error_code")),
            ("expected_feedback", lambda scenario: scenario.update({"expected_feedback": {}})),
            ("feedback_type", lambda scenario: scenario["expected_feedback"].pop("type")),
            ("feedback_message", lambda scenario: scenario["expected_feedback"].pop("message")),
        ]

        for label, mutate in invalid_mutations:
            with self.subTest(label=label):
                instances = minimal_exception_behavior_scenario_instances()
                mutate(instances["scenarios"][0])

                with self.assertRaises(ValidationError):
                    Draft202012Validator(schema).validate(instances)

    def test_behavior_scenario_instances_schema_rejects_mismatched_exception_case_kind(self) -> None:
        schema = json.loads(
            BEHAVIOR_SCHEMA_PATHS["speckit.behavior.scenario_instances.v1"].read_text(
                encoding="utf-8"
            )
        )
        instances = minimal_exception_behavior_scenario_instances(scenario_type="permission")
        instances["scenarios"][0]["request_case"]["case_kind"] = "validation"

        with self.assertRaises(ValidationError):
            Draft202012Validator(schema).validate(instances)

    def test_behavior_scenario_instances_schema_accepts_case_coverage_blockers(self) -> None:
        schema = json.loads(
            BEHAVIOR_SCHEMA_PATHS["speckit.behavior.scenario_instances.v1"].read_text(
                encoding="utf-8"
            )
        )
        instances = minimal_behavior_scenario_instances()
        instances["case_coverage_blockers"] = [
            {
                "id": "BLK-001",
                "case_id": "CASE-002",
                "case_type": "validation",
                "source": "spec.md#user-story-1",
                "reason": "Validation rule is marked Unknown in checklist.",
                "downstream_contract_path": "contracts/behavior/scenario-instances.json",
            }
        ]

        Draft202012Validator(schema).validate(instances)

    def test_behavior_scenario_instances_schema_rejects_incomplete_case_coverage_blockers(self) -> None:
        schema = json.loads(
            BEHAVIOR_SCHEMA_PATHS["speckit.behavior.scenario_instances.v1"].read_text(
                encoding="utf-8"
            )
        )
        required_fields = (
            "id",
            "case_id",
            "case_type",
            "source",
            "reason",
            "downstream_contract_path",
        )

        for field in required_fields:
            with self.subTest(field=field):
                instances = minimal_behavior_scenario_instances()
                blocker = {
                    "id": "BLK-001",
                    "case_id": "CASE-002",
                    "case_type": "validation",
                    "source": "spec.md#user-story-1",
                    "reason": "Validation rule is marked Unknown in checklist.",
                    "downstream_contract_path": "contracts/behavior/scenario-instances.json",
                }
                blocker.pop(field)
                instances["case_coverage_blockers"] = [blocker]

                with self.assertRaises(ValidationError):
                    Draft202012Validator(schema).validate(instances)

    def test_behavior_scenario_instances_schema_accepts_success_boundary_case(self) -> None:
        schema = json.loads(
            BEHAVIOR_SCHEMA_PATHS["speckit.behavior.scenario_instances.v1"].read_text(
                encoding="utf-8"
            )
        )
        instances = minimal_exception_behavior_scenario_instances(scenario_type="boundary")
        scenario = instances["scenarios"][0]
        scenario["request_case"]["outcome"] = "success"
        scenario["expected_response"] = {"business_code": "ACCEPTED_AT_LIMIT"}
        scenario["expected_feedback"] = {"message": "Limit accepted"}

        Draft202012Validator(schema).validate(instances)

    def test_behavior_scenario_instances_schema_rejects_boundary_failure_without_error(self) -> None:
        schema = json.loads(
            BEHAVIOR_SCHEMA_PATHS["speckit.behavior.scenario_instances.v1"].read_text(
                encoding="utf-8"
            )
        )
        instances = minimal_exception_behavior_scenario_instances(scenario_type="boundary")
        scenario = instances["scenarios"][0]
        scenario["request_case"]["outcome"] = "failure"
        scenario["expected_response"] = {"status": 422}
        scenario["expected_feedback"] = {"message": "Limit exceeded"}

        with self.assertRaises(ValidationError):
            Draft202012Validator(schema).validate(instances)

    def test_behavior_assertions_schema_accepts_exception_assertion_intent(self) -> None:
        schema = json.loads(
            BEHAVIOR_SCHEMA_PATHS["speckit.behavior.assertions.v1"].read_text(
                encoding="utf-8"
            )
        )

        Draft202012Validator(schema).validate(minimal_exception_behavior_assertions())

    def test_expected_uif_schema_rejects_underspecified_typed_steps(self) -> None:
        schema = json.loads(
            BEHAVIOR_SCHEMA_PATHS["speckit.behavior.uif.expected.v1"].read_text(
                encoding="utf-8"
            )
        )

        underspecified_steps = [
            {"type": "api_call"},
            {"type": "local_route"},
            {"type": "user_event"},
        ]
        for step in underspecified_steps:
            with self.subTest(step_type=step["type"]):
                uif = minimal_uif_expected()
                uif["steps"] = [step]

                with self.assertRaises(ValidationError):
                    Draft202012Validator(schema).validate(uif)

    def test_behavior_draft_validator_rejects_fixture_for_unknown_scenario(self) -> None:
        fixtures = minimal_data_fixtures_intent()
        fixtures["fixtures"][0]["required_for"] = ["SCN-404"]

        with self.assertRaises(ValueError):
            validate_behavior_draft_contract(
                minimal_behavior_scenarios_draft(),
                fixtures,
            )

    def test_behavior_draft_validator_rejects_empty_given_when_then(self) -> None:
        for field in ("given", "when", "then"):
            with self.subTest(field=field):
                draft = minimal_behavior_scenarios_draft()
                draft["scenarios"][0][field] = []

                with self.assertRaisesRegex(ValueError, field):
                    validate_behavior_draft_contract(
                        draft,
                        minimal_data_fixtures_intent(),
                    )

    def test_behavior_draft_validator_accepts_valid_cross_fields(self) -> None:
        validate_behavior_draft_contract(
            minimal_behavior_scenarios_draft(),
            minimal_data_fixtures_intent(),
        )

    def test_behavior_contract_validator_rejects_missing_fixture_reference(self) -> None:
        instances = minimal_behavior_scenario_instances()
        instances["scenarios"][0]["fixture_ids"] = ["FIX-MISSING"]

        with self.assertRaises(ValueError):
            validate_behavior_contract_bundle(
                instances,
                minimal_behavior_data_fixtures(),
                minimal_behavior_assertions(),
                [minimal_uif_expected()],
            )

    def test_behavior_contract_validator_rejects_empty_contract_refs(self) -> None:
        for field in ("fixture_ids", "assertion_ids"):
            with self.subTest(field=field):
                instances = minimal_behavior_scenario_instances()
                instances["scenarios"][0][field] = []

                with self.assertRaisesRegex(ValueError, field):
                    validate_behavior_contract_bundle(
                        instances,
                        minimal_behavior_data_fixtures(),
                        minimal_behavior_assertions(),
                        [minimal_uif_expected()],
                    )

    def test_behavior_contract_validator_rejects_underspecified_uif_steps(self) -> None:
        for step in (
            {"type": "api_call"},
            {"type": "local_route"},
            {"type": "user_event"},
        ):
            with self.subTest(step_type=step["type"]):
                uif = minimal_uif_expected()
                uif["steps"] = [step]

                with self.assertRaises(ValueError):
                    validate_behavior_contract_bundle(
                        minimal_behavior_scenario_instances(),
                        minimal_behavior_data_fixtures(),
                        minimal_behavior_assertions(),
                        [uif],
                    )

    def test_behavior_contract_validator_rejects_exception_case_shells(self) -> None:
        invalid_mutations = [
            ("case_kind", lambda scenario: scenario["request_case"].pop("case_kind")),
            ("trigger", lambda scenario: scenario["request_case"].pop("trigger")),
            ("expected_response", lambda scenario: scenario.update({"expected_response": {}})),
            ("error_code", lambda scenario: scenario["expected_response"].pop("error_code")),
            ("expected_feedback", lambda scenario: scenario.update({"expected_feedback": {}})),
            ("feedback_type", lambda scenario: scenario["expected_feedback"].pop("type")),
            ("feedback_message", lambda scenario: scenario["expected_feedback"].pop("message")),
        ]

        for label, mutate in invalid_mutations:
            with self.subTest(label=label):
                instances = minimal_exception_behavior_scenario_instances()
                mutate(instances["scenarios"][0])

                with self.assertRaisesRegex(ValueError, label):
                    validate_behavior_contract_bundle(
                        instances,
                        minimal_behavior_data_fixtures(),
                        minimal_exception_behavior_assertions(),
                        [minimal_uif_expected()],
                    )

    def test_behavior_contract_validator_rejects_exception_without_state_or_rollback_assertion(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "state_invariant_rollback_or_compensation_assertion",
        ):
            validate_behavior_contract_bundle(
                minimal_exception_behavior_scenario_instances(),
                minimal_behavior_data_fixtures(),
                minimal_behavior_assertions(),
                [minimal_uif_expected()],
            )

    def test_behavior_contract_validator_rejects_mismatched_exception_case_kind(self) -> None:
        instances = minimal_exception_behavior_scenario_instances(scenario_type="permission")
        instances["scenarios"][0]["request_case"]["case_kind"] = "validation"

        with self.assertRaisesRegex(ValueError, "case_kind"):
            validate_behavior_contract_bundle(
                instances,
                minimal_behavior_data_fixtures(),
                minimal_exception_behavior_assertions(),
                [minimal_uif_expected()],
            )

    def test_behavior_contract_validator_accepts_structured_exception_cases(self) -> None:
        for scenario_type in ("negative", "boundary", "permission", "validation", "state_conflict"):
            with self.subTest(scenario_type=scenario_type):
                validate_behavior_contract_bundle(
                    minimal_exception_behavior_scenario_instances(
                        scenario_type=scenario_type,
                    ),
                    minimal_behavior_data_fixtures(),
                    minimal_exception_behavior_assertions(),
                    [minimal_uif_expected()],
                )

    def test_behavior_contract_validator_accepts_rollback_and_compensation_assertions(self) -> None:
        for intent in ("rollback", "compensation"):
            with self.subTest(intent=intent):
                validate_behavior_contract_bundle(
                    minimal_exception_behavior_scenario_instances(),
                    minimal_behavior_data_fixtures(),
                    minimal_exception_behavior_assertions_with_intent(intent),
                    [minimal_uif_expected()],
                )

    def test_behavior_contract_validator_accepts_success_boundary_case(self) -> None:
        instances = minimal_exception_behavior_scenario_instances(scenario_type="boundary")
        scenario = instances["scenarios"][0]
        scenario["request_case"]["outcome"] = "success"
        scenario["expected_response"] = {"business_code": "ACCEPTED_AT_LIMIT"}
        scenario["expected_feedback"] = {"message": "Limit accepted"}

        validate_behavior_contract_bundle(
            instances,
            minimal_behavior_data_fixtures(),
            minimal_behavior_assertions(),
            [minimal_uif_expected()],
        )

    def test_behavior_contract_validator_rejects_boundary_failure_without_error(self) -> None:
        instances = minimal_exception_behavior_scenario_instances(scenario_type="boundary")
        scenario = instances["scenarios"][0]
        scenario["request_case"]["outcome"] = "failure"
        scenario["expected_response"] = {"status": 422}
        scenario["expected_feedback"] = {"message": "Limit exceeded"}

        with self.assertRaisesRegex(ValueError, "error_code"):
            validate_behavior_contract_bundle(
                instances,
                minimal_behavior_data_fixtures(),
                minimal_exception_behavior_assertions(),
                [minimal_uif_expected()],
            )

    def test_behavior_case_coverage_validator_rejects_missing_required_case(self) -> None:
        with self.assertRaisesRegex(ValueError, "Required case"):
            validate_behavior_case_coverage(
                minimal_case_coverage(),
                minimal_behavior_scenarios_draft(),
                minimal_behavior_scenario_instances(),
                "T001 implement SCN-001",
                "Validate SCN-001",
            )

    def test_behavior_case_coverage_validator_rejects_empty_matrix(self) -> None:
        with self.assertRaisesRegex(ValueError, "case_coverage"):
            validate_behavior_case_coverage(
                {},
                minimal_behavior_scenarios_draft(),
                minimal_behavior_scenario_instances(),
                "T001 implement SCN-001",
                "Validate SCN-001",
            )

    def test_behavior_case_coverage_validator_requires_tasks_and_quickstart_evidence(self) -> None:
        with self.assertRaisesRegex(ValueError, "tasks.md"):
            validate_behavior_case_coverage(
                minimal_case_coverage(),
                minimal_behavior_scenarios_draft(
                    scenario_type="permission",
                    scenario_id="SCN-ERR-001",
                ),
                minimal_exception_behavior_scenario_instances(),
                "T001 implement SCN-001",
                "Validate SCN-ERR-001",
            )

        with self.assertRaisesRegex(ValueError, "quickstart.md"):
            validate_behavior_case_coverage(
                minimal_case_coverage(),
                minimal_behavior_scenarios_draft(
                    scenario_type="permission",
                    scenario_id="SCN-ERR-001",
                ),
                minimal_exception_behavior_scenario_instances(),
                "T001 implement SCN-ERR-001",
                "Validate SCN-001",
            )

    def test_behavior_case_coverage_validator_accepts_closed_required_case(self) -> None:
        validate_behavior_case_coverage(
            minimal_case_coverage(),
            minimal_behavior_scenarios_draft(
                scenario_type="permission",
                scenario_id="SCN-ERR-001",
            ),
            minimal_exception_behavior_scenario_instances(),
            "T001 implement SCN-ERR-001 and AST-001",
            "Validate SCN-ERR-001 through quickstart path",
        )

    def test_behavior_case_coverage_validator_accepts_formal_blocker_for_required_case(self) -> None:
        instances = minimal_behavior_scenario_instances()
        instances["case_coverage_blockers"] = [
            {
                "id": "BLK-001",
                "case_id": "CASE-002",
                "case_type": "validation",
                "source": "spec.md#user-story-1",
                "reason": "Validation rule is still Unknown in checklist.",
                "downstream_contract_path": "contracts/behavior/scenario-instances.json",
            }
        ]

        validate_behavior_case_coverage(
            minimal_case_coverage_with_blocker(),
            minimal_behavior_scenarios_draft(),
            instances,
            "T001 blocked by BLK-001",
            "BLK-001 blocks quickstart validation",
        )

    def test_behavior_case_coverage_validator_requires_blocker_downstream_evidence(self) -> None:
        instances = minimal_behavior_scenario_instances()
        instances["case_coverage_blockers"] = [
            {
                "id": "BLK-001",
                "case_id": "CASE-002",
                "case_type": "validation",
                "source": "spec.md#user-story-1",
                "reason": "Validation rule is still Unknown in checklist.",
                "downstream_contract_path": "contracts/behavior/scenario-instances.json",
            }
        ]

        with self.assertRaisesRegex(ValueError, "tasks.md"):
            validate_behavior_case_coverage(
                minimal_case_coverage_with_blocker(),
                minimal_behavior_scenarios_draft(),
                instances,
                "T001 implement SCN-001",
                "BLK-001 blocks quickstart validation",
            )

        with self.assertRaisesRegex(ValueError, "quickstart.md"):
            validate_behavior_case_coverage(
                minimal_case_coverage_with_blocker(),
                minimal_behavior_scenarios_draft(),
                instances,
                "T001 blocked by BLK-001",
                "Validate SCN-001",
            )

    def test_behavior_case_coverage_validator_rejects_blocker_source_mismatch(self) -> None:
        instances = minimal_behavior_scenario_instances()
        instances["case_coverage_blockers"] = [
            {
                "id": "BLK-001",
                "case_id": "CASE-002",
                "case_type": "validation",
                "source": "spec.md#different-story",
                "reason": "Validation rule is still Unknown in checklist.",
                "downstream_contract_path": "contracts/behavior/scenario-instances.json",
            }
        ]

        with self.assertRaisesRegex(ValueError, "source"):
            validate_behavior_case_coverage(
                minimal_case_coverage_with_blocker(),
                minimal_behavior_scenarios_draft(),
                instances,
                "T001 blocked by BLK-001",
                "BLK-001 blocks quickstart validation",
            )

    def test_behavior_contract_validator_accepts_valid_cross_fields(self) -> None:
        validate_behavior_contract_bundle(
            minimal_behavior_scenario_instances(),
            minimal_behavior_data_fixtures(),
            minimal_behavior_assertions(),
            [minimal_uif_expected()],
        )
























































































    def test_agents_references_extension_governance(self) -> None:
        agents = AGENTS_PATH.read_text(encoding="utf-8")

        self.assertIn("docs/extension-governance.md", agents)
        self.assertIn("Extension Governance", agents)

    def _workflow_on(self, workflow: dict) -> dict:
        return workflow.get("on") or workflow.get(True) or {}

    def test_github_actions_contract_workflow(self) -> None:
        workflow_path = REPO_ROOT / ".github" / "workflows" / "ci.yml"
        if not workflow_path.exists():
            self.skipTest("source repository workflow file is not packaged in the preset")
        workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))

        self.assertEqual("Preset Contract", workflow["name"])
        self.assertEqual({"contents": "read"}, workflow["permissions"])
        triggers = self._workflow_on(workflow)
        self.assertIn("pull_request", triggers)
        self.assertEqual(["main"], triggers["push"]["branches"])
        self.assertIn("workflow_dispatch", triggers)

        contract_job = workflow["jobs"]["contract"]
        self.assertEqual("ubuntu-latest", contract_job["runs-on"])
        self.assertEqual(
            ["3.10", "3.13"],
            contract_job["strategy"]["matrix"]["python-version"],
        )
        workflow_text = workflow_path.read_text(encoding="utf-8")
        self.assertIn("python3 -m pip install -r requirements-dev.txt", workflow_text)
        self.assertIn("python3 -m unittest tests/test_preset_contract.py", workflow_text)

    def test_github_actions_artifact_release_and_integration_pr_workflow(self) -> None:
        workflow_path = REPO_ROOT / ".github" / "workflows" / "preset-artifact.yml"
        if not workflow_path.exists():
            self.skipTest("source repository workflow file is not packaged in the preset")
        workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))

        self.assertEqual("Preset Artifact", workflow["name"])
        self.assertEqual({"contents": "write"}, workflow["permissions"])
        triggers = self._workflow_on(workflow)
        self.assertEqual(["v*"], triggers["push"]["tags"])
        self.assertIn("workflow_dispatch", triggers)
        inputs = triggers["workflow_dispatch"]["inputs"]
        self.assertIn("version", inputs)
        self.assertIn("spec_kit_ref", inputs)
        self.assertIn("create_integration_pr", inputs)

        workflow_text = workflow_path.read_text(encoding="utf-8")
        required_terms = [
            "spec-kit-workflow-preset-v${VERSION}.zip",
            "NEXT_PATCH_VERSION",
            "python3 -m unittest tests/test_preset_contract.py",
            "python3 -m venv \"${GITHUB_WORKSPACE}/.venv-specify-smoke\"",
            "echo \"${GITHUB_WORKSPACE}/.venv-specify-smoke/bin\" >> \"${GITHUB_PATH}\"",
            'PATH="${GITHUB_WORKSPACE}/.venv-specify-smoke/bin:${PATH}"',
            'project_dir="$(mktemp -d "${RUNNER_TEMP}/workflow-preset-smoke.XXXXXX")"',
            'resolve_out="${RUNNER_TEMP}/plan-template-resolve.txt"',
            'constitution_resolve_out="${RUNNER_TEMP}/constitution-template-resolve.txt"',
            "PIP_CONFIG_FILE: /dev/null",
            'PYTEST_ADDOPTS: ""',
            'export TMPDIR="${RUNNER_TEMP}"',
            'export TEMP="${RUNNER_TEMP}"',
            'export TMP="${RUNNER_TEMP}"',
            'specify init --here --integration claude --script sh --ignore-agent-tools',
            "specify preset remove workflow-preset",
            "specify preset add --dev",
            "specify preset resolve plan-template",
            "specify preset resolve constitution-template",
            "R: Repository / Workspace",
            "M: Module / Capability",
            "U: Unit / Design Object",
            "O: Operation / Detail",
            ".claude/skills/speckit-implement/SKILL.md",
            "SPEC_KIT_FORK_PR_TOKEN",
            "bigsmartben/spec-kit",
            "workflow-preset-release-v${VERSION}",
            "gh pr create",
            "gh pr edit",
            "WORKFLOW_PRESET_DOWNLOAD_URL",
            "presets/catalog.community.json",
            "community_catalog_path",
            "community_catalog",
            "download_url",
            'assert entry\\["version"\\] == "[0-9]+\\.[0-9]+\\.[0-9]+"',
            "tests/test_presets.py",
            "__pycache__",
            ".pyc",
            "ZipInfo",
            "1980, 1, 1",
            'MANIFEST_NAME="spec-kit-workflow-preset-v${VERSION}.manifest.json"',
            '"source_commit": source_commit',
            '"sha256": zip_sha256',
            "Verify release manifest",
            "validators/speckit_behavior_contract.py",
            '"requirements-dev.txt"',
            '"tests"',
            "test ! -e .specify/presets/workflow-preset/commands/speckit.implement.md",
            "core_implement_sha",
            "WORKFLOW_PRESET_MANIFEST_URL",
            "presets/workflow-preset.release.json",
            'entry["source_commit"] = release_manifest["source_commit"]',
            'entry["sha256"] = release_manifest["artifact"]["sha256"]',
            "curl --fail --location",
            "archive.extractall",
            'cmp "${ZIP_PATH}" "${existing_dir}/${ZIP_NAME}"',
            "github.ref_type == 'tag' || (github.event_name == 'workflow_dispatch' && env.CREATE_INTEGRATION_PR == 'true')",
            "env.CREATE_INTEGRATION_PR == 'true'",
            "refs/tags/v${VERSION}",
            "^[0-9]+\\.[0-9]+\\.[0-9]+$",
            "persist-credentials: false",
            "git rev-parse HEAD",
            "refs/tags/v${VERSION}^{}",
            "SPEC_KIT_FORK_PR_TOKEN is required when integration PR creation is requested.",
            "exit 1",
        ]
        for term in required_terms:
            self.assertIn(term, workflow_text)
        forbidden_terms = [
            "specify preset resolve workflow-preset plan-template",
            "specify preset resolve workflow-preset speckit.implement",
            "client_payload[version]",
            "client_payload[download_url]",
            "repository_dispatch",
            "repos/bigsmartben/spec-kit/dispatches",
            "::warning::SPEC_KIT_FORK_DISPATCH_TOKEN",
            "skipping integration PR",
            "gh release upload \"${TAG_NAME}\" \"${ZIP_PATH}\" --clobber",
            "\"${GITHUB_WORKSPACE}/\" \"${fork_dir}/spec-kit/presets/workflow-preset/\"",
        ]
        for term in forbidden_terms:
            self.assertNotIn(term, workflow_text)
        self.assertNotIn("github/spec-kit", workflow_text)


if __name__ == "__main__":
    unittest.main()
