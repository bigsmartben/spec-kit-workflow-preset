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


def audit_cross_command_consistency(snapshot: dict[str, Any]) -> list[dict[str, str]]:
    """Return deterministic blocker findings without mutating the snapshot."""

    findings: list[dict[str, str]] = []
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
