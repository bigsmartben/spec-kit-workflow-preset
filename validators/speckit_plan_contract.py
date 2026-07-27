"""Pure in-memory semantic checks for representative Plan artifact bundles."""
from __future__ import annotations

from typing import Any, Iterable

from validators.speckit_test_contract import (
    validate_test_conditions,
    validate_test_readiness,
)


GATES = (
    "X0_CONTROL_READY",
    "X1_DECISIONS_READY",
    "X2A_DESIGN_READY",
    "X2B_UIUX_READY",
    "X2C_TEST_DESIGN_READY",
    "X2_RECONCILIATION_READY",
    "X3_VALIDATION_PATHS_READY",
)
INTERNAL_REF_PREFIXES = ("DEC-", "OBJ-", "IF-", "SEQ-", "UIF-", "TC-", "VAL-")
PLACEHOLDERS = ("[placeholder]", "<placeholder>", "TODO", "TBD")


def _duplicates(values: Iterable[str]) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return duplicates


def _strings(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for item in value.values():
            yield from _strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)
    elif isinstance(value, str):
        yield value


def _validate_artifact_decisions(artifacts: list[dict[str, Any]]) -> None:
    paths = [artifact.get("path") for artifact in artifacts]
    if any(not isinstance(path, str) or not path for path in paths):
        raise ValueError("every Plan artifact decision requires a path")
    if _duplicates(paths):
        raise ValueError("Plan artifact decisions contain duplicate paths")

    for artifact in artifacts:
        path = artifact["path"]
        decision = artifact.get("decision")
        if decision == "Required":
            if not artifact.get("owner") or not artifact.get("content"):
                raise ValueError(f"required artifact missing owner/content: {path}")
        elif decision == "N/A":
            if not artifact.get("reason"):
                raise ValueError(f"N/A artifact missing reason: {path}")
            if artifact.get("content"):
                raise ValueError(f"N/A artifact unexpectedly has content: {path}")
        elif decision == "Blocked":
            if not artifact.get("owner") or not artifact.get("blocker"):
                raise ValueError(f"blocked artifact missing owner/blocker: {path}")
        else:
            raise ValueError(f"artifact has invalid decision: {path}")


def _validate_technique_children(
    conditions: dict[str, Any],
    children: dict[str, list[str]],
) -> None:
    for condition in conditions["conditions"]:
        tc_id = condition["id"]
        techniques = {str(item).casefold() for item in condition["techniques"]}
        required_children: set[str] = set()
        if "bdd" in techniques:
            required_children.add("bdd")
        if techniques & {"scenario", "state_transition", "structured_scenario"}:
            required_children.add("scenario")
        if condition.get("fixture_refs"):
            required_children.add("fixture")
        if techniques & {"scenario", "state_transition", "structured_assertion"}:
            required_children.add("assertion")
        for child in required_children:
            if tc_id not in children.get(child, []):
                raise ValueError(f"{tc_id} missing technique-triggered {child} child")


def validate_plan_artifact_bundle(bundle: dict[str, Any]) -> None:
    """Validate Required/N/A decisions, refs, gates, and derived readiness."""

    lanes = bundle.get("lanes")
    if not isinstance(lanes, dict) or set(lanes) != {"X2-A", "X2-B", "X2-C"}:
        raise ValueError("Plan bundle must decide X2-A, X2-B, and X2-C")
    for lane, decision in lanes.items():
        status = decision.get("status")
        if status == "N/A" and not decision.get("reason"):
            raise ValueError(f"{lane} N/A missing reason")
        if status == "Blocked" and not decision.get("blocker"):
            raise ValueError(f"{lane} blocked missing blocker")
        if status not in {"Required", "N/A", "Blocked"}:
            raise ValueError(f"{lane} has invalid applicability")

    artifacts = bundle.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise ValueError("Plan bundle must include artifact decisions")
    _validate_artifact_decisions(artifacts)
    artifacts_by_path = {artifact["path"]: artifact for artifact in artifacts}
    for required_path in ("plan.md", "research.md"):
        if artifacts_by_path.get(required_path, {}).get("decision") != "Required":
            raise ValueError(f"Plan bundle missing required output: {required_path}")
    for contextual_path in ("class-diagram.md", "contracts/sequences.md"):
        if contextual_path not in artifacts_by_path:
            raise ValueError(
                f"Plan bundle missing contextual artifact decision: {contextual_path}"
            )
    if lanes["X2-A"]["status"] == "Required":
        if artifacts_by_path.get("data-model.md", {}).get("decision") != "Required":
            raise ValueError("active X2-A missing required data-model.md")
    x2b_status = lanes["X2-B"]["status"]
    uiux_decision = artifacts_by_path.get("ui-ux-design.md", {}).get("decision")
    if x2b_status == "Required":
        if artifacts_by_path.get("ui-ux-design.md", {}).get("decision") != "Required":
            raise ValueError("active X2-B missing required ui-ux-design.md")
        if not bundle.get("uif_contracts"):
            raise ValueError("active X2-B missing required UIF contract")
    elif x2b_status == "N/A":
        if uiux_decision != "N/A":
            raise ValueError("N/A X2-B must record ui-ux-design.md N/A")
    elif uiux_decision not in {"Required", "Blocked"}:
        raise ValueError(
            "blocked X2-B must preserve or block ui-ux-design.md, not mark it N/A"
        )

    x2c_status = lanes["X2-C"]["status"]
    x2c_paths = (
        "contracts/test/test-conditions.json",
        "quickstart.md",
        "test-readiness.md",
    )
    x2c_decisions = {
        path: artifacts_by_path.get(path, {}).get("decision") for path in x2c_paths
    }
    if x2c_status == "N/A":
        for path, decision in x2c_decisions.items():
            if decision != "N/A":
                raise ValueError(
                    f"N/A X2-C must record {path} as N/A"
                )
        if bundle.get("test_conditions") not in (None, {}):
            raise ValueError("N/A X2-C must not carry Test Conditions")
        if bundle.get("test_readiness_rows") not in (None, []):
            raise ValueError("N/A X2-C must not carry Test Readiness rows")
        if bundle.get("technique_children") not in (None, {}):
            raise ValueError("N/A X2-C must not carry technique children")
        if bundle.get("validation_paths") not in (None, []):
            raise ValueError("N/A X2-C must not carry VAL paths")
    else:
        allowed_decisions = (
            {"Required"} if x2c_status == "Required" else {"Required", "Blocked"}
        )
        for path, decision in x2c_decisions.items():
            if decision not in allowed_decisions:
                if x2c_status == "Required":
                    raise ValueError(f"active X2-C missing required output: {path}")
                raise ValueError(
                    f"Blocked X2-C must record {path} as Required/Blocked"
                )

    conditions_decision = x2c_decisions["contracts/test/test-conditions.json"]
    if conditions_decision == "Required":
        conditions = bundle.get("test_conditions")
        if not isinstance(conditions, dict):
            raise ValueError("required Test Conditions artifact missing content")
        bdd_refs = set(bundle.get("technique_children", {}).get("bdd", []))
        validate_test_conditions(
            conditions,
            available_bdd_tc_refs=bdd_refs or None,
        )
        _validate_technique_children(
            conditions,
            bundle.get("technique_children", {}),
        )
        condition_records = conditions["conditions"]
    else:
        if bundle.get("test_conditions") not in (None, {}):
            raise ValueError("non-required Test Conditions artifact must not carry content")
        if bundle.get("technique_children") not in (None, {}):
            raise ValueError(
                "non-required Test Conditions artifact must not carry technique children"
            )
        condition_records = []

    readiness_decision = x2c_decisions["test-readiness.md"]
    if readiness_decision == "Required":
        if conditions_decision != "Required":
            raise ValueError("required Test Readiness depends on required Test Conditions")
        readiness_rows = bundle.get("test_readiness_rows")
        if not isinstance(readiness_rows, list):
            raise ValueError("required Test Readiness missing structured rows")
        validate_test_readiness(conditions, readiness_rows)
    else:
        if bundle.get("test_readiness_rows") not in (None, []):
            raise ValueError("non-required Test Readiness must not carry rows")

    quickstart_decision = x2c_decisions["quickstart.md"]
    if quickstart_decision != "Required":
        if bundle.get("validation_paths") not in (None, []):
            raise ValueError("non-required quickstart must not carry VAL paths")

    declared_ids: list[str] = []
    declared_ids.extend(
        decision.get("id", "") for decision in bundle.get("decisions", [])
    )
    for artifact in artifacts:
        declared_ids.extend(artifact.get("declared_ids", []))
    declared_ids.extend(
        contract.get("id", "") for contract in bundle.get("uif_contracts", [])
    )
    for contract in bundle.get("uif_contracts", []):
        if not contract.get("source_refs") or not contract.get("requirement_refs"):
            raise ValueError(f"{contract.get('id', 'UIF')} missing source/UI mappings")
        if any(
            not str(ref).startswith("SRC-")
            for ref in contract["source_refs"]
        ):
            raise ValueError(f"{contract['id']} has invalid source mapping")
        if any(
            not str(ref).startswith(("UI-", "VIS-"))
            for ref in contract["requirement_refs"]
        ):
            raise ValueError(f"{contract['id']} has invalid UI/VIS mapping")
    declared_ids.extend(
        condition["id"] for condition in condition_records
    )
    declared_ids.extend(
        path.get("id", "") for path in bundle.get("validation_paths", [])
    )
    if any(not item for item in declared_ids) or _duplicates(declared_ids):
        raise ValueError("Plan bundle has missing or duplicate stable IDs")
    known_ids = set(declared_ids)

    consumed_refs: set[str] = set()
    for decision in bundle.get("decisions", []):
        consumed_refs.update(decision.get("affected_refs", []))
    for condition in condition_records:
        consumed_refs.update(condition.get("related_refs", []))
        if condition.get("quickstart_ref"):
            consumed_refs.add(condition["quickstart_ref"])
    for contract in bundle.get("uif_contracts", []):
        consumed_refs.update(contract.get("related_refs", []))
    for path in bundle.get("validation_paths", []):
        consumed_refs.update(path.get("covered_refs", []))

    unresolved = sorted(
        ref
        for ref in consumed_refs
        if ref.startswith(INTERNAL_REF_PREFIXES) and ref not in known_ids
    )
    if unresolved:
        raise ValueError(f"Plan bundle has unresolved internal refs: {unresolved}")

    reconciliation = bundle.get("reconciliation")
    if not isinstance(reconciliation, dict):
        raise ValueError("Plan bundle missing X2 reconciliation")
    if reconciliation.get("findings"):
        raise ValueError("Plan bundle reconciliation has unresolved findings")
    blocker_owners = reconciliation.get("blocker_owners")
    if not isinstance(blocker_owners, dict):
        raise ValueError("Plan bundle reconciliation missing blocker owners")
    for lane, decision in lanes.items():
        blocker = decision.get("blocker")
        if blocker and blocker_owners.get(blocker) != lane:
            raise ValueError(f"{blocker} has incorrect owning lane")
    for artifact in artifacts:
        blocker = artifact.get("blocker")
        if blocker and blocker_owners.get(blocker) != artifact.get("owner"):
            raise ValueError(f"{blocker} has incorrect artifact owner")
    for condition in condition_records:
        for blocker_field in ("blocker", "x3_blocker"):
            blocker = condition.get(blocker_field)
            if blocker and blocker not in blocker_owners:
                raise ValueError(
                    f"{condition['id']} {blocker_field} missing reconciliation owner"
                )
    for row in bundle.get("test_readiness_rows", []):
        blocker = row.get("blocker")
        if blocker and blocker not in blocker_owners:
            raise ValueError(
                f"{row['tc_id']} Test Readiness blocker missing reconciliation owner"
            )
    resolved_refs = set(reconciliation.get("resolved_refs", []))
    missing_reconciled = sorted(
        ref
        for ref in known_ids | consumed_refs
        if ref.startswith(INTERNAL_REF_PREFIXES) and ref not in resolved_refs
    )
    if missing_reconciled:
        raise ValueError(
            f"Plan bundle refs absent from reconciliation: {missing_reconciled}"
        )

    validation_ids = {
        path["id"] for path in bundle.get("validation_paths", [])
    }
    for condition in condition_records:
        quickstart_ref = condition.get("quickstart_ref")
        if quickstart_ref and quickstart_ref not in validation_ids:
            raise ValueError(f"{condition['id']} references missing VAL path")

    gates = bundle.get("gates")
    if not isinstance(gates, dict) or set(gates) != set(GATES):
        raise ValueError("Plan bundle must record every internal Gate")
    for gate, record in gates.items():
        status = record.get("status")
        evidence = record.get("evidence")
        if status not in {"READY", "N/A", "BLOCKED"}:
            raise ValueError(f"{gate} has invalid status")
        if not isinstance(evidence, list) or not evidence:
            raise ValueError(f"{gate} missing concrete evidence")
        if status == "BLOCKED" and not record.get("blockers"):
            raise ValueError(f"{gate} blocked without blocker evidence")
        for blocker in record.get("blockers", []):
            if blocker not in blocker_owners:
                raise ValueError(f"{gate} blocker missing reconciliation owner")
        if gate not in {
            "X2A_DESIGN_READY",
            "X2B_UIUX_READY",
            "X2C_TEST_DESIGN_READY",
            "X3_VALIDATION_PATHS_READY",
        } and status == "N/A":
            raise ValueError(f"{gate} cannot be N/A")
    for lane, gate in (
        ("X2-A", "X2A_DESIGN_READY"),
        ("X2-B", "X2B_UIUX_READY"),
        ("X2-C", "X2C_TEST_DESIGN_READY"),
    ):
        expected = {
            "Required": "READY",
            "N/A": "N/A",
            "Blocked": "BLOCKED",
        }[lanes[lane]["status"]]
        if gates[gate]["status"] != expected:
            raise ValueError(f"{gate} is inconsistent with {lane} applicability")
    x3_status = gates["X3_VALIDATION_PATHS_READY"]["status"]
    if x2c_status == "N/A" and x3_status != "N/A":
        raise ValueError("X3 must be N/A when X2-C is N/A")
    if x2c_status != "N/A" and x3_status == "N/A":
        raise ValueError("X3 cannot be N/A when X2-C is active or blocked")

    text = " ".join(_strings(bundle))
    normalized = text.casefold()
    if any(token.casefold() in normalized for token in PLACEHOLDERS):
        raise ValueError("Plan bundle contains unresolved placeholder")

    derived_ready = (
        all(record["status"] in {"READY", "N/A"} for record in gates.values())
        and not reconciliation.get("findings")
        and all(lane["status"] != "Blocked" for lane in lanes.values())
        and all(
            artifact["decision"] != "Blocked"
            for artifact in artifacts
        )
        and all(
            row.get("status") == "READY"
            for row in bundle.get("test_readiness_rows", [])
        )
        and all(
            condition.get("status") == "required"
            for condition in condition_records
        )
    )
    claimed_state = bundle.get("plan_output_ready")
    if claimed_state not in {"READY", "BLOCKED"}:
        raise ValueError("PLAN_OUTPUT_READY must be READY or BLOCKED")
    claimed_ready = claimed_state == "READY"
    if claimed_ready != derived_ready:
        raise ValueError("PLAN_OUTPUT_READY is inconsistent with Gate evidence")
