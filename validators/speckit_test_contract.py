"""Pure in-memory validators for Plan Test & Acceptance contracts."""
from __future__ import annotations

from typing import Any, Iterable


PIXEL_TERMS = {
    "pixel-perfect",
    "pixel perfect",
    "pixel_fidelity",
    "screenshot",
    "visual diff",
    "baseline capture",
    "visual restoration",
    "rendered visual review",
    "final visual review",
}


def _duplicates(values: Iterable[str]) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return duplicates


def _contains_pixel_scope(value: Any) -> bool:
    if isinstance(value, dict):
        return any(_contains_pixel_scope(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_pixel_scope(item) for item in value)
    if not isinstance(value, str):
        return False
    normalized = value.casefold().replace("-", " ")
    return any(term.replace("-", " ") in normalized for term in PIXEL_TERMS)


def validate_test_conditions(
    payload: dict[str, Any],
    *,
    available_bdd_tc_refs: set[str] | None = None,
) -> None:
    """Validate cross-field rules owned by the Test Conditions contract."""

    conditions = payload.get("conditions")
    if not isinstance(conditions, list) or not conditions:
        raise ValueError("test conditions must include at least one condition")

    ids = [condition.get("id") for condition in conditions]
    if any(not isinstance(item, str) or not item.startswith("TC-") for item in ids):
        raise ValueError("test condition ids must use TC-*")
    duplicates = _duplicates(ids)
    if duplicates:
        raise ValueError(f"duplicate test condition id: {sorted(duplicates)[0]}")

    for condition in conditions:
        condition_id = condition["id"]
        for field in (
            "source_refs",
            "levels",
            "types",
            "techniques",
            "environment_refs",
            "related_refs",
        ):
            if not isinstance(condition.get(field), list) or not condition[field]:
                raise ValueError(f"{condition_id} missing non-empty {field}")

        has_fixtures = bool(condition.get("fixture_refs"))
        has_no_fixture = bool(condition.get("no_fixture_rationale"))
        if has_fixtures == has_no_fixture:
            raise ValueError(
                f"{condition_id} must declare exactly one fixture_refs or no_fixture_rationale"
            )

        has_path = bool(condition.get("quickstart_ref"))
        has_x3_blocker = bool(condition.get("x3_blocker"))
        if has_path == has_x3_blocker:
            raise ValueError(
                f"{condition_id} must declare exactly one quickstart_ref or x3_blocker"
            )

        oracle = condition.get("oracle")
        if not isinstance(oracle, dict) or not oracle.get("kind") or "expected" not in oracle:
            raise ValueError(f"{condition_id} missing complete oracle")
        if not condition.get("risk_or_priority"):
            raise ValueError(f"{condition_id} missing risk_or_priority")
        if not condition.get("execution_mode"):
            raise ValueError(f"{condition_id} missing execution_mode")
        if not condition.get("evidence_requirement"):
            raise ValueError(f"{condition_id} missing evidence_requirement")

        status = condition.get("status")
        if status not in {"required", "blocked"}:
            raise ValueError(f"{condition_id} has invalid Test Condition status")
        if status == "blocked" and not condition.get("blocker"):
            raise ValueError(f"{condition_id} blocked condition missing blocker")

        if _contains_pixel_scope(condition):
            raise ValueError(f"{condition_id} contains pixel-level visual scope")

        if "BDD" in condition["techniques"]:
            if available_bdd_tc_refs is None or condition_id not in available_bdd_tc_refs:
                raise ValueError(f"{condition_id} selects BDD but has no BDD child artifact")


def validate_test_readiness(
    conditions: dict[str, Any],
    readiness_rows: list[dict[str, Any]],
) -> None:
    """Validate the one-row-per-required-TC readiness handoff."""

    required_ids = {
        condition["id"]
        for condition in conditions.get("conditions", [])
        if condition.get("status") == "required"
    }
    row_ids = [row.get("tc_id") for row in readiness_rows]
    if _duplicates(row_ids):
        raise ValueError("test readiness contains duplicate TC rows")
    if set(row_ids) != required_ids:
        missing = sorted(required_ids - set(row_ids))
        extra = sorted(set(row_ids) - required_ids)
        raise ValueError(f"test readiness TC mismatch missing={missing} extra={extra}")
    for row in readiness_rows:
        tc_id = row["tc_id"]
        status = row.get("status")
        if status not in {"READY", "BLOCKED"}:
            raise ValueError(f"{tc_id} has invalid Test Readiness status")
        if status == "READY" and not row.get("evidence"):
            raise ValueError(f"{tc_id} READY Test Readiness missing evidence")
        if status == "BLOCKED" and not row.get("blocker"):
            raise ValueError(f"{tc_id} BLOCKED Test Readiness missing blocker")
    if _contains_pixel_scope(readiness_rows):
        raise ValueError("test readiness contains pixel-level visual scope")
