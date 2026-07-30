"""Pure in-memory semantic checks for representative Plan artifact bundles."""
from __future__ import annotations

import re
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
INTERNAL_REF_PREFIXES = (
    "DEC-",
    "OBJ-",
    "IF-",
    "SEQ-",
    "UIF-",
    "X2B-",
    "TC-",
    "VAL-",
)
PLACEHOLDERS = ("[placeholder]", "<placeholder>", "TODO", "TBD")
SPEC_UI_PREFIX_TO_CLASS = {
    "UI-": "UI",
    "VIS-": "VIS",
    "RST-": "RST",
    "PXR-": "PXR",
    "PXT-": "PXT",
    "PEX-": "PEX",
    "ADP-": "ADP",
}
X2B_MAPPING_KINDS = {
    "general-ui",
    "pixel-target",
    "platform-adaptation",
}
X2B_KIND_ID_PREFIXES = {
    "general-ui": "X2B-UI-",
    "pixel-target": "X2B-PX-",
    "platform-adaptation": "X2B-ADP-",
}
SPEC_OWNED_MAPPING_FIELDS = {
    "statement",
    "requirement_statement",
    "acceptance",
    "baseline_identity",
    "baseline_source_ref",
    "baseline_locator",
    "viewport",
    "state",
    "rendering_context",
    "fidelity_mode",
    "acceptance_envelope",
    "bound",
    "exception_bound",
    "decisions",
    "adaptation_decision",
}
SHA256_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")


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


def _fail(code: str, detail: str) -> None:
    raise ValueError(f"{code}: {detail}")


def _spec_contract_class(ref: str) -> str | None:
    for prefix, contract_class in SPEC_UI_PREFIX_TO_CLASS.items():
        if ref.startswith(prefix):
            return contract_class
    return None


def _mapping_ownership_leaks(value: Any) -> set[str]:
    if isinstance(value, dict):
        leaks = set(value) & SPEC_OWNED_MAPPING_FIELDS
        for child in value.values():
            leaks.update(_mapping_ownership_leaks(child))
        return leaks
    if isinstance(value, list):
        leaks: set[str] = set()
        for child in value:
            leaks.update(_mapping_ownership_leaks(child))
        return leaks
    return set()


def _require_non_empty_list(
    item: dict[str, Any],
    field: str,
    context: str,
    *,
    code: str = "X2B_DELIVERY_DECISION_INCOMPLETE",
) -> list[Any]:
    value = item.get(field)
    if not isinstance(value, list) or not value:
        _fail(code, f"{context} missing non-empty {field}")
    return value


def _validate_spec_freshness(
    bundle: dict[str, Any],
    *,
    x2b_status: str,
) -> dict[str, Any]:
    spec_input = bundle.get("spec_input")
    if not isinstance(spec_input, dict):
        _fail("PLAN_SPEC_INPUT_STALE", "Plan bundle missing local Spec input evidence")
    digest_fields = ("current_sha256", "recorded_x0_sha256")
    digests = [spec_input.get(field) for field in digest_fields]
    if any(not isinstance(digest, str) or not SHA256_PATTERN.fullmatch(digest) for digest in digests):
        _fail(
            "PLAN_SPEC_INPUT_STALE",
            "Spec freshness evidence must use sha256:<64 lowercase hex>",
        )
    if len(set(digests)) != 1:
        _fail(
            "PLAN_SPEC_INPUT_STALE",
            "current Spec digest differs from recorded X0 or UI/UX digest",
        )
    uiux_digest = spec_input.get("recorded_uiux_sha256")
    if x2b_status == "N/A":
        if uiux_digest != "N/A":
            _fail(
                "PLAN_SPEC_INPUT_STALE",
                "inactive X2-B must record UI/UX Spec digest as N/A",
            )
    elif (
        not isinstance(uiux_digest, str)
        or not SHA256_PATTERN.fullmatch(uiux_digest)
        or uiux_digest != digests[0]
    ):
        _fail(
            "PLAN_SPEC_INPUT_STALE",
            "current Spec digest differs from recorded UI/UX digest",
        )
    return spec_input


def _validate_x2b_contract(
    bundle: dict[str, Any],
    *,
    x2b_status: str,
    decision_ids: set[str],
    uif_ids: set[str],
    known_internal_ids: set[str],
    asset_ids: set[str],
) -> set[str]:
    spec_input = _validate_spec_freshness(bundle, x2b_status=x2b_status)
    spec_refs = spec_input.get("ui_contract_refs")
    inventory = bundle.get("x2b_input_inventory")
    mappings = bundle.get("x2b_delivery_mappings")
    readiness_rows = bundle.get("uiux_readiness_rows")
    for name, value in (
        ("spec_input.ui_contract_refs", spec_refs),
        ("x2b_input_inventory", inventory),
        ("x2b_delivery_mappings", mappings),
        ("uiux_readiness_rows", readiness_rows),
    ):
        if not isinstance(value, list):
            _fail("X2B_DELIVERY_DECISION_INCOMPLETE", f"{name} must be a list")

    if x2b_status == "N/A":
        if spec_refs or inventory or mappings or readiness_rows:
            _fail(
                "X2B_SPEC_REF_UNMAPPED",
                "N/A X2-B must have no applicable UI Spec refs or delivery mappings",
            )
        non_ui_evidence = spec_input.get("non_ui_evidence")
        if (
            not isinstance(non_ui_evidence, dict)
            or not non_ui_evidence.get("spec_scope_ref")
            or not non_ui_evidence.get("reason")
        ):
            _fail(
                "X2B_DELIVERY_DECISION_INCOMPLETE",
                "N/A X2-B requires Spec scope ref and concrete non-UI reason",
            )
        return set()

    ref_values = [str(record.get("ref", "")) for record in spec_refs]
    if any(not ref or _spec_contract_class(ref) is None for ref in ref_values):
        _fail("X2B_SPEC_REF_UNKNOWN", "Spec UI input contains an unknown ref class")
    duplicates = _duplicates(ref_values)
    if duplicates:
        _fail(
            "X2B_SPEC_REF_DUPLICATE",
            f"Spec UI input duplicates {sorted(duplicates)[0]}",
        )

    spec_by_ref = dict(zip(ref_values, spec_refs))
    all_source_refs: set[str] = set()
    blocked_spec_refs: dict[str, str] = {}
    for ref, record in spec_by_ref.items():
        if record.get("contract_class") != _spec_contract_class(ref):
            _fail("X2B_SPEC_REF_UNKNOWN", f"{ref} has mismatched contract class")
        source_refs = _require_non_empty_list(
            record,
            "source_refs",
            f"Spec UI input {ref}",
        )
        if any(not str(source_ref).startswith("SRC-") for source_ref in source_refs):
            _fail("X2B_SPEC_REF_UNKNOWN", f"{ref} has invalid SRC ref")
        all_source_refs.update(map(str, source_refs))
        status = record.get("status")
        if status == "BLOCKED":
            blocker = record.get("blocker")
            if not isinstance(blocker, str) or not blocker:
                _fail("X2B_BLOCKER_SUPPRESSED", f"{ref} lacks its upstream blocker")
            blocked_spec_refs[ref] = blocker
        elif status != "specified":
            _fail("X2B_SPEC_REF_UNKNOWN", f"{ref} has invalid Spec status")
    if blocked_spec_refs and x2b_status != "Blocked":
        _fail(
            "X2B_BLOCKER_SUPPRESSED",
            "blocked Spec UI applicability requires blocked X2-B",
        )

    inventory_refs = [str(row.get("spec_ref", "")) for row in inventory]
    inventory_duplicates = _duplicates(inventory_refs)
    if inventory_duplicates:
        _fail(
            "X2B_SPEC_REF_DUPLICATE",
            f"X2-B input inventory duplicates {sorted(inventory_duplicates)[0]}",
        )
    unknown_inventory = set(inventory_refs) - set(spec_by_ref)
    if unknown_inventory:
        _fail(
            "X2B_SPEC_REF_UNKNOWN",
            f"X2-B inventory contains unknown {sorted(unknown_inventory)[0]}",
        )
    missing_inventory = set(spec_by_ref) - set(inventory_refs)
    if missing_inventory:
        _fail(
            "X2B_SPEC_REF_UNMAPPED",
            f"X2-B inventory omits {sorted(missing_inventory)[0]}",
        )
    inventory_by_ref = dict(zip(inventory_refs, inventory))

    for ref, spec_record in spec_by_ref.items():
        row = inventory_by_ref[ref]
        if row.get("contract_class") != spec_record.get("contract_class"):
            _fail("X2B_SPEC_REF_UNKNOWN", f"{ref} inventory class differs from Spec")
        if row.get("spec_status") != spec_record.get("status"):
            _fail("X2B_BLOCKER_SUPPRESSED", f"{ref} inventory hides Spec status")
        if ref in blocked_spec_refs:
            if (
                row.get("x2b_applicability") != "Blocked"
                or row.get("propagated_blocker") != blocked_spec_refs[ref]
                or row.get("mapping_ref")
            ):
                _fail(
                    "X2B_BLOCKER_SUPPRESSED",
                    f"{ref} does not propagate {blocked_spec_refs[ref]}",
                )
        elif (
            row.get("x2b_applicability") != "Required"
            or not row.get("mapping_ref")
            or row.get("propagated_blocker")
        ):
            _fail(
                "X2B_SPEC_REF_UNMAPPED",
                f"{ref} lacks one required X2B mapping ref",
            )

    mapping_ids = [str(mapping.get("id", "")) for mapping in mappings]
    if any(not mapping_id.startswith("X2B-") for mapping_id in mapping_ids):
        _fail(
            "X2B_DELIVERY_DECISION_INCOMPLETE",
            "delivery mapping ids must use X2B-*",
        )
    mapping_duplicates = _duplicates(mapping_ids)
    if mapping_duplicates:
        _fail(
            "X2B_SPEC_REF_DUPLICATE",
            f"delivery mappings duplicate {sorted(mapping_duplicates)[0]}",
        )
    mappings_by_id = dict(zip(mapping_ids, mappings))
    covered_by: dict[str, list[str]] = {ref: [] for ref in spec_by_ref}

    for mapping_id, mapping in mappings_by_id.items():
        forbidden = sorted(_mapping_ownership_leaks(mapping))
        if forbidden:
            _fail(
                "X2B_SPEC_OWNERSHIP_LEAK",
                f"{mapping_id} duplicates Spec-owned {forbidden[0]}",
            )
        kind = mapping.get("kind")
        if kind not in X2B_MAPPING_KINDS:
            _fail(
                "X2B_DELIVERY_DECISION_INCOMPLETE",
                f"{mapping_id} has invalid mapping kind",
            )
        if not mapping_id.startswith(X2B_KIND_ID_PREFIXES[str(kind)]):
            _fail(
                "X2B_DELIVERY_DECISION_INCOMPLETE",
                f"{mapping_id} prefix does not match {kind}",
            )
        mapped_refs = list(
            map(str, _require_non_empty_list(mapping, "spec_refs", mapping_id))
        )
        unknown_refs = set(mapped_refs) - set(spec_by_ref)
        if unknown_refs:
            _fail(
                "X2B_SPEC_REF_UNKNOWN",
                f"{mapping_id} references unknown {sorted(unknown_refs)[0]}",
            )
        for ref in mapped_refs:
            covered_by[ref].append(mapping_id)
            if ref in blocked_spec_refs:
                _fail(
                    "X2B_BLOCKER_SUPPRESSED",
                    f"{mapping_id} maps blocked Spec ref {ref}",
                )

        source_refs = set(
            map(str, _require_non_empty_list(mapping, "source_refs", mapping_id))
        )
        if not source_refs.issubset(all_source_refs):
            _fail("X2B_SPEC_REF_UNKNOWN", f"{mapping_id} has unknown SRC ref")
        required_sources = {
            str(source_ref)
            for ref in mapped_refs
            for source_ref in spec_by_ref[ref].get("source_refs", [])
        }
        if not required_sources.issubset(source_refs):
            _fail(
                "X2B_SPEC_REF_UNMAPPED",
                f"{mapping_id} omits a mapped Spec source ref",
            )
        decision_refs = set(
            map(str, _require_non_empty_list(mapping, "decision_refs", mapping_id))
        )
        if not decision_refs.issubset(decision_ids):
            _fail("X2B_SPEC_REF_UNKNOWN", f"{mapping_id} has unknown DEC-UI ref")
        if any(not ref.startswith("DEC-UI-") for ref in decision_refs):
            _fail(
                "X2B_DELIVERY_DECISION_INCOMPLETE",
                f"{mapping_id} decision refs must use DEC-UI-*",
            )
        for field in ("uif_refs", "interface_refs", "asset_refs"):
            refs = mapping.get(field, [])
            if not isinstance(refs, list):
                _fail(
                    "X2B_DELIVERY_DECISION_INCOMPLETE",
                    f"{mapping_id} {field} must be a list",
                )
            if field == "uif_refs" and not set(map(str, refs)).issubset(uif_ids):
                _fail("X2B_SPEC_REF_UNKNOWN", f"{mapping_id} has unknown UIF ref")
            if field == "interface_refs":
                if any(not str(ref).startswith("IF-") for ref in refs) or not set(
                    map(str, refs)
                ).issubset(known_internal_ids):
                    _fail(
                        "X2B_SPEC_REF_UNKNOWN",
                        f"{mapping_id} has unknown interface ref",
                    )
            if field == "asset_refs" and not set(map(str, refs)).issubset(asset_ids):
                _fail("X2B_SPEC_REF_UNKNOWN", f"{mapping_id} has unknown asset ref")

        if kind == "general-ui":
            if any(_spec_contract_class(ref) not in {"UI", "VIS", "RST"} for ref in mapped_refs):
                _fail(
                    "X2B_DELIVERY_DECISION_INCOMPLETE",
                    f"{mapping_id} general mapping has non-general Spec ref",
                )
            for field in (
                "surface_region_binding",
                "component_delivery",
                "navigation_input_responsive_accessibility",
            ):
                if not mapping.get(field):
                    _fail(
                        "X2B_DELIVERY_DECISION_INCOMPLETE",
                        f"{mapping_id} missing {field}",
                    )
        elif kind == "pixel-target":
            if any(_spec_contract_class(ref) not in {"PXR", "PXT", "PEX"} for ref in mapped_refs):
                _fail(
                    "X2B_DELIVERY_DECISION_INCOMPLETE",
                    f"{mapping_id} pixel mapping has non-pixel Spec ref",
                )
            pxr_ref = str(mapping.get("pxr_ref", ""))
            pxt_ref = str(mapping.get("pxt_ref", ""))
            pex_refs = list(map(str, mapping.get("pex_refs", [])))
            if (
                _spec_contract_class(pxr_ref) != "PXR"
                or _spec_contract_class(pxt_ref) != "PXT"
                or pxr_ref not in spec_by_ref
                or pxt_ref not in spec_by_ref
            ):
                _fail(
                    "X2B_PIXEL_TARGET_UNMAPPED",
                    f"{mapping_id} lacks resolvable PXR/PXT refs",
                )
            if pxt_ref not in mapped_refs:
                _fail(
                    "X2B_PIXEL_TARGET_UNMAPPED",
                    f"{mapping_id} does not own its PXT ref",
                )
            if any(ref not in spec_by_ref or _spec_contract_class(ref) != "PEX" for ref in pex_refs):
                _fail(
                    "X2B_PIXEL_EXCEPTION_UNRESOLVED",
                    f"{mapping_id} has unknown PEX ref",
                )
            if any(ref not in mapped_refs for ref in pex_refs):
                _fail(
                    "X2B_PIXEL_EXCEPTION_UNRESOLVED",
                    f"{mapping_id} does not bind every PEX ref",
                )
            mapped_pex_refs = {
                ref for ref in mapped_refs if _spec_contract_class(ref) == "PEX"
            }
            if set(pex_refs) != mapped_pex_refs:
                _fail(
                    "X2B_PIXEL_EXCEPTION_UNRESOLVED",
                    f"{mapping_id} PEX bindings do not match mapped exceptions",
                )
            ui_vis_refs = list(
                map(str, _require_non_empty_list(mapping, "ui_vis_refs", mapping_id))
            )
            if any(ref not in spec_by_ref or _spec_contract_class(ref) not in {"UI", "VIS"} for ref in ui_vis_refs):
                _fail(
                    "X2B_SPEC_REF_UNKNOWN",
                    f"{mapping_id} has unknown UI/VIS ref",
                )
            if any(ref in blocked_spec_refs for ref in ui_vis_refs):
                _fail(
                    "X2B_BLOCKER_SUPPRESSED",
                    f"{mapping_id} consumes a blocked UI/VIS ref",
                )
            ui_vis_sources = {
                str(source_ref)
                for ref in ui_vis_refs
                for source_ref in spec_by_ref[ref].get("source_refs", [])
            }
            if not ui_vis_sources.issubset(source_refs):
                _fail(
                    "X2B_SPEC_REF_UNMAPPED",
                    f"{mapping_id} omits a UI/VIS source ref",
                )
            for field in (
                "target_region_binding",
                "delivery_mapping",
                "local_delivery_review_method",
            ):
                if not mapping.get(field):
                    _fail(
                        "X2B_DELIVERY_DECISION_INCOMPLETE",
                        f"{mapping_id} missing {field}",
                    )
        else:
            if len(mapped_refs) != 1 or _spec_contract_class(mapped_refs[0]) != "ADP":
                _fail(
                    "X2B_ADAPTATION_UNMAPPED",
                    f"{mapping_id} must map one ADP policy/dimension ref",
                )
            if mapping.get("adp_ref") != mapped_refs[0]:
                _fail(
                    "X2B_ADAPTATION_UNMAPPED",
                    f"{mapping_id} ADP ref differs from its mapped Spec ref",
                )
            ui_vis_refs = list(
                map(str, _require_non_empty_list(mapping, "ui_vis_refs", mapping_id))
            )
            if any(ref not in spec_by_ref or _spec_contract_class(ref) not in {"UI", "VIS"} for ref in ui_vis_refs):
                _fail(
                    "X2B_SPEC_REF_UNKNOWN",
                    f"{mapping_id} has unknown UI/VIS ref",
                )
            if any(ref in blocked_spec_refs for ref in ui_vis_refs):
                _fail(
                    "X2B_BLOCKER_SUPPRESSED",
                    f"{mapping_id} consumes a blocked UI/VIS ref",
                )
            ui_vis_sources = {
                str(source_ref)
                for ref in ui_vis_refs
                for source_ref in spec_by_ref[ref].get("source_refs", [])
            }
            if not ui_vis_sources.issubset(source_refs):
                _fail(
                    "X2B_SPEC_REF_UNMAPPED",
                    f"{mapping_id} omits a UI/VIS source ref",
                )
            for field in ("target_context_binding", "target_delivery_design"):
                if not mapping.get(field):
                    _fail(
                        "X2B_DELIVERY_DECISION_INCOMPLETE",
                        f"{mapping_id} missing {field}",
                    )

        status = mapping.get("status")
        if status == "BLOCKED":
            if not mapping.get("blocker"):
                _fail(
                    "X2B_DELIVERY_DECISION_INCOMPLETE",
                    f"{mapping_id} BLOCKED without blocker",
                )
        elif status != "READY":
            _fail(
                "X2B_DELIVERY_DECISION_INCOMPLETE",
                f"{mapping_id} has invalid delivery status",
            )

    if (
        any(mapping.get("status") == "BLOCKED" for mapping in mappings)
        and x2b_status != "Blocked"
    ):
        _fail(
            "X2B_DELIVERY_DECISION_INCOMPLETE",
            "a blocked delivery mapping requires blocked X2-B",
        )

    for ref, mapping_refs in covered_by.items():
        if ref in blocked_spec_refs:
            if mapping_refs:
                _fail("X2B_BLOCKER_SUPPRESSED", f"{ref} blocker was mapped as delivery")
            continue
        if not mapping_refs:
            contract_class = _spec_contract_class(ref)
            code = {
                "PXT": "X2B_PIXEL_TARGET_UNMAPPED",
                "PEX": "X2B_PIXEL_EXCEPTION_UNRESOLVED",
                "ADP": "X2B_ADAPTATION_UNMAPPED",
            }.get(str(contract_class), "X2B_SPEC_REF_UNMAPPED")
            _fail(code, f"{ref} has no delivery mapping")
        if len(mapping_refs) != 1:
            _fail(
                "X2B_SPEC_REF_DUPLICATE",
                f"{ref} is mapped by {mapping_refs}",
            )
        if inventory_by_ref[ref].get("mapping_ref") != mapping_refs[0]:
            _fail(
                "X2B_SPEC_REF_UNMAPPED",
                f"{ref} inventory mapping does not resolve",
            )

    readiness_mapping_refs = [str(row.get("mapping_ref", "")) for row in readiness_rows]
    readiness_duplicates = _duplicates(readiness_mapping_refs)
    if readiness_duplicates:
        _fail(
            "X2B_SPEC_REF_DUPLICATE",
            f"UI/UX readiness duplicates {sorted(readiness_duplicates)[0]}",
        )
    if set(readiness_mapping_refs) != set(mapping_ids):
        _fail(
            "X2B_DELIVERY_DECISION_INCOMPLETE",
            "UI/UX readiness must contain one row per delivery mapping",
        )
    readiness_by_mapping = dict(zip(readiness_mapping_refs, readiness_rows))
    for mapping_id, mapping in mappings_by_id.items():
        row = readiness_by_mapping[mapping_id]
        if row.get("status") != mapping.get("status"):
            _fail(
                "X2B_DELIVERY_DECISION_INCOMPLETE",
                f"{mapping_id} readiness status differs from mapping",
            )
        if row.get("status") == "READY" and not row.get("evidence"):
            _fail(
                "X2B_DELIVERY_DECISION_INCOMPLETE",
                f"{mapping_id} READY readiness lacks evidence",
            )
        if row.get("status") == "BLOCKED" and row.get("blocker") != mapping.get(
            "blocker"
        ):
            _fail(
                "X2B_DELIVERY_DECISION_INCOMPLETE",
                f"{mapping_id} readiness fails to propagate blocker",
            )

    required_mapping_refs = {
        str(row["mapping_ref"])
        for row in inventory
        if row.get("x2b_applicability") == "Required"
    }
    if required_mapping_refs != set(mapping_ids):
        unknown_mapping = set(mapping_ids) - required_mapping_refs
        if unknown_mapping:
            _fail(
                "X2B_SPEC_REF_UNKNOWN",
                f"orphan mapping {sorted(unknown_mapping)[0]}",
            )
        _fail(
            "X2B_SPEC_REF_UNMAPPED",
            "inventory references a missing X2B mapping",
        )
    return set(mapping_ids)


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
    base_known_ids = set(declared_ids)
    declared_asset_refs = bundle.get("declared_asset_refs", [])
    if not isinstance(declared_asset_refs, list):
        _fail(
            "X2B_DELIVERY_DECISION_INCOMPLETE",
            "declared_asset_refs must be a list",
        )
    x2b_mapping_ids = _validate_x2b_contract(
        bundle,
        x2b_status=x2b_status,
        decision_ids={
            str(decision.get("id", "")) for decision in bundle.get("decisions", [])
        },
        uif_ids={
            str(contract.get("id", "")) for contract in bundle.get("uif_contracts", [])
        },
        known_internal_ids=base_known_ids,
        asset_ids=set(map(str, declared_asset_refs)),
    )
    declared_ids.extend(sorted(x2b_mapping_ids))
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
    for mapping in bundle.get("x2b_delivery_mappings", []):
        for field in (
            "decision_refs",
            "uif_refs",
            "interface_refs",
        ):
            consumed_refs.update(mapping.get(field, []))
    for row in bundle.get("uiux_readiness_rows", []):
        if row.get("mapping_ref"):
            consumed_refs.add(row["mapping_ref"])

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
