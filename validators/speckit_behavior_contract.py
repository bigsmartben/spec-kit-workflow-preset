"""Behavior contract validators for the workflow preset."""
from __future__ import annotations

from typing import Any

CASE_TYPES = {"positive", "negative", "boundary", "permission", "validation", "state_conflict"}

FAILURE_CASE_TYPES = {"negative", "permission", "validation", "state_conflict"}

def _duplicate_ids(items: list[dict[str, Any]], *, key: str, context: str) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for item in items:
        item_id = item.get(key)
        if item_id in seen:
            duplicates.add(item_id)
        seen.add(item_id)
    if duplicates:
        duplicate = sorted(duplicates)[0]
        raise ValueError(f"{context} duplicates {key}: {duplicate}")
    return seen

def _require_non_empty_list(item: dict[str, Any], *, key: str, context: str) -> None:
    values = item.get(key)
    item_id = item.get("id", "<unknown>")
    if not isinstance(values, list) or not values:
        raise ValueError(f"{context} {item_id} must include non-empty {key}")

def _validate_expected_uif_contract(uif_contract: dict[str, Any]) -> None:
    uif_id = uif_contract.get("id", "<unknown>")
    source_refs = uif_contract.get("source_refs")
    if not isinstance(source_refs, list) or not source_refs:
        raise ValueError(
            f"expected UIF contract {uif_id} must include non-empty source_refs"
        )
    if any(not str(ref).startswith("SRC-") for ref in source_refs):
        raise ValueError(
            f"expected UIF contract {uif_id} has invalid source_refs"
        )

    requirement_refs = uif_contract.get("requirement_refs")
    if not isinstance(requirement_refs, list) or not requirement_refs:
        raise ValueError(
            f"expected UIF contract {uif_id} must include non-empty requirement_refs"
        )
    if any(
        not str(ref).startswith(("UI-", "VIS-"))
        for ref in requirement_refs
    ):
        raise ValueError(
            f"expected UIF contract {uif_id} has non-UI/VIS requirement_refs"
        )

    steps = uif_contract.get("steps")
    if not isinstance(steps, list) or not steps:
        raise ValueError(f"expected UIF contract {uif_id} must include non-empty steps")

    for index, step in enumerate(steps):
        step_type = step.get("type")
        context = f"expected UIF contract {uif_id} step {index}"
        if step_type == "api_call":
            api = step.get("api")
            if not isinstance(api, dict) or not api.get("method") or not api.get("path"):
                raise ValueError(f"{context} api_call requires api.method and api.path")
        elif step_type == "local_route":
            if "to" not in step or step.get("to") in ("", None):
                raise ValueError(f"{context} local_route requires to")
        elif step_type == "user_event":
            if not step.get("id") and not step.get("label"):
                raise ValueError(f"{context} user_event requires id or label")

def _validate_non_positive_behavior_scenario(
    scenario: dict[str, Any],
    assertions_by_id: dict[str, dict[str, Any]],
) -> None:
    scenario_id = scenario.get("id", "<unknown>")
    scenario_type = scenario.get("type")
    if scenario_type == "positive":
        return

    request_case = scenario.get("request_case")
    if not isinstance(request_case, dict):
        raise ValueError(f"behavior scenario {scenario_id} must include request_case")
    case_kind = request_case.get("case_kind")
    if not case_kind:
        raise ValueError(f"behavior scenario {scenario_id} missing case_kind")
    if case_kind != scenario_type:
        raise ValueError(f"behavior scenario {scenario_id} case_kind must match type")
    outcome = request_case.get("outcome")
    if outcome not in {"success", "failure"}:
        raise ValueError(f"behavior scenario {scenario_id} missing outcome")
    if not request_case.get("trigger"):
        raise ValueError(f"behavior scenario {scenario_id} missing trigger")

    if scenario_type in FAILURE_CASE_TYPES and outcome != "failure":
        raise ValueError(f"behavior scenario {scenario_id} failure case must declare failure outcome")
    if outcome != "failure":
        return

    expected_response = scenario.get("expected_response")
    if not isinstance(expected_response, dict) or not expected_response:
        raise ValueError(f"behavior scenario {scenario_id} missing expected_response")
    if not expected_response.get("error_code"):
        raise ValueError(f"behavior scenario {scenario_id} missing error_code")

    expected_feedback = scenario.get("expected_feedback")
    if expected_feedback is not None:
        if not isinstance(expected_feedback, dict) or not expected_feedback:
            raise ValueError(f"behavior scenario {scenario_id} has invalid expected_feedback")
        if not expected_feedback.get("type"):
            raise ValueError(f"behavior scenario {scenario_id} missing feedback_type")
        if not expected_feedback.get("message"):
            raise ValueError(f"behavior scenario {scenario_id} missing feedback_message")

    invariant_intents = {"state_invariant", "rollback", "compensation"}
    if not any(
        assertions_by_id.get(assertion_id, {}).get("intent") in invariant_intents
        for assertion_id in scenario.get("assertion_ids", [])
    ):
        raise ValueError(
            f"behavior scenario {scenario_id} missing state_invariant_rollback_or_compensation_assertion"
        )

def _case_coverage_blockers_by_id(scenario_instances: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        blocker["id"]: blocker
        for blocker in scenario_instances.get("case_coverage_blockers", [])
        if "id" in blocker
    }

def validate_behavior_case_coverage(
    case_coverage: dict[str, Any],
    scenarios_draft: dict[str, Any],
    scenario_instances: dict[str, Any],
    tasks_text: str,
    quickstart_text: str,
) -> None:
    draft_by_id = {
        scenario.get("id"): scenario
        for scenario in scenarios_draft.get("scenarios", [])
        if "id" in scenario
    }
    formal_by_id = {
        scenario.get("id"): scenario
        for scenario in scenario_instances.get("scenarios", [])
        if "id" in scenario
    }
    blockers_by_id = _case_coverage_blockers_by_id(scenario_instances)

    coverage_rows = case_coverage.get("case_coverage")
    if not isinstance(coverage_rows, list) or not coverage_rows:
        raise ValueError("case_coverage must include a non-empty case_coverage matrix")

    for row in coverage_rows:
        story = row.get("story", "<unknown>")
        case_type = row.get("case_type")
        status = row.get("status")
        context = f"{story} {case_type}"

        if case_type not in CASE_TYPES:
            raise ValueError(f"case coverage row {context} has unknown case_type")
        if status not in {"Required", "Not Applicable", "Unknown"}:
            raise ValueError(f"case coverage row {context} has unknown status")

        if status == "Not Applicable":
            if not row.get("rationale"):
                raise ValueError(f"Not Applicable case {context} missing rationale")
            continue

        if status == "Unknown":
            if not row.get("blocker_id"):
                raise ValueError(f"Unknown case {context} missing Blocking Items reference")
            continue

        if status != "Required":
            continue

        if not row.get("source"):
            raise ValueError(f"Required case {context} missing source")

        scenario_id = row.get("scenario_id")
        blocker_id = row.get("blocker_id")
        if bool(scenario_id) == bool(blocker_id):
            raise ValueError(
                f"Required case {context} must name exactly one scenario_id or blocker_id"
            )

        if blocker_id:
            blocker = blockers_by_id.get(blocker_id)
            if blocker is None:
                raise ValueError(f"Required case {context} references unknown blocker")
            if blocker.get("case_id") != row.get("case_id"):
                raise ValueError(f"Required case {context} blocker case_id mismatch")
            if blocker.get("case_type") != case_type:
                raise ValueError(f"Required case {context} blocker case_type mismatch")
            if blocker.get("source") != row.get("source"):
                raise ValueError(f"Required case {context} blocker source mismatch")
            if blocker_id not in tasks_text:
                raise ValueError(f"Required case {context} missing tasks.md blocker evidence")
            if blocker_id not in quickstart_text:
                raise ValueError(f"Required case {context} missing quickstart.md blocker evidence")
            continue

        draft = draft_by_id.get(scenario_id)
        formal = formal_by_id.get(scenario_id)
        if draft is None or formal is None:
            raise ValueError(f"Required case {context} missing draft or formal scenario")
        if draft.get("type") != case_type or formal.get("type") != case_type:
            raise ValueError(f"Required case {context} scenario type mismatch")
        if scenario_id not in tasks_text:
            raise ValueError(f"Required case {context} missing tasks.md evidence")
        if scenario_id not in quickstart_text:
            raise ValueError(f"Required case {context} missing quickstart.md evidence")

def validate_behavior_draft_contract(
    scenarios_draft: dict[str, Any],
    data_fixtures_intent: dict[str, Any],
) -> None:
    scenarios = scenarios_draft.get("scenarios", [])
    if not scenarios:
        raise ValueError("behavior draft scenarios must include at least one scenario")

    scenario_ids = _duplicate_ids(
        scenarios,
        key="id",
        context="behavior draft scenarios",
    )
    for scenario in scenarios:
        for key in ("given", "when", "then"):
            _require_non_empty_list(
                scenario,
                key=key,
                context="behavior draft scenario",
            )

    _duplicate_ids(
        data_fixtures_intent.get("fixtures", []),
        key="id",
        context="behavior data fixture intents",
    )

    for fixture in data_fixtures_intent.get("fixtures", []):
        for scenario_id in fixture.get("required_for", []):
            if scenario_id not in scenario_ids:
                raise ValueError(f"fixture required_for references unknown scenario: {scenario_id}")

def validate_behavior_contract_bundle(
    scenario_instances: dict[str, Any],
    data_fixtures: dict[str, Any],
    assertions: dict[str, Any],
    uif_expected_contracts: list[dict[str, Any]],
    test_condition_ids: set[str] | None = None,
) -> None:
    scenarios = scenario_instances.get("scenarios", [])
    if not scenarios:
        raise ValueError("behavior scenario instances must include at least one scenario")

    scenario_ids = _duplicate_ids(
        scenarios,
        key="id",
        context="behavior scenario instances",
    )
    fixture_ids = _duplicate_ids(
        data_fixtures.get("fixtures", []),
        key="id",
        context="behavior data fixtures",
    )
    assertion_ids = _duplicate_ids(
        assertions.get("assertions", []),
        key="id",
        context="behavior assertions",
    )
    assertions_by_id = {
        assertion["id"]: assertion
        for assertion in assertions.get("assertions", [])
        if "id" in assertion
    }
    uif_path_ids = _duplicate_ids(
        uif_expected_contracts,
        key="id",
        context="expected UIF contracts",
    )
    for uif_contract in uif_expected_contracts:
        _validate_expected_uif_contract(uif_contract)

    for scenario in scenarios:
        _require_non_empty_list(
            scenario,
            key="assertion_ids",
            context="behavior scenario instance",
        )
        _require_non_empty_list(
            scenario,
            key="test_condition_refs",
            context="behavior scenario instance",
        )

        has_fixture_refs = bool(scenario.get("fixture_ids"))
        has_no_fixture_rationale = bool(scenario.get("no_fixture_rationale"))
        if has_fixture_refs == has_no_fixture_rationale:
            raise ValueError(
                "scenario must declare exactly one fixture_ids or no_fixture_rationale"
            )

        uif_path_id = scenario.get("uif_path_id")
        has_non_ui_rationale = bool(scenario.get("non_ui_rationale"))
        if bool(uif_path_id) == has_non_ui_rationale:
            raise ValueError(
                "scenario must declare exactly one uif_path_id or non_ui_rationale"
            )
        if uif_path_id and uif_path_id not in uif_path_ids:
            raise ValueError(f"scenario references unknown uif_path_id: {uif_path_id}")

        for fixture_id in scenario.get("fixture_ids", []):
            if fixture_id not in fixture_ids:
                raise ValueError(f"scenario references unknown fixture: {fixture_id}")

        for assertion_id in scenario.get("assertion_ids", []):
            if assertion_id not in assertion_ids:
                raise ValueError(f"scenario references unknown assertion: {assertion_id}")

        if test_condition_ids is not None:
            for tc_id in scenario.get("test_condition_refs", []):
                if tc_id not in test_condition_ids:
                    raise ValueError(
                        f"scenario references unknown test condition: {tc_id}"
                    )

        _validate_non_positive_behavior_scenario(scenario, assertions_by_id)

    if len(scenario_ids) != len(scenario_instances.get("scenarios", [])):
        raise ValueError("behavior scenario instances contain duplicate ids")
