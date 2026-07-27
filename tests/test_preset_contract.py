from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from validators.speckit_analyze_contract import (
    audit_cross_command_consistency,
    audit_data_model_obligations,
    audit_source_reference_contract,
)
from validators.speckit_behavior_contract import validate_behavior_contract_bundle
from validators.speckit_plan_contract import validate_plan_artifact_bundle
from validators.speckit_test_contract import (
    validate_test_conditions,
    validate_test_readiness,
)


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "preset.yml"
COMMANDS = ROOT / "commands"
TEMPLATES = ROOT / "templates"
SCHEMAS = ROOT / "schemas"
VALIDATORS = ROOT / "validators"
GOVERNANCE = ROOT / "docs" / "extension-governance.md"
README = ROOT / "README.md"
AGENTS = ROOT / "AGENTS.md"
CROSS_AGENT = ROOT / "tests" / "contracts" / "speckit-cross-agent-protocol.md"
ARTIFACT_WORKFLOW = ROOT / ".github" / "workflows" / "preset-artifact.yml"
PLAN_BUNDLE_FIXTURES = ROOT / "tests" / "fixtures" / "plan_bundles"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_json(path: Path) -> dict:
    return json.loads(read(path))


def minimal_test_conditions(*, technique: str = "contract_testing") -> dict:
    return {
        "contract_type": "speckit.test.conditions.v1",
        "feature": "refund",
        "conditions": [
            {
                "id": "TC-001",
                "source_refs": ["FR-001"],
                "risk_or_priority": "high",
                "levels": ["contract"],
                "types": ["functional"],
                "techniques": [technique],
                "execution_mode": "sandbox",
                "fixture_refs": ["FIX-001"],
                "environment_refs": ["ENV-SANDBOX"],
                "oracle": {"kind": "response", "expected": "SUCCESS"},
                "evidence_requirement": "captured command output",
                "related_refs": ["contracts/api/refund.yaml"],
                "quickstart_ref": "VAL-001",
                "status": "required",
            }
        ],
    }


def minimal_uif() -> dict:
    return {
        "contract_type": "speckit.behavior.uif.expected.v1",
        "id": "UIF-001",
        "source": "ui-ux-design.md#uif-contracts",
        "source_refs": ["SRC-003"],
        "requirement_refs": ["UI-001", "VIS-001"],
        "type": "expected",
        "start_view": {"id": "VIEW-001", "name": "Order"},
        "steps": [
            {"id": "EVT-001", "type": "user_event", "label": "Submit"},
            {
                "type": "api_call",
                "api": {"method": "POST", "path": "/orders/1/refund"},
            },
        ],
        "feedback_candidates": [
            {"id": "FB-001", "type": "toast", "message": "Submitted"}
        ],
        "visual_item_refs": ["VIS-001"],
        "viewport_matrix_refs": ["UI-001#viewports"],
        "state_matrix_refs": ["UI-001#states"],
        "visual_proof_refs": [],
        "accepted_exception_refs": [],
    }


def source_contract_snapshot() -> dict:
    return {
        "spec": {
            "requirement_refs": ["FR-001", "FR-002", "UI-001", "VIS-001"],
            "sources": [
                {
                    "ref": "SRC-001",
                    "role": "requirement-input",
                    "locator_or_description": "current conversation direction",
                    "authorized_scope": "refund submission behavior",
                    "projected_refs": ["FR-001"],
                    "status": "projected",
                },
                {
                    "ref": "SRC-002",
                    "role": "requirement-input",
                    "locator_or_description": "opaque product document",
                    "revision": "supplied-r7",
                    "authorized_scope": "refund eligibility section",
                    "feature_slice": "refund eligibility",
                    "broad": True,
                    "projected_refs": ["FR-002"],
                    "status": "projected",
                },
                {
                    "ref": "SRC-003",
                    "role": "visual-input",
                    "locator_or_description": "opaque executable visual reference",
                    "authorized_scope": "refund error states",
                    "projected_refs": ["UI-001", "VIS-001"],
                    "status": "projected",
                    "uif_required": True,
                },
                {
                    "ref": "SRC-004",
                    "role": "technical-evidence",
                    "locator_or_description": "latency measurement report",
                    "authorized_scope": "technical evidence citation only",
                    "projected_refs": [],
                    "status": "retained",
                },
                {
                    "ref": "SRC-005",
                    "role": "context-only",
                    "locator_or_description": "competitor overview",
                    "authorized_scope": "background only",
                    "projected_refs": [],
                    "status": "context-only",
                },
            ],
        },
        "plan": {
            "ui_ux_mappings": [
                {"source_ref": "SRC-003", "requirement_ref": "UI-001"},
                {"source_ref": "SRC-003", "requirement_ref": "VIS-001"},
            ],
            "uif_mappings": [
                {"source_ref": "SRC-003", "requirement_ref": "UI-001"},
                {"source_ref": "SRC-003", "requirement_ref": "VIS-001"},
            ],
        },
    }


def minimal_assertions() -> dict:
    return {
        "contract_type": "speckit.behavior.assertions.v1",
        "assertions": [
            {
                "id": "AST-001",
                "target": "refund.status",
                "operator": "equals",
                "expected": "PENDING",
                "intent": "business_state",
            }
        ],
    }


class ManifestAndGovernanceTests(unittest.TestCase):
    def test_manifest_declares_existing_files_and_no_implement_override(self) -> None:
        manifest = yaml.safe_load(read(MANIFEST))
        entries = manifest["provides"]["templates"]
        names = {entry["name"] for entry in entries}

        self.assertEqual(len(names), len(entries))
        self.assertEqual(7, sum(entry["type"] == "command" for entry in entries))
        self.assertNotIn("speckit.implement", names)
        for entry in entries:
            self.assertTrue((ROOT / entry["file"]).exists(), entry)

        for forbidden in (
            COMMANDS / "speckit.implement.md",
            SCHEMAS / "speckit.implement.manifest.v1.schema.json",
            SCHEMAS / "speckit.implement.handoff.v2.schema.json",
            SCHEMAS / "speckit.implement.receipt.v1.schema.json",
            VALIDATORS / "speckit_implement_contract.py",
        ):
            self.assertFalse(forbidden.exists(), forbidden)

    def test_manifest_strategies_enforce_negative_ownership(self) -> None:
        entries = {
            item["name"]: item
            for item in yaml.safe_load(read(MANIFEST))["provides"]["templates"]
        }
        self.assertEqual("replace", entries["speckit.constitution"]["strategy"])
        self.assertEqual("replace", entries["speckit.specify"]["strategy"])
        self.assertEqual("replace", entries["speckit.clarify"]["strategy"])
        for wrapped in (
            "speckit.checklist",
            "speckit.plan",
            "speckit.tasks",
            "speckit.analyze",
            "spec-template",
            "plan-template",
        ):
            self.assertEqual("wrap", entries[wrapped]["strategy"])

    def test_governance_uses_one_authority_and_gate_vocabulary(self) -> None:
        documents = (read(GOVERNANCE), read(AGENTS), read(CROSS_AGENT))
        for document in documents:
            self.assertIn("Spec Kit core", document)
            self.assertNotIn("implementation-manifest.json", document)
            self.assertNotIn("worker-result.json", document)

        governance = documents[0]
        self.assertIn("Authority And Gate Ownership", governance)
        self.assertIn("Requirement Command Independence", governance)
        self.assertIn("X0–X4 Planning Artifact Boundaries", governance)
        self.assertIn("Tasks As A Pure Plan Mapper", governance)
        self.assertIn("Analyze Cross-Command Audit", governance)
        self.assertIn("Source Reference Contract", governance)
        self.assertIn(
            "SRC-* + UI/VIS-* -> ui-ux-design.md -> UIF source_refs + requirement_refs",
            governance,
        )

    def test_source_contract_adds_no_intake_or_transfer_runtime(self) -> None:
        for path in (
            ROOT / "templates" / "source-import-manifest.json",
            ROOT / "schemas" / "speckit.source-import.v1.schema.json",
            ROOT / "validators" / "speckit_source_adapter.py",
            ROOT / "commands" / "speckit.intake.md",
            ROOT / "scripts" / "source-dispatch.sh",
        ):
            self.assertFalse(path.exists(), path)

        for document in (
            read(GOVERNANCE),
            read(COMMANDS / "speckit.specify.md"),
            read(COMMANDS / "speckit.plan.md"),
            read(COMMANDS / "speckit.analyze.md"),
        ):
            self.assertNotIn("## Intake", document)


class ConstitutionAndArchitectureTests(unittest.TestCase):
    def test_constitution_replacement_preserves_hooks_and_independent_scopes(self) -> None:
        command = read(COMMANDS / "speckit.constitution.md")
        self.assertIn("strategy: replace", command)
        self.assertNotIn("{CORE_TEMPLATE}", command)
        for term in (
            "## User Input",
            "hooks.before_constitution",
            "hooks.after_constitution",
            "Explicit Input Agreement",
            "Independent Write Scopes",
            "CONSTITUTION_OUTPUT_READY",
            "ARCHITECTURE_OUTPUT_READY",
            "intent-first",
            "repo-first",
            "technical-evidence",
            "locator remains opaque",
        ):
            self.assertIn(term, command)

    def test_constitution_template_owns_sdd_governance_only(self) -> None:
        template = read(TEMPLATES / "constitution-template.md")
        for term in (
            "{CORE_TEMPLATE}",
            "SDD Workflow Governance",
            "Gate Ownership",
            "Command Internal Gate",
            "Official Core Gate",
            "Cross-Command Consistency Gate",
            "Intake is external evidence acquisition, not an SDD stage",
        ):
            self.assertIn(term, template)
        for mapping in (
            "R: Repository / Workspace",
            "M: Module / Capability",
            "U: Unit / Design Object",
            "O: Operation / Detail",
            "Planning locks M + U",
        ):
            self.assertIn(mapping, template)

    def test_architecture_template_is_pure_technical_ssot(self) -> None:
        template = read(TEMPLATES / "architecture-template.md")
        self.assertEqual(
            [
                "Architecture Overview",
                "System Boundary",
                "Conceptual Model",
                "Technical Decisions & Evidence",
                "Technical Constraints & Gaps",
            ],
            re.findall(r"^## (.+)$", template, flags=re.MULTILINE),
        )
        for prefix in ("BND-", "CON-", "DEC-", "CST-", "GAP-"):
            self.assertIn(prefix, template)
        for state in (
            "observed-current",
            "inferred",
            "approved-target",
            "migration-gap",
        ):
            self.assertIn(state, template)
        for forbidden in (
            "Planning Guardrails",
            "Planning Implication",
            "Planning Impact",
            "/speckit.plan",
            "/speckit.tasks",
        ):
            self.assertNotIn(forbidden, template)


class RequirementCommandTests(unittest.TestCase):
    def test_full_spectrum_spec_carrier_is_optional_and_stable(self) -> None:
        template = read(TEMPLATES / "spec-template.md")
        for heading in (
            "Functional Requirements",
            "Non-Functional Requirements",
            "UX Journeys and Interaction Expectations",
            "UI Surfaces and States",
            "Visual Requirements and Sources",
            "Security and Privacy",
            "Data and Integration Constraints",
            "Dependencies and Boundaries",
            "Assumptions",
            "Exclusions",
            "Source References",
            "Unresolved Product Decisions",
            "Source Evidence Blockers",
            "Clarifications",
        ):
            self.assertIn(heading, template)
        for prefix in ("FR-", "NFR-", "UX-", "UI-", "VIS-"):
            self.assertIn(prefix, template)
        self.assertIn("content carrier, not a completeness checklist", template)

    def test_source_reference_template_has_one_source_neutral_shape(self) -> None:
        template = read(TEMPLATES / "spec-template.md")
        for column in (
            "SRC ref",
            "Role",
            "Opaque locator / description",
            "Revision / identity",
            "Authorized scope / facts",
            "Projected requirement refs",
            "Status / blocker",
        ):
            self.assertIn(column, template)
        for role in (
            "requirement-input",
            "visual-input",
            "technical-evidence",
            "context-only",
        ):
            self.assertIn(role, template)
        self.assertIn("broad source without a\nsafe feature slice", template)

    def test_specify_has_no_core_checklist_side_effect(self) -> None:
        command = read(COMMANDS / "speckit.specify.md")
        for term in (
            "strategy: replace",
            "hooks.before_specify",
            "hooks.after_specify",
            "SPECIFY_FEATURE_DIRECTORY",
            ".specify/feature.json",
            "Authorized Source Input Contract",
            "Full-Spectrum Projection",
            "feature-local WHAT/WHY SSOT",
            "Do not compute completeness",
        ):
            self.assertIn(term, command)
        self.assertIn("checklists/requirements.md", command)
        self.assertIn("MUST NOT create, read, evaluate, or modify", command)
        self.assertNotIn("{CORE_TEMPLATE}", command)

    def test_source_commands_keep_external_actions_outside_preset(self) -> None:
        specify = read(COMMANDS / "speckit.specify.md")
        clarify = read(COMMANDS / "speckit.clarify.md")
        checklist = read(COMMANDS / "speckit.checklist.md")
        for term in (
            "dereference or execute a locator",
            "import manifest",
            "provider-specific\nschema",
            "Intake is not an SDD stage",
        ):
            self.assertIn(term, specify)
        self.assertIn("external\nwrite-back or synchronization", clarify)
        self.assertIn("preserve the originating `SRC-*` provenance", clarify)
        self.assertIn("MUST NOT dereference a locator", checklist)

    def test_clarify_writes_only_spec_and_uses_cross_domain_priority(self) -> None:
        command = read(COMMANDS / "speckit.clarify.md")
        for term in (
            "strategy: replace",
            "Run `{SCRIPT}` once",
            "Read and write only `FEATURE_SPEC`",
            "impact × uncertainty",
            "exactly one at a time",
            "## Clarifications",
            "Local Validation After Every Write",
        ):
            self.assertIn(term, command)
        self.assertNotIn("{CORE_TEMPLATE}", command)
        self.assertNotIn("checklists/requirements.md", command)

    def test_checklist_generates_unanswered_questions_only(self) -> None:
        command = read(COMMANDS / "speckit.checklist.md")
        self.assertIn("{CORE_TEMPLATE}", command)
        self.assertIn("question-form", command)
        self.assertIn("Generated items remain unchecked questions", command)
        self.assertIn("MUST NOT modify `spec.md`", command)
        for path in (TEMPLATES / "requirements").glob("*.md"):
            template = read(path)
            self.assertRegex(template, r"- \[ \] CHK-")
            self.assertNotIn("PASS | BLOCKED", template)
            self.assertNotIn("Readiness Matrix", template)


class PlanContractTests(unittest.TestCase):
    def test_plan_nests_x0_x4_in_core_without_new_cross_command_gate(self) -> None:
        command = read(COMMANDS / "speckit.plan.md")
        self.assertIn("{CORE_TEMPLATE}", command)
        for marker in (
            "Core setup + plan-template materialization -> X0",
            "Core Phase 0 Outline & Research",
            "Core Phase 1 Design & Contracts",
            "Core post-design Constitution re-check",
            "Preset closeout before completion report",
        ):
            self.assertIn(marker, command)
        for gate in (
            "X0_CONTROL_READY",
            "X1_DECISIONS_READY",
            "X2A_DESIGN_READY",
            "X2B_UIUX_READY",
            "X2C_TEST_DESIGN_READY",
            "X3_VALIDATION_PATHS_READY",
            "PLAN_OUTPUT_READY",
        ):
            self.assertIn(gate, command)
        self.assertIn("Plan never amends Architecture", command)
        self.assertIn("validates Plan outputs only", command)
        self.assertNotIn("Architecture Conformance Gate", command)

    def test_plan_has_deterministic_gates_reconciliation_and_resume(self) -> None:
        command = read(COMMANDS / "speckit.plan.md")
        for term in (
            "Deterministic Execution Spine",
            "Entry conditions",
            "Bounded reads",
            "Owned writes",
            "Failure handling",
            "Ownership And Conditional Artifact Decisions",
            "X2 — Cross-Lane Reconciliation",
            "X2_RECONCILIATION_READY",
            "Continuation And Resume",
            "first Gate whose evidence is absent",
            "never unconditionally overwrite",
            "Derive `PLAN_OUTPUT_READY`",
        ):
            self.assertIn(term, command)
        for work_unit_field in (
            "assigned_scope",
            "allowed_reads",
            "allowed_writes",
            "required_outputs",
            "validation_gate",
            "blockers",
            "context_gaps",
        ):
            self.assertIn(work_unit_field, command)

    def test_plan_conditional_decision_table_covers_contextual_outputs(self) -> None:
        command = read(COMMANDS / "speckit.plan.md")
        for term in (
            "`class-diagram.md`",
            "`contracts/sequences.md`",
            "X2-B + `ui-ux-design.md`/UIF",
            "BDD/scenario child",
            "fixture child",
            "assertion child",
            "never infer N/A merely because an artifact is absent",
        ):
            self.assertIn(term, command)

    def test_plan_control_template_has_lanes_navigation_and_closeout(self) -> None:
        template = read(TEMPLATES / "plan-template.md")
        for term in (
            "X0 Feature Plan Control",
            "Active Lane Matrix",
            "Cross-Lane Dependency Register",
            "Internal Gate Summary",
            "Artifact Navigation",
            "Design Object Derivation Index",
            "X4 Closeout Summary",
            "PLAN_OUTPUT_READY",
            "X2 Cross-Lane Reconciliation",
            "Resume Checkpoint",
        ):
            self.assertIn(term, template)
        self.assertIn("Repository Topology", template)
        self.assertIn("No task IDs, exact per-task paths", template)

    def test_plan_artifact_templates_have_non_overlapping_ownership(self) -> None:
        class_template = read(TEMPLATES / "class-diagram-template.md")
        sequence_template = read(TEMPLATES / "sequences-template.md")
        ui_template = read(TEMPLATES / "ui-ux-design-template.md")
        quickstart = read(TEMPLATES / "quickstart-template.md")
        readiness = read(TEMPLATES / "test-readiness-template.md")

        self.assertIn("Do not copy complete domain fields", class_template)
        self.assertIn("Rollback / compensation", sequence_template)
        self.assertIn("X4 UI/UX Delivery Readiness", ui_template)
        self.assertIn("Pixel delivery/review is owned here", ui_template)
        self.assertIn("SRC + UI/VIS refs", ui_template)
        self.assertIn("does not dereference", ui_template)
        self.assertIn("### VAL-001", quickstart)
        self.assertIn("Cleanup/reset", quickstart)
        self.assertIn("Every required `TC-*` has exactly one row", readiness)
        self.assertIn("MUST NOT appear", readiness)
        readiness_table = [
            line for line in readiness.splitlines() if line.startswith("| TC ID")
        ][0]
        readiness_separator = [
            line for line in readiness.splitlines() if line.startswith("|---")
        ][0]
        self.assertEqual(
            readiness_table.count("|"),
            readiness_separator.count("|"),
        )

    def test_removed_behavior_parents_are_not_packaged(self) -> None:
        for path in (
            TEMPLATES / "behavior" / "uif-intent.json",
            TEMPLATES / "behavior" / "data-fixtures-intent.json",
            TEMPLATES / "behavior" / "behavior-testability.md",
            SCHEMAS / "speckit.behavior.uif.intent.v1.schema.json",
            SCHEMAS / "speckit.behavior.data-fixtures.intent.v1.schema.json",
        ):
            self.assertFalse(path.exists(), path)


class PlanBundleSemanticTests(unittest.TestCase):
    def test_four_representative_plan_bundles_are_closed(self) -> None:
        fixtures = sorted(PLAN_BUNDLE_FIXTURES.glob("*.json"))
        self.assertEqual(
            {
                "async_retry_compensation.json",
                "minimal_repository.json",
                "non_ui_single_interface.json",
                "ui_only.json",
            },
            {path.name for path in fixtures},
        )
        for fixture in fixtures:
            with self.subTest(bundle=fixture.name):
                validate_plan_artifact_bundle(load_json(fixture))

    def test_plan_bundle_rejects_n_a_without_reason_and_missing_children(self) -> None:
        bundle = load_json(PLAN_BUNDLE_FIXTURES / "non_ui_single_interface.json")
        del bundle["artifacts"][5]["reason"]
        with self.assertRaisesRegex(ValueError, "N/A artifact missing reason"):
            validate_plan_artifact_bundle(bundle)

        bundle = load_json(PLAN_BUNDLE_FIXTURES / "non_ui_single_interface.json")
        bundle["artifacts"] = [
            artifact
            for artifact in bundle["artifacts"]
            if artifact["path"] != "quickstart.md"
        ]
        with self.assertRaisesRegex(ValueError, "missing required output"):
            validate_plan_artifact_bundle(bundle)

        bundle = load_json(PLAN_BUNDLE_FIXTURES / "async_retry_compensation.json")
        bundle["technique_children"]["assertion"] = []
        with self.assertRaisesRegex(ValueError, "technique-triggered assertion"):
            validate_plan_artifact_bundle(bundle)

    def test_plan_bundle_rejects_ref_drift_placeholder_and_false_ready(self) -> None:
        bundle = load_json(PLAN_BUNDLE_FIXTURES / "ui_only.json")
        bundle["test_conditions"]["conditions"][0]["related_refs"] = ["UIF-RENAMED"]
        with self.assertRaisesRegex(ValueError, "unresolved internal refs"):
            validate_plan_artifact_bundle(bundle)

        bundle = load_json(PLAN_BUNDLE_FIXTURES / "minimal_repository.json")
        bundle["artifacts"][0]["content"] = "TODO decide scope"
        with self.assertRaisesRegex(ValueError, "unresolved placeholder"):
            validate_plan_artifact_bundle(bundle)

        bundle = load_json(PLAN_BUNDLE_FIXTURES / "non_ui_single_interface.json")
        bundle["gates"]["X2_RECONCILIATION_READY"] = {
            "status": "BLOCKED",
            "evidence": ["BLK-REF-001"],
            "blockers": ["BLK-REF-001"],
        }
        bundle["reconciliation"]["blocker_owners"] = {
            "BLK-REF-001": "X2 reconciliation"
        }
        with self.assertRaisesRegex(ValueError, "PLAN_OUTPUT_READY is inconsistent"):
            validate_plan_artifact_bundle(bundle)

    def test_plan_bundle_validates_test_readiness_rows(self) -> None:
        bundle = load_json(PLAN_BUNDLE_FIXTURES / "non_ui_single_interface.json")
        bundle["test_readiness_rows"] = []
        with self.assertRaisesRegex(ValueError, "test readiness TC mismatch"):
            validate_plan_artifact_bundle(bundle)

    def test_blocked_test_readiness_row_blocks_plan_output(self) -> None:
        bundle = load_json(PLAN_BUNDLE_FIXTURES / "non_ui_single_interface.json")
        bundle["test_readiness_rows"][0] = {
            "tc_id": "TC-001",
            "status": "BLOCKED",
            "blocker": "BLK-TEST-ENV-001",
        }
        bundle["reconciliation"]["blocker_owners"] = {
            "BLK-TEST-ENV-001": "X4"
        }
        with self.assertRaisesRegex(ValueError, "PLAN_OUTPUT_READY is inconsistent"):
            validate_plan_artifact_bundle(bundle)

        bundle["plan_output_ready"] = "BLOCKED"
        validate_plan_artifact_bundle(bundle)

    def test_blocked_test_condition_blocks_plan_output(self) -> None:
        bundle = load_json(PLAN_BUNDLE_FIXTURES / "non_ui_single_interface.json")
        condition = bundle["test_conditions"]["conditions"][0]
        condition["status"] = "blocked"
        condition["blocker"] = "BLK-TC-001"
        bundle["test_readiness_rows"] = []
        bundle["reconciliation"]["blocker_owners"] = {"BLK-TC-001": "X2-C"}
        with self.assertRaisesRegex(ValueError, "PLAN_OUTPUT_READY is inconsistent"):
            validate_plan_artifact_bundle(bundle)

        bundle["plan_output_ready"] = "BLOCKED"
        validate_plan_artifact_bundle(bundle)

    def test_plan_bundle_allows_blocked_x2b_without_relabeling_it_n_a(self) -> None:
        bundle = load_json(PLAN_BUNDLE_FIXTURES / "ui_only.json")
        bundle["lanes"]["X2-B"] = {
            "status": "Blocked",
            "blocker": "BLK-UI-001",
        }
        uiux = next(
            artifact
            for artifact in bundle["artifacts"]
            if artifact["path"] == "ui-ux-design.md"
        )
        uiux.clear()
        uiux.update(
            {
                "path": "ui-ux-design.md",
                "decision": "Blocked",
                "owner": "X2-B",
                "blocker": "BLK-UI-001",
            }
        )
        bundle["gates"]["X2B_UIUX_READY"] = {
            "status": "BLOCKED",
            "evidence": ["BLK-UI-001"],
            "blockers": ["BLK-UI-001"],
        }
        bundle["reconciliation"]["blocker_owners"] = {"BLK-UI-001": "X2-B"}
        bundle["plan_output_ready"] = "BLOCKED"
        validate_plan_artifact_bundle(bundle)

    def test_blocked_x2c_preserves_unaffected_required_outputs(self) -> None:
        bundle = load_json(PLAN_BUNDLE_FIXTURES / "non_ui_single_interface.json")
        bundle["lanes"]["X2-C"] = {
            "status": "Blocked",
            "blocker": "BLK-X2C-001",
        }
        readiness = next(
            artifact
            for artifact in bundle["artifacts"]
            if artifact["path"] == "test-readiness.md"
        )
        readiness.clear()
        readiness.update(
            {
                "path": "test-readiness.md",
                "decision": "Blocked",
                "owner": "X4",
                "blocker": "BLK-READINESS-001",
            }
        )
        bundle["test_readiness_rows"] = []
        bundle["gates"]["X2C_TEST_DESIGN_READY"] = {
            "status": "BLOCKED",
            "evidence": ["BLK-X2C-001"],
            "blockers": ["BLK-X2C-001"],
        }
        bundle["reconciliation"]["blocker_owners"] = {
            "BLK-X2C-001": "X2-C",
            "BLK-READINESS-001": "X4",
        }
        bundle["plan_output_ready"] = "BLOCKED"
        validate_plan_artifact_bundle(bundle)

    def test_required_x2a_allows_pure_domain_design_without_interface(self) -> None:
        bundle = load_json(PLAN_BUNDLE_FIXTURES / "minimal_repository.json")
        bundle["artifacts"] = [
            artifact
            for artifact in bundle["artifacts"]
            if artifact["path"] != "contracts/library.json"
        ]
        bundle["decisions"][0]["affected_refs"].remove("IF-LIB-001")
        bundle["test_conditions"]["conditions"][0]["related_refs"].remove(
            "IF-LIB-001"
        )
        bundle["validation_paths"][0]["covered_refs"].remove("IF-LIB-001")
        bundle["reconciliation"]["resolved_refs"].remove("IF-LIB-001")
        bundle["gates"]["X2A_DESIGN_READY"]["evidence"] = [
            "data-model.md#OBJ-VALUE-001"
        ]
        validate_plan_artifact_bundle(bundle)

    def test_plan_bundle_allows_x2c_and_x3_n_a_with_reasons(self) -> None:
        bundle = load_json(PLAN_BUNDLE_FIXTURES / "non_ui_single_interface.json")
        bundle["lanes"]["X2-C"] = {
            "status": "N/A",
            "reason": "The scoped documentation-only change has no Test obligation.",
        }
        for artifact in bundle["artifacts"]:
            if artifact["path"] in {
                "contracts/test/test-conditions.json",
                "quickstart.md",
                "test-readiness.md",
            }:
                path = artifact["path"]
                artifact.clear()
                artifact.update(
                    {
                        "path": path,
                        "decision": "N/A",
                        "reason": "No Test or runnable validation obligation applies.",
                    }
                )
        bundle["decisions"][0]["affected_refs"] = ["IF-001"]
        bundle.pop("test_conditions")
        bundle.pop("technique_children")
        bundle.pop("test_readiness_rows")
        bundle["validation_paths"] = []
        bundle["reconciliation"]["resolved_refs"] = ["DEC-IF-001", "IF-001"]
        bundle["gates"]["X2C_TEST_DESIGN_READY"] = {
            "status": "N/A",
            "evidence": ["plan.md#active-lane-matrix-no-test"],
        }
        bundle["gates"]["X3_VALIDATION_PATHS_READY"] = {
            "status": "N/A",
            "evidence": ["plan.md#active-lane-matrix-no-validation-path"],
        }
        validate_plan_artifact_bundle(bundle)

    def test_plan_bundle_allows_pixel_delivery_language_only_in_uiux(self) -> None:
        bundle = load_json(PLAN_BUNDLE_FIXTURES / "ui_only.json")
        bundle["artifacts"][5][
            "content"
        ] = "Pixel-perfect delivery and visual diff review remain owned by UI/UX."
        validate_plan_artifact_bundle(bundle)

    def test_plan_bundle_rejects_pixel_test_scope(self) -> None:
        bundle = load_json(PLAN_BUNDLE_FIXTURES / "ui_only.json")
        bundle["test_conditions"]["conditions"][0][
            "evidence_requirement"
        ] = "screenshot diff"
        with self.assertRaisesRegex(ValueError, "pixel-level visual scope"):
            validate_plan_artifact_bundle(bundle)

    def test_plan_bundle_rejects_unknown_plan_output_state(self) -> None:
        bundle = load_json(PLAN_BUNDLE_FIXTURES / "non_ui_single_interface.json")
        bundle["gates"]["X2_RECONCILIATION_READY"] = {
            "status": "BLOCKED",
            "evidence": ["BLK-REF-001"],
            "blockers": ["BLK-REF-001"],
        }
        bundle["reconciliation"]["blocker_owners"] = {
            "BLK-REF-001": "X2 reconciliation"
        }
        bundle["plan_output_ready"] = "NOT_A_STATE"
        with self.assertRaisesRegex(
            ValueError,
            "PLAN_OUTPUT_READY must be READY or BLOCKED",
        ):
            validate_plan_artifact_bundle(bundle)


class SchemaAndValidatorTests(unittest.TestCase):
    def test_all_json_artifacts_parse_and_all_schemas_are_valid(self) -> None:
        for path in [*SCHEMAS.glob("*.json"), *TEMPLATES.rglob("*.json")]:
            load_json(path)
        for path in SCHEMAS.glob("*.json"):
            Draft202012Validator.check_schema(load_json(path))

    def test_test_conditions_schema_accepts_generalized_non_bdd_contract(self) -> None:
        payload = minimal_test_conditions()
        schema = load_json(SCHEMAS / "speckit.test.conditions.v1.schema.json")
        Draft202012Validator(schema).validate(payload)
        validate_test_conditions(payload)

        condition = payload["conditions"][0]
        condition["types"] = ["security", "performance", "recovery"]
        condition["techniques"] = ["boundary_value", "state_transition"]
        condition["oracle"] = {"kind": "threshold", "expected": 500}
        validate_test_conditions(payload)

    def test_test_validator_rejects_pixel_scope_and_incomplete_dimensions(self) -> None:
        payload = minimal_test_conditions()
        payload["conditions"][0]["evidence_requirement"] = "screenshot diff baseline"
        with self.assertRaisesRegex(ValueError, "pixel-level visual scope"):
            validate_test_conditions(payload)

        payload = minimal_test_conditions()
        payload["conditions"][0]["levels"] = []
        with self.assertRaisesRegex(ValueError, "non-empty levels"):
            validate_test_conditions(payload)

    def test_bdd_requires_child_and_readiness_has_one_row_per_required_tc(self) -> None:
        payload = minimal_test_conditions(technique="BDD")
        with self.assertRaisesRegex(ValueError, "no BDD child"):
            validate_test_conditions(payload)
        validate_test_conditions(payload, available_bdd_tc_refs={"TC-001"})
        validate_test_readiness(
            payload,
            [
                {
                    "tc_id": "TC-001",
                    "status": "READY",
                    "evidence": "quickstart.md#VAL-001",
                }
            ],
        )
        with self.assertRaisesRegex(ValueError, "TC mismatch"):
            validate_test_readiness(payload, [])

    def test_expected_uif_reference_fields_match_schema(self) -> None:
        validator = Draft202012Validator(
            load_json(SCHEMAS / "speckit.behavior.uif.expected.v1.schema.json")
        )
        uif = minimal_uif()
        validator.validate(uif)
        validate_behavior_contract_bundle(
            {
                "scenarios": [
                    {
                        "id": "SCN-UI-001",
                        "type": "positive",
                        "test_condition_refs": ["TC-001"],
                        "fixture_ids": ["FIX-001"],
                        "uif_path_id": "UIF-001",
                        "assertion_ids": ["AST-001"],
                    }
                ]
            },
            {"fixtures": [{"id": "FIX-001"}]},
            minimal_assertions(),
            [uif],
            {"TC-001"},
        )

        missing_source_mapping = minimal_uif()
        del missing_source_mapping["source_refs"]
        with self.assertRaises(ValidationError):
            validator.validate(missing_source_mapping)
        with self.assertRaisesRegex(ValueError, "non-empty source_refs"):
            validate_behavior_contract_bundle(
                {
                    "scenarios": [
                        {
                            "id": "SCN-UI-001",
                            "type": "positive",
                            "test_condition_refs": ["TC-001"],
                            "fixture_ids": ["FIX-001"],
                            "uif_path_id": "UIF-001",
                            "assertion_ids": ["AST-001"],
                        }
                    ]
                },
                {"fixtures": [{"id": "FIX-001"}]},
                minimal_assertions(),
                [missing_source_mapping],
                {"TC-001"},
            )

    def test_scenario_bundle_supports_non_ui_and_fixture_free_acceptance(self) -> None:
        instances = {
            "contract_type": "speckit.behavior.scenario_instances.v1",
            "scenarios": [
                {
                    "id": "SCN-NONUI-001",
                    "title": "Reject duplicate command",
                    "type": "positive",
                    "test_condition_refs": ["TC-001"],
                    "non_ui_rationale": "Command-only contract.",
                    "no_fixture_rationale": "Input is self-contained.",
                    "request_case": {"id": "REQ-001"},
                    "expected_response": {"error_code": "DUPLICATE"},
                    "assertion_ids": ["AST-001"],
                }
            ],
        }
        Draft202012Validator(
            load_json(
                SCHEMAS / "speckit.behavior.scenario-instances.v1.schema.json"
            )
        ).validate(instances)
        validate_behavior_contract_bundle(
            instances,
            {"fixtures": []},
            minimal_assertions(),
            [],
            {"TC-001"},
        )

    def test_scenario_bundle_rejects_unknown_child_refs(self) -> None:
        instances = {
            "scenarios": [
                {
                    "id": "SCN-001",
                    "test_condition_refs": ["TC-UNKNOWN"],
                    "non_ui_rationale": "No UI.",
                    "no_fixture_rationale": "No setup.",
                    "assertion_ids": ["AST-UNKNOWN"],
                    "type": "positive",
                }
            ]
        }
        with self.assertRaisesRegex(ValueError, "unknown assertion"):
            validate_behavior_contract_bundle(
                instances,
                {"fixtures": []},
                minimal_assertions(),
                [],
                {"TC-001"},
            )


class TasksAndAnalyzeTests(unittest.TestCase):
    def test_tasks_is_pure_plan_mapper_and_required_tc_overrides_core_optional(self) -> None:
        command = read(COMMANDS / "speckit.tasks.md")
        for stage in (
            "T0 — Plan Handoff Preflight",
            "T1 — Concrete Path Binding",
            "T2 — Dependency Graph",
            "T3 — Story / Capability Derivation",
            "T4 — Functional Validation And Evidence",
            "T5 — Final Code Review",
        ):
            self.assertIn(stage, command)
        self.assertIn("Tasks MUST NOT drop", command)
        self.assertIn("tests are optional", command)
        self.assertIn("PLAN_OUTPUT_INCOMPLETE", command)
        self.assertIn("Exact paths are a Tasks output", command)
        self.assertIn("Spec/Checklist as direct\nstrategy inputs", command)

    def test_tasks_forbids_pixel_work_and_keeps_final_review_last(self) -> None:
        command = read(COMMANDS / "speckit.tasks.md")
        self.assertIn("Never generate", command)
        for forbidden_task in (
            "visual_acceptance",
            "pixel_fidelity_review",
            "screenshot comparison",
            "visual diff",
            "baseline capture",
            "visual restoration",
            "final visual review",
            "pixel-level layout/style assertions",
            "screenshot-based evidence",
            "source dereference",
            "external-source validation",
            "provider-tool",
        ):
            self.assertIn(forbidden_task, command)
        self.assertIn("append the final phase after user-story tasks", command)
        self.assertIn("no phase may follow it", command)
        self.assertIn("MUST NOT\njudge rendered visual fidelity", command)

    def test_analyze_is_read_only_and_owns_all_cross_command_chains(self) -> None:
        command = read(COMMANDS / "speckit.analyze.md")
        for term in (
            "Analyze exclusively owns Cross-Command Consistency Gates",
            "MUST NOT modify or repair any artifact",
            "One-Pass Inventory",
            "Use stable IDs as the primary consistency surface",
            "first blocker",
            "Constitution To Spec / Plan",
            "Architecture To Plan Products",
            "Spec To X0/X1/X2/X3/X4",
            "Plan To Tasks",
            "Implementation Readiness: PASS | BLOCKED",
            "Confirm no files were written",
        ):
            self.assertIn(term, command)
        self.assertIn("repo-first planning within Architecture constraints", command)
        self.assertIn("Do not classify Plan as Greenfield/Brownfield", command)

    def test_source_shapes_converge_without_external_coupling(self) -> None:
        self.assertEqual(
            [],
            audit_source_reference_contract(source_contract_snapshot()),
        )

    def test_source_audit_reports_role_slice_and_projection_failures(self) -> None:
        snapshot = source_contract_snapshot()
        snapshot["spec"]["sources"].extend(
            [
                {
                    "ref": "SRC-006",
                    "role": "provider-input",
                    "locator_or_description": "provider-specific packet",
                    "provider_node_id": "node-42",
                    "authorized_scope": "refund feature",
                    "projected_refs": [],
                    "status": "retained",
                },
                {
                    "ref": "SRC-007",
                    "role": "context-only",
                    "locator_or_description": "background note",
                    "authorized_scope": "background only",
                    "projected_refs": ["FR-001"],
                    "status": "projected",
                },
                {
                    "ref": "SRC-008",
                    "role": "requirement-input",
                    "locator_or_description": "broad roadmap",
                    "authorized_scope": "entire roadmap",
                    "broad": True,
                    "projected_refs": [],
                    "status": "projected",
                },
            ]
        )
        codes = {
            finding["code"]
            for finding in audit_source_reference_contract(snapshot)
        }
        self.assertTrue(
            {
                "SRC_ROLE_INVALID",
                "SRC_FIELD_INVALID",
                "SRC_ROLE_PROJECTION_INVALID",
                "SRC_FEATURE_SLICE_MISSING",
                "SRC_ORPHAN",
            }.issubset(codes)
        )

    def test_source_audit_reports_local_integrity_and_x2b_uif_gaps(self) -> None:
        snapshot = source_contract_snapshot()
        snapshot["spec"]["sources"].append(
            dict(snapshot["spec"]["sources"][0])
        )
        snapshot["spec"]["sources"][2]["projected_refs"].append("UI-404")
        snapshot["spec"]["sources"][4]["status"] = "contradictory"
        snapshot["referenced_source_refs"] = ["SRC-404"]
        snapshot["plan"]["ui_ux_mappings"] = []
        snapshot["plan"]["uif_mappings"] = []

        codes = {
            finding["code"]
            for finding in audit_source_reference_contract(snapshot)
        }
        self.assertTrue(
            {
                "SRC_REF_MISSING",
                "SRC_REF_DUPLICATE",
                "SRC_PROJECTED_REF_MISSING",
                "SRC_STATUS_CONTRADICTORY",
                "SRC_UIUX_MAPPING_MISSING",
                "SRC_UIF_MAPPING_MISSING",
            }.issubset(codes)
        )

    def test_audit_reports_deterministic_vertical_breaks(self) -> None:
        snapshot = {
            "architecture": {
                "revision": "ARCH-2",
                "decisions": ["DEC-001"],
                "concepts": ["CON-001"],
                "boundaries": ["BND-001"],
                "constraints": ["CST-001"],
                "gaps": ["GAP-001"],
            },
            "plan": {
                "architecture_revision": "ARCH-1",
                "research_refs": [],
                "data_model_refs": [],
                "contract_refs": [],
                "plan_constraint_refs": [],
                "blocker_refs": [],
                "design_objects": ["PaymentCoordinator"],
                "required_test_conditions": ["TC-001"],
                "mu_scope": "checkout/PaymentCoordinator",
            },
            "tasks": {
                "design_object_refs": [],
                "test_condition_refs": [],
                "mu_scope": "repository/*",
            },
        }
        self.assertEqual(
            [
                "ARCH_REVISION_STALE",
                "ARCH_DECISION_OMITTED",
                "ARCH_CONCEPT_OMITTED",
                "ARCH_BOUNDARY_OMITTED",
                "ARCH_CONSTRAINT_OMITTED",
                "ARCH_GAP_OMITTED",
                "PLAN_TASK_MAPPING_MISSING",
                "PLAN_REQUIRED_TEST_TASK_MISSING",
                "MU_SCOPE_WIDENED",
            ],
            [
                finding["code"]
                for finding in audit_cross_command_consistency(snapshot)
            ],
        )

    def test_issue_24_obligations_map_to_stable_analyze_codes(self) -> None:
        required = {
            "idempotency_key",
            "provider_task_binding",
            "provider_lock",
            "retry_context",
            "recovery_decision",
            "readiness_lifecycle",
        }
        findings = audit_data_model_obligations(required, {"provider_lock"})
        self.assertEqual(
            {
                "ARCH_DATA_MODEL_IDEMPOTENCY_MISSING",
                "ARCH_PROVIDER_BINDING_MISSING",
                "ARCH_RETRY_CONTEXT_MISSING",
                "ARCH_RECOVERY_DECISION_MISSING",
                "ARCH_LIFECYCLE_PROJECTION_MISSING",
            },
            {finding["code"] for finding in findings},
        )

    def test_closed_cross_command_chain_has_no_findings(self) -> None:
        snapshot = {
            "architecture": {
                "revision": "ARCH-2",
                "decisions": ["DEC-001"],
                "concepts": ["CON-001"],
                "boundaries": ["BND-001"],
                "constraints": ["CST-001"],
                "gaps": ["GAP-001"],
            },
            "plan": {
                "architecture_revision": "ARCH-2",
                "research_refs": ["DEC-001"],
                "data_model_refs": ["CON-001"],
                "contract_refs": ["BND-001"],
                "plan_constraint_refs": ["CST-001"],
                "blocker_refs": ["GAP-001"],
                "design_objects": ["PaymentCoordinator"],
                "required_test_conditions": ["TC-001"],
                "mu_scope": "checkout/PaymentCoordinator",
            },
            "tasks": {
                "design_object_refs": ["PaymentCoordinator"],
                "test_condition_refs": ["TC-001"],
                "mu_scope": "checkout/PaymentCoordinator",
            },
        }
        self.assertEqual([], audit_cross_command_consistency(snapshot))


class ReleaseBoundaryTests(unittest.TestCase):
    def test_release_workflow_smokes_install_and_preserves_core_implement(self) -> None:
        workflow = read(ARTIFACT_WORKFLOW)
        for term in (
            "specify init --here",
            "specify preset add --dev",
            "specify integration upgrade claude",
            "specify preset resolve plan-template",
            "test -f .claude/skills/speckit-implement/SKILL.md",
            "test ! -e .specify/presets/workflow-preset/commands/speckit.implement.md",
            "validators/speckit_plan_contract.py",
            "tests/fixtures/plan_bundles/minimal_repository.json",
            "tests/fixtures/plan_bundles/ui_only.json",
        ):
            self.assertIn(term, workflow)

    def test_public_docs_do_not_claim_preset_implement_ownership(self) -> None:
        for document in (read(README), read(GOVERNANCE), read(AGENTS)):
            self.assertIn("Spec Kit core", document)
            self.assertNotIn("preset-owned Implement", document)


if __name__ == "__main__":
    unittest.main()
