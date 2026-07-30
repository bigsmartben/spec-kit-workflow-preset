"""Pure in-memory cross-command audit helpers used by contract fixtures."""
from __future__ import annotations

from typing import Any


ARCH_PROJECTION = {
    "decisions": ("research_refs", "ARCH_DECISION_OMITTED"),
    "concepts": ("data_model_refs", "ARCH_CONCEPT_OMITTED"),
    "boundaries": ("contract_refs", "ARCH_BOUNDARY_OMITTED"),
    "constraints": ("plan_constraint_refs", "ARCH_CONSTRAINT_OMITTED"),
    "gaps": ("blocker_refs", "ARCH_GAP_OMITTED"),
}

DATA_MODEL_OBLIGATION_CODES = {
    "idempotency_key": "ARCH_DATA_MODEL_IDEMPOTENCY_MISSING",
    "provider_task_binding": "ARCH_PROVIDER_BINDING_MISSING",
    "provider_lock": "ARCH_PROVIDER_LOCK_MISSING",
    "retry_context": "ARCH_RETRY_CONTEXT_MISSING",
    "recovery_decision": "ARCH_RECOVERY_DECISION_MISSING",
    "readiness_lifecycle": "ARCH_LIFECYCLE_PROJECTION_MISSING",
}

SOURCE_ROLES = {
    "requirement-input",
    "visual-input",
    "technical-evidence",
    "context-only",
}

NORMATIVE_REQUIREMENT_PREFIXES = ("FR-", "NFR-", "UX-", "UI-", "VIS-")
VISUAL_REQUIREMENT_PREFIXES = ("UI-", "VIS-")
SOURCE_ROW_FIELDS = {
    "ref",
    "role",
    "locator_or_description",
    "revision",
    "bounded_scope",
    "supplied_facts",
    "projected_refs",
    "status",
    "blocker",
    # In-memory audit hints derived from row prose and downstream applicability.
    "broad",
    "feature_slice",
    "ui_ux_applicable",
    "uif_required",
}


def _finding(
    code: str,
    *,
    source: str,
    target: str,
    evidence: str,
    owner: str,
) -> dict[str, str]:
    return {
        "severity": "BLOCKER",
        "code": code,
        "source": source,
        "target": target,
        "evidence": evidence,
        "owner": owner,
    }


def _source_pair_set(rows: Any) -> set[tuple[str, str]]:
    if not isinstance(rows, list):
        return set()
    return {
        (str(row.get("source_ref")), str(row.get("requirement_ref")))
        for row in rows
        if isinstance(row, dict)
        and row.get("source_ref")
        and row.get("requirement_ref")
    }


def audit_source_reference_contract(
    snapshot: dict[str, Any],
) -> list[dict[str, str]]:
    """Audit local source rows and projections without external access."""

    findings: list[dict[str, str]] = []
    spec = snapshot.get("spec", {})
    plan = snapshot.get("plan", {})
    sources = spec.get("sources", [])
    if not isinstance(sources, list):
        return [
            _finding(
                "SRC_CONTRACT_INVALID",
                source="spec.md:Source References",
                target="local source inventory",
                evidence="sources must be a list",
                owner="speckit.specify",
            )
        ]

    source_refs = [
        str(source.get("ref"))
        for source in sources
        if isinstance(source, dict) and source.get("ref")
    ]
    duplicate_refs = sorted(
        {ref for ref in source_refs if source_refs.count(ref) > 1}
    )
    for ref in duplicate_refs:
        findings.append(
            _finding(
                "SRC_REF_DUPLICATE",
                source=f"spec.md:{ref}",
                target="spec.md:Source References",
                evidence="source identity is not unique",
                owner="speckit.specify",
            )
        )

    known_refs = set(source_refs)
    requirement_refs = set(spec.get("requirement_refs", []))
    downstream_refs = set(snapshot.get("referenced_source_refs", []))
    downstream_refs.update(plan.get("source_refs", []))
    ui_ux_mappings = _source_pair_set(plan.get("ui_ux_mappings"))
    uif_mappings = _source_pair_set(plan.get("uif_mappings"))
    downstream_refs.update(source_ref for source_ref, _ in ui_ux_mappings)
    downstream_refs.update(source_ref for source_ref, _ in uif_mappings)

    for source in sources:
        if not isinstance(source, dict):
            findings.append(
                _finding(
                    "SRC_CONTRACT_INVALID",
                    source="spec.md:Source References",
                    target="local source inventory",
                    evidence="source row must be an object",
                    owner="speckit.specify",
                )
            )
            continue

        if not source.get("ref"):
            findings.append(
                _finding(
                    "SRC_REF_MISSING",
                    source="spec.md:Source References row",
                    target="spec.md:SRC ref",
                    evidence="source row has no local identity",
                    owner="speckit.specify",
                )
            )

        ref = str(source.get("ref", "<missing>"))
        role = source.get("role")
        projected_refs = source.get("projected_refs", [])
        if not isinstance(projected_refs, list):
            projected_refs = []

        invalid_fields = sorted(set(source) - SOURCE_ROW_FIELDS)
        if invalid_fields:
            findings.append(
                _finding(
                    "SRC_FIELD_INVALID",
                    source=f"spec.md:{ref}",
                    target="spec.md:Source References columns",
                    evidence=f"provider/source-specific field: {invalid_fields[0]}",
                    owner="speckit.specify",
                )
            )

        if not isinstance(role, str) or role not in SOURCE_ROLES:
            findings.append(
                _finding(
                    "SRC_ROLE_INVALID",
                    source=f"spec.md:{ref}",
                    target="spec.md:Source References.role",
                    evidence=str(role),
                    owner="speckit.specify",
                )
            )

        if not source.get("locator_or_description"):
            findings.append(
                _finding(
                    "SRC_IDENTITY_MISSING",
                    source=f"spec.md:{ref}",
                    target="spec.md:opaque locator / description",
                    evidence="missing local source description",
                    owner="speckit.specify",
                )
            )

        if not source.get("bounded_scope"):
            findings.append(
                _finding(
                    "SRC_BOUNDED_SCOPE_MISSING",
                    source=f"spec.md:{ref}",
                    target="spec.md:bounded feature scope",
                    evidence="missing explicit feature scope",
                    owner="speckit.specify",
                )
            )

        supplied_facts = source.get("supplied_facts")
        if not isinstance(supplied_facts, list):
            findings.append(
                _finding(
                    "SRC_SUPPLIED_FACTS_INVALID",
                    source=f"spec.md:{ref}",
                    target="spec.md:supplied content / facts",
                    evidence="supplied_facts must be a list",
                    owner="speckit.specify",
                )
            )
            supplied_facts = []

        if not source.get("status"):
            findings.append(
                _finding(
                    "SRC_STATUS_MISSING",
                    source=f"spec.md:{ref}",
                    target="spec.md:status / blocker",
                    evidence="missing local projection status",
                    owner="speckit.specify",
                )
            )

        status = str(source.get("status", "")).lower()
        blocker = source.get("blocker")
        if "block" in status and (
            not isinstance(blocker, str) or not blocker.strip()
        ):
            findings.append(
                _finding(
                    "SRC_BLOCKER_MISSING",
                    source=f"spec.md:{ref}",
                    target="spec.md:status / blocker",
                    evidence="BLOCKED source lacks a stable blocker",
                    owner="speckit.specify",
                )
            )
        elif blocker and "block" not in status:
            findings.append(
                _finding(
                    "SRC_STATUS_MISSING",
                    source=f"spec.md:{ref}",
                    target="spec.md:status / blocker",
                    evidence="source blocker requires BLOCKED status",
                    owner="speckit.specify",
                )
            )
        if projected_refs and not supplied_facts:
            findings.append(
                _finding(
                    "SRC_EVIDENCE_MISSING",
                    source=f"spec.md:{ref}",
                    target="local requirement projection",
                    evidence="locator-only input cannot support projected requirements",
                    owner="speckit.specify",
                )
            )
        elif (
            not supplied_facts
            and "block" not in status
            and "evidence_missing" not in status
        ):
            findings.append(
                _finding(
                    "SRC_EVIDENCE_MISSING",
                    source=f"spec.md:{ref}",
                    target="spec.md:status / blocker",
                    evidence="locator-only input lacks SRC_EVIDENCE_MISSING blocker",
                    owner="speckit.specify",
                )
            )

        if "contradict" in status:
            findings.append(
                _finding(
                    "SRC_STATUS_CONTRADICTORY",
                    source=f"spec.md:{ref}",
                    target="local requirement projection",
                    evidence=str(source.get("status")),
                    owner="speckit.clarify",
                )
            )

        if (
            source.get("broad")
            and not source.get("feature_slice")
            and "block" not in status
            and "clarif" not in status
        ):
            findings.append(
                _finding(
                    "SRC_FEATURE_SLICE_MISSING",
                    source=f"spec.md:{ref}",
                    target="spec.md:bounded feature scope",
                    evidence="broad source projected without safe feature slice",
                    owner="speckit.specify",
                )
            )

        normative_refs = [
            str(projected_ref)
            for projected_ref in projected_refs
            if str(projected_ref).startswith(NORMATIVE_REQUIREMENT_PREFIXES)
        ]
        invalid_for_role = False
        if role in {"technical-evidence", "context-only"} and normative_refs:
            invalid_for_role = True
        elif role == "visual-input" and any(
            not ref_value.startswith(VISUAL_REQUIREMENT_PREFIXES)
            for ref_value in normative_refs
        ):
            invalid_for_role = True
        if invalid_for_role:
            findings.append(
                _finding(
                    "SRC_ROLE_PROJECTION_INVALID",
                    source=f"spec.md:{ref}",
                    target="spec.md:projected requirement refs",
                    evidence=f"{role} -> {normative_refs}",
                    owner="speckit.specify",
                )
            )

        missing_projected_refs = sorted(set(projected_refs) - requirement_refs)
        if missing_projected_refs:
            findings.append(
                _finding(
                    "SRC_PROJECTED_REF_MISSING",
                    source=f"spec.md:{ref}",
                    target=f"spec.md:{missing_projected_refs[0]}",
                    evidence="projected requirement ref does not exist locally",
                    owner="speckit.specify",
                )
            )

        if (
            not projected_refs
            and ref not in downstream_refs
            and status not in {"retained", "context-only"}
            and "block" not in status
            and "clarif" not in status
        ):
            findings.append(
                _finding(
                    "SRC_ORPHAN",
                    source=f"spec.md:{ref}",
                    target="local requirements or blocker",
                    evidence="source has no local projection or retained reason",
                    owner="speckit.specify",
                )
            )

        if source.get("ui_ux_applicable", True):
            for projected_ref in normative_refs:
                if not projected_ref.startswith(VISUAL_REQUIREMENT_PREFIXES):
                    continue
                pair = (ref, projected_ref)
                if pair not in ui_ux_mappings:
                    findings.append(
                        _finding(
                            "SRC_UIUX_MAPPING_MISSING",
                            source=f"spec.md:{ref}+{projected_ref}",
                            target="ui-ux-design.md",
                            evidence="applicable source/UI-VIS pair is unmapped",
                            owner="speckit.plan",
                        )
                    )
                if source.get("uif_required") and pair not in uif_mappings:
                    findings.append(
                        _finding(
                            "SRC_UIF_MAPPING_MISSING",
                            source=f"spec.md:{ref}+{projected_ref}",
                            target="contracts/uif/*.expected.json",
                            evidence="required UIF source/requirement pair is unmapped",
                            owner="speckit.plan",
                        )
                    )

    for missing_ref in sorted(downstream_refs - known_refs):
        findings.append(
            _finding(
                "SRC_REF_MISSING",
                source=f"downstream:{missing_ref}",
                target="spec.md:Source References",
                evidence="referenced source does not exist locally",
                owner="speckit.specify",
            )
        )

    return findings


def audit_cross_command_consistency(snapshot: dict[str, Any]) -> list[dict[str, str]]:
    """Return deterministic blocker findings without mutating the snapshot."""

    findings = audit_source_reference_contract(snapshot)
    architecture = snapshot.get("architecture", {})
    plan = snapshot.get("plan", {})
    tasks = snapshot.get("tasks", {})

    architecture_revision = architecture.get("revision")
    if architecture_revision and plan.get("architecture_revision") != architecture_revision:
        findings.append(
            _finding(
                "ARCH_REVISION_STALE",
                source=f"architecture:{architecture_revision}",
                target="plan.md:Architecture Revision",
                evidence=str(plan.get("architecture_revision")),
                owner="speckit.plan",
            )
        )

    for architecture_key, (plan_key, code) in ARCH_PROJECTION.items():
        required = set(architecture.get(architecture_key, []))
        projected = set(plan.get(plan_key, []))
        missing = sorted(required - projected)
        if missing:
            findings.append(
                _finding(
                    code,
                    source=f"architecture:{missing[0]}",
                    target=f"plan-products:{plan_key}",
                    evidence="missing stable ID projection",
                    owner="speckit.plan",
                )
            )

    if plan.get("spec_conflicts"):
        findings.append(
            _finding(
                "SPEC_PLAN_CONFLICT",
                source=str(plan["spec_conflicts"][0]),
                target="plan products",
                evidence="explicit contradictory mapping",
                owner="speckit.plan",
            )
        )

    planned_objects = set(plan.get("design_objects", []))
    task_objects = set(tasks.get("design_object_refs", []))
    missing_objects = sorted(planned_objects - task_objects)
    if missing_objects:
        findings.append(
            _finding(
                "PLAN_TASK_MAPPING_MISSING",
                source=f"plan:{missing_objects[0]}",
                target="tasks.md",
                evidence="no concrete path task",
                owner="speckit.tasks",
            )
        )

    required_conditions = set(plan.get("required_test_conditions", []))
    task_conditions = set(tasks.get("test_condition_refs", []))
    missing_conditions = sorted(required_conditions - task_conditions)
    if missing_conditions:
        findings.append(
            _finding(
                "PLAN_REQUIRED_TEST_TASK_MISSING",
                source=f"test-readiness:{missing_conditions[0]}",
                target="tasks.md",
                evidence="Required Test Condition has no required task",
                owner="speckit.tasks",
            )
        )

    if plan.get("mu_scope") and tasks.get("mu_scope") != plan.get("mu_scope"):
        findings.append(
            _finding(
                "MU_SCOPE_WIDENED",
                source=f"plan:{plan.get('mu_scope')}",
                target="tasks.md:M+U",
                evidence=str(tasks.get("mu_scope")),
                owner="speckit.tasks",
            )
        )

    return findings


def audit_data_model_obligations(
    required_obligations: set[str],
    projected_obligations: set[str],
) -> list[dict[str, str]]:
    """Audit the concrete #24 Architecture-to-data-model failure surface."""

    findings: list[dict[str, str]] = []
    for obligation in sorted(required_obligations - projected_obligations):
        code = DATA_MODEL_OBLIGATION_CODES.get(
            obligation,
            "ARCH_DATA_MODEL_OBLIGATION_MISSING",
        )
        findings.append(
            _finding(
                code,
                source=f"architecture/spec:{obligation}",
                target="data-model.md",
                evidence="required model/state/invariant projection missing",
                owner="speckit.plan",
            )
        )
    return findings
