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

CANONICAL_UI_PREFIXES = (
    "UIAX-", "UIAC-", "UIP-", "UIR-", "UIC-", "UID-", "UIS-", "UIV-",
    "UIW-", "UIT-", "UIA-", "UIM-", "UIE-", "UIN-",
)
NORMATIVE_REQUIREMENT_PREFIXES = (
    "FR-", "NFR-", "UX-", "UI-", "VIS-", *CANONICAL_UI_PREFIXES
)
VISUAL_REQUIREMENT_PREFIXES = ("UI-", "VIS-", *CANONICAL_UI_PREFIXES)
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
    if "canonical_objects" in snapshot.get("spec", {}):
        findings.extend(audit_canonical_ui_chain(snapshot))
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


def audit_canonical_ui_chain(snapshot: dict[str, Any]) -> list[dict[str, str]]:
    """Audit UI/VIS -> Canonical -> X2-B -> Tasks -> Final Review locally."""

    findings: list[dict[str, str]] = []
    spec = snapshot.get("spec", {})
    plan = snapshot.get("plan", {})
    tasks = snapshot.get("tasks", {})
    objects = spec.get("canonical_objects", [])
    if not isinstance(objects, list):
        return [
            _finding(
                "CANONICAL_UI_CONTRACT_INVALID",
                source="spec.md#Canonical-UI-Specification",
                target="Canonical UI object registry",
                evidence="canonical_objects must be a list",
                owner="speckit.specify",
            )
        ]

    object_ids = [
        str(item.get("id", "")) for item in objects if isinstance(item, dict)
    ]
    known_ids = set(object_ids)
    for object_id in sorted({ref for ref in object_ids if object_ids.count(ref) > 1}):
        findings.append(
            _finding(
                "CANONICAL_UI_REF_DUPLICATE",
                source=f"spec.md:{object_id}",
                target="Canonical UI object registry",
                evidence="stable Canonical UI ID is duplicated",
                owner="speckit.specify",
            )
        )
    objects_by_id = {
        str(item.get("id")): item
        for item in objects
        if isinstance(item, dict) and item.get("id")
    }
    for object_id, item in objects_by_id.items():
        for relation_ref in map(str, item.get("relation_refs", [])):
            if relation_ref not in known_ids:
                findings.append(
                    _finding(
                        "CANONICAL_UI_RELATION_DANGLING",
                        source=f"spec.md:{object_id}",
                        target=f"spec.md:{relation_ref}",
                        evidence="Canonical UI relation does not resolve",
                        owner="speckit.specify",
                    )
                )
        object_type = str(item.get("type", ""))
        if object_type in {"page", "region", "component", "content", "state", "event"}:
            outbound = bool(item.get("relation_refs"))
            inbound = any(
                object_id in set(map(str, other.get("relation_refs", [])))
                for other_id, other in objects_by_id.items()
                if other_id != object_id
            )
            if item.get("status") == "specified" and not outbound and not inbound:
                findings.append(
                    _finding(
                        "CANONICAL_UI_ORPHAN",
                        source=f"spec.md:{object_id}",
                        target="spec.md#Canonical-UI-Specification",
                        evidence="composition-critical Canonical UI object is orphaned",
                        owner="speckit.specify",
                    )
                )

    ui_requirement_refs = set(map(str, spec.get("ui_requirement_refs", [])))
    governed_requirements = {
        str(ref)
        for item in objects_by_id.values()
        for ref in item.get("requirement_refs", [])
    }
    for requirement_ref in sorted(ui_requirement_refs - governed_requirements):
        findings.append(
            _finding(
                "CANONICAL_UI_REQUIREMENT_UNCOVERED",
                source=f"spec.md:{requirement_ref}",
                target="spec.md#Canonical-UI-Specification",
                evidence="UI/VIS requirement has no governing Canonical object",
                owner="speckit.specify",
            )
        )

    mappings = plan.get("x2b_delivery_mappings", [])
    if not isinstance(mappings, list):
        mappings = []
    mapping_coverage: dict[str, list[dict[str, Any]]] = {
        object_id: [] for object_id in known_ids
    }
    mappings_by_id: dict[str, dict[str, Any]] = {}
    for mapping in mappings:
        if not isinstance(mapping, dict):
            continue
        mapping_id = str(mapping.get("id", ""))
        mappings_by_id[mapping_id] = mapping
        for ref in map(str, mapping.get("spec_refs", [])):
            if ref in mapping_coverage:
                mapping_coverage[ref].append(mapping)
    for object_id, item in objects_by_id.items():
        if item.get("status") != "specified":
            continue
        covered = mapping_coverage[object_id]
        if not covered:
            findings.append(
                _finding(
                    "X2B_CANONICAL_MAPPING_MISSING",
                    source=f"spec.md:{object_id}",
                    target="ui-ux-design.md",
                    evidence="Canonical UI object has no X2-B mapping",
                    owner="speckit.plan",
                )
            )
            continue
        if len(covered) > 1:
            findings.append(
                _finding(
                    "X2B_CANONICAL_MAPPING_DUPLICATE",
                    source=f"spec.md:{object_id}",
                    target="ui-ux-design.md",
                    evidence="Canonical UI object enters multiple X2-B mappings",
                    owner="speckit.plan",
                )
            )
            continue
        mapping = covered[0]
        binding = mapping.get("canonical_bindings", {}).get(object_id, {})
        expected_requirements = set(map(str, item.get("requirement_refs", [])))
        if (
            not isinstance(binding, dict)
            or not binding.get("target")
            or set(map(str, binding.get("requirement_refs", [])))
            != expected_requirements
        ):
            findings.append(
                _finding(
                    "X2B_CANONICAL_REQUIREMENT_WEAKENED",
                    source=f"spec.md:{object_id}",
                    target=f"ui-ux-design.md:{mapping.get('id')}",
                    evidence="target binding is absent or loses owning requirements",
                    owner="speckit.plan",
                )
            )

    task_items = tasks.get("items", [])
    if not isinstance(task_items, list):
        task_items = []
    for mapping_id, mapping in mappings_by_id.items():
        canonical_refs = {
            str(ref)
            for ref in mapping.get("spec_refs", [])
            if str(ref).startswith(CANONICAL_UI_PREFIXES)
        }
        if not canonical_refs or mapping.get("status") != "READY":
            continue
        matching_tasks = [
            item
            for item in task_items
            if isinstance(item, dict)
            and mapping_id in set(map(str, item.get("mapping_refs", [])))
        ]
        task_refs = {
            str(ref)
            for item in matching_tasks
            for ref in item.get("canonical_refs", [])
        }
        has_paths = any(item.get("paths") for item in matching_tasks)
        if not has_paths or task_refs != canonical_refs:
            findings.append(
                _finding(
                    "TASK_CANONICAL_REF_MISSING",
                    source=f"ui-ux-design.md:{mapping_id}",
                    target="tasks.md",
                    evidence="Tasks lose Canonical refs or concrete target paths",
                    owner="speckit.tasks",
                )
            )

    required_review_refs = {
        object_id
        for object_id, item in objects_by_id.items()
        if item.get("status") == "specified"
    }
    review_refs = set(map(str, tasks.get("final_review_canonical_refs", [])))
    if required_review_refs - review_refs:
        findings.append(
            _finding(
                "FINAL_REVIEW_CANONICAL_REF_MISSING",
                source="tasks.md:implementation mappings",
                target="tasks.md:Final Code Review",
                evidence="Final Code Review omits applicable Canonical UI refs",
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
