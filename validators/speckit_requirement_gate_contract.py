"""Pure in-memory contract helpers for the canonical Requirement Gate.

The helpers deliberately do not parse or write Markdown.  Tests pass an
in-memory projection of ``checklists/requirements.md`` so the preset can prove
cross-field rules without introducing a runtime, manifest, or transaction
protocol.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
import re
from typing import Any, Iterable, Mapping


REQUIREMENT_GATE_CONTRACT = "speckit.requirement-gate.v1"
CANONICAL_REQUIREMENT_GATE_PATH = "checklists/requirements.md"
STANDARD_REQUIREMENT_GATES = (
    "requirements",
    "behavior",
    "ux",
    "security",
    "nfr",
    "visual",
)
REQUIREMENT_RULE_GATES = {
    "BEH-CASES": {"behavior"},
    "BEH-OBSERVABLE": {"behavior"},
    "BEH-LIFECYCLE": {"behavior"},
    "BEH-SCOPE": {"behavior"},
    "DOM-SCOPE": {"requirements", "ux", "security"},
    "DOM-ACTOR-STATE": {"requirements", "ux", "security"},
    "DOM-MEASURE": {"requirements", "ux", "security"},
    "DOM-COVERAGE": {"requirements", "ux", "security"},
    "NFR-MEASURE": {"nfr"},
    "NFR-COVERAGE": {"nfr"},
    "NFR-CONTEXT": {"nfr"},
    "NFR-ABSTRACTION": {"nfr"},
    "UI-STATES": {"ux"},
    "UX-JOURNEY": {"ux"},
    "VIS-TRACE": {"visual"},
    "VIS-SOURCE": {"visual"},
    "UI-EVIDENCE": {"visual"},
    "UI-INFERENCE": {"visual"},
    "RST-COVERAGE": {"visual"},
    "PXR-PROFILE": {"visual"},
    "PXR-EXCEPTION": {"visual"},
    "ADP-COVERAGE": {"visual"},
    "ADP-TRACE": {"visual"},
    "UI-BOUNDARY": {"requirements"},
}
LEGACY_DOMAIN_PATHS = {
    "checklists/behavior.md",
    "checklists/ux.md",
    "checklists/security.md",
    "checklists/nfr.md",
    "checklists/visual.md",
}
BLOCKER_CLASSES = {
    "product-decision",
    "source-evidence",
    "template-structure",
    "legacy-layout",
}
BLOCKER_OWNERS = {
    "product-decision": "clarify",
    "source-evidence": "source-owner",
    "template-structure": "checklist",
    "legacy-layout": "checklist",
}
SHA256_REVISION_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
SPEC_EVIDENCE_PATTERN = re.compile(
    r"^spec\.md#(?P<spec_ref>[A-Z][A-Z0-9]*-\d+)(?::.+)?$"
)
PLACEHOLDER_PATTERN = re.compile(
    r"(?:\bTODO\b|\bTBD\b|NEEDS CLARIFICATION|<[^>]+>|\[(?:TODO|TBD)\])",
    flags=re.IGNORECASE,
)
BUNDLE_KEYS = {
    "path",
    "metadata",
    "semantic_groups",
    "gate_summary",
    "planning_readiness",
}
METADATA_KEYS = {"stage", "contract", "spec_revision", "planning_readiness"}
GROUP_KEYS = {"spec_ref", "checks", "blockers", "manual_notes"}
CHECK_KEYS = {
    "id",
    "rule_key",
    "gate",
    "concern",
    "spec_refs",
    "status",
    "evidence_refs",
    "blocker_ref",
}
BLOCKER_KEYS = {
    "id",
    "primary_spec_ref",
    "semantic_key",
    "gap",
    "affected_check_ids",
    "class",
    "owner",
    "status",
    "replacement_refs",
    "reason",
}
SUMMARY_KEYS = {
    "gate",
    "applicability",
    "applicability_reason",
    "status",
    "check_refs",
    "blocker_refs",
    "check_count",
    "blocker_count",
}
READINESS_KEYS = {"status", "spec_revision", "blocker_refs"}


def _finding(code: str, evidence: str, *, path: str = "") -> dict[str, str]:
    return {"code": code, "path": path, "evidence": evidence}


def _non_empty_strings(value: Any) -> bool:
    return (
        isinstance(value, list)
        and bool(value)
        and all(isinstance(item, str) and item.strip() for item in value)
    )


def _spec_refs_from_evidence(value: Any) -> set[str]:
    if not _non_empty_strings(value):
        return set()
    refs: set[str] = set()
    for item in value:
        match = SPEC_EVIDENCE_PATTERN.fullmatch(item)
        if match is None:
            return set()
        refs.add(match.group("spec_ref"))
    return refs


def _reason_has_current_spec_ref(reason: Any, known_spec_refs: set[str]) -> bool:
    if not isinstance(reason, str) or not reason.strip():
        return False
    return any(
        re.search(rf"(?<![A-Z0-9-]){re.escape(spec_ref)}(?![A-Z0-9-])", reason)
        for spec_ref in known_spec_refs
    )


def _unexpected_keys(value: Mapping[str, Any], allowed: set[str]) -> list[str]:
    return sorted(str(key) for key in set(value) - allowed)


def _has_placeholder(value: Any) -> bool:
    return isinstance(value, str) and PLACEHOLDER_PATTERN.search(value) is not None


def _open_blockers(groups: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        blocker
        for group in groups
        for blocker in group.get("blockers", [])
        if isinstance(blocker, dict) and blocker.get("status") == "OPEN"
    ]


def select_authoritative_requirement_gate(
    candidates: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    """Select the one authoritative bundle without consuming legacy files."""

    canonical: list[dict[str, Any]] = []
    ignored: list[dict[str, Any]] = []
    findings: list[dict[str, str]] = []

    for candidate in candidates:
        path = str(candidate.get("path", ""))
        if path == CANONICAL_REQUIREMENT_GATE_PATH:
            canonical.append(candidate)
            continue
        ignored.append(candidate)
        if path in LEGACY_DOMAIN_PATHS:
            findings.append(
                _finding(
                    "REQUIREMENT_GATE_LEGACY_LAYOUT",
                    "legacy domain file is preserved but never consumed",
                    path=path,
                )
            )

    if not canonical:
        findings.append(
            _finding(
                "REQUIREMENT_GATE_MISSING",
                "canonical checklists/requirements.md is missing",
                path=CANONICAL_REQUIREMENT_GATE_PATH,
            )
        )
    elif len(canonical) > 1:
        findings.append(
            _finding(
                "REQUIREMENT_GATE_DUPLICATE",
                "more than one canonical Requirement Gate candidate",
                path=CANONICAL_REQUIREMENT_GATE_PATH,
            )
        )

    return {
        "authoritative": canonical[0] if len(canonical) == 1 else None,
        "ignored": ignored,
        "findings": findings,
    }


def _derive_gate_summary(
    groups: list[dict[str, Any]],
    applicability: Mapping[str, tuple[str, str | None]],
) -> list[dict[str, Any]]:
    checks_by_gate: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for group in groups:
        for check in group.get("checks", []):
            if isinstance(check, dict):
                checks_by_gate[str(check.get("gate", ""))].append(check)

    summary: list[dict[str, Any]] = []
    for gate in STANDARD_REQUIREMENT_GATES:
        gate_applicability, reason = applicability[gate]
        checks = checks_by_gate[gate]
        blocker_refs = sorted(
            {
                str(check["blocker_ref"])
                for check in checks
                if check.get("status") == "BLOCKED" and check.get("blocker_ref")
            }
        )
        if gate_applicability == "NOT_APPLICABLE":
            status = "PASS"
        else:
            status = (
                "PASS"
                if checks and all(check.get("status") == "PASS" for check in checks)
                else "BLOCKED"
            )
        summary.append(
            {
                "gate": gate,
                "applicability": gate_applicability,
                "applicability_reason": reason,
                "status": status,
                "check_refs": sorted(
                    str(check.get("id", "")) for check in checks if check.get("id")
                ),
                "blocker_refs": blocker_refs,
                "check_count": len(checks),
                "blocker_count": len(blocker_refs),
            }
        )
    return summary


def _derive_planning_readiness(
    *,
    spec_revision: str,
    current_spec_revision: str,
    gate_summary: list[dict[str, Any]],
    groups: list[dict[str, Any]],
) -> dict[str, Any]:
    blocker_refs = sorted(
        str(blocker["id"])
        for blocker in _open_blockers(groups)
        if blocker.get("id")
    )
    ready = (
        spec_revision == current_spec_revision
        and len(gate_summary) == len(STANDARD_REQUIREMENT_GATES)
        and all(item.get("status") == "PASS" for item in gate_summary)
        and not blocker_refs
    )
    return {
        "status": "PASS" if ready else "BLOCKED",
        "spec_revision": spec_revision,
        "blocker_refs": blocker_refs,
    }


def rebuild_requirement_gate(
    *,
    spec_revision: str,
    all_spec_refs: Iterable[str],
    semantic_groups: Iterable[dict[str, Any]],
    applicability: Mapping[str, tuple[str, str | None]],
    previous_bundle: dict[str, Any] | None = None,
    focus: str | None = None,
) -> dict[str, Any]:
    """Assemble Checklist's one canonical in-memory bundle.

    ``focus`` intentionally cannot select a path or omit a Gate. Stable IDs and
    lifecycle rows come from the supplied semantic records. Clearly delimited
    manual notes are carried forward by stable Spec ref but never participate
    in derivation.
    """

    del focus
    if SHA256_REVISION_PATTERN.fullmatch(spec_revision) is None:
        raise ValueError("Spec Revision must be an exact lowercase SHA-256")

    groups = deepcopy(list(semantic_groups))
    previous_notes: dict[str, Any] = {}
    if isinstance(previous_bundle, dict):
        for old_group in previous_bundle.get("semantic_groups", []):
            if (
                isinstance(old_group, dict)
                and isinstance(old_group.get("spec_ref"), str)
                and "manual_notes" in old_group
            ):
                previous_notes.setdefault(
                    old_group["spec_ref"],
                    deepcopy(old_group["manual_notes"]),
                )
    for group in groups:
        if (
            isinstance(group, dict)
            and "manual_notes" not in group
            and group.get("spec_ref") in previous_notes
        ):
            group["manual_notes"] = previous_notes[group["spec_ref"]]

    missing_gates = set(STANDARD_REQUIREMENT_GATES) - set(applicability)
    extra_gates = set(applicability) - set(STANDARD_REQUIREMENT_GATES)
    if missing_gates or extra_gates:
        raise ValueError("applicability must define exactly the six standard Gates")

    summary = _derive_gate_summary(groups, applicability)
    readiness = _derive_planning_readiness(
        spec_revision=spec_revision,
        current_spec_revision=spec_revision,
        gate_summary=summary,
        groups=groups,
    )
    bundle = {
        "path": CANONICAL_REQUIREMENT_GATE_PATH,
        "metadata": {
            "stage": "requirements",
            "contract": REQUIREMENT_GATE_CONTRACT,
            "spec_revision": spec_revision,
            "planning_readiness": readiness["status"],
        },
        "semantic_groups": groups,
        "gate_summary": summary,
        "planning_readiness": readiness,
    }
    result = inspect_requirement_gate_bundle(
        bundle,
        current_spec_revision=spec_revision,
        all_spec_refs=all_spec_refs,
    )
    if result["status"] != "PASS":
        codes = ", ".join(finding["code"] for finding in result["findings"])
        raise ValueError(f"assembled Requirement Gate is invalid: {codes}")
    return bundle


def inspect_core_wrapper_contract(
    *,
    checklist_output_paths: Iterable[str],
    plan_events: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    """Validate wrapper capabilities without parsing command Markdown."""

    findings: list[dict[str, str]] = []
    outputs = list(checklist_output_paths)
    if outputs != [CANONICAL_REQUIREMENT_GATE_PATH]:
        findings.append(
            _finding(
                "REQUIREMENT_GATE_CORE_WRAPPER_INCOMPATIBLE",
                f"Checklist outputs must be exactly [{CANONICAL_REQUIREMENT_GATE_PATH}]",
            )
        )

    events = list(plan_events)
    names = [str(event.get("name", "")) for event in events]
    required = ("path-resolution", "canonical-preflight", "core-setup")
    if any(name not in names for name in required):
        findings.append(
            _finding(
                "REQUIREMENT_GATE_CORE_WRAPPER_INCOMPATIBLE",
                "Plan wrapper is missing path resolution, canonical preflight, or Core setup",
            )
        )
    else:
        path_index = names.index("path-resolution")
        preflight_index = names.index("canonical-preflight")
        setup_index = names.index("core-setup")
        first_write_index = next(
            (
                index
                for index, event in enumerate(events)
                if event.get("writes") is True
            ),
            len(events),
        )
        first_hook_index = next(
            (
                index
                for index, event in enumerate(events)
                if event.get("hook") is True
            ),
            len(events),
        )
        if not (
            path_index < preflight_index < setup_index
            and preflight_index < first_write_index
            and preflight_index < first_hook_index
        ):
            findings.append(
                _finding(
                    "REQUIREMENT_GATE_CORE_WRAPPER_INCOMPATIBLE",
                    "canonical preflight must precede every hook and write-bearing Core step",
                )
            )

    return {
        "status": "PASS" if not findings else "BLOCKED",
        "findings": findings,
    }


def inspect_requirement_gate_bundle(
    bundle: Any,
    *,
    current_spec_revision: str,
    all_spec_refs: Iterable[str],
    require_ready: bool = False,
) -> dict[str, Any]:
    """Validate structure, references, and strictly derived state.

    Findings are stable records rather than exceptions so one test can assert
    several independent contract failures.
    """

    findings: list[dict[str, str]] = []
    if not isinstance(bundle, dict):
        return {
            "status": "BLOCKED",
            "findings": [
                _finding(
                    "REQUIREMENT_GATE_MALFORMED",
                    "bundle must be an object",
                    path=CANONICAL_REQUIREMENT_GATE_PATH,
                )
            ],
            "derived_gate_summary": [],
            "derived_planning_readiness": None,
        }
    extra_bundle_keys = _unexpected_keys(bundle, BUNDLE_KEYS)
    if extra_bundle_keys:
        findings.append(
            _finding(
                "REQUIREMENT_GATE_LAYOUT_EXTRA_FIELD",
                f"unexpected document fields: {extra_bundle_keys}",
                path=CANONICAL_REQUIREMENT_GATE_PATH,
            )
        )

    path = str(bundle.get("path", ""))
    if path != CANONICAL_REQUIREMENT_GATE_PATH:
        findings.append(
            _finding(
                "REQUIREMENT_GATE_PATH_INVALID",
                path or "<missing>",
                path=path,
            )
        )

    metadata = bundle.get("metadata")
    if not isinstance(metadata, dict):
        findings.append(
            _finding(
                "REQUIREMENT_GATE_METADATA_MALFORMED",
                "File Metadata is missing",
                path=path,
            )
        )
        metadata = {}
    else:
        extra_metadata_keys = _unexpected_keys(metadata, METADATA_KEYS)
        if extra_metadata_keys:
            findings.append(
                _finding(
                    "REQUIREMENT_GATE_LAYOUT_EXTRA_FIELD",
                    f"unexpected File Metadata fields: {extra_metadata_keys}",
                    path=path,
                )
            )
    if metadata.get("stage") != "requirements":
        findings.append(
            _finding(
                "REQUIREMENT_GATE_METADATA_MALFORMED",
                "Stage must be requirements",
                path=path,
            )
        )
    if metadata.get("contract") != REQUIREMENT_GATE_CONTRACT:
        findings.append(
            _finding(
                "REQUIREMENT_GATE_METADATA_MALFORMED",
                f"contract must be {REQUIREMENT_GATE_CONTRACT}",
                path=path,
            )
        )
    spec_revision = metadata.get("spec_revision")
    if (
        not isinstance(spec_revision, str)
        or SHA256_REVISION_PATTERN.fullmatch(spec_revision) is None
    ):
        findings.append(
            _finding(
                "REQUIREMENT_GATE_METADATA_MALFORMED",
                "Spec Revision must use sha256:<64 lowercase hex characters>",
                path=path,
            )
        )
        spec_revision = ""
    elif spec_revision != current_spec_revision:
        findings.append(
            _finding(
                "REQUIREMENT_GATE_SPEC_REVISION_STALE",
                f"{spec_revision} != {current_spec_revision}",
                path=path,
            )
        )

    groups = bundle.get("semantic_groups")
    if not isinstance(groups, list) or not groups:
        findings.append(
            _finding(
                "REQUIREMENT_GATE_GROUPS_MALFORMED",
                "Semantic Requirement Groups must be a non-empty list",
                path=path,
            )
        )
        groups = []

    known_spec_refs = set(all_spec_refs)
    seen_group_refs: set[str] = set()
    seen_check_ids: set[str] = set()
    seen_blocker_ids: set[str] = set()
    seen_open_root_keys: set[tuple[str, str, str]] = set()
    checks_by_id: dict[str, dict[str, Any]] = {}
    check_group_by_id: dict[str, str] = {}
    blockers_by_id: dict[str, dict[str, Any]] = {}
    applicability: dict[str, tuple[str, str | None]] = {}

    raw_summary = bundle.get("gate_summary")
    if isinstance(raw_summary, list):
        for record in raw_summary:
            if not isinstance(record, dict):
                continue
            gate = str(record.get("gate", ""))
            if gate in STANDARD_REQUIREMENT_GATES and gate not in applicability:
                applicability[gate] = (
                    str(record.get("applicability", "")),
                    record.get("applicability_reason"),
                )
    else:
        raw_summary = []
    for gate in STANDARD_REQUIREMENT_GATES:
        applicability.setdefault(gate, ("", None))

    for group in groups:
        if not isinstance(group, dict):
            findings.append(
                _finding(
                    "REQUIREMENT_GATE_GROUPS_MALFORMED",
                    "every semantic group must be an object",
                    path=path,
                )
            )
            continue
        spec_ref = str(group.get("spec_ref", ""))
        extra_group_keys = _unexpected_keys(group, GROUP_KEYS)
        if extra_group_keys:
            findings.append(
                _finding(
                    "REQUIREMENT_GATE_LAYOUT_EXTRA_FIELD",
                    f"{spec_ref or '<missing>'} unexpected group fields: {extra_group_keys}",
                    path=path,
                )
            )
        if not spec_ref:
            findings.append(
                _finding(
                    "REQUIREMENT_GATE_SPEC_REF_UNKNOWN",
                    "semantic group has no Spec ref",
                    path=path,
                )
            )
        elif spec_ref in seen_group_refs:
            findings.append(
                _finding(
                    "REQUIREMENT_GATE_SPEC_REF_DUPLICATE",
                    spec_ref,
                    path=path,
                )
            )
        elif spec_ref not in known_spec_refs:
            findings.append(
                _finding(
                    "REQUIREMENT_GATE_SPEC_REF_UNKNOWN",
                    spec_ref,
                    path=path,
                )
            )
        seen_group_refs.add(spec_ref)

        checks = group.get("checks")
        blockers = group.get("blockers")
        if not isinstance(checks, list) or not isinstance(blockers, list):
            findings.append(
                _finding(
                    "REQUIREMENT_GATE_GROUPS_MALFORMED",
                    f"{spec_ref} needs Check and Blocker lists",
                    path=path,
                )
            )
            continue

        for check in checks:
            if not isinstance(check, dict):
                findings.append(
                    _finding(
                        "REQUIREMENT_GATE_CHECK_MALFORMED",
                        f"{spec_ref} contains a non-object Check",
                        path=path,
                    )
                )
                continue
            check_id = str(check.get("id", ""))
            extra_check_keys = _unexpected_keys(check, CHECK_KEYS)
            if extra_check_keys:
                findings.append(
                    _finding(
                        "REQUIREMENT_GATE_LAYOUT_EXTRA_FIELD",
                        f"{check_id or '<missing>'} unexpected Check fields: {extra_check_keys}",
                        path=path,
                    )
                )
            if not check_id:
                findings.append(
                    _finding(
                        "REQUIREMENT_GATE_CHECK_MALFORMED",
                        f"{spec_ref} Check has no ID",
                        path=path,
                    )
                )
                continue
            if check_id in seen_check_ids:
                findings.append(
                    _finding(
                        "REQUIREMENT_GATE_CHECK_DUPLICATE",
                        check_id,
                        path=path,
                    )
                )
            seen_check_ids.add(check_id)
            checks_by_id[check_id] = check
            check_group_by_id[check_id] = spec_ref

            gate = check.get("gate")
            rule_key = str(check.get("rule_key", ""))
            if (
                gate not in STANDARD_REQUIREMENT_GATES
                or rule_key not in REQUIREMENT_RULE_GATES
                or gate not in REQUIREMENT_RULE_GATES.get(rule_key, set())
                or not str(check.get("concern", "")).strip()
            ):
                findings.append(
                    _finding(
                        "REQUIREMENT_GATE_CHECK_MALFORMED",
                        f"{check_id} needs a mapped Rule key, one allowed Gate, and one atomic concern",
                        path=path,
                    )
                )
            if _has_placeholder(check.get("concern")):
                findings.append(
                    _finding(
                        "REQUIREMENT_GATE_PLACEHOLDER",
                        f"{check_id} concern contains a placeholder",
                        path=path,
                    )
                )
            spec_refs = check.get("spec_refs")
            if not _non_empty_strings(spec_refs):
                findings.append(
                    _finding(
                        "REQUIREMENT_GATE_CHECK_MALFORMED",
                        f"{check_id} needs resolvable Spec refs",
                        path=path,
                    )
                )
            else:
                if len(set(spec_refs)) != len(spec_refs):
                    findings.append(
                        _finding(
                            "REQUIREMENT_GATE_CHECK_MALFORMED",
                            f"{check_id} contains duplicate Spec refs",
                            path=path,
                        )
                    )
                if spec_ref not in spec_refs:
                    findings.append(
                        _finding(
                            "REQUIREMENT_GATE_CHECK_GROUP_MISMATCH",
                            f"{check_id} does not reference owning group {spec_ref}",
                            path=path,
                        )
                    )
                for check_spec_ref in spec_refs:
                    if check_spec_ref not in known_spec_refs:
                        findings.append(
                            _finding(
                                "REQUIREMENT_GATE_SPEC_REF_UNKNOWN",
                                f"{check_id} -> {check_spec_ref}",
                                path=path,
                            )
                        )

            status = check.get("status")
            evidence_refs = check.get("evidence_refs")
            blocker_ref = check.get("blocker_ref")
            if status == "PASS":
                if not _non_empty_strings(evidence_refs) or blocker_ref is not None:
                    findings.append(
                        _finding(
                            "REQUIREMENT_GATE_CHECK_RESULT_INVALID",
                            f"{check_id} PASS needs evidence and no Blocker",
                            path=path,
                        )
                    )
                else:
                    evidence_spec_refs = _spec_refs_from_evidence(evidence_refs)
                    if (
                        not evidence_spec_refs
                        or not set(spec_refs).issubset(evidence_spec_refs)
                        or not evidence_spec_refs.issubset(known_spec_refs)
                    ):
                        findings.append(
                            _finding(
                                "REQUIREMENT_GATE_CHECK_EVIDENCE_INVALID",
                                f"{check_id} evidence must resolve every Check Spec ref in current spec.md",
                                path=path,
                            )
                        )
            elif status == "BLOCKED":
                if evidence_refs not in ([], None) or not isinstance(
                    blocker_ref, str
                ):
                    findings.append(
                        _finding(
                            "REQUIREMENT_GATE_CHECK_RESULT_INVALID",
                            f"{check_id} BLOCKED needs exactly one root-cause Blocker",
                            path=path,
                        )
                    )
            else:
                findings.append(
                    _finding(
                        "REQUIREMENT_GATE_CHECK_RESULT_INVALID",
                        f"{check_id} has invalid status",
                        path=path,
                    )
                )

        for blocker in blockers:
            if not isinstance(blocker, dict):
                findings.append(
                    _finding(
                        "REQUIREMENT_GATE_BLOCKER_MALFORMED",
                        f"{spec_ref} contains a non-object Blocker",
                        path=path,
                    )
                )
                continue
            blocker_id = str(blocker.get("id", ""))
            extra_blocker_keys = _unexpected_keys(blocker, BLOCKER_KEYS)
            if extra_blocker_keys:
                findings.append(
                    _finding(
                        "REQUIREMENT_GATE_LAYOUT_EXTRA_FIELD",
                        f"{blocker_id or '<missing>'} unexpected Blocker fields: {extra_blocker_keys}",
                        path=path,
                    )
                )
            if not blocker_id:
                findings.append(
                    _finding(
                        "REQUIREMENT_GATE_BLOCKER_MALFORMED",
                        f"{spec_ref} Blocker has no ID",
                        path=path,
                    )
                )
                continue
            if blocker_id in seen_blocker_ids:
                findings.append(
                    _finding(
                        "REQUIREMENT_GATE_BLOCKER_DUPLICATE",
                        blocker_id,
                        path=path,
                    )
                )
            seen_blocker_ids.add(blocker_id)
            blockers_by_id[blocker_id] = blocker

            blocker_class = blocker.get("class")
            if blocker_class not in BLOCKER_CLASSES:
                findings.append(
                    _finding(
                        "REQUIREMENT_GATE_BLOCKER_CLASS_INVALID",
                        blocker_id,
                        path=path,
                    )
                )
            elif blocker.get("owner") != BLOCKER_OWNERS[blocker_class]:
                findings.append(
                    _finding(
                        "REQUIREMENT_GATE_BLOCKER_OWNER_INVALID",
                        blocker_id,
                        path=path,
                    )
                )
            if (
                blocker.get("primary_spec_ref") != spec_ref
                or not str(blocker.get("semantic_key", "")).strip()
                or not str(blocker.get("gap", "")).strip()
            ):
                findings.append(
                    _finding(
                        "REQUIREMENT_GATE_BLOCKER_MALFORMED",
                        f"{blocker_id} needs primary ref, semantic key, and minimal gap",
                        path=path,
                    )
                )
            if _has_placeholder(blocker.get("gap")):
                findings.append(
                    _finding(
                        "REQUIREMENT_GATE_PLACEHOLDER",
                        f"{blocker_id} gap contains a placeholder",
                        path=path,
                    )
                )
            if blocker.get("status") == "OPEN":
                root_key = (
                    spec_ref,
                    str(blocker.get("semantic_key", "")),
                    str(blocker_class),
                )
                if root_key in seen_open_root_keys:
                    findings.append(
                        _finding(
                            "REQUIREMENT_GATE_BLOCKER_ROOT_DUPLICATE",
                            f"{spec_ref}:{root_key[1]}",
                            path=path,
                        )
                    )
                seen_open_root_keys.add(root_key)
            if blocker.get("status") not in {
                "OPEN",
                "RESOLVED",
                "RETIRED",
                "SUPERSEDED",
            }:
                findings.append(
                    _finding(
                        "REQUIREMENT_GATE_BLOCKER_MALFORMED",
                        f"{blocker_id} has invalid lifecycle status",
                        path=path,
                    )
                )
            replacement_refs = blocker.get("replacement_refs")
            if not isinstance(replacement_refs, list) or not all(
                isinstance(item, str) and item.strip()
                for item in replacement_refs
            ):
                findings.append(
                    _finding(
                        "REQUIREMENT_GATE_BLOCKER_LIFECYCLE_INVALID",
                        f"{blocker_id} replacement refs must be a list of IDs",
                        path=path,
                    )
                )
            elif len(set(replacement_refs)) != len(replacement_refs):
                findings.append(
                    _finding(
                        "REQUIREMENT_GATE_BLOCKER_LIFECYCLE_INVALID",
                        f"{blocker_id} contains duplicate successor refs",
                        path=path,
                    )
                )
            if blocker.get("status") == "SUPERSEDED" and not replacement_refs:
                findings.append(
                    _finding(
                        "REQUIREMENT_GATE_BLOCKER_LIFECYCLE_INVALID",
                        f"{blocker_id} SUPERSEDED needs successor refs",
                        path=path,
                    )
                )
            if blocker.get("status") in {"OPEN", "RESOLVED", "RETIRED"} and (
                replacement_refs
            ):
                findings.append(
                    _finding(
                        "REQUIREMENT_GATE_BLOCKER_LIFECYCLE_INVALID",
                        f"{blocker_id} current/resolved/retired state cannot have successors",
                        path=path,
                    )
                )
            if blocker.get("status") == "RETIRED" and not str(
                blocker.get("reason", "")
            ).strip():
                findings.append(
                    _finding(
                        "REQUIREMENT_GATE_BLOCKER_LIFECYCLE_INVALID",
                        f"{blocker_id} RETIRED needs a reason",
                        path=path,
                    )
                )

    inbound_by_blocker: dict[str, set[str]] = defaultdict(set)
    for check_id, check in checks_by_id.items():
        blocker_ref = check.get("blocker_ref")
        if isinstance(blocker_ref, str):
            inbound_by_blocker[blocker_ref].add(check_id)
            if blocker_ref not in blockers_by_id:
                findings.append(
                    _finding(
                        "REQUIREMENT_GATE_BLOCKER_UNKNOWN",
                        f"{check_id} -> {blocker_ref}",
                        path=path,
                    )
                )

    for blocker_id, blocker in blockers_by_id.items():
        affected = blocker.get("affected_check_ids")
        affected_set = set(affected) if _non_empty_strings(affected) else set()
        if _non_empty_strings(affected) and len(affected_set) != len(affected):
            findings.append(
                _finding(
                    "REQUIREMENT_GATE_BLOCKER_AFFECTED_CHECK_MISMATCH",
                    f"{blocker_id} contains duplicate affected Check refs",
                    path=path,
                )
            )
        inbound = inbound_by_blocker.get(blocker_id, set())
        if blocker.get("status") == "OPEN":
            if affected_set != inbound or not inbound:
                findings.append(
                    _finding(
                        "REQUIREMENT_GATE_BLOCKER_AFFECTED_CHECK_MISMATCH",
                        f"{blocker_id}: declared={sorted(affected_set)} actual={sorted(inbound)}",
                        path=path,
                    )
                )
            cross_group_checks = sorted(
                check_id
                for check_id in inbound
                if check_group_by_id.get(check_id)
                != blocker.get("primary_spec_ref")
            )
            if cross_group_checks:
                findings.append(
                    _finding(
                        "REQUIREMENT_GATE_BLOCKER_CROSS_GROUP",
                        f"{blocker_id} crosses Semantic Groups: {cross_group_checks}",
                        path=path,
                    )
                )
        elif inbound:
            findings.append(
                _finding(
                    "REQUIREMENT_GATE_BLOCKER_LIFECYCLE_INVALID",
                    f"{blocker_id} is not OPEN but still blocks current Checks",
                    path=path,
                )
            )
        for successor in blocker.get("replacement_refs", []):
            if successor == blocker_id or successor not in blockers_by_id:
                findings.append(
                    _finding(
                        "REQUIREMENT_GATE_BLOCKER_LIFECYCLE_INVALID",
                        f"{blocker_id} has invalid successor {successor}",
                        path=path,
                    )
                )

    if blockers_by_id:
        try:
            validate_id_lifecycle(blockers_by_id.values(), kind="Blocker")
        except ValueError as error:
            findings.append(
                _finding(
                    "REQUIREMENT_GATE_BLOCKER_LIFECYCLE_INVALID",
                    str(error),
                    path=path,
                )
            )

    missing_group_refs = known_spec_refs - seen_group_refs
    if missing_group_refs:
        findings.append(
            _finding(
                "REQUIREMENT_GATE_SPEC_REF_MISSING",
                f"missing Semantic Groups: {sorted(missing_group_refs)}",
                path=path,
            )
        )

    summary_counts = Counter(
        str(record.get("gate", ""))
        for record in raw_summary
        if isinstance(record, dict)
    )
    for gate in STANDARD_REQUIREMENT_GATES:
        if summary_counts[gate] == 0:
            findings.append(
                _finding(
                    "REQUIREMENT_GATE_SUMMARY_MISSING",
                    gate,
                    path=path,
                )
            )
        elif summary_counts[gate] > 1:
            findings.append(
                _finding(
                    "REQUIREMENT_GATE_SUMMARY_DUPLICATE",
                    gate,
                    path=path,
                )
            )
        app, reason = applicability[gate]
        matching_summary_records = [
            record
            for record in raw_summary
            if isinstance(record, dict) and record.get("gate") == gate
        ]
        for record in matching_summary_records:
            extra_summary_keys = _unexpected_keys(record, SUMMARY_KEYS)
            if extra_summary_keys:
                findings.append(
                    _finding(
                        "REQUIREMENT_GATE_LAYOUT_EXTRA_FIELD",
                        f"{gate} unexpected Summary fields: {extra_summary_keys}",
                        path=path,
                    )
                )
        if _has_placeholder(reason):
            findings.append(
                _finding(
                    "REQUIREMENT_GATE_PLACEHOLDER",
                    f"{gate} applicability reason contains a placeholder",
                    path=path,
                )
            )
        if app not in {"APPLICABLE", "NOT_APPLICABLE"}:
            findings.append(
                _finding(
                    "REQUIREMENT_GATE_APPLICABILITY_INVALID",
                    gate,
                    path=path,
                )
            )
        elif app == "NOT_APPLICABLE" and not _reason_has_current_spec_ref(
            reason, known_spec_refs
        ):
            findings.append(
                _finding(
                    "REQUIREMENT_GATE_APPLICABILITY_REASON_MISSING",
                    f"{gate} needs a concrete current Spec ref",
                    path=path,
                )
            )
        if app == "NOT_APPLICABLE" and any(
            check.get("gate") == gate for check in checks_by_id.values()
        ):
            findings.append(
                _finding(
                    "REQUIREMENT_GATE_NOT_APPLICABLE_HAS_CHECKS",
                    gate,
                    path=path,
                )
            )

    derived_summary = _derive_gate_summary(groups, applicability)
    if raw_summary != derived_summary:
        findings.append(
            _finding(
                "REQUIREMENT_GATE_SUMMARY_DRIFT",
                "Six-Gate Summary is not strictly derived from current Checks",
                path=path,
            )
        )

    derived_readiness = _derive_planning_readiness(
        spec_revision=spec_revision,
        current_spec_revision=current_spec_revision,
        gate_summary=derived_summary,
        groups=groups,
    )
    raw_readiness = bundle.get("planning_readiness")
    if isinstance(raw_readiness, dict):
        extra_readiness_keys = _unexpected_keys(raw_readiness, READINESS_KEYS)
        if extra_readiness_keys:
            findings.append(
                _finding(
                    "REQUIREMENT_GATE_LAYOUT_EXTRA_FIELD",
                    f"unexpected Planning Readiness fields: {extra_readiness_keys}",
                    path=path,
                )
            )
    if raw_readiness != derived_readiness:
        findings.append(
            _finding(
                "PLANNING_READINESS_DERIVATION_INVALID",
                "Planning Readiness is not strictly derived",
                path=path,
            )
        )
    if metadata.get("planning_readiness") != derived_readiness["status"]:
        findings.append(
            _finding(
                "PLANNING_READINESS_METADATA_DRIFT",
                "File Metadata Planning Readiness disagrees with derived state",
                path=path,
            )
        )
    if require_ready and derived_readiness["status"] != "PASS":
        findings.append(
            _finding(
                "REQUIREMENT_GATE_PREFLIGHT_BLOCKED",
                "all applicable Gates must PASS with zero open Blockers",
                path=path,
            )
        )

    return {
        "status": "PASS" if not findings else "BLOCKED",
        "findings": findings,
        "derived_gate_summary": derived_summary,
        "derived_planning_readiness": derived_readiness,
    }


def clarification_candidates(
    bundle: dict[str, Any],
    *,
    limit: int = 5,
    priority_by_blocker: Mapping[str, tuple[int, int]] | None = None,
) -> list[dict[str, Any]]:
    """Return at most five product questions, one per shared root cause."""

    if not isinstance(limit, int) or limit < 1 or limit > 5:
        raise ValueError("Clarify candidate limit must be between 1 and 5")
    if priority_by_blocker is not None and any(
        not isinstance(score, tuple)
        or len(score) != 2
        or not all(isinstance(value, int) and value >= 0 for value in score)
        for score in priority_by_blocker.values()
    ):
        raise ValueError("Clarify priority must be non-negative impact/uncertainty")

    candidates: list[dict[str, Any]] = []
    for group in bundle.get("semantic_groups", []):
        for blocker in group.get("blockers", []):
            if (
                blocker.get("status") == "OPEN"
                and blocker.get("class") == "product-decision"
            ):
                candidates.append(
                    {
                        "blocker_id": blocker["id"],
                        "spec_ref": blocker["primary_spec_ref"],
                        "semantic_key": blocker["semantic_key"],
                        "gap": blocker["gap"],
                        "affected_check_ids": list(blocker["affected_check_ids"]),
                    }
                )
    priorities = priority_by_blocker or {}
    candidates.sort(
        key=lambda candidate: (
            -(
                priorities.get(candidate["blocker_id"], (0, 0))[0]
                * priorities.get(candidate["blocker_id"], (0, 0))[1]
            ),
            candidate["blocker_id"],
        )
    )
    return candidates[:limit]


def reconcile_requirement_gate(
    bundle: dict[str, Any] | None,
    *,
    current_spec_revision: str,
    all_spec_refs: Iterable[str],
    current_evidence_by_check: Mapping[str, list[str]],
) -> dict[str, Any]:
    """Refresh all Check results and derived state after a Clarify Spec write.

    The caller supplies evidence from the current Spec.  This makes a stale
    Revision or zero-question closeout re-evaluate every Check instead of
    trusting prior PASS text.
    """

    if bundle is None:
        return {
            "updated": None,
            "status": "BLOCKED",
            "findings": [
                _finding(
                    "REQUIREMENT_GATE_MISSING",
                    "Clarify must not create the missing Gate",
                    path=CANONICAL_REQUIREMENT_GATE_PATH,
                )
            ],
            "candidates": [],
        }

    updated = deepcopy(bundle)
    raw_gate_summary = updated.get("gate_summary")
    summary_gates = (
        [
            record.get("gate")
            for record in raw_gate_summary
            if isinstance(record, dict)
        ]
        if isinstance(raw_gate_summary, list)
        else []
    )
    if (
        updated.get("path") != CANONICAL_REQUIREMENT_GATE_PATH
        or not isinstance(updated.get("metadata"), dict)
        or updated.get("metadata", {}).get("stage") != "requirements"
        or updated.get("metadata", {}).get("contract")
        != REQUIREMENT_GATE_CONTRACT
        or not isinstance(updated.get("semantic_groups"), list)
        or not isinstance(updated.get("gate_summary"), list)
        or Counter(summary_gates)
        != Counter({gate: 1 for gate in STANDARD_REQUIREMENT_GATES})
        or any(
            not isinstance(group, dict)
            or not group.get("spec_ref")
            or not isinstance(group.get("checks"), list)
            or not isinstance(group.get("blockers"), list)
            for group in updated.get("semantic_groups", [])
        )
    ):
        return {
            "updated": None,
            "status": "BLOCKED",
            "findings": [
                _finding(
                    "REQUIREMENT_GATE_MALFORMED",
                    "Clarify preserves malformed Canonical Layout unchanged",
                    path=CANONICAL_REQUIREMENT_GATE_PATH,
                )
            ],
            "candidates": [],
        }

    stored_revision = updated["metadata"].get("spec_revision")
    structural_result = inspect_requirement_gate_bundle(
        updated,
        current_spec_revision=(
            stored_revision if isinstance(stored_revision, str) else ""
        ),
        all_spec_refs=all_spec_refs,
    )
    repairable_derived_codes = {
        "REQUIREMENT_GATE_SUMMARY_DRIFT",
        "PLANNING_READINESS_DERIVATION_INVALID",
        "PLANNING_READINESS_METADATA_DRIFT",
    }
    structural_findings = [
        finding
        for finding in structural_result["findings"]
        if finding["code"] not in repairable_derived_codes
    ]
    if structural_findings:
        return {
            "updated": None,
            "status": "BLOCKED",
            "findings": [
                _finding(
                    "REQUIREMENT_GATE_MALFORMED",
                    "Clarify preserves malformed Canonical Layout unchanged",
                    path=CANONICAL_REQUIREMENT_GATE_PATH,
                ),
                *structural_findings,
            ],
            "candidates": [],
        }

    reconciliation_findings: list[dict[str, str]] = []
    for group in updated["semantic_groups"]:
        for check in group.get("checks", []):
            check_id = str(check.get("id", ""))
            evidence = current_evidence_by_check.get(check_id, [])
            if _non_empty_strings(evidence):
                check["status"] = "PASS"
                check["evidence_refs"] = list(evidence)
                check["blocker_ref"] = None
            else:
                check["status"] = "BLOCKED"
                check["evidence_refs"] = []
                if not check.get("blocker_ref"):
                    reconciliation_findings.append(
                        _finding(
                            "REQUIREMENT_GATE_RECONCILIATION_BLOCKER_REQUIRED",
                            f"{check_id} has no current evidence or root-cause Blocker",
                            path=CANONICAL_REQUIREMENT_GATE_PATH,
                        )
                    )

    if reconciliation_findings:
        return {
            "updated": None,
            "status": "BLOCKED",
            "findings": reconciliation_findings,
            "candidates": clarification_candidates(bundle),
        }

    for group in updated["semantic_groups"]:
        blockers_by_id = {
            blocker.get("id"): blocker for blocker in group.get("blockers", [])
        }
        inbound: dict[str, list[str]] = defaultdict(list)
        for check in group.get("checks", []):
            if check.get("status") == "BLOCKED" and check.get("blocker_ref"):
                inbound[str(check["blocker_ref"])].append(str(check["id"]))
        for blocker_id, blocker in blockers_by_id.items():
            affected = sorted(inbound.get(str(blocker_id), []))
            if affected:
                blocker["status"] = "OPEN"
                blocker["affected_check_ids"] = affected
            elif blocker.get("status") == "OPEN":
                blocker["status"] = "RESOLVED"
                blocker["affected_check_ids"] = []

    updated["metadata"]["spec_revision"] = current_spec_revision
    applicability = {
        record["gate"]: (
            record["applicability"],
            record.get("applicability_reason"),
        )
        for record in updated["gate_summary"]
        if isinstance(record, dict)
        and record.get("gate") in STANDARD_REQUIREMENT_GATES
    }
    for gate in STANDARD_REQUIREMENT_GATES:
        applicability.setdefault(gate, ("", None))
    updated["gate_summary"] = _derive_gate_summary(
        updated["semantic_groups"],
        applicability,
    )
    updated["planning_readiness"] = _derive_planning_readiness(
        spec_revision=current_spec_revision,
        current_spec_revision=current_spec_revision,
        gate_summary=updated["gate_summary"],
        groups=updated["semantic_groups"],
    )
    updated["metadata"]["planning_readiness"] = updated["planning_readiness"]["status"]

    unresolved_checks = sorted(
        check_id
        for group in updated["semantic_groups"]
        for check in group.get("checks", [])
        if check.get("status") == "BLOCKED"
        for check_id in [str(check.get("id", ""))]
    )
    findings = list(reconciliation_findings)
    if unresolved_checks:
        findings.append(
            _finding(
                "PLANNING_READINESS_BLOCKED",
                ", ".join(unresolved_checks),
                path=CANONICAL_REQUIREMENT_GATE_PATH,
            )
        )
    return {
        "updated": updated,
        "status": updated["planning_readiness"]["status"],
        "findings": findings,
        "candidates": clarification_candidates(updated),
    }


def preflight_requirement_gate(
    bundle: dict[str, Any] | None,
    *,
    current_spec_revision: str,
    all_spec_refs: Iterable[str],
) -> dict[str, Any]:
    """Read-only Plan preflight over the single authoritative bundle."""

    if bundle is None:
        return {
            "status": "BLOCKED",
            "write_count": 0,
            "hooks_started": False,
            "core_setup_started": False,
            "next_step": None,
            "findings": [
                _finding(
                    "REQUIREMENT_GATE_PREFLIGHT_BLOCKED",
                    "canonical Requirement Gate is missing",
                    path=CANONICAL_REQUIREMENT_GATE_PATH,
                )
            ],
        }
    result = inspect_requirement_gate_bundle(
        bundle,
        current_spec_revision=current_spec_revision,
        all_spec_refs=all_spec_refs,
        require_ready=True,
    )
    findings = list(result["findings"])
    if result["status"] == "BLOCKED" and not any(
        finding["code"] == "REQUIREMENT_GATE_PREFLIGHT_BLOCKED"
        for finding in findings
    ):
        smallest_reason = (
            findings[0]["code"] if findings else "unknown Requirement Gate failure"
        )
        findings.append(
            _finding(
                "REQUIREMENT_GATE_PREFLIGHT_BLOCKED",
                smallest_reason,
                path=CANONICAL_REQUIREMENT_GATE_PATH,
            )
        )
    return {
        "status": result["status"],
        "write_count": 0,
        "hooks_started": False,
        "core_setup_started": False,
        "next_step": (
            "CORE_PRE_EXECUTION_HOOKS" if result["status"] == "PASS" else None
        ),
        "findings": findings,
    }


def validate_id_lifecycle(
    records: Iterable[dict[str, Any]],
    *,
    kind: str,
) -> None:
    """Validate stable Spec or Blocker split/merge/retirement records."""

    rows = list(records)
    by_id = {str(row.get("id", "")): row for row in rows}
    if "" in by_id or len(by_id) != len(rows):
        raise ValueError(f"{kind} lifecycle IDs must be present and unique")

    normalized_kind = kind.casefold()
    if normalized_kind == "spec":
        allowed = {"ACTIVE", "REPLACED", "RETIRED", "NOT_APPLICABLE"}
        replacement_status = "REPLACED"
        no_successor_statuses = {"ACTIVE", "RETIRED", "NOT_APPLICABLE"}
        reason_statuses = {"RETIRED", "NOT_APPLICABLE"}
    elif normalized_kind == "blocker":
        allowed = {"OPEN", "RESOLVED", "RETIRED", "SUPERSEDED"}
        replacement_status = "SUPERSEDED"
        no_successor_statuses = {"OPEN", "RESOLVED", "RETIRED"}
        reason_statuses = {"RETIRED"}
    else:
        raise ValueError("kind must be Spec or Blocker")

    for item_id, row in by_id.items():
        status = row.get("status")
        if status not in allowed:
            raise ValueError(f"{kind} {item_id} has invalid lifecycle status")
        replacements = row.get("replacement_refs", [])
        if not isinstance(replacements, list):
            raise ValueError(f"{kind} {item_id} replacement refs must be a list")
        if status in no_successor_statuses and replacements:
            raise ValueError(f"{kind} {item_id} {status} cannot have replacements")
        if status == replacement_status and not replacements:
            raise ValueError(
                f"{kind} {item_id} {replacement_status} needs successor refs"
            )
        if status in reason_statuses and not str(
            row.get("reason", "")
        ).strip():
            raise ValueError(f"{kind} {item_id} retirement/N/A needs a reason")
        for replacement in replacements:
            if replacement not in by_id:
                raise ValueError(
                    f"{kind} {item_id} has unknown successor {replacement}"
                )
            if replacement == item_id:
                raise ValueError(f"{kind} {item_id} cannot replace itself")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(item_id: str) -> None:
        if item_id in visiting:
            raise ValueError(f"{kind} lifecycle contains a replacement cycle")
        if item_id in visited:
            return
        visiting.add(item_id)
        for successor in by_id[item_id].get("replacement_refs", []):
            visit(successor)
        visiting.remove(item_id)
        visited.add(item_id)

    for item_id in by_id:
        visit(item_id)
