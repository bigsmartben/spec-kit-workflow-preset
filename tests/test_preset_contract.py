from __future__ import annotations

from copy import deepcopy
import json
import re
import shutil
import subprocess
import tempfile
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
from validators.speckit_requirement_gate_contract import (
    CANONICAL_REQUIREMENT_GATE_PATH,
    REQUIREMENT_GATE_CONTRACT,
    REQUIREMENT_RULE_GATES,
    STANDARD_REQUIREMENT_GATES,
    clarification_candidates,
    inspect_core_wrapper_contract,
    inspect_requirement_gate_bundle,
    preflight_requirement_gate,
    rebuild_requirement_gate,
    reconcile_requirement_gate,
    select_authoritative_requirement_gate,
    validate_id_lifecycle,
)
from validators.speckit_spec_contract import (
    ADAPTATION_DIMENSIONS,
    CONFLICT_PRECEDENCE,
    RESTORATION_DIMENSIONS,
    validate_ui_specification_contract,
)
from validators.speckit_tasks_contract import (
    FINAL_REVIEW_SCOPES,
    MAPPING_DIMENSIONS,
    validate_tasks_x2b_derivation,
)
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
REQUIREMENT_GATE_FIXTURES = ROOT / "tests" / "fixtures" / "requirement_gates"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_json(path: Path) -> dict:
    return json.loads(read(path))


def replace_string_values(value, old: str, new: str):
    if isinstance(value, dict):
        return {
            key: replace_string_values(child, old, new)
            for key, child in value.items()
        }
    if isinstance(value, list):
        return [replace_string_values(child, old, new) for child in value]
    if isinstance(value, str):
        return value.replace(old, new)
    return value


def requirement_gate_bundle(
    *,
    revision: str = f"sha256:{'c' * 64}",
    blocked_gates: tuple[str, ...] = (),
    blocker_class: str = "product-decision",
) -> dict:
    gate_contract = {
        "requirements": ("REQ", "DOM-SCOPE"),
        "behavior": ("BEH", "BEH-OBSERVABLE"),
        "ux": ("UX", "UX-JOURNEY"),
        "security": ("SEC", "DOM-ACTOR-STATE"),
        "nfr": ("NFR", "NFR-MEASURE"),
        "visual": ("VIS", "UI-EVIDENCE"),
    }
    blocker_id = "BLK-FR-017-01"
    checks = []
    for gate in STANDARD_REQUIREMENT_GATES:
        gate_code, rule_key = gate_contract[gate]
        check_id = f"CHK-{gate_code}-001"
        blocked = gate in blocked_gates
        checks.append(
            {
                "id": check_id,
                "rule_key": rule_key,
                "gate": gate,
                "concern": f"{gate} atomic quality",
                "spec_refs": ["FR-017"],
                "status": "BLOCKED" if blocked else "PASS",
                "evidence_refs": [] if blocked else ["spec.md#FR-017"],
                "blocker_ref": blocker_id if blocked else None,
            }
        )
    affected = sorted(
        check["id"] for check in checks if check["status"] == "BLOCKED"
    )
    blockers = []
    if affected:
        blockers.append(
            {
                "id": blocker_id,
                "primary_spec_ref": "FR-017",
                "semantic_key": "authorization-subject",
                "gap": "The actor allowed to authorize the action is unresolved.",
                "affected_check_ids": affected,
                "class": blocker_class,
                "owner": (
                    "clarify" if blocker_class == "product-decision" else "source-owner"
                ),
                "status": "OPEN",
                "replacement_refs": [],
            }
        )
    summary = []
    for gate in STANDARD_REQUIREMENT_GATES:
        gate_checks = [check for check in checks if check["gate"] == gate]
        gate_blockers = sorted(
            {
                check["blocker_ref"]
                for check in gate_checks
                if check["blocker_ref"] is not None
            }
        )
        summary.append(
            {
                "gate": gate,
                "applicability": "APPLICABLE",
                "applicability_reason": None,
                "status": (
                    "PASS"
                    if all(check["status"] == "PASS" for check in gate_checks)
                    else "BLOCKED"
                ),
                "check_refs": sorted(check["id"] for check in gate_checks),
                "blocker_refs": gate_blockers,
                "check_count": len(gate_checks),
                "blocker_count": len(gate_blockers),
            }
        )
    readiness = "BLOCKED" if affected else "PASS"
    return {
        "path": CANONICAL_REQUIREMENT_GATE_PATH,
        "metadata": {
            "stage": "requirements",
            "contract": REQUIREMENT_GATE_CONTRACT,
            "spec_revision": revision,
            "planning_readiness": readiness,
        },
        "semantic_groups": [
            {
                "spec_ref": "FR-017",
                "checks": checks,
                "blockers": blockers,
                "manual_notes": "preserve me",
            }
        ],
        "gate_summary": summary,
        "planning_readiness": {
            "status": readiness,
            "spec_revision": revision,
            "blocker_refs": [blocker_id] if affected else [],
        },
    }


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
                    "bounded_scope": "refund submission behavior",
                    "supplied_facts": ["refunds can be submitted"],
                    "projected_refs": ["FR-001"],
                    "status": "projected",
                },
                {
                    "ref": "SRC-002",
                    "role": "requirement-input",
                    "locator_or_description": "opaque product document",
                    "revision": "supplied-r7",
                    "bounded_scope": "refund eligibility section",
                    "supplied_facts": ["eligibility rules in the supplied section"],
                    "feature_slice": "refund eligibility",
                    "broad": True,
                    "projected_refs": ["FR-002"],
                    "status": "projected",
                },
                {
                    "ref": "SRC-003",
                    "role": "visual-input",
                    "locator_or_description": "opaque executable visual reference",
                    "bounded_scope": "refund error states",
                    "supplied_facts": ["supplied error-state markup and appearance"],
                    "projected_refs": ["UI-001", "VIS-001"],
                    "status": "projected",
                    "uif_required": True,
                },
                {
                    "ref": "SRC-004",
                    "role": "technical-evidence",
                    "locator_or_description": "latency measurement report",
                    "bounded_scope": "technical evidence citation only",
                    "supplied_facts": ["latency measurement"],
                    "projected_refs": [],
                    "status": "retained",
                },
                {
                    "ref": "SRC-005",
                    "role": "context-only",
                    "locator_or_description": "competitor overview",
                    "bounded_scope": "background only",
                    "supplied_facts": ["competitor context"],
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


def minimal_ui_spec_contract() -> dict:
    requirements = [
        {
            "id": "UI-001",
            "kind": "interaction",
            "statement": "The refund panel exposes error feedback.",
            "source_refs": ["SRC-UI-001"],
            "evidence_locators": ["refund.html#refund-panel"],
            "evidence_support": ["surface", "state", "viewport", "interaction"],
            "surface": "refund panel",
            "state": "validation error with supplied invalid amount",
            "viewport": "1280x720 web",
            "derivation": "observed",
            "acceptance": "The cited error text is visible in the panel.",
            "outcome_only": True,
            "status": "specified",
        },
        {
            "id": "VIS-001",
            "kind": "restoration",
            "statement": "The refund panel matches the supplied baseline.",
            "source_refs": ["SRC-UI-001"],
            "evidence_locators": ["baseline.png#refund-panel"],
            "evidence_support": ["surface", "state", "viewport", "restoration"],
            "surface": "refund panel",
            "state": "validation error with supplied invalid amount",
            "viewport": "1280x720 web",
            "derivation": "observed",
            "acceptance": "PXT-001 satisfies its declared envelope.",
            "outcome_only": True,
            "status": "specified",
        },
    ]
    return {
        "sources": [
            {
                "ref": "SRC-UI-001",
                "role": "visual-input",
                "locator_or_description": "supplied refund HTML and baseline",
                "bounded_scope": "refund error panel",
                "supplied_facts": [
                    "refund.html#refund-panel",
                    "baseline.png#refund-panel",
                ],
                "projected_refs": ["UI-001", "VIS-001"],
                "status": "projected",
            }
        ],
        "all_spec_requirement_refs": [
            requirement["id"] for requirement in requirements
        ],
        "requirements": requirements,
        "restoration_requested": True,
        "restoration_dimensions": [
            {
                "dimension": dimension,
                "requirement_refs": ["VIS-001"],
                "source_refs": ["SRC-UI-001"],
                "evidence_locators": ["baseline.png#refund-panel"],
                "acceptance": f"{dimension} matches the cited baseline.",
                "status": "required",
            }
            for dimension in sorted(RESTORATION_DIMENSIONS)
        ],
        "pixel_restoration_requested": True,
        "pixel_profiles": [
            {
                "id": "PXR-001",
                "scope": "refund panel",
                "requirement_refs": ["UI-001", "VIS-001"],
                "source_refs": ["SRC-UI-001"],
                "target_refs": ["PXT-001"],
                "target_matrix": [
                    {
                        "target_ref": "PXT-001",
                        "surface": "refund panel",
                        "state": "validation error with supplied invalid amount",
                        "viewport": "1280x720",
                    }
                ],
                "fidelity_mode": "pixel-tolerant",
                "exception_policy": "Only stable PEX refs weaken exact regions.",
                "exception_refs": ["PEX-001"],
                "status": "specified",
            }
        ],
        "pixel_targets": [
            {
                "id": "PXT-001",
                "profile_id": "PXR-001",
                "surface": "refund panel",
                "state": "validation error with supplied invalid amount",
                "viewport": "1280x720",
                "device_pixel_ratio": "1",
                "baseline_source_ref": "SRC-UI-001",
                "baseline_locator": "baseline.png#refund-panel",
                "rendering_context": {
                    "fonts": "Inter with supplied fallback",
                    "color_mode": "light",
                    "locale": "en-US",
                    "platform": "Chromium on Windows",
                },
                "visual_dimensions": {
                    "geometry-sizing-spacing-alignment-flow": "match baseline",
                    "overflow-and-clipping": "match baseline",
                    "typography": "match baseline family/size/weight/metrics",
                    "color-border-radius-shadow-opacity-effects": "match baseline",
                    "asset-identity-variant-crop-aspect-fitting": "match baseline",
                    "layering-stacking-fixed-sticky-occlusion": "match baseline",
                },
                "fidelity_mode": "pixel-tolerant",
                "acceptance_envelope": {
                    "kind": "per-channel",
                    "threshold": 1,
                },
                "exception_refs": ["PEX-001"],
                "derivation": "observed",
                "status": "specified",
            }
        ],
        "pixel_exceptions": [
            {
                "id": "PEX-001",
                "target_refs": ["PXT-001"],
                "region": "timestamp text only",
                "reason": "dynamic value",
                "allowed_divergence": "glyph pixels inside timestamp bounds",
                "bound": "the measured timestamp bounding box",
                "requirement_refs": ["VIS-001"],
                "source_refs": ["SRC-UI-001"],
            }
        ],
        "cross_platform_restoration_requested": True,
        "adaptation_policies": [
            {
                "id": "ADP-001",
                "source_platform": "HTML/Web",
                "target_platform": "Android",
                "mode": "brand-preserving-native",
                "target_contexts": {
                    "window_or_device": "compact portrait",
                    "input": "touch and external keyboard",
                    "accessibility": "font scale 1.0-2.0 and screen reader",
                    "locale": "en-US plus RTL expansion",
                },
                "source_refs": ["SRC-UI-001"],
                "conflict_precedence": list(CONFLICT_PRECEDENCE),
                "decisions": [
                    {
                        "dimension": dimension,
                        "decision": (
                            "preserve"
                            if dimension
                            in {
                                "content-and-information-hierarchy",
                                "task-flow-and-navigation",
                                "ui-state-and-feedback",
                                "color-effects-and-brand",
                            }
                            else "adapt"
                        ),
                        "requirement_refs": ["UI-001", "VIS-001"],
                        "source_refs": ["SRC-UI-001"],
                        "outcome": f"Target outcome for {dimension}.",
                        "acceptance": f"Observe the declared {dimension} outcome.",
                        "status": "specified",
                    }
                    for dimension in sorted(ADAPTATION_DIMENSIONS)
                ],
                "status": "specified",
            }
        ],
    }


def minimal_tasks_x2b_bundle() -> dict:
    ui_dimensions = sorted(MAPPING_DIMENSIONS["UI"])
    pixel_dimensions = sorted(MAPPING_DIMENSIONS["PX"])
    adaptation_dimensions = sorted(MAPPING_DIMENSIONS["ADP"])
    pixel_binding_dimensions = [
        dimension
        for dimension in pixel_dimensions
        if dimension != "asset-preparation"
    ]
    return {
        "plan_output_ready": "READY",
        "current_plan_revision": "PLAN-47",
        "tasks_handoff_revision": "PLAN-47",
        "uiux_delivery_readiness": "READY",
        "declared_traceability_refs": [
            "UI-001",
            "VIS-001",
            "PXT-001",
            "PEX-001",
            "ADP-001",
        ],
        "x2b_mappings": [
            {
                "id": "X2B-UI-001",
                "status": "Required",
                "implementation_dimensions": list(ui_dimensions),
                "depends_on": [],
                "traceability_refs": ["UI-001"],
            },
            {
                "id": "X2B-PX-001",
                "status": "Required",
                "implementation_dimensions": list(pixel_dimensions),
                "depends_on": ["X2B-UI-001"],
                "traceability_refs": [
                    "VIS-001",
                    "PXT-001",
                    "PEX-001",
                ],
            },
            {
                "id": "X2B-ADP-001",
                "status": "Required",
                "implementation_dimensions": list(adaptation_dimensions),
                "depends_on": ["X2B-UI-001"],
                "traceability_refs": ["ADP-001"],
            },
            {
                "id": "X2B-PX-REVIEW-001",
                "status": "Required",
                "implementation_dimensions": [],
                "depends_on": [],
                "traceability_refs": ["PXT-001"],
                "review_method_only": True,
                "no_task_rationale": (
                    "The Plan records only a review method; Tasks cannot "
                    "execute rendered visual comparison."
                ),
            },
            {
                "id": "X2B-ADP-NA-001",
                "status": "N/A",
                "implementation_dimensions": [],
                "depends_on": [],
                "traceability_refs": [],
                "reason": "The supplied slice targets one platform.",
            },
        ],
        "tasks": [
            {
                "id": "T040",
                "kind": "implementation",
                "action_classes": ["implementation"],
                "paths": ["src/ui/RefundPanel.tsx"],
                "mapping_refs": ["X2B-UI-001"],
                "implementation_dimensions": list(ui_dimensions),
                "traceability_refs": ["UI-001"],
                "depends_on": [],
                "parallel": False,
                "description": "Implement the mapped component and UI states.",
            },
            {
                "id": "T041",
                "kind": "implementation",
                "action_classes": ["implementation"],
                "paths": ["src/ui/assets/refund-panel.svg"],
                "mapping_refs": ["X2B-PX-001"],
                "implementation_dimensions": ["asset-preparation"],
                "traceability_refs": ["VIS-001", "PXT-001"],
                "depends_on": ["T040"],
                "parallel": False,
                "description": "Prepare the locally authorized panel asset.",
            },
            {
                "id": "T042",
                "kind": "implementation",
                "action_classes": ["implementation"],
                "paths": ["src/ui/RefundPanel.tsx"],
                "mapping_refs": ["X2B-PX-001"],
                "implementation_dimensions": pixel_binding_dimensions,
                "traceability_refs": ["VIS-001", "PXT-001", "PEX-001"],
                "depends_on": ["T040", "T041"],
                "parallel": False,
                "description": "Implement mapped visual dimensions and bind assets.",
            },
            {
                "id": "T043",
                "kind": "implementation",
                "action_classes": ["implementation"],
                "paths": ["src/platform/android/RefundPanel.kt"],
                "mapping_refs": ["X2B-ADP-001"],
                "implementation_dimensions": list(adaptation_dimensions),
                "traceability_refs": ["ADP-001"],
                "depends_on": ["T040"],
                "parallel": False,
                "description": "Implement the mapped Android adaptation.",
            },
        ],
        "required_test_readiness_tc_refs": ["TC-UI-001"],
        "test_tasks": [
            {
                "id": "T044",
                "action_classes": ["functional-validation"],
                "tc_refs": ["TC-UI-001"],
                "paths": ["tests/ui/test_refund_panel.py"],
            }
        ],
        "phases": ["Setup", "Refund panel", "Final Code Review"],
        "final_review": {
            "phase": "Final Code Review",
            "kind": "code-design-contract-review",
            "action_classes": ["code-design-contract-review"],
            "mapping_refs": [
                "X2B-UI-001",
                "X2B-PX-001",
                "X2B-ADP-001",
            ],
            "scopes": [
                "implementation-conformance",
                "x2b-blockers-and-plan-drift",
                FINAL_REVIEW_SCOPES["UI"],
                FINAL_REVIEW_SCOPES["PX"],
                FINAL_REVIEW_SCOPES["ADP"],
            ],
            "paths": [
                "src/ui/RefundPanel.tsx",
                "src/ui/assets/refund-panel.svg",
                "src/platform/android/RefundPanel.kt",
            ],
            "description": "Review code/design-contract conformance for X2-B.",
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

        self.assertIn("stable-ID", entries["spec-template"]["description"])
        self.assertIn(
            "one semantic-grouped requirements.md",
            entries["speckit.checklist"]["description"],
        )
        self.assertIn("synchronize", entries["speckit.clarify"]["description"])
        self.assertIn(
            "Hard-gate the canonical requirements.md",
            entries["speckit.plan"]["description"],
        )

    def test_governance_uses_one_authority_and_gate_vocabulary(self) -> None:
        documents = (read(GOVERNANCE), read(AGENTS), read(CROSS_AGENT))
        for document in documents:
            self.assertIn("Spec Kit core", document)
            self.assertNotIn("implementation-manifest.json", document)
            self.assertNotIn("worker-result.json", document)

        governance = documents[0]
        self.assertIn("Authority And Gate Ownership", governance)
        self.assertIn("Requirement Command Ownership", governance)
        self.assertIn("X0–X4 Planning Artifact Boundaries", governance)
        self.assertIn("Tasks As A Pure Plan Mapper", governance)
        self.assertIn("Analyze Cross-Command Audit", governance)
        self.assertIn("Source Reference Contract", governance)
        self.assertIn("Clarify -> Checklist -> Clarify", governance)
        self.assertIn("speckit_requirement_gate_contract.py", governance)
        self.assertIn(
            "“Zero Blocker” in Planning Readiness means no `OPEN`",
            governance,
        )
        self.assertIn(
            "SRC-* + UI/VIS/RST/PXR/PXT/PEX/ADP refs",
            governance,
        )
        self.assertIn(
            "X2B-* delivery mappings + UIF source_refs/requirement_refs",
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
            "UI Specification Contract",
            "UI Evidence Projection Rules",
            "Restoration Equivalence",
            "Pixel-Restoration Profiles",
            "Cross-Platform Restoration Adaptation",
            "Security and Privacy",
            "Data and Integration Constraints",
            "Dependencies and Boundaries",
            "Assumptions",
            "Exclusions",
            "Semantic ID Lifecycle",
            "Source References",
            "Unresolved Product Decisions",
            "Source Evidence Blockers",
            "Clarifications",
        ):
            self.assertIn(heading, template)
        for prefix in (
            "FR-",
            "NFR-",
            "UX-",
            "UI-",
            "VIS-",
            "SEC-",
            "DAT-",
            "DEP-",
            "BND-",
            "ASM-",
            "EXC-",
        ):
            self.assertIn(prefix, template)
        self.assertIn("content carrier, not a completeness checklist", template)
        self.assertIn("Every item names its current stable semantic refs", template)
        self.assertIn("affected stable\n  local refs", template)

    def test_source_reference_template_has_one_source_neutral_shape(self) -> None:
        template = read(TEMPLATES / "spec-template.md")
        for column in (
            "SRC ref",
            "Role",
            "Opaque locator / description",
            "Revision / identity",
            "Bounded feature scope",
            "Supplied content / facts",
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
            "Bounded Supplied Input Contract",
            "Full-Spectrum Projection",
            "feature-local WHAT/WHY SSOT",
            "stable semantic ref",
            "preserve an ID for meaning-preserving edits",
            "Do not compute completeness",
        ):
            self.assertIn(term, command)
        self.assertIn("checklists/requirements.md", command)
        self.assertIn("MUST NOT create, read, evaluate, or modify", command)
        self.assertNotIn("{CORE_TEMPLATE}", command)

    def test_specify_starts_at_bounded_evidence_without_upstream_responsibilities(
        self,
    ) -> None:
        specify = read(COMMANDS / "speckit.specify.md")
        clarify = read(COMMANDS / "speckit.clarify.md")
        checklist = read(COMMANDS / "speckit.checklist.md")
        for term in (
            "bounded content or source-backed facts have already\nbeen supplied",
            "locator without supplied content or source-backed facts is provenance only",
            "SRC_EVIDENCE_MISSING",
            "UI Evidence Projection Rules",
            "surface x state x viewport",
            "PIXEL_PROFILE_INCOMPLETE",
            "one allowed adaptation mode",
        ):
            self.assertIn(term, specify)
        for forbidden in (
            "authorization",
            "tool-call",
            "provider",
            "plugin",
            "dereference",
            "adapter",
            "external synchronization",
        ):
            self.assertNotIn(forbidden, specify.casefold())
        self.assertIn("external\nwrite-back or synchronization", clarify)
        self.assertIn("preserve the originating `SRC-*` provenance", clarify)
        self.assertIn("MUST NOT dereference a locator", checklist)

    def test_ui_spec_template_exposes_deterministic_restoration_contracts(self) -> None:
        template = read(TEMPLATES / "spec-template.md")
        for term in (
            "Evidence locator(s) within supplied input",
            "observed / derived / assumed / unresolved / conflicting",
            "HTML / semantic markup",
            "CSS / computed-style facts",
            "responsive-viewports",
            "PXR-001",
            "PXT-001",
            "PEX-001",
            "pixel-exact",
            "pixel-tolerant",
            "perceptual-equivalent",
            "structural-only",
            "framework-equivalent",
            "native-adaptive",
            "brand-preserving-native",
            "visual-equivalent-native",
            "target-platform hard constraints and accessibility requirements",
            "`Swift` is invalid",
            "Concrete widgets, classes, code properties",
        ):
            self.assertIn(term, template)
        self.assertIn("UI requirement source of truth inside `spec.md`", template)
        self.assertIn("capture/comparison\nprocedures", template)

    def test_visual_checklist_covers_evidence_pixel_and_adaptation_quality(self) -> None:
        checklist = read(TEMPLATES / "requirements" / "visual-gate.md")
        for checklist_id in (
            "CHK-UI-003",
            "CHK-RST-001",
            "CHK-PXR-001",
            "CHK-PXR-002",
            "CHK-ADP-001",
            "CHK-ADP-002",
            "CHK-BND-001",
        ):
            self.assertIn(checklist_id, checklist)

    def test_clarify_reconciles_one_gate_by_shared_root_cause(self) -> None:
        command = read(COMMANDS / "speckit.clarify.md")
        for term in (
            "strategy: replace",
            "Run `{SCRIPT}` once",
            "Two-File Ownership",
            "impact × uncertainty",
            "exactly one at a time",
            "## Clarifications",
            "Local Validation After Every Spec Write",
            "Mandatory Closeout Reconciliation",
            "speckit.requirement-gate.v1",
            "Three Gate Checks referencing one Blocker produce one question",
            "REQUIREMENT_GATE_LEGACY_LAYOUT",
            "stale/unsynchronized",
        ):
            self.assertIn(term, command)
        self.assertNotIn("{CORE_TEMPLATE}", command)
        self.assertIn("existing `FEATURE_DIR/checklists/requirements.md`", command)
        self.assertIn("does not create a missing Gate", command)

    def test_checklist_generates_one_semantic_grouped_gate(self) -> None:
        command = read(COMMANDS / "speckit.checklist.md")
        self.assertIn("{CORE_TEMPLATE}", command)
        self.assertIn("exactly FEATURE_DIR/checklists/requirements.md", command)
        self.assertIn("Semantic Requirement Groups", command)
        self.assertIn("shared root-cause Blocker", command)
        self.assertIn("Six-Gate Summary", command)
        self.assertIn("Planning Readiness", command)
        self.assertIn("REQUIREMENT_GATE_CORE_WRAPPER_INCOMPATIBLE", command)
        self.assertIn("REQUIREMENT_GATE_LEGACY_LAYOUT", command)
        self.assertIn("never selects a filename", command)
        self.assertIn("MUST NOT modify `spec.md`", command)
        self.assertIn("never become runtime files", command)
        self.assertIn("do not execute any\nembedded Core step", command)
        self.assertIn("Rule key", command)
        self.assertIn("spec.md#<Spec semantic ref>", command)
        for path in (TEMPLATES / "requirements").glob("*.md"):
            template = read(path)
            self.assertIn("fragment", template.casefold())
            self.assertNotIn("**Stage**:", template)
            self.assertNotIn("**Spec Revision**:", template)

    def test_requirement_fragments_have_unique_rule_keys_and_cover_six_gates(
        self,
    ) -> None:
        rule_keys: list[str] = []
        covered_gates: set[str] = set()
        parsed_rule_gates: dict[str, set[str]] = {}
        for path in sorted((TEMPLATES / "requirements").glob("*.md")):
            for line in read(path).splitlines():
                cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
                if (
                    len(cells) != 3
                    or not re.fullmatch(r"[A-Z]+(?:-[A-Z]+)+", cells[0])
                ):
                    continue
                rule_keys.append(cells[0])
                gates = {
                    gate.strip() for gate in cells[1].split("/") if gate.strip()
                }
                parsed_rule_gates[cells[0]] = gates
                covered_gates.update(gates)

        self.assertEqual(len(rule_keys), len(set(rule_keys)))
        self.assertEqual(set(STANDARD_REQUIREMENT_GATES), covered_gates)
        self.assertEqual(set(REQUIREMENT_RULE_GATES), set(rule_keys))
        self.assertEqual(REQUIREMENT_RULE_GATES, parsed_rule_gates)

    def test_plan_preflights_one_gate_before_any_write(self) -> None:
        command = read(COMMANDS / "speckit.plan.md")
        for term in (
            "Canonical Requirement Gate Preflight",
            "--json --paths-only",
            "Read the resolved current `spec.md` and only",
            "`checklists/requirements.md`",
            "speckit.requirement-gate.v1",
            "REQUIREMENT_GATE_PREFLIGHT_BLOCKED",
            "zero Plan writes",
            "REQUIREMENT_GATE_CORE_WRAPPER_INCOMPATIBLE",
            "path-only resolution -> canonical preflight -> Core pre-execution hooks",
        ):
            self.assertIn(term, command)
        self.assertIn("must not\nexecute a second scan", command)


class RequirementGateReconciliationTests(unittest.TestCase):
    CURRENT_REVISION = f"sha256:{'c' * 64}"

    def inspect(self, bundle: dict, *, require_ready: bool = False) -> dict:
        return inspect_requirement_gate_bundle(
            bundle,
            current_spec_revision=self.CURRENT_REVISION,
            all_spec_refs={"FR-017"},
            require_ready=require_ready,
        )

    def test_canonical_ready_bundle_is_valid_and_strictly_derived(self) -> None:
        result = self.inspect(requirement_gate_bundle(), require_ready=True)
        self.assertEqual("PASS", result["status"])
        self.assertEqual([], result["findings"])
        self.assertEqual(6, len(result["derived_gate_summary"]))
        self.assertEqual(
            "PASS", result["derived_planning_readiness"]["status"]
        )

    def test_revision_rule_key_and_current_spec_evidence_are_structural(self) -> None:
        invalid_revision = requirement_gate_bundle(revision="sha256:not-a-digest")
        codes = {
            finding["code"] for finding in self.inspect(invalid_revision)["findings"]
        }
        self.assertIn("REQUIREMENT_GATE_METADATA_MALFORMED", codes)

        missing_rule = requirement_gate_bundle()
        missing_rule["semantic_groups"][0]["checks"][0].pop("rule_key")
        codes = {
            finding["code"] for finding in self.inspect(missing_rule)["findings"]
        }
        self.assertIn("REQUIREMENT_GATE_CHECK_MALFORMED", codes)

        wrong_rule_gate = requirement_gate_bundle()
        wrong_rule_gate["semantic_groups"][0]["checks"][0][
            "rule_key"
        ] = "UI-EVIDENCE"
        codes = {
            finding["code"]
            for finding in self.inspect(wrong_rule_gate)["findings"]
        }
        self.assertIn("REQUIREMENT_GATE_CHECK_MALFORMED", codes)

        foreign_evidence = requirement_gate_bundle()
        foreign_evidence["semantic_groups"][0]["checks"][0]["evidence_refs"] = [
            "README.md#FR-017"
        ]
        codes = {
            finding["code"] for finding in self.inspect(foreign_evidence)["findings"]
        }
        self.assertIn("REQUIREMENT_GATE_CHECK_EVIDENCE_INVALID", codes)

        wrong_ref = requirement_gate_bundle()
        wrong_ref["semantic_groups"][0]["checks"][0]["evidence_refs"] = [
            "spec.md#FR-404"
        ]
        codes = {finding["code"] for finding in self.inspect(wrong_ref)["findings"]}
        self.assertIn("REQUIREMENT_GATE_CHECK_EVIDENCE_INVALID", codes)

        duplicated_spec_ref = requirement_gate_bundle()
        duplicated_spec_ref["semantic_groups"][0]["checks"][0]["spec_refs"].append(
            "FR-017"
        )
        codes = {
            finding["code"]
            for finding in self.inspect(duplicated_spec_ref)["findings"]
        }
        self.assertIn("REQUIREMENT_GATE_CHECK_MALFORMED", codes)

    def test_canonical_layout_rejects_answer_copies_and_missing_semantic_groups(
        self,
    ) -> None:
        copied_answer = requirement_gate_bundle()
        copied_answer["semantic_groups"][0]["checks"][0][
            "accepted_answer"
        ] = "Only administrators may authorize deletion."
        codes = {
            finding["code"] for finding in self.inspect(copied_answer)["findings"]
        }
        self.assertIn("REQUIREMENT_GATE_LAYOUT_EXTRA_FIELD", codes)

        missing_group = inspect_requirement_gate_bundle(
            requirement_gate_bundle(),
            current_spec_revision=self.CURRENT_REVISION,
            all_spec_refs={"FR-017", "SEC-001"},
        )
        self.assertIn(
            "REQUIREMENT_GATE_SPEC_REF_MISSING",
            {finding["code"] for finding in missing_group["findings"]},
        )

    def test_checklist_first_focus_and_rerun_build_one_idempotent_bundle(self) -> None:
        source = requirement_gate_bundle(blocked_gates=("requirements",))
        applicability = {
            record["gate"]: (
                record["applicability"],
                record.get("applicability_reason"),
            )
            for record in source["gate_summary"]
        }
        groups = deepcopy(source["semantic_groups"])
        groups[0]["manual_notes"] = "manual\nnotes\nstay byte-for-byte"

        first = rebuild_requirement_gate(
            spec_revision=self.CURRENT_REVISION,
            all_spec_refs={"FR-017"},
            semantic_groups=groups,
            applicability=applicability,
        )
        focused = rebuild_requirement_gate(
            spec_revision=self.CURRENT_REVISION,
            all_spec_refs={"FR-017"},
            semantic_groups=groups,
            applicability=applicability,
            focus="security",
        )
        rerun_groups = deepcopy(groups)
        rerun_groups[0].pop("manual_notes")
        rerun = rebuild_requirement_gate(
            spec_revision=self.CURRENT_REVISION,
            all_spec_refs={"FR-017"},
            semantic_groups=rerun_groups,
            applicability=applicability,
            previous_bundle=first,
        )

        self.assertEqual(CANONICAL_REQUIREMENT_GATE_PATH, first["path"])
        self.assertEqual(first, focused)
        self.assertEqual(first, rerun)
        self.assertEqual(
            "manual\nnotes\nstay byte-for-byte",
            rerun["semantic_groups"][0]["manual_notes"],
        )
        self.assertEqual(
            [check["id"] for check in first["semantic_groups"][0]["checks"]],
            [check["id"] for check in rerun["semantic_groups"][0]["checks"]],
        )

        wording_only = deepcopy(groups)
        wording_only[0]["checks"][0]["concern"] = (
            "requirements atomic quality, wording clarified"
        )
        rewritten = rebuild_requirement_gate(
            spec_revision=self.CURRENT_REVISION,
            all_spec_refs={"FR-017"},
            semantic_groups=wording_only,
            applicability=applicability,
            previous_bundle=first,
        )
        self.assertEqual(
            first["semantic_groups"][0]["checks"][0]["id"],
            rewritten["semantic_groups"][0]["checks"][0]["id"],
        )

    def test_one_root_cause_is_shared_across_three_gates_and_one_question(self) -> None:
        bundle = requirement_gate_bundle(
            blocked_gates=("requirements", "behavior", "security")
        )
        self.assertEqual("PASS", self.inspect(bundle)["status"])
        candidates = clarification_candidates(bundle)
        self.assertEqual(1, len(candidates))
        self.assertEqual(
            ["CHK-BEH-001", "CHK-REQ-001", "CHK-SEC-001"],
            candidates[0]["affected_check_ids"],
        )

    def test_two_distinct_root_causes_under_one_spec_ref_do_not_merge(self) -> None:
        bundle = requirement_gate_bundle(blocked_gates=("requirements",))
        group = bundle["semantic_groups"][0]
        ux_check = next(check for check in group["checks"] if check["gate"] == "ux")
        ux_check.update(
            status="BLOCKED",
            evidence_refs=[],
            blocker_ref="BLK-FR-017-02",
        )
        group["blockers"].append(
            {
                "id": "BLK-FR-017-02",
                "primary_spec_ref": "FR-017",
                "semantic_key": "deletion-scope",
                "gap": "Deletion scope is unresolved.",
                "affected_check_ids": ["CHK-UX-001"],
                "class": "product-decision",
                "owner": "clarify",
                "status": "OPEN",
                "replacement_refs": [],
            }
        )
        ux_summary = next(
            item for item in bundle["gate_summary"] if item["gate"] == "ux"
        )
        ux_summary.update(
            status="BLOCKED",
            blocker_refs=["BLK-FR-017-02"],
            blocker_count=1,
        )
        bundle["planning_readiness"]["blocker_refs"] = [
            "BLK-FR-017-01",
            "BLK-FR-017-02",
        ]
        self.assertEqual("PASS", self.inspect(bundle)["status"])
        self.assertEqual(2, len(clarification_candidates(bundle)))

    def test_same_topic_under_different_spec_refs_does_not_merge(self) -> None:
        first = requirement_gate_bundle(blocked_gates=("requirements",))
        second_group = deepcopy(first["semantic_groups"][0])
        second_group["spec_ref"] = "FR-018"
        second_group["checks"] = [deepcopy(second_group["checks"][0])]
        second_group["checks"][0].update(
            id="CHK-REQ-018",
            spec_refs=["FR-018"],
            blocker_ref="BLK-FR-018-01",
        )
        second_group["blockers"][0].update(
            id="BLK-FR-018-01",
            primary_spec_ref="FR-018",
            affected_check_ids=["CHK-REQ-018"],
        )
        first["semantic_groups"].append(second_group)
        candidates = clarification_candidates(first)
        self.assertEqual(
            ["BLK-FR-017-01", "BLK-FR-018-01"],
            [candidate["blocker_id"] for candidate in candidates],
        )

        invalid_merge = deepcopy(first)
        second = invalid_merge["semantic_groups"][1]
        second["checks"][0]["blocker_ref"] = "BLK-FR-017-01"
        second["blockers"] = []
        invalid_merge["semantic_groups"][0]["blockers"][0][
            "affected_check_ids"
        ].append("CHK-REQ-018")
        result = inspect_requirement_gate_bundle(
            invalid_merge,
            current_spec_revision=self.CURRENT_REVISION,
            all_spec_refs={"FR-017", "FR-018"},
        )
        self.assertIn(
            "REQUIREMENT_GATE_BLOCKER_CROSS_GROUP",
            {finding["code"] for finding in result["findings"]},
        )

    def test_clarify_candidate_queue_is_capped_at_five_root_causes(self) -> None:
        groups = []
        for index in range(1, 7):
            spec_ref = f"FR-{index:03d}"
            groups.append(
                {
                    "spec_ref": spec_ref,
                    "blockers": [
                        {
                            "id": f"BLK-{index:03d}",
                            "primary_spec_ref": spec_ref,
                            "semantic_key": f"root-{index}",
                            "gap": f"Decision {index} is unresolved.",
                            "affected_check_ids": [f"CHK-{index:03d}"],
                            "class": "product-decision",
                            "status": "OPEN",
                        }
                    ],
                }
            )
        candidates = clarification_candidates(
            {"semantic_groups": groups},
            priority_by_blocker={
                "BLK-006": (5, 5),
                "BLK-005": (4, 4),
                "BLK-004": (3, 3),
                "BLK-003": (2, 2),
                "BLK-002": (1, 1),
                "BLK-001": (0, 0),
            },
        )
        self.assertEqual(5, len(candidates))
        self.assertEqual(
            ["BLK-006", "BLK-005", "BLK-004", "BLK-003", "BLK-002"],
            [candidate["blocker_id"] for candidate in candidates],
        )

    def test_pass_evidence_and_blocker_are_mutually_exclusive(self) -> None:
        bundle = requirement_gate_bundle()
        bundle["semantic_groups"][0]["checks"][0][
            "blocker_ref"
        ] = "BLK-FR-017-01"
        codes = {finding["code"] for finding in self.inspect(bundle)["findings"]}
        self.assertIn("REQUIREMENT_GATE_CHECK_RESULT_INVALID", codes)

    def test_duplicate_semantic_root_cause_is_rejected(self) -> None:
        bundle = requirement_gate_bundle(blocked_gates=("requirements",))
        duplicate = deepcopy(bundle["semantic_groups"][0]["blockers"][0])
        duplicate["id"] = "BLK-FR-017-DUP"
        bundle["semantic_groups"][0]["blockers"].append(duplicate)
        codes = {finding["code"] for finding in self.inspect(bundle)["findings"]}
        self.assertIn("REQUIREMENT_GATE_BLOCKER_ROOT_DUPLICATE", codes)

    def test_shared_blocker_affected_refs_must_match_all_inbound_checks(self) -> None:
        bundle = requirement_gate_bundle(
            blocked_gates=("requirements", "behavior", "security")
        )
        bundle["semantic_groups"][0]["blockers"][0]["affected_check_ids"] = [
            "CHK-REQ-001"
        ]
        codes = {finding["code"] for finding in self.inspect(bundle)["findings"]}
        self.assertIn("REQUIREMENT_GATE_BLOCKER_AFFECTED_CHECK_MISMATCH", codes)

    def test_duplicate_or_orphan_refs_are_stably_rejected(self) -> None:
        duplicate = requirement_gate_bundle()
        duplicate["semantic_groups"][0]["checks"].append(
            deepcopy(duplicate["semantic_groups"][0]["checks"][0])
        )
        codes = {finding["code"] for finding in self.inspect(duplicate)["findings"]}
        self.assertIn("REQUIREMENT_GATE_CHECK_DUPLICATE", codes)

        orphan = requirement_gate_bundle(blocked_gates=("requirements",))
        orphan["semantic_groups"][0]["checks"][0]["blocker_ref"] = "BLK-UNKNOWN"
        codes = {finding["code"] for finding in self.inspect(orphan)["findings"]}
        self.assertIn("REQUIREMENT_GATE_BLOCKER_UNKNOWN", codes)

        duplicate_group = requirement_gate_bundle()
        duplicate_group["semantic_groups"].append(
            deepcopy(duplicate_group["semantic_groups"][0])
        )
        codes = {
            finding["code"] for finding in self.inspect(duplicate_group)["findings"]
        }
        self.assertIn("REQUIREMENT_GATE_SPEC_REF_DUPLICATE", codes)

        duplicate_blocker = requirement_gate_bundle(
            blocked_gates=("requirements",)
        )
        duplicate_blocker["semantic_groups"][0]["blockers"].append(
            deepcopy(duplicate_blocker["semantic_groups"][0]["blockers"][0])
        )
        codes = {
            finding["code"]
            for finding in self.inspect(duplicate_blocker)["findings"]
        }
        self.assertIn("REQUIREMENT_GATE_BLOCKER_DUPLICATE", codes)

        unknown_spec = requirement_gate_bundle()
        unknown_spec["semantic_groups"][0]["spec_ref"] = "FR-404"
        codes = {
            finding["code"] for finding in self.inspect(unknown_spec)["findings"]
        }
        self.assertIn("REQUIREMENT_GATE_SPEC_REF_UNKNOWN", codes)

        wrong_class = requirement_gate_bundle(blocked_gates=("security",))
        wrong_class["semantic_groups"][0]["blockers"][0]["class"] = (
            "provider-evidence"
        )
        codes = {
            finding["code"] for finding in self.inspect(wrong_class)["findings"]
        }
        self.assertIn("REQUIREMENT_GATE_BLOCKER_CLASS_INVALID", codes)

        wrong_owner = requirement_gate_bundle(blocked_gates=("security",))
        wrong_owner["semantic_groups"][0]["blockers"][0]["owner"] = "checklist"
        codes = {
            finding["code"] for finding in self.inspect(wrong_owner)["findings"]
        }
        self.assertIn("REQUIREMENT_GATE_BLOCKER_OWNER_INVALID", codes)

    def test_summary_missing_duplicate_and_drift_are_rejected(self) -> None:
        missing = requirement_gate_bundle()
        missing["gate_summary"].pop()
        codes = {finding["code"] for finding in self.inspect(missing)["findings"]}
        self.assertIn("REQUIREMENT_GATE_SUMMARY_MISSING", codes)

        duplicate = requirement_gate_bundle()
        duplicate["gate_summary"].append(deepcopy(duplicate["gate_summary"][0]))
        codes = {finding["code"] for finding in self.inspect(duplicate)["findings"]}
        self.assertIn("REQUIREMENT_GATE_SUMMARY_DUPLICATE", codes)

        drift = requirement_gate_bundle()
        drift["gate_summary"][0]["check_count"] = 99
        codes = {finding["code"] for finding in self.inspect(drift)["findings"]}
        self.assertIn("REQUIREMENT_GATE_SUMMARY_DRIFT", codes)

    def test_not_applicable_gate_requires_current_reason(self) -> None:
        bundle = requirement_gate_bundle()
        group = bundle["semantic_groups"][0]
        group["checks"] = [
            check for check in group["checks"] if check["gate"] != "visual"
        ]
        visual = next(
            item for item in bundle["gate_summary"] if item["gate"] == "visual"
        )
        visual.update(
            applicability="NOT_APPLICABLE",
            applicability_reason=None,
            status="PASS",
            check_refs=[],
            blocker_refs=[],
            check_count=0,
            blocker_count=0,
        )
        codes = {finding["code"] for finding in self.inspect(bundle)["findings"]}
        self.assertIn("REQUIREMENT_GATE_APPLICABILITY_REASON_MISSING", codes)
        visual["applicability_reason"] = "This feature has no visible surface."
        codes = {finding["code"] for finding in self.inspect(bundle)["findings"]}
        self.assertIn("REQUIREMENT_GATE_APPLICABILITY_REASON_MISSING", codes)
        visual["applicability_reason"] = (
            "FR-017 explicitly has no user-visible surface."
        )
        self.assertEqual("PASS", self.inspect(bundle)["status"])

    def test_partial_clarification_preserves_one_shared_blocker(self) -> None:
        bundle = requirement_gate_bundle(
            blocked_gates=("requirements", "behavior", "security")
        )
        evidence = {
            check["id"]: ["spec.md#FR-017"]
            for check in bundle["semantic_groups"][0]["checks"]
            if check["gate"] != "security"
        }
        result = reconcile_requirement_gate(
            bundle,
            current_spec_revision=self.CURRENT_REVISION,
            all_spec_refs={"FR-017"},
            current_evidence_by_check=evidence,
        )
        self.assertEqual("BLOCKED", result["status"])
        self.assertEqual(1, len(result["candidates"]))
        blocker = result["updated"]["semantic_groups"][0]["blockers"][0]
        self.assertEqual(["CHK-SEC-001"], blocker["affected_check_ids"])
        requirements_summary = next(
            item
            for item in result["updated"]["gate_summary"]
            if item["gate"] == "requirements"
        )
        self.assertEqual("PASS", requirements_summary["status"])

    def test_one_answer_closes_multiple_checks_and_all_gates(self) -> None:
        bundle = requirement_gate_bundle(
            blocked_gates=("requirements", "behavior", "security")
        )
        evidence = {
            check["id"]: ["spec.md#FR-017"]
            for check in bundle["semantic_groups"][0]["checks"]
        }
        result = reconcile_requirement_gate(
            bundle,
            current_spec_revision=self.CURRENT_REVISION,
            all_spec_refs={"FR-017"},
            current_evidence_by_check=evidence,
        )
        self.assertEqual("PASS", result["status"])
        self.assertEqual([], result["candidates"])
        blocker = result["updated"]["semantic_groups"][0]["blockers"][0]
        self.assertEqual("RESOLVED", blocker["status"])
        self.assertEqual([], blocker["affected_check_ids"])

    def test_zero_question_closeout_refreshes_stale_revision(self) -> None:
        bundle = requirement_gate_bundle(revision=f"sha256:{'5' * 64}")
        evidence = {
            check["id"]: ["spec.md#FR-017"]
            for check in bundle["semantic_groups"][0]["checks"]
        }
        result = reconcile_requirement_gate(
            bundle,
            current_spec_revision=self.CURRENT_REVISION,
            all_spec_refs={"FR-017"},
            current_evidence_by_check=evidence,
        )
        self.assertEqual("PASS", result["status"])
        self.assertEqual(
            self.CURRENT_REVISION,
            result["updated"]["metadata"]["spec_revision"],
        )
        self.assertEqual(
            self.CURRENT_REVISION,
            result["updated"]["planning_readiness"]["spec_revision"],
        )

    def test_reconciliation_rerun_is_idempotent(self) -> None:
        bundle = requirement_gate_bundle(
            blocked_gates=("requirements", "behavior", "security")
        )
        evidence = {
            check["id"]: ["spec.md#FR-017"]
            for check in bundle["semantic_groups"][0]["checks"]
        }
        first = reconcile_requirement_gate(
            bundle,
            current_spec_revision=self.CURRENT_REVISION,
            all_spec_refs={"FR-017"},
            current_evidence_by_check=evidence,
        )["updated"]
        second = reconcile_requirement_gate(
            first,
            current_spec_revision=self.CURRENT_REVISION,
            all_spec_refs={"FR-017"},
            current_evidence_by_check=evidence,
        )["updated"]
        self.assertEqual(first, second)

    def test_missing_or_malformed_gate_is_not_created_or_rewritten(self) -> None:
        missing = reconcile_requirement_gate(
            None,
            current_spec_revision=self.CURRENT_REVISION,
            all_spec_refs={"FR-017"},
            current_evidence_by_check={},
        )
        self.assertIsNone(missing["updated"])
        self.assertEqual("REQUIREMENT_GATE_MISSING", missing["findings"][0]["code"])

        malformed = reconcile_requirement_gate(
            {"path": CANONICAL_REQUIREMENT_GATE_PATH},
            current_spec_revision=self.CURRENT_REVISION,
            all_spec_refs={"FR-017"},
            current_evidence_by_check={},
        )
        self.assertIsNone(malformed["updated"])
        self.assertEqual(
            "REQUIREMENT_GATE_MALFORMED", malformed["findings"][0]["code"]
        )

        duplicate = requirement_gate_bundle()
        duplicate["semantic_groups"][0]["checks"].append(
            deepcopy(duplicate["semantic_groups"][0]["checks"][0])
        )
        before = deepcopy(duplicate)
        malformed_duplicate = reconcile_requirement_gate(
            duplicate,
            current_spec_revision=self.CURRENT_REVISION,
            all_spec_refs={"FR-017"},
            current_evidence_by_check={},
        )
        self.assertIsNone(malformed_duplicate["updated"])
        self.assertEqual(before, duplicate)
        self.assertIn(
            "REQUIREMENT_GATE_CHECK_DUPLICATE",
            {finding["code"] for finding in malformed_duplicate["findings"]},
        )

    def test_reconciliation_never_hides_new_missing_evidence(self) -> None:
        original = requirement_gate_bundle()
        result = reconcile_requirement_gate(
            original,
            current_spec_revision=self.CURRENT_REVISION,
            all_spec_refs={"FR-017"},
            current_evidence_by_check={},
        )
        self.assertEqual("BLOCKED", result["status"])
        self.assertIsNone(result["updated"])
        self.assertEqual("PASS", original["planning_readiness"]["status"])
        self.assertIn(
            "REQUIREMENT_GATE_RECONCILIATION_BLOCKER_REQUIRED",
            {finding["code"] for finding in result["findings"]},
        )

    def test_source_evidence_blocker_never_becomes_product_question(self) -> None:
        bundle = requirement_gate_bundle(
            blocked_gates=("visual",),
            blocker_class="source-evidence",
        )
        self.assertEqual([], clarification_candidates(bundle))
        evidence = {
            check["id"]: ["spec.md#FR-017"]
            for check in bundle["semantic_groups"][0]["checks"]
            if check["gate"] != "visual"
        }
        reconciled = reconcile_requirement_gate(
            bundle,
            current_spec_revision=self.CURRENT_REVISION,
            all_spec_refs={"FR-017"},
            current_evidence_by_check=evidence,
        )
        blocker = reconciled["updated"]["semantic_groups"][0]["blockers"][0]
        self.assertEqual("source-evidence", blocker["class"])
        self.assertEqual("source-owner", blocker["owner"])
        self.assertEqual([], reconciled["candidates"])

    def test_interrupted_second_write_recovers_from_stale_gate_only(self) -> None:
        stale_gate = requirement_gate_bundle(
            revision=f"sha256:{'5' * 64}",
            blocked_gates=("requirements", "behavior", "security"),
        )
        stale_snapshot = deepcopy(stale_gate)
        evidence = {
            check["id"]: ["spec.md#FR-017"]
            for check in stale_gate["semantic_groups"][0]["checks"]
        }
        failed_sync_state = preflight_requirement_gate(
            stale_gate,
            current_spec_revision=self.CURRENT_REVISION,
            all_spec_refs={"FR-017"},
        )
        self.assertEqual("BLOCKED", failed_sync_state["status"])
        self.assertEqual(0, failed_sync_state["write_count"])
        self.assertIn(
            "REQUIREMENT_GATE_SPEC_REVISION_STALE",
            {finding["code"] for finding in failed_sync_state["findings"]},
        )
        recovered = reconcile_requirement_gate(
            stale_gate,
            current_spec_revision=self.CURRENT_REVISION,
            all_spec_refs={"FR-017"},
            current_evidence_by_check=evidence,
        )
        self.assertEqual("PASS", recovered["status"])
        self.assertEqual(stale_snapshot, stale_gate)
        self.assertEqual(
            self.CURRENT_REVISION,
            recovered["updated"]["metadata"]["spec_revision"],
        )
        self.assertEqual([], recovered["candidates"])

    def test_legacy_and_advisory_files_are_ignored_byte_for_byte(self) -> None:
        canonical = requirement_gate_bundle()
        advisory = {
            "path": "checklists/copy.md",
            "bytes": "manual advisory content",
        }
        legacy = {
            "path": "checklists/behavior.md",
            "bytes": "legacy product answer must not be imported",
        }
        result = select_authoritative_requirement_gate(
            [canonical, advisory, legacy]
        )
        self.assertIs(canonical, result["authoritative"])
        self.assertEqual([advisory, legacy], result["ignored"])
        self.assertEqual(
            ["REQUIREMENT_GATE_LEGACY_LAYOUT"],
            [finding["code"] for finding in result["findings"]],
        )

    def test_plan_preflight_is_read_only_and_blocks_stale_or_open_gate(self) -> None:
        stale = preflight_requirement_gate(
            requirement_gate_bundle(revision=f"sha256:{'5' * 64}"),
            current_spec_revision=self.CURRENT_REVISION,
            all_spec_refs={"FR-017"},
        )
        self.assertEqual("BLOCKED", stale["status"])
        self.assertEqual(0, stale["write_count"])
        self.assertFalse(stale["hooks_started"])
        self.assertFalse(stale["core_setup_started"])
        self.assertIsNone(stale["next_step"])
        self.assertIn(
            "REQUIREMENT_GATE_SPEC_REVISION_STALE",
            {finding["code"] for finding in stale["findings"]},
        )
        self.assertIn(
            "PLANNING_READINESS_DERIVATION_INVALID",
            {finding["code"] for finding in stale["findings"]},
        )

        open_gate = preflight_requirement_gate(
            requirement_gate_bundle(blocked_gates=("behavior",)),
            current_spec_revision=self.CURRENT_REVISION,
            all_spec_refs={"FR-017"},
        )
        self.assertEqual("BLOCKED", open_gate["status"])
        self.assertEqual(0, open_gate["write_count"])
        self.assertIn(
            "REQUIREMENT_GATE_PREFLIGHT_BLOCKED",
            {finding["code"] for finding in open_gate["findings"]},
        )

    def test_plan_preflight_zero_writes_for_every_named_failure_class(self) -> None:
        cases: list[dict] = []

        n_a_without_reason = requirement_gate_bundle()
        group = n_a_without_reason["semantic_groups"][0]
        group["checks"] = [
            check for check in group["checks"] if check["gate"] != "visual"
        ]
        visual = next(
            row for row in n_a_without_reason["gate_summary"]
            if row["gate"] == "visual"
        )
        visual.update(
            applicability="NOT_APPLICABLE",
            applicability_reason=None,
            status="PASS",
            check_refs=[],
            blocker_refs=[],
            check_count=0,
            blocker_count=0,
        )
        cases.append(n_a_without_reason)

        malformed_ref = requirement_gate_bundle()
        malformed_ref["semantic_groups"][0]["checks"][0]["spec_refs"] = ["FR-404"]
        cases.append(malformed_ref)

        placeholder = requirement_gate_bundle()
        placeholder["semantic_groups"][0]["checks"][0]["concern"] = (
            "TODO define authorization quality"
        )
        cases.append(placeholder)

        residual_open_blocker = requirement_gate_bundle()
        residual_open_blocker["semantic_groups"][0]["blockers"].append(
            {
                "id": "BLK-FR-017-RESIDUAL",
                "primary_spec_ref": "FR-017",
                "semantic_key": "residual-open-root",
                "gap": "An OPEN root cause remains after PASS text.",
                "affected_check_ids": ["CHK-REQ-001"],
                "class": "product-decision",
                "owner": "clarify",
                "status": "OPEN",
                "replacement_refs": [],
            }
        )
        cases.append(residual_open_blocker)

        old_plan = {
            "plan.md": "old plan bytes",
            "research.md": "old research bytes",
        }
        old_plan_snapshot = deepcopy(old_plan)
        for bundle in cases:
            bundle_snapshot = deepcopy(bundle)
            result = preflight_requirement_gate(
                bundle,
                current_spec_revision=self.CURRENT_REVISION,
                all_spec_refs={"FR-017"},
            )
            self.assertEqual("BLOCKED", result["status"])
            self.assertEqual(0, result["write_count"])
            self.assertFalse(result["hooks_started"])
            self.assertFalse(result["core_setup_started"])
            self.assertIsNone(result["next_step"])
            self.assertIn(
                "REQUIREMENT_GATE_PREFLIGHT_BLOCKED",
                {finding["code"] for finding in result["findings"]},
            )
            self.assertEqual(bundle_snapshot, bundle)
            self.assertEqual(old_plan_snapshot, old_plan)

    def test_issue_50_revision_gap_fixture_closes_only_after_full_sync(self) -> None:
        fixture = load_json(
            REQUIREMENT_GATE_FIXTURES / "issue_50_revision_gap.json"
        )
        self.assertEqual(2, len(clarification_candidates(fixture)))

        partial_evidence = {
            "CHK-REQ-017": ["spec.md#FR-017"],
            "CHK-BEH-017": ["spec.md#FR-017"],
            "CHK-SEC-017": ["spec.md#FR-017"],
            "CHK-NFR-017": ["spec.md#FR-017"],
            "CHK-VIS-017": ["spec.md#FR-017"],
        }
        partial = reconcile_requirement_gate(
            fixture,
            current_spec_revision=self.CURRENT_REVISION,
            all_spec_refs={"FR-017"},
            current_evidence_by_check=partial_evidence,
        )
        self.assertEqual("BLOCKED", partial["status"])
        self.assertEqual(1, len(partial["candidates"]))
        blocked_preflight = preflight_requirement_gate(
            partial["updated"],
            current_spec_revision=self.CURRENT_REVISION,
            all_spec_refs={"FR-017"},
        )
        self.assertEqual("BLOCKED", blocked_preflight["status"])
        self.assertEqual(0, blocked_preflight["write_count"])

        full_evidence = dict(partial_evidence)
        full_evidence["CHK-UX-017"] = ["spec.md#FR-017"]
        full = reconcile_requirement_gate(
            partial["updated"],
            current_spec_revision=self.CURRENT_REVISION,
            all_spec_refs={"FR-017"},
            current_evidence_by_check=full_evidence,
        )
        self.assertEqual("PASS", full["status"])
        ready_preflight = preflight_requirement_gate(
            full["updated"],
            current_spec_revision=self.CURRENT_REVISION,
            all_spec_refs={"FR-017"},
        )
        self.assertEqual("PASS", ready_preflight["status"])
        self.assertEqual(0, ready_preflight["write_count"])
        self.assertEqual("CORE_PRE_EXECUTION_HOOKS", ready_preflight["next_step"])
        self.assertFalse(ready_preflight["hooks_started"])
        self.assertFalse(ready_preflight["core_setup_started"])

    def test_spec_and_blocker_id_split_merge_retire_are_traceable(self) -> None:
        spec_records = [
            {
                "id": "FR-001",
                "status": "REPLACED",
                "replacement_refs": ["FR-002", "FR-003"],
                "reason": "Split two meanings.",
            },
            {
                "id": "FR-002",
                "status": "ACTIVE",
                "replacement_refs": [],
            },
            {
                "id": "FR-003",
                "status": "RETIRED",
                "replacement_refs": [],
                "reason": "No longer in scope.",
            },
            {
                "id": "FR-004",
                "status": "REPLACED",
                "replacement_refs": ["FR-002"],
                "reason": "Merged into the current authorization rule.",
            },
        ]
        validate_id_lifecycle(spec_records, kind="Spec")

        blocker_records = [
            {
                "id": "BLK-001",
                "status": "SUPERSEDED",
                "replacement_refs": ["BLK-003"],
            },
            {
                "id": "BLK-002",
                "status": "SUPERSEDED",
                "replacement_refs": ["BLK-003"],
            },
            {
                "id": "BLK-003",
                "status": "OPEN",
                "replacement_refs": [],
            },
            {
                "id": "BLK-004",
                "status": "RETIRED",
                "replacement_refs": [],
                "reason": "The referenced product scope was retired.",
            },
        ]
        validate_id_lifecycle(blocker_records, kind="Blocker")

        with self.assertRaisesRegex(ValueError, "unknown successor"):
            validate_id_lifecycle(
                [
                    {
                        "id": "BLK-001",
                        "status": "SUPERSEDED",
                        "replacement_refs": ["BLK-404"],
                    }
                ],
                kind="Blocker",
            )

        with self.assertRaisesRegex(ValueError, "replacement cycle"):
            validate_id_lifecycle(
                [
                    {
                        "id": "FR-010",
                        "status": "REPLACED",
                        "replacement_refs": ["FR-011"],
                    },
                    {
                        "id": "FR-011",
                        "status": "REPLACED",
                        "replacement_refs": ["FR-010"],
                    },
                ],
                kind="Spec",
            )

    def test_wrapper_capability_failure_is_an_explicit_blocker(self) -> None:
        compatible = inspect_core_wrapper_contract(
            checklist_output_paths=[CANONICAL_REQUIREMENT_GATE_PATH],
            plan_events=[
                {"name": "path-resolution", "writes": False},
                {"name": "canonical-preflight", "writes": False},
                {"name": "before-plan-hook", "hook": True, "writes": False},
                {"name": "core-setup", "writes": True},
            ],
        )
        self.assertEqual("PASS", compatible["status"])

        extra_output = inspect_core_wrapper_contract(
            checklist_output_paths=[
                CANONICAL_REQUIREMENT_GATE_PATH,
                "checklists/security.md",
            ],
            plan_events=[
                {"name": "path-resolution", "writes": False},
                {"name": "canonical-preflight", "writes": False},
                {"name": "core-setup", "writes": True},
            ],
        )
        write_first = inspect_core_wrapper_contract(
            checklist_output_paths=[CANONICAL_REQUIREMENT_GATE_PATH],
            plan_events=[
                {"name": "path-resolution", "writes": False},
                {"name": "core-setup", "writes": True},
                {"name": "canonical-preflight", "writes": False},
            ],
        )
        for result in (extra_output, write_first):
            self.assertEqual("BLOCKED", result["status"])
            self.assertEqual(
                {"REQUIREMENT_GATE_CORE_WRAPPER_INCOMPATIBLE"},
                {finding["code"] for finding in result["findings"]},
            )


class CoreWrapperInstallationTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("specify"), "specify CLI is not on PATH")
    def test_installed_composition_enforces_single_output_and_write_first_gate(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            source = temp_root / "source"
            project = temp_root / "project"
            shutil.copytree(
                ROOT,
                source,
                ignore=shutil.ignore_patterns(".git", ".venv", "__pycache__"),
            )
            subprocess.run(
                [
                    "specify",
                    "init",
                    str(project),
                    "--integration",
                    "codex",
                    "--ignore-agent-tools",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                ["specify", "preset", "remove", "workflow-preset"],
                cwd=project,
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                ["specify", "preset", "add", "--dev", str(source)],
                cwd=project,
                check=True,
                capture_output=True,
                text=True,
            )

            composed = (
                project
                / ".specify"
                / "presets"
                / "workflow-preset"
                / ".composed"
            )
            checklist = read(composed / "speckit.checklist.md")
            plan = read(composed / "speckit.plan.md")

            self.assertNotIn("{CORE_TEMPLATE}", checklist)
            self.assertLess(
                checklist.index("## Preset Checklist Ownership"),
                checklist.index("## User Input"),
            )
            self.assertLess(
                checklist.index("Create or recompute `FEATURE_DIR/checklists/<domain>.md`"),
                checklist.index("## Authoritative Core Conflict Resolution"),
            )
            self.assertIn(
                "do not execute any\nembedded Core step that creates "
                "Domain/advisory/focus checklist files",
                checklist,
            )
            self.assertIn(
                "any $ARGUMENTS focus\n  -> exactly "
                "FEATURE_DIR/checklists/requirements.md",
                checklist,
            )

            canonical_preflight = plan.index(
                "## Canonical Requirement Gate Preflight"
            )
            inherited_preflight = plan.index("## Requirement Gate Preflight")
            pre_execution_hooks = plan.index("## Pre-Execution Checks")
            first_write = plan.index("1. **Materialize plan**")
            self.assertLess(canonical_preflight, inherited_preflight)
            self.assertLess(inherited_preflight, pre_execution_hooks)
            self.assertLess(pre_execution_hooks, first_write)
            for core_marker in (
                "### Phase 0: Outline & Research",
                "### Phase 1: Design & Contracts",
                "Re-evaluate Constitution Check post-design",
                "## Mandatory Post-Execution Hooks",
                "## Completion Report",
            ):
                self.assertIn(core_marker, plan)
            self.assertIn(
                "path-only resolution -> canonical preflight "
                "-> Core pre-execution hooks\n  -> Core write-bearing setup",
                plan,
            )


class UISpecContractTests(unittest.TestCase):
    def test_complete_ui_spec_contract_is_valid(self) -> None:
        validate_ui_specification_contract(minimal_ui_spec_contract())

    def test_locator_only_and_visual_role_overreach_are_rejected(self) -> None:
        payload = minimal_ui_spec_contract()
        payload["sources"][0]["supplied_facts"] = []
        with self.assertRaisesRegex(ValueError, "locator alone"):
            validate_ui_specification_contract(payload)

        payload = minimal_ui_spec_contract()
        payload["sources"][0]["projected_refs"].append("FR-001")
        payload["all_spec_requirement_refs"].append("FR-001")
        with self.assertRaisesRegex(ValueError, "visual-input projects unrelated"):
            validate_ui_specification_contract(payload)

    def test_requirement_source_can_project_mixed_spec_and_ui_refs(self) -> None:
        payload = minimal_ui_spec_contract()
        payload["sources"][0]["role"] = "requirement-input"
        payload["sources"][0]["projected_refs"].append("FR-001")
        payload["all_spec_requirement_refs"].append("FR-001")
        validate_ui_specification_contract(payload)

    def test_derivation_gap_and_conflict_states_remain_distinguishable(self) -> None:
        payload = minimal_ui_spec_contract()
        requirement = payload["requirements"][0]
        requirement["derivation"] = "derived"
        with self.assertRaisesRegex(ValueError, "derived_from"):
            validate_ui_specification_contract(payload)

        payload = minimal_ui_spec_contract()
        requirement = payload["requirements"][0]
        requirement["derivation"] = "derived"
        requirement["derived_from"] = ["invented-observation"]
        with self.assertRaisesRegex(ValueError, "does not cite an observation"):
            validate_ui_specification_contract(payload)

        payload = minimal_ui_spec_contract()
        requirement = payload["requirements"][0]
        requirement["derivation"] = "assumed"
        with self.assertRaisesRegex(ValueError, "documented default"):
            validate_ui_specification_contract(payload)

        payload = minimal_ui_spec_contract()
        requirement = payload["requirements"][0]
        requirement["derivation"] = "conflicting"
        requirement["status"] = "BLOCKED"
        requirement["blocker"] = "UI_EVIDENCE_CONFLICT"
        with self.assertRaisesRegex(ValueError, "needs two locators"):
            validate_ui_specification_contract(payload)

        payload = minimal_ui_spec_contract()
        requirement = payload["requirements"][0]
        requirement["derivation"] = "unresolved"
        with self.assertRaisesRegex(ValueError, "must remain BLOCKED"):
            validate_ui_specification_contract(payload)

        payload = minimal_ui_spec_contract()
        requirement = payload["requirements"][0]
        requirement["derivation"] = "unresolved"
        requirement["status"] = "BLOCKED"
        requirement["blocker"] = "UI_EVIDENCE_MISSING"
        requirement["evidence_locators"] = []
        del requirement["acceptance"]
        validate_ui_specification_contract(payload)

    def test_state_viewport_evidence_and_outcome_ownership_are_structural(self) -> None:
        payload = minimal_ui_spec_contract()
        payload["requirements"][0]["evidence_support"].remove("viewport")
        with self.assertRaisesRegex(ValueError, "corresponding evidence for viewport"):
            validate_ui_specification_contract(payload)

        payload = minimal_ui_spec_contract()
        payload["requirements"][0]["evidence_locators"] = ["missing.html#state"]
        with self.assertRaisesRegex(ValueError, "not present in supplied source facts"):
            validate_ui_specification_contract(payload)

        payload = minimal_ui_spec_contract()
        payload["requirements"][0]["outcome_only"] = False
        with self.assertRaisesRegex(ValueError, "observable outcome, not implementation"):
            validate_ui_specification_contract(payload)

        payload = minimal_ui_spec_contract()
        payload["requirements"][0]["framework_component"] = "RefundPanel"
        with self.assertRaisesRegex(
            ValueError,
            "implementation/source-unsupported field",
        ):
            validate_ui_specification_contract(payload)

        payload = minimal_ui_spec_contract()
        payload["sources"].append(
            {
                "ref": "SRC-UI-002",
                "role": "visual-input",
                "locator_or_description": "unsupplied design locator",
                "bounded_scope": "refund success state",
                "supplied_facts": [],
                "projected_refs": [],
                "status": "BLOCKED",
                "blocker": "SRC_EVIDENCE_MISSING",
            }
        )
        validate_ui_specification_contract(payload)

    def test_restoration_dimensions_and_pixel_target_contract_are_closed(self) -> None:
        payload = minimal_ui_spec_contract()
        payload["restoration_dimensions"].pop()
        with self.assertRaisesRegex(ValueError, "dimension matrix is incomplete"):
            validate_ui_specification_contract(payload)

        payload = minimal_ui_spec_contract()
        del payload["pixel_targets"][0]["rendering_context"]
        with self.assertRaisesRegex(ValueError, "incomplete rendering_context"):
            validate_ui_specification_contract(payload)

        payload = minimal_ui_spec_contract()
        payload["pixel_targets"][0]["baseline_locator"] = "missing.png#panel"
        with self.assertRaisesRegex(ValueError, "not present in supplied source facts"):
            validate_ui_specification_contract(payload)

        payload = minimal_ui_spec_contract()
        payload["pixel_targets"][0]["exception_refs"] = ["PEX-404"]
        with self.assertRaisesRegex(ValueError, "unknown accepted exception"):
            validate_ui_specification_contract(payload)

        payload = minimal_ui_spec_contract()
        payload["pixel_exceptions"][0]["source_refs"] = []
        with self.assertRaisesRegex(ValueError, "non-empty source_refs"):
            validate_ui_specification_contract(payload)

        payload = minimal_ui_spec_contract()
        payload["pixel_targets"][0]["visual_dimensions"].pop("typography")
        with self.assertRaisesRegex(ValueError, "incomplete visual_dimensions"):
            validate_ui_specification_contract(payload)

        payload = minimal_ui_spec_contract()
        payload["pixel_targets"][0]["acceptance_envelope"]["kind"] = "perceptual"
        with self.assertRaisesRegex(ValueError, "mismatches fidelity mode"):
            validate_ui_specification_contract(payload)

        payload = minimal_ui_spec_contract()
        payload["pixel_targets"][0]["fidelity_mode"] = "structural-only"
        with self.assertRaisesRegex(ValueError, "differs from its profile"):
            validate_ui_specification_contract(payload)

        payload = minimal_ui_spec_contract()
        payload["pixel_profiles"][0]["exception_refs"] = []
        with self.assertRaisesRegex(ValueError, "outside its profile policy"):
            validate_ui_specification_contract(payload)

        payload = minimal_ui_spec_contract()
        payload["pixel_profiles"] = []
        payload["pixel_targets"] = []
        payload["pixel_exceptions"] = []
        with self.assertRaisesRegex(ValueError, "stable specified or blocked profile"):
            validate_ui_specification_contract(payload)

        payload = minimal_ui_spec_contract()
        payload["pixel_profiles"][0]["status"] = "BLOCKED"
        payload["pixel_profiles"][0]["blocker"] = "PIXEL_BASELINE_MISSING"
        del payload["pixel_profiles"][0]["fidelity_mode"]
        del payload["pixel_profiles"][0]["exception_policy"]
        payload["pixel_targets"][0]["status"] = "BLOCKED"
        payload["pixel_targets"][0]["blocker"] = "PIXEL_BASELINE_MISSING"
        for field in (
            "baseline_source_ref",
            "baseline_locator",
            "rendering_context",
            "visual_dimensions",
            "acceptance_envelope",
        ):
            del payload["pixel_targets"][0][field]
        validate_ui_specification_contract(payload)

    def test_adaptation_policy_rejects_ambiguity_and_lower_priority_override(
        self,
    ) -> None:
        payload = minimal_ui_spec_contract()
        payload["adaptation_policies"][0]["target_platform"] = "Swift"
        with self.assertRaisesRegex(ValueError, "not a target platform"):
            validate_ui_specification_contract(payload)

        payload = minimal_ui_spec_contract()
        payload["adaptation_policies"][0]["mode"] = "hybrid"
        with self.assertRaisesRegex(ValueError, "invalid adaptation mode"):
            validate_ui_specification_contract(payload)

        payload = minimal_ui_spec_contract()
        payload["adaptation_policies"][0]["decisions"].pop()
        with self.assertRaisesRegex(ValueError, "incomplete or duplicated"):
            validate_ui_specification_contract(payload)

        payload = minimal_ui_spec_contract()
        del payload["adaptation_policies"][0]["target_contexts"]["accessibility"]
        with self.assertRaisesRegex(ValueError, "incomplete target contexts"):
            validate_ui_specification_contract(payload)

        payload = minimal_ui_spec_contract()
        adaptive_decision = next(
            decision
            for decision in payload["adaptation_policies"][0]["decisions"]
            if decision["decision"] == "adapt"
        )
        adaptive_decision["source_refs"] = []
        with self.assertRaisesRegex(ValueError, "must cite source evidence"):
            validate_ui_specification_contract(payload)

        payload = minimal_ui_spec_contract()
        content_decision = next(
            decision
            for decision in payload["adaptation_policies"][0]["decisions"]
            if decision["dimension"] == "content-and-information-hierarchy"
        )
        content_decision["decision"] = "adapt"
        with self.assertRaisesRegex(ValueError, "fails to preserve"):
            validate_ui_specification_contract(payload)

        payload = minimal_ui_spec_contract()
        decision = payload["adaptation_policies"][0]["decisions"][0]
        decision["hard_constraint_conflict"] = True
        decision["decision"] = "preserve"
        with self.assertRaisesRegex(ValueError, "override a hard constraint"):
            validate_ui_specification_contract(payload)

        payload = minimal_ui_spec_contract()
        decision = payload["adaptation_policies"][0]["decisions"][0]
        decision["decision"] = "blocked"
        decision["status"] = "BLOCKED"
        decision["blocker"] = "TARGET_CONTEXT_CONFLICT"
        with self.assertRaisesRegex(ValueError, "must be BLOCKED"):
            validate_ui_specification_contract(payload)

        payload = minimal_ui_spec_contract()
        payload["adaptation_policies"] = []
        with self.assertRaisesRegex(ValueError, "requires an adaptation policy"):
            validate_ui_specification_contract(payload)

        payload = minimal_ui_spec_contract()
        policy = payload["adaptation_policies"][0]
        policy["mode"] = "visual-equivalent-native"
        with self.assertRaisesRegex(ValueError, "override requires an explicit reason"):
            validate_ui_specification_contract(payload)

        payload = minimal_ui_spec_contract()
        policy = payload["adaptation_policies"][0]
        policy["target_platform"] = "HTML/Web"
        policy["mode"] = "framework-equivalent"
        for policy_decision in policy["decisions"]:
            policy_decision["decision"] = "preserve"
        validate_ui_specification_contract(payload)
        policy["decisions"][0]["decision"] = "adapt"
        with self.assertRaisesRegex(ValueError, "framework-equivalent diverges"):
            validate_ui_specification_contract(payload)


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
        for issue_46_term in (
            "Consumed Spec SHA-256",
            "PLAN_SPEC_INPUT_STALE",
            "reference-only Spec UI Input Inventory",
            "general UI mappings",
            "pixel-target mappings",
            "platform-adaptation mappings",
            "every applicable `PXT-*` and `ADP-*`",
            "never relabeled N/A",
        ):
            self.assertIn(issue_46_term, command)

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

    def test_plan_x2b_uses_stable_ui_consumption_failure_codes(self) -> None:
        command = read(COMMANDS / "speckit.plan.md")
        validator = read(VALIDATORS / "speckit_plan_contract.py")
        for code in (
            "PLAN_SPEC_INPUT_STALE",
            "X2B_SPEC_REF_UNMAPPED",
            "X2B_SPEC_REF_DUPLICATE",
            "X2B_SPEC_REF_UNKNOWN",
            "X2B_PIXEL_TARGET_UNMAPPED",
            "X2B_PIXEL_EXCEPTION_UNRESOLVED",
            "X2B_ADAPTATION_UNMAPPED",
            "X2B_BLOCKER_SUPPRESSED",
            "X2B_SPEC_OWNERSHIP_LEAK",
            "X2B_DELIVERY_DECISION_INCOMPLETE",
        ):
            self.assertIn(code, command)
            self.assertIn(code, validator)

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
        self.assertIn("Consumed Spec SHA-256", template)
        self.assertIn("Current local Spec SHA-256", template)
        self.assertIn("Invalidate affected X2-B", template)

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
        for issue_46_term in (
            "Consumed Spec SHA-256",
            "Spec UI Input Inventory",
            "General UI Delivery Mappings",
            "Pixel-Target Delivery Mappings",
            "Platform-Adaptation Delivery Mappings",
            "X2B-UI-001",
            "X2B-PX-001",
            "X2B-ADP-001",
            "does not copy requirement statements",
            "must not repeat or weaken those values",
            "Every required `X2B-*` mapping has exactly one closed row",
        ):
            self.assertIn(issue_46_term, ui_template)
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

    def test_plan_bundle_rejects_stale_spec_and_generic_mapping_gaps(self) -> None:
        bundle = load_json(PLAN_BUNDLE_FIXTURES / "ui_only.json")
        bundle["spec_input"]["current_sha256"] = (
            "sha256:eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
        )
        with self.assertRaisesRegex(ValueError, "PLAN_SPEC_INPUT_STALE"):
            validate_plan_artifact_bundle(bundle)

        bundle = load_json(PLAN_BUNDLE_FIXTURES / "ui_only.json")
        bundle["x2b_delivery_mappings"][0]["spec_refs"].remove("UI-001")
        with self.assertRaisesRegex(ValueError, "X2B_SPEC_REF_UNMAPPED"):
            validate_plan_artifact_bundle(bundle)

    def test_plan_bundle_rejects_pixel_and_adaptation_mapping_gaps(self) -> None:
        bundle = load_json(PLAN_BUNDLE_FIXTURES / "ui_only.json")
        pixel_mapping = next(
            mapping
            for mapping in bundle["x2b_delivery_mappings"]
            if mapping["kind"] == "pixel-target"
        )
        pixel_mapping["spec_refs"].remove("PXT-001")
        with self.assertRaisesRegex(ValueError, "X2B_PIXEL_TARGET_UNMAPPED"):
            validate_plan_artifact_bundle(bundle)

        bundle = load_json(PLAN_BUNDLE_FIXTURES / "ui_only.json")
        pixel_mapping = next(
            mapping
            for mapping in bundle["x2b_delivery_mappings"]
            if mapping["kind"] == "pixel-target"
        )
        pixel_mapping["spec_refs"].remove("PEX-001")
        with self.assertRaisesRegex(ValueError, "X2B_PIXEL_EXCEPTION_UNRESOLVED"):
            validate_plan_artifact_bundle(bundle)

        bundle = load_json(PLAN_BUNDLE_FIXTURES / "ui_only.json")
        bundle["x2b_delivery_mappings"] = [
            mapping
            for mapping in bundle["x2b_delivery_mappings"]
            if mapping["id"] != "X2B-ADP-002"
        ]
        bundle["uiux_readiness_rows"] = [
            row
            for row in bundle["uiux_readiness_rows"]
            if row["mapping_ref"] != "X2B-ADP-002"
        ]
        with self.assertRaisesRegex(ValueError, "X2B_ADAPTATION_UNMAPPED"):
            validate_plan_artifact_bundle(bundle)

    def test_plan_bundle_rejects_duplicate_unknown_and_incomplete_x2b_rows(
        self,
    ) -> None:
        bundle = load_json(PLAN_BUNDLE_FIXTURES / "ui_only.json")
        bundle["x2b_input_inventory"].append(
            dict(bundle["x2b_input_inventory"][0])
        )
        with self.assertRaisesRegex(ValueError, "X2B_SPEC_REF_DUPLICATE"):
            validate_plan_artifact_bundle(bundle)

        bundle = load_json(PLAN_BUNDLE_FIXTURES / "ui_only.json")
        orphan = dict(bundle["x2b_delivery_mappings"][0])
        orphan["id"] = "X2B-UI-ORPHAN-001"
        orphan["spec_refs"] = ["UI-404"]
        bundle["x2b_delivery_mappings"].append(orphan)
        with self.assertRaisesRegex(ValueError, "X2B_SPEC_REF_UNKNOWN"):
            validate_plan_artifact_bundle(bundle)

        bundle = load_json(PLAN_BUNDLE_FIXTURES / "ui_only.json")
        del bundle["x2b_delivery_mappings"][0]["component_delivery"]
        with self.assertRaisesRegex(
            ValueError,
            "X2B_DELIVERY_DECISION_INCOMPLETE",
        ):
            validate_plan_artifact_bundle(bundle)

        bundle = load_json(PLAN_BUNDLE_FIXTURES / "ui_only.json")
        bundle["uiux_readiness_rows"].pop()
        with self.assertRaisesRegex(
            ValueError,
            "X2B_DELIVERY_DECISION_INCOMPLETE",
        ):
            validate_plan_artifact_bundle(bundle)

    def test_plan_bundle_propagates_spec_blockers_and_rejects_ownership_leaks(
        self,
    ) -> None:
        bundle = load_json(PLAN_BUNDLE_FIXTURES / "ui_only.json")
        bundle["spec_input"]["ui_contract_refs"][0]["status"] = "BLOCKED"
        bundle["spec_input"]["ui_contract_refs"][0]["blocker"] = "UI-SRC-BLOCKED"
        with self.assertRaisesRegex(ValueError, "X2B_BLOCKER_SUPPRESSED"):
            validate_plan_artifact_bundle(bundle)

        for forbidden_field in (
            "statement",
            "acceptance",
            "fidelity_mode",
            "acceptance_envelope",
            "baseline_locator",
            "bound",
            "exception_bound",
            "decisions",
            "adaptation_decision",
        ):
            with self.subTest(field=forbidden_field):
                bundle = load_json(PLAN_BUNDLE_FIXTURES / "ui_only.json")
                bundle["x2b_delivery_mappings"][0][forbidden_field] = "copied"
                with self.assertRaisesRegex(
                    ValueError,
                    "X2B_SPEC_OWNERSHIP_LEAK",
                ):
                    validate_plan_artifact_bundle(bundle)

        bundle = load_json(PLAN_BUNDLE_FIXTURES / "ui_only.json")
        pixel_mapping = next(
            mapping
            for mapping in bundle["x2b_delivery_mappings"]
            if mapping["kind"] == "pixel-target"
        )
        pixel_mapping["delivery_mapping"] = {
            "layout_delivery": "component-owned",
            "acceptance_envelope": {"kind": "copied"},
        }
        with self.assertRaisesRegex(ValueError, "X2B_SPEC_OWNERSHIP_LEAK"):
            validate_plan_artifact_bundle(bundle)

    def test_plan_x2b_mapping_kind_requires_matching_id_prefix(self) -> None:
        cases = (
            ("X2B-UI-001", "X2B-PX-999"),
            ("X2B-PX-001", "X2B-UI-999"),
            ("X2B-ADP-001", "X2B-UI-998"),
        )
        for old_id, mismatched_id in cases:
            with self.subTest(old_id=old_id, mismatched_id=mismatched_id):
                bundle = replace_string_values(
                    load_json(PLAN_BUNDLE_FIXTURES / "ui_only.json"),
                    old_id,
                    mismatched_id,
                )
                with self.assertRaisesRegex(
                    ValueError,
                    "X2B_DELIVERY_DECISION_INCOMPLETE",
                ):
                    validate_plan_artifact_bundle(bundle)

    def test_plan_bundle_accepts_same_stable_spec_blocker_propagation(self) -> None:
        bundle = load_json(PLAN_BUNDLE_FIXTURES / "ui_only.json")
        blocker = "BLK-SPEC-UI-001"
        bundle["spec_input"]["ui_contract_refs"][0]["status"] = "BLOCKED"
        bundle["spec_input"]["ui_contract_refs"][0]["blocker"] = blocker
        inventory_row = next(
            row
            for row in bundle["x2b_input_inventory"]
            if row["spec_ref"] == "UI-001"
        )
        inventory_row["spec_status"] = "BLOCKED"
        inventory_row["x2b_applicability"] = "Blocked"
        inventory_row["propagated_blocker"] = blocker
        del inventory_row["mapping_ref"]
        general_mapping = next(
            mapping
            for mapping in bundle["x2b_delivery_mappings"]
            if mapping["id"] == "X2B-UI-001"
        )
        general_mapping["spec_refs"].remove("UI-001")
        for mapping in bundle["x2b_delivery_mappings"]:
            if "ui_vis_refs" in mapping:
                mapping["ui_vis_refs"] = ["VIS-001"]
        bundle["lanes"]["X2-B"] = {"status": "Blocked", "blocker": blocker}
        bundle["gates"]["X2B_UIUX_READY"] = {
            "status": "BLOCKED",
            "evidence": [blocker],
            "blockers": [blocker],
        }
        bundle["reconciliation"]["blocker_owners"] = {blocker: "X2-B"}
        bundle["plan_output_ready"] = "BLOCKED"
        validate_plan_artifact_bundle(bundle)

    def test_blocked_x2b_mapping_blocks_gate_and_plan_output(self) -> None:
        bundle = load_json(PLAN_BUNDLE_FIXTURES / "ui_only.json")
        blocker = "BLK-X2B-DELIVERY-001"
        mapping = bundle["x2b_delivery_mappings"][0]
        mapping["status"] = "BLOCKED"
        mapping["blocker"] = blocker
        readiness = next(
            row
            for row in bundle["uiux_readiness_rows"]
            if row["mapping_ref"] == mapping["id"]
        )
        readiness.clear()
        readiness.update(
            {
                "mapping_ref": mapping["id"],
                "status": "BLOCKED",
                "blocker": blocker,
            }
        )
        bundle["lanes"]["X2-B"] = {"status": "Blocked", "blocker": blocker}
        bundle["gates"]["X2B_UIUX_READY"] = {
            "status": "BLOCKED",
            "evidence": [blocker],
            "blockers": [blocker],
        }
        bundle["reconciliation"]["blocker_owners"] = {blocker: "X2-B"}
        bundle["plan_output_ready"] = "BLOCKED"
        validate_plan_artifact_bundle(bundle)

    def test_non_ui_bundle_closes_x2b_with_scoped_spec_evidence(self) -> None:
        bundle = load_json(PLAN_BUNDLE_FIXTURES / "minimal_repository.json")
        self.assertTrue(bundle["spec_input"]["non_ui_evidence"])
        self.assertEqual([], bundle["spec_input"]["ui_contract_refs"])
        self.assertEqual("N/A", bundle["gates"]["X2B_UIUX_READY"]["status"])
        validate_plan_artifact_bundle(bundle)

        del bundle["spec_input"]["non_ui_evidence"]["reason"]
        with self.assertRaisesRegex(
            ValueError,
            "X2B_DELIVERY_DECISION_INCOMPLETE",
        ):
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

    def test_tasks_x2b_complete_bundle_maps_all_classes_once(self) -> None:
        bundle = minimal_tasks_x2b_bundle()
        validate_tasks_x2b_derivation(bundle)
        task_refs = [
            mapping_ref
            for task in bundle["tasks"]
            for mapping_ref in task["mapping_refs"]
        ]
        self.assertEqual(1, task_refs.count("X2B-UI-001"))
        self.assertEqual(2, task_refs.count("X2B-PX-001"))
        self.assertEqual(1, task_refs.count("X2B-ADP-001"))
        self.assertNotIn("X2B-PX-REVIEW-001", task_refs)
        self.assertNotIn("X2B-ADP-NA-001", task_refs)

    def test_tasks_x2b_preflight_rejects_stale_handoff(self) -> None:
        bundle = minimal_tasks_x2b_bundle()
        bundle["tasks_handoff_revision"] = "PLAN-46"
        with self.assertRaisesRegex(ValueError, "PLAN_OUTPUT_INCOMPLETE"):
            validate_tasks_x2b_derivation(bundle)

    def test_tasks_x2b_required_mapping_must_have_concrete_tasks(self) -> None:
        bundle = minimal_tasks_x2b_bundle()
        bundle["tasks"] = [
            task for task in bundle["tasks"] if task["id"] != "T043"
        ]
        with self.assertRaisesRegex(ValueError, "TASK_X2B_MAPPING_UNMAPPED"):
            validate_tasks_x2b_derivation(bundle)

    def test_tasks_x2b_duplicate_mapping_and_unknown_ref_are_stable(self) -> None:
        duplicate = minimal_tasks_x2b_bundle()
        duplicate["x2b_mappings"].append(
            deepcopy(duplicate["x2b_mappings"][0])
        )
        with self.assertRaisesRegex(ValueError, "TASK_X2B_MAPPING_DUPLICATE"):
            validate_tasks_x2b_derivation(duplicate)

        unknown = minimal_tasks_x2b_bundle()
        unknown["tasks"][0]["mapping_refs"] = ["X2B-UI-404"]
        with self.assertRaisesRegex(ValueError, "TASK_X2B_REF_UNKNOWN"):
            validate_tasks_x2b_derivation(unknown)

    def test_tasks_x2b_blocker_never_becomes_normal_task(self) -> None:
        bundle = minimal_tasks_x2b_bundle()
        bundle["x2b_mappings"].append(
            {
                "id": "X2B-UI-BLOCKED-001",
                "status": "Blocked",
                "implementation_dimensions": [],
                "depends_on": [],
                "traceability_refs": ["UI-001"],
                "blocker": "BLOCK-UI-001",
            }
        )
        with self.assertRaisesRegex(ValueError, "PLAN_OUTPUT_INCOMPLETE"):
            validate_tasks_x2b_derivation(bundle)

        suppressed = minimal_tasks_x2b_bundle()
        suppressed["x2b_mappings"].append(
            {
                "id": "X2B-UI-BLOCKED-001",
                "status": "Blocked",
                "implementation_dimensions": [],
                "depends_on": [],
                "traceability_refs": ["UI-001"],
                "blocker": "BLOCK-UI-001",
            }
        )
        task = deepcopy(suppressed["tasks"][0])
        task["id"] = "T045"
        task["paths"] = ["src/ui/BlockedPanel.tsx"]
        task["mapping_refs"] = ["X2B-UI-BLOCKED-001"]
        suppressed["tasks"].append(task)
        with self.assertRaisesRegex(ValueError, "TASK_X2B_BLOCKER_SUPPRESSED"):
            validate_tasks_x2b_derivation(suppressed)

    def test_tasks_x2b_requires_full_pixel_and_adaptation_dimensions(self) -> None:
        pixel = minimal_tasks_x2b_bundle()
        pixel["tasks"][2]["implementation_dimensions"].remove("typography")
        with self.assertRaisesRegex(
            ValueError,
            "TASK_X2B_IMPLEMENTATION_DIMENSION_UNCOVERED",
        ):
            validate_tasks_x2b_derivation(pixel)

        adaptation = minimal_tasks_x2b_bundle()
        adaptation["tasks"][3]["implementation_dimensions"].remove(
            "localization"
        )
        with self.assertRaisesRegex(ValueError, "TASK_X2B_ADAPTATION_UNCOVERED"):
            validate_tasks_x2b_derivation(adaptation)

    def test_tasks_x2b_derives_dependencies_without_fixed_lane_order(self) -> None:
        missing_asset_edge = minimal_tasks_x2b_bundle()
        missing_asset_edge["tasks"][2]["depends_on"].remove("T041")
        with self.assertRaisesRegex(ValueError, "TASK_X2B_MAPPING_UNMAPPED"):
            validate_tasks_x2b_derivation(missing_asset_edge)

        independent_platform = minimal_tasks_x2b_bundle()
        independent_platform["x2b_mappings"][2]["depends_on"] = []
        independent_platform["tasks"][3]["depends_on"] = []
        independent_platform["tasks"][3]["parallel"] = True
        validate_tasks_x2b_derivation(independent_platform)

        transitive = minimal_tasks_x2b_bundle()
        transitive["x2b_mappings"][1]["depends_on"] = []
        transitive["tasks"][2]["depends_on"] = ["T041"]
        validate_tasks_x2b_derivation(transitive)

        cyclic = minimal_tasks_x2b_bundle()
        cyclic["tasks"][0]["depends_on"] = ["T042"]
        with self.assertRaisesRegex(ValueError, "TASK_X2B_MAPPING_UNMAPPED"):
            validate_tasks_x2b_derivation(cyclic)

        dependent_parallel = minimal_tasks_x2b_bundle()
        dependent_parallel["tasks"][2]["parallel"] = True
        with self.assertRaisesRegex(ValueError, "TASK_X2B_MAPPING_UNMAPPED"):
            validate_tasks_x2b_derivation(dependent_parallel)

    def test_tasks_x2b_rejects_spec_ownership_and_visual_execution(self) -> None:
        for owned_field in (
            "statement",
            "baseline_identity",
            "baseline_source_ref",
            "baseline_locator",
            "rendering_context",
            "fidelity_mode",
            "acceptance",
            "acceptance_envelope",
            "bound",
            "exception_bound",
            "adaptation_decisions",
            "adaptation_decision",
        ):
            with self.subTest(owned_field=owned_field):
                bundle = minimal_tasks_x2b_bundle()
                bundle["tasks"][0][owned_field] = "copied from Spec"
                with self.assertRaisesRegex(
                    ValueError,
                    "TASK_SPEC_OWNERSHIP_LEAK",
                ):
                    validate_tasks_x2b_derivation(bundle)

        for forbidden in (
            "screenshot capture",
            "capture screenshots",
            "take screenshots",
            "generate a baseline",
            "produce the baseline",
            "evaluate the acceptance threshold",
            "compare pixels",
            "run visual-diff",
            "pixel comparison",
            "perceptual comparison",
            "visual acceptance",
            "final rendered visual review",
        ):
            with self.subTest(forbidden=forbidden):
                bundle = minimal_tasks_x2b_bundle()
                bundle["tasks"][0]["description"] = forbidden
                with self.assertRaisesRegex(
                    ValueError,
                    "TASK_VISUAL_EXECUTION_LEAK",
                ):
                    validate_tasks_x2b_derivation(bundle)

        bundle = minimal_tasks_x2b_bundle()
        bundle["tasks"][0]["description"] = (
            "Use pixel-tolerant fidelity semantics."
        )
        with self.assertRaisesRegex(ValueError, "TASK_SPEC_OWNERSHIP_LEAK"):
            validate_tasks_x2b_derivation(bundle)

        bundle = minimal_tasks_x2b_bundle()
        bundle["tasks"][0]["description"] = "Prepare the component."
        bundle["tasks"][0]["action_classes"] = ["visual-execution"]
        with self.assertRaisesRegex(ValueError, "TASK_VISUAL_EXECUTION_LEAK"):
            validate_tasks_x2b_derivation(bundle)

    def test_tasks_tests_are_derived_only_from_required_test_readiness(self) -> None:
        bundle = minimal_tasks_x2b_bundle()
        bundle["test_tasks"][0]["tc_refs"] = ["TC-VISUAL-INVENTED"]
        with self.assertRaisesRegex(ValueError, "TASK_SPEC_OWNERSHIP_LEAK"):
            validate_tasks_x2b_derivation(bundle)

        bundle = minimal_tasks_x2b_bundle()
        bundle["test_tasks"][0]["action_classes"] = ["visual-execution"]
        with self.assertRaisesRegex(ValueError, "TASK_VISUAL_EXECUTION_LEAK"):
            validate_tasks_x2b_derivation(bundle)

    def test_tasks_x2b_rejects_orphan_mapping_traceability(self) -> None:
        bundle = minimal_tasks_x2b_bundle()
        bundle["x2b_mappings"][0]["traceability_refs"] = []
        with self.assertRaisesRegex(ValueError, "TASK_X2B_REF_UNKNOWN"):
            validate_tasks_x2b_derivation(bundle)

    def test_tasks_final_review_covers_x2b_and_stays_last(self) -> None:
        missing_mapping = minimal_tasks_x2b_bundle()
        missing_mapping["final_review"]["mapping_refs"].remove("X2B-PX-001")
        with self.assertRaisesRegex(
            ValueError,
            "TASK_FINAL_REVIEW_MAPPING_MISSING",
        ):
            validate_tasks_x2b_derivation(missing_mapping)

        not_last = minimal_tasks_x2b_bundle()
        not_last["phases"].append("Visual Acceptance")
        with self.assertRaisesRegex(
            ValueError,
            "TASK_FINAL_REVIEW_MAPPING_MISSING",
        ):
            validate_tasks_x2b_derivation(not_last)

        visual_review = minimal_tasks_x2b_bundle()
        visual_review["final_review"]["description"] = "Run screenshot diff"
        with self.assertRaisesRegex(ValueError, "TASK_VISUAL_EXECUTION_LEAK"):
            validate_tasks_x2b_derivation(visual_review)

    def test_tasks_non_ui_handoff_remains_valid_without_x2b(self) -> None:
        bundle = {
            "plan_output_ready": "READY",
            "current_plan_revision": "PLAN-NON-UI",
            "tasks_handoff_revision": "PLAN-NON-UI",
            "uiux_delivery_readiness": "N/A",
            "declared_traceability_refs": [],
            "x2b_mappings": [],
            "tasks": [],
            "required_test_readiness_tc_refs": [],
            "test_tasks": [],
            "phases": ["Service implementation", "Final Code Review"],
            "final_review": {
                "phase": "Final Code Review",
                "kind": "code-design-contract-review",
                "action_classes": ["code-design-contract-review"],
                "mapping_refs": [],
                "scopes": [
                    "implementation-conformance",
                ],
                "paths": ["src/service/refund.py"],
                "description": "Review non-UI code/design-contract conformance.",
            },
        }
        validate_tasks_x2b_derivation(bundle)

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
                    "bounded_scope": "refund feature",
                    "supplied_facts": ["provider packet content"],
                    "projected_refs": [],
                    "status": "retained",
                },
                {
                    "ref": "SRC-007",
                    "role": "context-only",
                    "locator_or_description": "background note",
                    "bounded_scope": "background only",
                    "supplied_facts": ["background note"],
                    "projected_refs": ["FR-001"],
                    "status": "projected",
                },
                {
                    "ref": "SRC-008",
                    "role": "requirement-input",
                    "locator_or_description": "broad roadmap",
                    "bounded_scope": "entire roadmap",
                    "supplied_facts": ["broad roadmap content"],
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

    def test_source_audit_blocks_locator_only_projection(self) -> None:
        snapshot = source_contract_snapshot()
        snapshot["spec"]["sources"][2]["supplied_facts"] = []
        codes = {
            finding["code"]
            for finding in audit_source_reference_contract(snapshot)
        }
        self.assertIn("SRC_EVIDENCE_MISSING", codes)

    def test_source_audit_accepts_stable_blocker_and_rejects_missing_blocker(
        self,
    ) -> None:
        snapshot = source_contract_snapshot()
        source = snapshot["spec"]["sources"][0]
        source["supplied_facts"] = []
        source["projected_refs"] = []
        source["status"] = "BLOCKED"
        source["blocker"] = "SRC_EVIDENCE_MISSING"
        findings = audit_source_reference_contract(snapshot)
        self.assertNotIn(
            "SRC_FIELD_INVALID",
            {finding["code"] for finding in findings},
        )
        self.assertFalse(
            any(
                finding["source"] == "spec.md:SRC-001"
                for finding in findings
            )
        )

        del source["blocker"]
        codes = {
            finding["code"]
            for finding in audit_source_reference_contract(snapshot)
            if finding["source"] == "spec.md:SRC-001"
        }
        self.assertIn("SRC_BLOCKER_MISSING", codes)

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
