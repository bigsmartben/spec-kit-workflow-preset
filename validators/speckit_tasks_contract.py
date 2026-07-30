"""Pure in-memory validation for Plan X2-B to Tasks derivation."""
from __future__ import annotations

import re
from typing import Any, Iterable


MAPPING_DIMENSIONS = {
    "UI": {
        "component",
        "state",
        "interaction",
        "navigation",
        "responsive",
        "accessibility",
    },
    "PX": {
        "geometry",
        "sizing",
        "spacing",
        "alignment",
        "flow",
        "overflow",
        "clipping",
        "typography",
        "text-metrics",
        "color",
        "gradient",
        "border",
        "radius",
        "shadow",
        "opacity",
        "effects",
        "asset-preparation",
        "asset-binding",
        "asset-crop",
        "asset-aspect",
        "asset-fitting",
        "layering",
        "stacking",
        "fixed-sticky",
        "occlusion",
    },
    "ADP": {
        "target-component",
        "navigation",
        "presentation",
        "input-modality",
        "gestures",
        "system-ui",
        "safe-regions",
        "adaptive-layout",
        "accessibility-scaling",
        "localization",
        "layout-direction",
    },
}
FINAL_REVIEW_SCOPES = {
    "UI": "component-state-interaction",
    "PX": "geometry-typography-appearance-asset-layering-overflow-clipping",
    "ADP": (
        "platform-navigation-input-system-safe-region-adaptive-"
        "accessibility-localization"
    ),
}
SPEC_OWNED_FIELDS = {
    "statement",
    "requirement_statement",
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
}
FORBIDDEN_VISUAL_EXECUTION_TERMS = {
    "visual_acceptance",
    "pixel_fidelity_review",
    "screenshot capture",
    "screenshot comparison",
    "screenshot diff",
    "screenshot-based evidence",
    "baseline production",
    "baseline capture",
    "pixel comparison",
    "pixel/perceptual comparison",
    "perceptual comparison",
    "visual diff",
    "visual acceptance",
    "visual restoration",
    "rendered fidelity",
    "rendered-fidelity",
    "final rendered visual review",
    "fidelity mode evaluation",
    "fidelity-mode evaluation",
    "acceptance envelope evaluation",
    "acceptance-envelope evaluation",
    "threshold evaluation",
    "source dereference",
    "external source acquisition",
    "external source certification",
}
SPEC_SEMANTIC_VALUE_TERMS = {
    "pixel-exact",
    "pixel-tolerant",
    "perceptual-equivalent",
    "structural-only",
    "acceptance envelope",
    "exception bound",
    "adaptation decision",
}
VISUAL_EXECUTION_PATTERNS = {
    "capture screenshot": (
        r"\b(?:capture|captures|captured|capturing|take|takes|took|taking|"
        r"generate|generates|generated|generating|produce|produces|produced|"
        r"producing)\b.{0,24}\bscreenshots?\b"
    ),
    "screenshot execution": (
        r"\bscreenshots?\b.{0,24}\b(?:capture|comparison|compare|diff|"
        r"production|produce)\b"
    ),
    "compare pixels": (
        r"\b(?:compare|compares|compared|comparing)\b.{0,24}\bpixels?\b"
    ),
    "pixel comparison": (
        r"\bpixels?\b.{0,24}\b(?:compare|compares|compared|comparing|"
        r"comparison)\b"
    ),
    "baseline production": (
        r"\b(?:generate|generates|generated|generating|produce|produces|"
        r"produced|producing|create|creates|created|creating|render|renders|"
        r"rendered|rendering)\b.{0,24}\b(?:a |the )?baseline\b"
    ),
    "acceptance threshold evaluation": (
        r"\b(?:evaluate|evaluates|evaluated|evaluating|check|checks|checked|"
        r"checking|judge|judges|judged|judging)\b.{0,32}\b(?:acceptance )?"
        r"thresholds?\b"
    ),
}
TASK_ACTION_CLASSES = {
    "implementation",
    "functional-validation",
    "visual-execution",
}
FINAL_REVIEW_ACTION_CLASS = "code-design-contract-review"
TRACEABILITY_PREFIXES = ("UI-", "VIS-", "PXT-", "PEX-", "ADP-")


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
        for child in value.values():
            yield from _strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _strings(child)
    elif isinstance(value, str):
        yield value


def _normalized_text(value: Any) -> str:
    text = " ".join(_strings(value)).casefold()
    text = re.sub(r"[_/\\-]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _visual_execution_leaks(value: Any) -> set[str]:
    normalized = _normalized_text(value)
    leaks = {
        term
        for term in FORBIDDEN_VISUAL_EXECUTION_TERMS
        if _normalized_text(term) in normalized
    }
    leaks.update(
        label
        for label, pattern in VISUAL_EXECUTION_PATTERNS.items()
        if re.search(pattern, normalized)
    )
    return leaks


def _spec_semantic_value_leaks(value: Any) -> set[str]:
    normalized = _normalized_text(value)
    return {
        term
        for term in SPEC_SEMANTIC_VALUE_TERMS
        if _normalized_text(term) in normalized
    }


def _ownership_leaks(value: Any) -> set[str]:
    if isinstance(value, dict):
        leaks = set(value) & SPEC_OWNED_FIELDS
        for child in value.values():
            leaks.update(_ownership_leaks(child))
        return leaks
    if isinstance(value, list):
        leaks: set[str] = set()
        for child in value:
            leaks.update(_ownership_leaks(child))
        return leaks
    return set()


def _fail(code: str, detail: str) -> None:
    raise ValueError(f"{code}: {detail}")


def _require_list(
    item: dict[str, Any],
    field: str,
    context: str,
    *,
    allow_empty: bool = False,
    error_code: str = "TASK_X2B_MAPPING_UNMAPPED",
) -> list[Any]:
    value = item.get(field)
    if not isinstance(value, list) or (not value and not allow_empty):
        _fail(
            error_code,
            f"{context} missing {'list' if allow_empty else 'non-empty list'} {field}",
        )
    return value


def _mapping_class(mapping_ref: str) -> str | None:
    for mapping_class in ("UI", "PX", "ADP"):
        if mapping_ref.startswith(f"X2B-{mapping_class}-"):
            return mapping_class
    return None


def _depends_on(
    task_id: str,
    prerequisite_id: str,
    dependency_graph: dict[str, set[str]],
) -> bool:
    pending = list(dependency_graph[task_id])
    visited: set[str] = set()
    while pending:
        current = pending.pop()
        if current == prerequisite_id:
            return True
        if current in visited:
            continue
        visited.add(current)
        pending.extend(dependency_graph[current])
    return False


def _validate_acyclic_dependencies(
    dependency_graph: dict[str, set[str]],
) -> None:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(task_id: str) -> None:
        if task_id in visiting:
            _fail(
                "TASK_X2B_MAPPING_UNMAPPED",
                f"task dependency cycle reaches {task_id}",
            )
        if task_id in visited:
            return
        visiting.add(task_id)
        for dependency_id in dependency_graph[task_id]:
            visit(dependency_id)
        visiting.remove(task_id)
        visited.add(task_id)

    for task_id in dependency_graph:
        visit(task_id)


def _validate_preflight(bundle: dict[str, Any]) -> None:
    if bundle.get("plan_output_ready") != "READY":
        _fail("PLAN_OUTPUT_INCOMPLETE", "PLAN_OUTPUT_READY is not READY")
    current_revision = bundle.get("current_plan_revision")
    handoff_revision = bundle.get("tasks_handoff_revision")
    if (
        not isinstance(current_revision, str)
        or not current_revision
        or handoff_revision != current_revision
    ):
        _fail(
            "PLAN_OUTPUT_INCOMPLETE",
            "Tasks handoff revision is missing or stale",
        )
    if bundle.get("uiux_delivery_readiness") not in {"READY", "N/A"}:
        _fail(
            "PLAN_OUTPUT_INCOMPLETE",
            "UI/UX Delivery Readiness is not closed",
        )


def validate_tasks_x2b_derivation(bundle: dict[str, Any]) -> None:
    """Validate X2-B mapping coverage without executing or persisting tasks."""

    _validate_preflight(bundle)
    mappings = bundle.get("x2b_mappings")
    tasks = bundle.get("tasks")
    test_tasks = bundle.get("test_tasks")
    phases = bundle.get("phases")
    if not isinstance(mappings, list) or not isinstance(tasks, list):
        _fail(
            "PLAN_OUTPUT_INCOMPLETE",
            "Tasks derivation requires X2-B inventory and task candidates",
        )
    if not isinstance(test_tasks, list) or not isinstance(phases, list):
        _fail(
            "PLAN_OUTPUT_INCOMPLETE",
            "Tasks derivation requires test-task and phase inventories",
        )
    if bundle.get("uiux_delivery_readiness") == "N/A" and (mappings or tasks):
        _fail(
            "TASK_X2B_REF_UNKNOWN",
            "non-UI handoff cannot contain X2-B mappings or X2-B tasks",
        )

    mapping_ids = [str(mapping.get("id", "")) for mapping in mappings]
    if any(_mapping_class(mapping_id) is None for mapping_id in mapping_ids):
        _fail("TASK_X2B_REF_UNKNOWN", "unknown X2B mapping id class")
    duplicate_mappings = _duplicates(mapping_ids)
    if duplicate_mappings:
        _fail(
            "TASK_X2B_MAPPING_DUPLICATE",
            f"duplicate mapping {sorted(duplicate_mappings)[0]}",
        )
    mappings_by_id = dict(zip(mapping_ids, mappings))
    declared_traceability_refs = set(
        map(str, bundle.get("declared_traceability_refs", []))
    )

    blocked_mapping_ids: set[str] = set()
    implementation_mapping_ids: set[str] = set()
    review_only_mapping_ids: set[str] = set()
    for mapping_id, mapping in mappings_by_id.items():
        mapping_class = str(_mapping_class(mapping_id))
        status = mapping.get("status")
        dimensions = set(
            map(
                str,
                _require_list(
                    mapping,
                    "implementation_dimensions",
                    mapping_id,
                    allow_empty=True,
                ),
            )
        )
        invalid_dimensions = dimensions - MAPPING_DIMENSIONS[mapping_class]
        if invalid_dimensions:
            code = (
                "TASK_X2B_ADAPTATION_UNCOVERED"
                if mapping_class == "ADP"
                else "TASK_X2B_IMPLEMENTATION_DIMENSION_UNCOVERED"
            )
            _fail(
                code,
                f"{mapping_id} has invalid dimension {sorted(invalid_dimensions)[0]}",
            )
        dependencies = list(
            map(
                str,
                _require_list(
                    mapping,
                    "depends_on",
                    mapping_id,
                    allow_empty=True,
                ),
            )
        )
        if mapping_id in dependencies:
            _fail("TASK_X2B_REF_UNKNOWN", f"{mapping_id} depends on itself")
        traceability_refs = mapping.get("traceability_refs")
        if not isinstance(traceability_refs, list):
            _fail(
                "TASK_X2B_REF_UNKNOWN",
                f"{mapping_id} traceability_refs must be a list",
            )
        if status == "Required" and not traceability_refs:
            _fail(
                "TASK_X2B_REF_UNKNOWN",
                f"{mapping_id} is orphaned from upstream Plan refs",
            )
        if any(
            not str(ref).startswith(TRACEABILITY_PREFIXES)
            or str(ref) not in declared_traceability_refs
            for ref in traceability_refs
        ):
            _fail(
                "TASK_X2B_REF_UNKNOWN",
                f"{mapping_id} has unknown traceability ref",
            )

        if status == "Required":
            if mapping.get("review_method_only") is True:
                if dimensions or not mapping.get("no_task_rationale"):
                    _fail(
                        "TASK_X2B_MAPPING_UNMAPPED",
                        f"{mapping_id} invalid review-method-only rationale",
                    )
                review_only_mapping_ids.add(mapping_id)
            else:
                if not dimensions:
                    _fail(
                        "TASK_X2B_IMPLEMENTATION_DIMENSION_UNCOVERED",
                        f"{mapping_id} has no implementation dimensions",
                    )
                implementation_mapping_ids.add(mapping_id)
        elif status == "Blocked":
            if not mapping.get("blocker"):
                _fail(
                    "TASK_X2B_BLOCKER_SUPPRESSED",
                    f"{mapping_id} blocked without stable blocker",
                )
            blocked_mapping_ids.add(mapping_id)
        elif status == "N/A":
            if not mapping.get("reason"):
                _fail("TASK_X2B_MAPPING_UNMAPPED", f"{mapping_id} N/A lacks reason")
        else:
            _fail("TASK_X2B_REF_UNKNOWN", f"{mapping_id} has invalid handoff status")

    for mapping_id, mapping in mappings_by_id.items():
        unknown_dependencies = set(map(str, mapping.get("depends_on", []))) - set(
            mappings_by_id
        )
        if unknown_dependencies:
            _fail(
                "TASK_X2B_REF_UNKNOWN",
                f"{mapping_id} depends on unknown {sorted(unknown_dependencies)[0]}",
            )

    task_ids = [str(task.get("id", "")) for task in tasks]
    if any(not task_id.startswith("T") for task_id in task_ids):
        _fail("TASK_X2B_REF_UNKNOWN", "implementation task ids must use T*")
    duplicate_tasks = _duplicates(task_ids)
    if duplicate_tasks:
        _fail(
            "TASK_X2B_MAPPING_DUPLICATE",
            f"duplicate task id {sorted(duplicate_tasks)[0]}",
        )
    tasks_by_id = dict(zip(task_ids, tasks))
    task_ids_by_mapping: dict[str, set[str]] = {
        mapping_id: set() for mapping_id in mappings_by_id
    }
    dimensions_by_mapping: dict[str, set[str]] = {
        mapping_id: set() for mapping_id in mappings_by_id
    }
    mapping_path_dimensions: set[tuple[str, str, str]] = set()

    for task_id, task in tasks_by_id.items():
        if task.get("kind") != "implementation":
            _fail(
                "TASK_X2B_REF_UNKNOWN",
                f"{task_id} is not an implementation task candidate",
            )
        action_classes = set(
            map(
                str,
                _require_list(task, "action_classes", task_id),
            )
        )
        if "visual-execution" in action_classes:
            _fail(
                "TASK_VISUAL_EXECUTION_LEAK",
                f"{task_id} declares forbidden visual-execution",
            )
        if (
            not action_classes.issubset(TASK_ACTION_CLASSES)
            or action_classes != {"implementation"}
        ):
            _fail(
                "TASK_X2B_REF_UNKNOWN",
                f"{task_id} has invalid X2-B action classes",
            )
        paths = list(map(str, _require_list(task, "paths", task_id)))
        if any(not path or path.endswith(("/", "\\")) for path in paths):
            _fail(
                "TASK_X2B_MAPPING_UNMAPPED",
                f"{task_id} lacks a concrete file/configuration/asset path",
            )
        mapping_refs = list(
            map(str, _require_list(task, "mapping_refs", task_id))
        )
        unknown_mapping_refs = set(mapping_refs) - set(mappings_by_id)
        if unknown_mapping_refs:
            _fail(
                "TASK_X2B_REF_UNKNOWN",
                f"{task_id} references unknown {sorted(unknown_mapping_refs)[0]}",
            )
        blocked_refs = set(mapping_refs) & blocked_mapping_ids
        if blocked_refs:
            _fail(
                "TASK_X2B_BLOCKER_SUPPRESSED",
                f"{task_id} implements blocked {sorted(blocked_refs)[0]}",
            )
        review_only_refs = set(mapping_refs) & review_only_mapping_ids
        if review_only_refs:
            _fail(
                "TASK_X2B_MAPPING_UNMAPPED",
                f"{task_id} executes review-method-only {sorted(review_only_refs)[0]}",
            )
        task_dimensions = set(
            map(str, _require_list(task, "implementation_dimensions", task_id))
        )
        for mapping_ref in mapping_refs:
            mapping_class = str(_mapping_class(mapping_ref))
            invalid_for_mapping = task_dimensions - MAPPING_DIMENSIONS[mapping_class]
            if invalid_for_mapping:
                code = (
                    "TASK_X2B_ADAPTATION_UNCOVERED"
                    if mapping_class == "ADP"
                    else "TASK_X2B_IMPLEMENTATION_DIMENSION_UNCOVERED"
                )
                _fail(
                    code,
                    f"{task_id} has invalid dimension for {mapping_ref}",
                )
            extra_dimensions = task_dimensions - set(
                map(
                    str,
                    mappings_by_id[mapping_ref]["implementation_dimensions"],
                )
            )
            if extra_dimensions:
                code = (
                    "TASK_X2B_ADAPTATION_UNCOVERED"
                    if mapping_class == "ADP"
                    else "TASK_X2B_IMPLEMENTATION_DIMENSION_UNCOVERED"
                )
                _fail(
                    code,
                    f"{task_id} invents dimension for {mapping_ref}",
                )
            task_ids_by_mapping[mapping_ref].add(task_id)
            dimensions_by_mapping[mapping_ref].update(task_dimensions)
            for path in paths:
                for dimension in task_dimensions:
                    key = (mapping_ref, path, dimension)
                    if key in mapping_path_dimensions:
                        _fail(
                            "TASK_X2B_MAPPING_DUPLICATE",
                            f"duplicate task coverage for {mapping_ref}/{path}/{dimension}",
                        )
                    mapping_path_dimensions.add(key)

        traceability_refs = task.get("traceability_refs", [])
        if not isinstance(traceability_refs, list):
            _fail("TASK_X2B_REF_UNKNOWN", f"{task_id} traceability_refs must be a list")
        if any(
            not str(ref).startswith(TRACEABILITY_PREFIXES)
            or str(ref) not in declared_traceability_refs
            for ref in traceability_refs
        ):
            _fail("TASK_X2B_REF_UNKNOWN", f"{task_id} has unknown traceability ref")
        mapped_traceability_refs = {
            str(ref)
            for mapping_ref in mapping_refs
            for ref in mappings_by_id[mapping_ref].get("traceability_refs", [])
        }
        if not set(map(str, traceability_refs)).issubset(mapped_traceability_refs):
            _fail(
                "TASK_X2B_REF_UNKNOWN",
                f"{task_id} reinterprets traceability outside its mapping",
            )

        task_dependencies = task.get("depends_on")
        if not isinstance(task_dependencies, list):
            _fail("TASK_X2B_REF_UNKNOWN", f"{task_id} depends_on must be a list")
        if task_id in task_dependencies:
            _fail("TASK_X2B_REF_UNKNOWN", f"{task_id} depends on itself")
        parallel = task.get("parallel")
        if not isinstance(parallel, bool):
            _fail(
                "TASK_X2B_REF_UNKNOWN",
                f"{task_id} parallel marker must be boolean",
            )
        if parallel and task_dependencies:
            _fail(
                "TASK_X2B_MAPPING_UNMAPPED",
                f"{task_id} cannot be parallel while dependencies remain",
            )

        ownership_leaks = sorted(_ownership_leaks(task))
        if ownership_leaks:
            _fail(
                "TASK_SPEC_OWNERSHIP_LEAK",
                f"{task_id} copies Spec-owned {ownership_leaks[0]}",
            )
        semantic_leaks = sorted(_spec_semantic_value_leaks(task))
        if semantic_leaks:
            _fail(
                "TASK_SPEC_OWNERSHIP_LEAK",
                f"{task_id} reinterprets Spec-owned {semantic_leaks[0]}",
            )
        visual_leaks = sorted(_visual_execution_leaks(task))
        if visual_leaks:
            _fail(
                "TASK_VISUAL_EXECUTION_LEAK",
                f"{task_id} contains forbidden {visual_leaks[0]}",
            )

    for task_id, task in tasks_by_id.items():
        unknown_dependencies = set(map(str, task.get("depends_on", []))) - set(
            tasks_by_id
        )
        if unknown_dependencies:
            _fail(
                "TASK_X2B_REF_UNKNOWN",
                f"{task_id} depends on unknown task {sorted(unknown_dependencies)[0]}",
            )
    dependency_graph = {
        task_id: set(map(str, task.get("depends_on", [])))
        for task_id, task in tasks_by_id.items()
    }
    _validate_acyclic_dependencies(dependency_graph)

    for mapping_id in implementation_mapping_ids:
        mapping = mappings_by_id[mapping_id]
        if not task_ids_by_mapping[mapping_id]:
            _fail(
                "TASK_X2B_MAPPING_UNMAPPED",
                f"{mapping_id} has no concrete implementation task",
            )
        missing_dimensions = set(map(str, mapping["implementation_dimensions"])) - (
            dimensions_by_mapping[mapping_id]
        )
        if missing_dimensions:
            code = (
                "TASK_X2B_ADAPTATION_UNCOVERED"
                if _mapping_class(mapping_id) == "ADP"
                else "TASK_X2B_IMPLEMENTATION_DIMENSION_UNCOVERED"
            )
            _fail(
                code,
                f"{mapping_id} lacks task coverage for {sorted(missing_dimensions)[0]}",
            )

        for dependency_ref in map(str, mapping.get("depends_on", [])):
            dependency_tasks = task_ids_by_mapping[dependency_ref]
            if not dependency_tasks:
                continue
            for task_id in task_ids_by_mapping[mapping_id]:
                if task_id in dependency_tasks:
                    continue
                if not any(
                    _depends_on(task_id, dependency_task, dependency_graph)
                    for dependency_task in dependency_tasks
                ):
                    _fail(
                        "TASK_X2B_MAPPING_UNMAPPED",
                        f"{task_id} omits dependency from {dependency_ref}",
                    )

    task_items = list(tasks_by_id.items())
    for index, (left_id, left) in enumerate(task_items):
        left_paths = set(map(str, left.get("paths", [])))
        for right_id, right in task_items[index + 1 :]:
            if not left_paths.intersection(set(map(str, right.get("paths", [])))):
                continue
            if not _depends_on(
                left_id,
                right_id,
                dependency_graph,
            ) and not _depends_on(
                right_id,
                left_id,
                dependency_graph,
            ):
                _fail(
                    "TASK_X2B_MAPPING_UNMAPPED",
                    f"{left_id} and {right_id} share a path without dependency",
                )

    for mapping_id in implementation_mapping_ids:
        mapping_task_ids = task_ids_by_mapping[mapping_id]
        preparation_tasks = {
            task_id
            for task_id in mapping_task_ids
            if "asset-preparation"
            in set(map(str, tasks_by_id[task_id]["implementation_dimensions"]))
        }
        binding_tasks = {
            task_id
            for task_id in mapping_task_ids
            if "asset-binding"
            in set(map(str, tasks_by_id[task_id]["implementation_dimensions"]))
        }
        for binding_task in binding_tasks - preparation_tasks:
            if preparation_tasks and not any(
                _depends_on(binding_task, task_id, dependency_graph)
                for task_id in preparation_tasks
            ):
                _fail(
                    "TASK_X2B_MAPPING_UNMAPPED",
                    f"{binding_task} must depend on asset preparation",
                )

    required_tc_refs = set(
        map(str, bundle.get("required_test_readiness_tc_refs", []))
    )
    covered_tc_refs: set[str] = set()
    for test_task in test_tasks:
        action_classes = set(
            map(
                str,
                _require_list(
                    test_task,
                    "action_classes",
                    "functional UI test task",
                    error_code="TASK_SPEC_OWNERSHIP_LEAK",
                ),
            )
        )
        if "visual-execution" in action_classes:
            _fail(
                "TASK_VISUAL_EXECUTION_LEAK",
                "functional UI test task declares visual-execution",
            )
        if action_classes != {"functional-validation"}:
            _fail(
                "TASK_SPEC_OWNERSHIP_LEAK",
                "functional UI test task has invalid action classes",
            )
        tc_refs = test_task.get("tc_refs")
        if not isinstance(tc_refs, list) or not tc_refs:
            _fail(
                "TASK_SPEC_OWNERSHIP_LEAK",
                "functional UI test task lacks Required Test Readiness TC ref",
            )
        unknown_tc_refs = set(map(str, tc_refs)) - required_tc_refs
        if unknown_tc_refs:
            _fail(
                "TASK_SPEC_OWNERSHIP_LEAK",
                f"test task invents {sorted(unknown_tc_refs)[0]} from visual mapping",
            )
        covered_tc_refs.update(map(str, tc_refs))
    if covered_tc_refs != required_tc_refs:
        _fail(
            "TASK_X2B_REF_UNKNOWN",
            "Required Test Readiness TC refs do not match generated test tasks",
        )

    final_review = bundle.get("final_review")
    if not isinstance(final_review, dict):
        _fail("TASK_FINAL_REVIEW_MAPPING_MISSING", "Final Code Review is absent")
    if not phases or phases[-1] != "Final Code Review":
        _fail(
            "TASK_FINAL_REVIEW_MAPPING_MISSING",
            "Final Code Review is not the last mandatory phase",
        )
    if (
        final_review.get("phase") != "Final Code Review"
        or final_review.get("kind") != "code-design-contract-review"
    ):
        _fail(
            "TASK_FINAL_REVIEW_MAPPING_MISSING",
            "Final Code Review has an invalid review contract",
        )
    review_action_classes = set(
        map(
            str,
            _require_list(
                final_review,
                "action_classes",
                "Final Code Review",
                error_code="TASK_FINAL_REVIEW_MAPPING_MISSING",
            ),
        )
    )
    if review_action_classes != {FINAL_REVIEW_ACTION_CLASS}:
        _fail(
            "TASK_FINAL_REVIEW_MAPPING_MISSING",
            "Final Code Review has an invalid action class",
        )
    review_mapping_refs = set(
        map(
            str,
            _require_list(
                final_review,
                "mapping_refs",
                "Final Code Review",
                allow_empty=True,
                error_code="TASK_FINAL_REVIEW_MAPPING_MISSING",
            ),
        )
    )
    if review_mapping_refs != implementation_mapping_ids:
        _fail(
            "TASK_FINAL_REVIEW_MAPPING_MISSING",
            "Final Code Review does not cover every implementation mapping",
        )
    review_scopes = set(
        map(
            str,
            _require_list(
                final_review,
                "scopes",
                "Final Code Review",
                error_code="TASK_FINAL_REVIEW_MAPPING_MISSING",
            ),
        )
    )
    required_review_scopes = {"implementation-conformance"}
    if mappings:
        required_review_scopes.add("x2b-blockers-and-plan-drift")
    required_review_scopes.update(
        FINAL_REVIEW_SCOPES[str(_mapping_class(mapping_id))]
        for mapping_id in implementation_mapping_ids
    )
    if not required_review_scopes.issubset(review_scopes):
        _fail(
            "TASK_FINAL_REVIEW_MAPPING_MISSING",
            "Final Code Review lacks an X2-B implementation scope",
        )
    review_paths = set(
        map(
            str,
            _require_list(
                final_review,
                "paths",
                "Final Code Review",
                error_code="TASK_FINAL_REVIEW_MAPPING_MISSING",
            ),
        )
    )
    implementation_paths = {
        str(path)
        for task in tasks
        for path in task.get("paths", [])
    }
    if not implementation_paths.issubset(review_paths):
        _fail(
            "TASK_FINAL_REVIEW_MAPPING_MISSING",
            "Final Code Review omits an implementation path",
        )
    ownership_leaks = sorted(_ownership_leaks(final_review))
    if ownership_leaks:
        _fail(
            "TASK_SPEC_OWNERSHIP_LEAK",
            f"Final Code Review copies Spec-owned {ownership_leaks[0]}",
        )
    semantic_leaks = sorted(_spec_semantic_value_leaks(final_review))
    if semantic_leaks:
        _fail(
            "TASK_SPEC_OWNERSHIP_LEAK",
            f"Final Code Review reinterprets Spec-owned {semantic_leaks[0]}",
        )
    visual_leaks = sorted(_visual_execution_leaks(final_review))
    if visual_leaks:
        _fail(
            "TASK_VISUAL_EXECUTION_LEAK",
            f"Final Code Review contains forbidden {visual_leaks[0]}",
        )

    if blocked_mapping_ids:
        _fail(
            "PLAN_OUTPUT_INCOMPLETE",
            "blocked X2-B mappings prevent complete-looking tasks",
        )
