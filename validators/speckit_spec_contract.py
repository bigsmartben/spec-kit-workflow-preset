"""Pure in-memory validation for the feature-local UI specification contract."""
from __future__ import annotations

from typing import Any, Iterable


SOURCE_ROLES = {
    "requirement-input",
    "visual-input",
    "technical-evidence",
    "context-only",
}
UI_REQUIREMENT_PREFIXES = ("UI-", "VIS-")
UI_KINDS = {
    "content",
    "structure",
    "interaction",
    "state",
    "responsive",
    "accessibility",
    "visual",
    "asset",
    "restoration",
}
DERIVATIONS = {"observed", "derived", "assumed", "unresolved", "conflicting"}
EVIDENCE_DIMENSIONS = {
    "content",
    "structure",
    "surface",
    "state",
    "viewport",
    "interaction",
    "responsive",
    "accessibility",
    "visual",
    "asset",
    "restoration",
}
KIND_EVIDENCE_DIMENSION = {
    "content": "content",
    "structure": "structure",
    "interaction": "interaction",
    "state": "state",
    "responsive": "responsive",
    "accessibility": "accessibility",
    "visual": "visual",
    "asset": "asset",
    "restoration": "restoration",
}
RESTORATION_DIMENSIONS = {
    "content",
    "information-structure",
    "visual-appearance",
    "interaction-feedback",
    "ui-states",
    "responsive-viewports",
    "accessibility",
    "asset-identity-substitution",
}
FIDELITY_MODES = {
    "pixel-exact",
    "pixel-tolerant",
    "perceptual-equivalent",
    "structural-only",
}
PIXEL_VISUAL_DIMENSIONS = {
    "geometry-sizing-spacing-alignment-flow",
    "overflow-and-clipping",
    "typography",
    "color-border-radius-shadow-opacity-effects",
    "asset-identity-variant-crop-aspect-fitting",
    "layering-stacking-fixed-sticky-occlusion",
}
RENDERING_CONTEXT_FIELDS = {"fonts", "color_mode", "locale", "platform"}
TARGET_CONTEXT_FIELDS = {"window_or_device", "input", "accessibility", "locale"}
PROHIBITED_REQUIREMENT_FIELDS = {
    "dom_structure",
    "css_structure",
    "framework_component",
    "widget_class",
    "code_property",
    "resource_path",
    "capture_method",
    "comparison_method",
    "implementation_strategy",
}
ADAPTATION_MODES = {
    "framework-equivalent",
    "native-adaptive",
    "brand-preserving-native",
    "visual-equivalent-native",
}
ADAPTATION_DECISIONS = {"preserve", "adapt", "add", "omit", "clarify", "blocked"}
ADAPTATION_DIMENSIONS = {
    "content-and-information-hierarchy",
    "task-flow-and-navigation",
    "surface-and-component-role",
    "ui-state-and-feedback",
    "geometry-and-composition",
    "typography",
    "color-effects-and-brand",
    "assets-and-variants",
    "input-modality-and-gestures",
    "responsive-adaptive-layout",
    "system-ui-and-safe-regions",
    "accessibility-and-user-scaling",
    "localization-and-layout-direction",
}
CONFLICT_PRECEDENCE = [
    "target-hard-constraints-and-accessibility",
    "explicit-product-requirements",
    "adaptation-policy-and-dimension-decisions",
    "source-backed-ui-evidence",
    "target-platform-defaults",
    "implementation-preference",
]


def _duplicates(values: Iterable[str]) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return duplicates


def _require_list(item: dict[str, Any], field: str, context: str) -> list[Any]:
    value = item.get(field)
    if not isinstance(value, list) or not value:
        raise ValueError(f"{context} missing non-empty {field}")
    return value


def _blocked(item: dict[str, Any]) -> bool:
    return str(item.get("status", "")).upper() == "BLOCKED"


def _require_blocker(item: dict[str, Any], context: str) -> None:
    if not _blocked(item) or not item.get("blocker"):
        raise ValueError(f"{context} must remain BLOCKED with a stable blocker")


def _validate_evidence_locators(
    locators: Iterable[Any],
    source_refs: Iterable[str],
    sources_by_id: dict[str, dict[str, Any]],
    context: str,
) -> None:
    supplied_facts = {
        str(fact)
        for source_ref in source_refs
        for fact in sources_by_id[source_ref].get("supplied_facts", [])
    }
    unsupported = set(map(str, locators)) - supplied_facts
    if unsupported:
        raise ValueError(
            f"{context} evidence locator is not present in supplied source facts: "
            f"{sorted(unsupported)[0]}"
        )


def _validate_sources(
    sources: list[dict[str, Any]],
    requirement_ids: set[str],
) -> dict[str, dict[str, Any]]:
    source_ids = [str(source.get("ref", "")) for source in sources]
    if any(not source_id.startswith("SRC-") for source_id in source_ids):
        raise ValueError("source refs must use SRC-*")
    duplicates = _duplicates(source_ids)
    if duplicates:
        raise ValueError(f"duplicate source ref: {sorted(duplicates)[0]}")

    sources_by_id = dict(zip(source_ids, sources))
    for source_id, source in sources_by_id.items():
        if source.get("role") not in SOURCE_ROLES:
            raise ValueError(f"{source_id} has invalid source role")
        if not source.get("locator_or_description"):
            raise ValueError(f"{source_id} missing opaque locator/description")
        if not source.get("bounded_scope"):
            raise ValueError(f"{source_id} missing bounded feature scope")

        projected_refs = source.get("projected_refs")
        if not isinstance(projected_refs, list):
            raise ValueError(f"{source_id} projected_refs must be a list")
        supplied_facts = source.get("supplied_facts")
        if not isinstance(supplied_facts, list):
            raise ValueError(f"{source_id} supplied_facts must be a list")
        if projected_refs and not supplied_facts:
            raise ValueError(
                f"{source_id} locator alone cannot support requirement projection"
            )
        if not supplied_facts:
            if projected_refs:
                raise ValueError(f"{source_id} missing evidence cannot project requirements")
            if not _blocked(source) or source.get("blocker") != "SRC_EVIDENCE_MISSING":
                raise ValueError(
                    f"{source_id} locator-only input must use SRC_EVIDENCE_MISSING"
                )
        elif projected_refs and source.get("status") != "projected":
            raise ValueError(f"{source_id} projected refs require projected status")
        elif not projected_refs and source.get("status") not in {
            "retained",
            "context-only",
            "BLOCKED",
        }:
            raise ValueError(f"{source_id} has invalid non-projecting status")
        if _blocked(source) and not source.get("blocker"):
            raise ValueError(f"{source_id} BLOCKED source lacks stable blocker")

        missing_refs = set(map(str, projected_refs)) - requirement_ids
        if missing_refs:
            raise ValueError(
                f"{source_id} projects unknown requirement: {sorted(missing_refs)[0]}"
            )
        normative_refs = [
            str(ref)
            for ref in projected_refs
            if str(ref).startswith(("FR-", "NFR-", "UX-", "UI-", "VIS-"))
        ]
        role = source["role"]
        if role in {"technical-evidence", "context-only"} and normative_refs:
            raise ValueError(f"{source_id} role cannot project normative requirements")
        if role == "visual-input" and any(
            not ref.startswith(UI_REQUIREMENT_PREFIXES) for ref in normative_refs
        ):
            raise ValueError(f"{source_id} visual-input projects unrelated requirement")

    return sources_by_id


def _validate_requirements(
    requirements: list[dict[str, Any]],
    sources_by_id: dict[str, dict[str, Any]],
) -> None:
    requirement_ids = [str(requirement.get("id", "")) for requirement in requirements]
    if any(not requirement_id.startswith(UI_REQUIREMENT_PREFIXES) for requirement_id in requirement_ids):
        raise ValueError("UI specification requirement ids must use UI-* or VIS-*")
    duplicates = _duplicates(requirement_ids)
    if duplicates:
        raise ValueError(f"duplicate UI requirement id: {sorted(duplicates)[0]}")

    requirements_by_id = dict(zip(requirement_ids, requirements))
    observed_ids = {
        requirement_id
        for requirement_id, requirement in requirements_by_id.items()
        if requirement.get("derivation") == "observed"
    }
    for requirement_id, requirement in requirements_by_id.items():
        prohibited_fields = sorted(set(requirement) & PROHIBITED_REQUIREMENT_FIELDS)
        if prohibited_fields:
            raise ValueError(
                f"{requirement_id} contains implementation/source-unsupported field: "
                f"{prohibited_fields[0]}"
            )
        if requirement.get("kind") not in UI_KINDS:
            raise ValueError(f"{requirement_id} has invalid requirement kind")
        for field in ("statement", "surface", "state", "viewport"):
            if not requirement.get(field):
                raise ValueError(f"{requirement_id} missing {field}")
        if not _blocked(requirement) and not requirement.get("acceptance"):
            raise ValueError(f"{requirement_id} missing acceptance")
        if requirement.get("outcome_only") is not True:
            raise ValueError(
                f"{requirement_id} must define an observable outcome, not implementation"
            )

        source_refs = list(map(str, _require_list(requirement, "source_refs", requirement_id)))
        missing_sources = set(source_refs) - set(sources_by_id)
        if missing_sources:
            raise ValueError(
                f"{requirement_id} references unknown source: {sorted(missing_sources)[0]}"
            )
        for source_ref in source_refs:
            if requirement_id not in sources_by_id[source_ref]["projected_refs"]:
                raise ValueError(
                    f"{requirement_id} missing reciprocal projection from {source_ref}"
                )

        derivation = requirement.get("derivation")
        if derivation not in DERIVATIONS:
            raise ValueError(f"{requirement_id} has invalid derivation")
        evidence_locators = requirement.get("evidence_locators")
        if not isinstance(evidence_locators, list):
            raise ValueError(f"{requirement_id} evidence_locators must be a list")
        if derivation in {"observed", "derived"} and not evidence_locators:
            raise ValueError(f"{requirement_id} lacks cited supplied evidence")
        if derivation in {"observed", "derived"}:
            _validate_evidence_locators(
                evidence_locators,
                source_refs,
                sources_by_id,
                requirement_id,
            )
            evidence_support = set(
                map(
                    str,
                    _require_list(requirement, "evidence_support", requirement_id),
                )
            )
            if not evidence_support.issubset(EVIDENCE_DIMENSIONS):
                raise ValueError(f"{requirement_id} has invalid evidence support")
            required_support = {"surface", "state", "viewport"}
            required_support.add(KIND_EVIDENCE_DIMENSION[str(requirement["kind"])])
            missing_support = required_support - evidence_support
            if missing_support:
                raise ValueError(
                    f"{requirement_id} lacks corresponding evidence for "
                    f"{sorted(missing_support)[0]}"
                )
        if derivation == "derived":
            derived_from = set(
                map(str, _require_list(requirement, "derived_from", requirement_id))
            )
            valid_derivation_inputs = set(map(str, evidence_locators)) | observed_ids
            if not derived_from.issubset(valid_derivation_inputs):
                raise ValueError(
                    f"{requirement_id} derived_from does not cite an observation"
                )
        if derivation == "assumed" and not requirement.get("assumption"):
            raise ValueError(f"{requirement_id} assumed requirement lacks documented default")
        if derivation == "conflicting" and len(evidence_locators) < 2:
            raise ValueError(f"{requirement_id} conflicting requirement needs two locators")
        if derivation in {"unresolved", "conflicting"}:
            _require_blocker(requirement, requirement_id)
        elif _blocked(requirement):
            _require_blocker(requirement, requirement_id)
        elif requirement.get("status") != "specified":
            raise ValueError(f"{requirement_id} has invalid status")


def _validate_restoration(
    payload: dict[str, Any],
    requirement_ids: set[str],
    sources_by_id: dict[str, dict[str, Any]],
) -> None:
    if not payload.get("restoration_requested"):
        return
    rows = payload.get("restoration_dimensions")
    if not isinstance(rows, list):
        raise ValueError("restoration requires a dimension matrix")
    dimensions = [str(row.get("dimension", "")) for row in rows]
    if set(dimensions) != RESTORATION_DIMENSIONS or len(dimensions) != len(
        RESTORATION_DIMENSIONS
    ):
        raise ValueError("restoration dimension matrix is incomplete or duplicated")
    for row in rows:
        context = f"restoration dimension {row['dimension']}"
        refs = set(map(str, _require_list(row, "requirement_refs", context)))
        if not refs.issubset(requirement_ids):
            raise ValueError(f"{context} references unknown UI/VIS requirement")
        status = str(row.get("status", ""))
        if status == "required":
            if not row.get("acceptance"):
                raise ValueError(f"{context} missing measurable acceptance")
            row_source_refs = list(
                map(str, _require_list(row, "source_refs", context))
            )
            if not set(row_source_refs).issubset(set(sources_by_id)):
                raise ValueError(f"{context} references unknown source")
            evidence_locators = _require_list(row, "evidence_locators", context)
            _validate_evidence_locators(
                evidence_locators,
                row_source_refs,
                sources_by_id,
                context,
            )
        elif status == "not-applicable":
            if not row.get("rationale"):
                raise ValueError(f"{context} N/A missing rationale")
        elif status == "BLOCKED":
            _require_blocker(row, context)
        else:
            raise ValueError(f"{context} has invalid status")


def _validate_pixel_profiles(
    payload: dict[str, Any],
    requirement_ids: set[str],
    sources_by_id: dict[str, dict[str, Any]],
) -> None:
    source_ids = set(sources_by_id)
    profiles = payload.get("pixel_profiles", [])
    targets = payload.get("pixel_targets", [])
    exceptions = payload.get("pixel_exceptions", [])
    if not all(isinstance(items, list) for items in (profiles, targets, exceptions)):
        raise ValueError("pixel profile structures must be lists")

    profile_ids = [str(profile.get("id", "")) for profile in profiles]
    target_ids = [str(target.get("id", "")) for target in targets]
    exception_ids = [str(exception.get("id", "")) for exception in exceptions]
    if _duplicates(profile_ids) or _duplicates(target_ids) or _duplicates(exception_ids):
        raise ValueError("pixel restoration ids must be unique")
    if any(not item.startswith("PXR-") for item in profile_ids):
        raise ValueError("pixel profile ids must use PXR-*")
    if any(not item.startswith("PXT-") for item in target_ids):
        raise ValueError("pixel target ids must use PXT-*")
    if any(not item.startswith("PEX-") for item in exception_ids):
        raise ValueError("pixel exception ids must use PEX-*")

    targets_by_id = dict(zip(target_ids, targets))
    exceptions_by_id = dict(zip(exception_ids, exceptions))
    profiles_by_id = dict(zip(profile_ids, profiles))
    for profile_id, profile in zip(profile_ids, profiles):
        profile_blocked = _blocked(profile)
        if profile_blocked:
            _require_blocker(profile, profile_id)
        elif profile.get("status") != "specified":
            raise ValueError(f"{profile_id} has invalid status")
        mode = profile.get("fidelity_mode")
        if mode is not None and mode not in FIDELITY_MODES:
            raise ValueError(f"{profile_id} has invalid fidelity mode")
        if not profile_blocked and mode not in FIDELITY_MODES:
            raise ValueError(f"{profile_id} missing fidelity mode")
        for field in ("scope", "exception_policy"):
            if not profile_blocked and not profile.get(field):
                raise ValueError(f"{profile_id} missing {field}")
        refs = set(map(str, _require_list(profile, "requirement_refs", profile_id)))
        if not refs.issubset(requirement_ids):
            raise ValueError(f"{profile_id} references unknown UI/VIS requirement")
        profile_sources = set(map(str, _require_list(profile, "source_refs", profile_id)))
        if not profile_sources.issubset(source_ids):
            raise ValueError(f"{profile_id} references unknown source")
        declared_targets = list(map(str, _require_list(profile, "target_refs", profile_id)))
        declared_exceptions = profile.get("exception_refs")
        if not isinstance(declared_exceptions, list):
            raise ValueError(f"{profile_id} exception_refs must be a list")
        if not set(map(str, declared_exceptions)).issubset(set(exception_ids)):
            raise ValueError(f"{profile_id} references unknown accepted exception")
        if len(declared_targets) != len(set(declared_targets)):
            raise ValueError(f"{profile_id} target matrix contains duplicates")
        missing_targets = set(declared_targets) - set(targets_by_id)
        if missing_targets:
            raise ValueError(f"{profile_id} target matrix references unknown target")
        actual_targets = {
            target_id
            for target_id, target in targets_by_id.items()
            if target.get("profile_id") == profile_id
        }
        if set(declared_targets) != actual_targets:
            raise ValueError(f"{profile_id} target matrix is incomplete")
        has_blocked_target = any(
            _blocked(targets_by_id[target_ref]) for target_ref in declared_targets
        )
        if has_blocked_target and not _blocked(profile):
            raise ValueError(f"{profile_id} must be BLOCKED while a target is blocked")
        target_matrix = _require_list(profile, "target_matrix", profile_id)
        matrix_by_ref = {
            str(row.get("target_ref")): (
                str(row.get("surface")),
                str(row.get("state")),
                str(row.get("viewport")),
            )
            for row in target_matrix
            if isinstance(row, dict)
        }
        if set(matrix_by_ref) != set(declared_targets):
            raise ValueError(f"{profile_id} applicable target matrix is incomplete")
        if len(set(matrix_by_ref.values())) != len(matrix_by_ref):
            raise ValueError(f"{profile_id} applicable target matrix is duplicated")
        for target_ref, expected_coordinates in matrix_by_ref.items():
            actual_target = targets_by_id[target_ref]
            actual_coordinates = (
                str(actual_target.get("surface")),
                str(actual_target.get("state")),
                str(actual_target.get("viewport")),
            )
            if actual_coordinates != expected_coordinates:
                raise ValueError(f"{profile_id} target matrix coordinates do not resolve")

    for target_id, target in targets_by_id.items():
        context = f"pixel target {target_id}"
        for field in ("profile_id", "surface", "state", "viewport"):
            if not target.get(field):
                raise ValueError(f"{context} missing {field}")
        if target.get("profile_id") not in profile_ids:
            raise ValueError(f"{context} references unknown profile")
        if _blocked(target):
            _require_blocker(target, context)
            continue
        for field in (
            "device_pixel_ratio",
            "baseline_locator",
            "acceptance_envelope",
        ):
            if not target.get(field):
                raise ValueError(f"{context} missing {field}")
        rendering_context = target.get("rendering_context")
        if not isinstance(rendering_context, dict) or set(rendering_context) != (
            RENDERING_CONTEXT_FIELDS
        ):
            raise ValueError(f"{context} has incomplete rendering_context")
        if any(not value for value in rendering_context.values()):
            raise ValueError(f"{context} has empty rendering_context constraint")
        visual_dimensions = target.get("visual_dimensions")
        if not isinstance(visual_dimensions, dict) or set(visual_dimensions) != (
            PIXEL_VISUAL_DIMENSIONS
        ):
            raise ValueError(f"{context} has incomplete visual_dimensions")
        if any(not value for value in visual_dimensions.values()):
            raise ValueError(f"{context} has empty visual dimension outcome")
        if target.get("baseline_source_ref") not in source_ids:
            raise ValueError(f"{context} lacks one resolvable baseline source")
        profile = profiles_by_id[str(target["profile_id"])]
        if target.get("baseline_source_ref") not in profile["source_refs"]:
            raise ValueError(f"{context} baseline source is outside its profile")
        _validate_evidence_locators(
            [target["baseline_locator"]],
            [str(target["baseline_source_ref"])],
            sources_by_id,
            context,
        )
        fidelity_mode = target.get("fidelity_mode")
        if fidelity_mode not in FIDELITY_MODES:
            raise ValueError(f"{context} has invalid fidelity mode")
        if fidelity_mode != profile.get("fidelity_mode"):
            raise ValueError(f"{context} fidelity mode differs from its profile")
        envelope = target.get("acceptance_envelope")
        if not isinstance(envelope, dict):
            raise ValueError(f"{context} acceptance_envelope must be structured")
        expected_envelope_kinds = {
            "pixel-exact": {"equality"},
            "pixel-tolerant": {"per-channel", "per-pixel", "aggregate"},
            "perceptual-equivalent": {"perceptual"},
            "structural-only": {"structural"},
        }
        if envelope.get("kind") not in expected_envelope_kinds[str(fidelity_mode)]:
            raise ValueError(f"{context} acceptance envelope mismatches fidelity mode")
        if "threshold" not in envelope:
            raise ValueError(f"{context} acceptance envelope lacks threshold")
        if fidelity_mode in {"perceptual-equivalent", "structural-only"} and not envelope.get(
            "metric"
        ):
            raise ValueError(f"{context} acceptance envelope lacks metric")
        if fidelity_mode == "pixel-exact" and envelope.get("threshold") != 0:
            raise ValueError(f"{context} pixel-exact threshold must be zero")
        exception_refs = target.get("exception_refs")
        if not isinstance(exception_refs, list):
            raise ValueError(f"{context} exception_refs must be a list")
        unknown_exceptions = set(map(str, exception_refs)) - set(exceptions_by_id)
        if unknown_exceptions:
            raise ValueError(f"{context} references unknown accepted exception")
        if not set(map(str, exception_refs)).issubset(
            set(map(str, profile["exception_refs"]))
        ):
            raise ValueError(f"{context} exception is outside its profile policy")
        if target.get("derivation") not in {"observed", "derived"}:
            raise ValueError(f"{context} must be source-backed or BLOCKED")
        if target.get("status") != "specified":
            raise ValueError(f"{context} has invalid status")

    for exception_id, exception in exceptions_by_id.items():
        context = f"pixel exception {exception_id}"
        for field in ("region", "reason", "allowed_divergence", "bound"):
            if not exception.get(field):
                raise ValueError(f"{context} missing {field}")
        target_refs = set(map(str, _require_list(exception, "target_refs", context)))
        if not target_refs.issubset(set(target_ids)):
            raise ValueError(f"{context} references unknown target")
        refs = set(map(str, _require_list(exception, "requirement_refs", context)))
        if not refs.issubset(requirement_ids):
            raise ValueError(f"{context} references unknown UI/VIS requirement")
        exception_sources = set(
            map(str, _require_list(exception, "source_refs", context))
        )
        if not exception_sources.issubset(source_ids):
            raise ValueError(f"{context} references unknown source")

    if payload.get("pixel_restoration_requested") and not profiles:
        raise ValueError(
            "pixel restoration request needs a stable specified or blocked profile"
        )


def _validate_adaptation(
    payload: dict[str, Any],
    requirement_ids: set[str],
    source_ids: set[str],
) -> None:
    policies = payload.get("adaptation_policies", [])
    if not isinstance(policies, list):
        raise ValueError("adaptation_policies must be a list")
    if payload.get("cross_platform_restoration_requested") and not policies:
        raise ValueError("cross-platform restoration requires an adaptation policy")

    policy_ids = [str(policy.get("id", "")) for policy in policies]
    if _duplicates(policy_ids):
        raise ValueError("adaptation policy ids must be unique")
    for policy_id, policy in zip(policy_ids, policies):
        if _blocked(policy):
            _require_blocker(policy, policy_id)
        elif policy.get("status") != "specified":
            raise ValueError(f"{policy_id} has invalid status")
        if not policy_id.startswith("ADP-"):
            raise ValueError("adaptation policy ids must use ADP-*")
        source_platform = policy.get("source_platform")
        target_platform = policy.get("target_platform")
        if not source_platform or not target_platform:
            raise ValueError(f"{policy_id} missing source or target platform")
        if str(target_platform).casefold() == "swift":
            raise ValueError(f"{policy_id} Swift alone is not a target platform")
        if policy.get("mode") not in ADAPTATION_MODES:
            raise ValueError(f"{policy_id} has invalid adaptation mode")
        mode = str(policy["mode"])
        source_platform_normalized = str(source_platform).casefold()
        target_platform_normalized = str(target_platform).casefold()
        web_platforms = {"html", "html/web", "web"}
        if mode == "framework-equivalent" and (
            source_platform_normalized not in web_platforms
            or target_platform_normalized not in web_platforms
        ):
            raise ValueError(
                f"{policy_id} framework-equivalent requires HTML/Web endpoints"
            )
        if (
            target_platform_normalized in {"android", "ios", "ipados"}
            and mode != "brand-preserving-native"
            and not policy.get("mode_override_reason")
        ):
            raise ValueError(
                f"{policy_id} native mode override requires an explicit reason"
            )
        target_contexts = policy.get("target_contexts")
        if not isinstance(target_contexts, dict) or set(target_contexts) != (
            TARGET_CONTEXT_FIELDS
        ):
            raise ValueError(f"{policy_id} has incomplete target contexts")
        if any(not value for value in target_contexts.values()):
            raise ValueError(f"{policy_id} has empty target context")
        policy_sources = set(map(str, _require_list(policy, "source_refs", policy_id)))
        if not policy_sources.issubset(source_ids):
            raise ValueError(f"{policy_id} references unknown source")
        if policy.get("conflict_precedence") != CONFLICT_PRECEDENCE:
            raise ValueError(f"{policy_id} has invalid conflict precedence")

        decisions = policy.get("decisions")
        if not isinstance(decisions, list):
            raise ValueError(f"{policy_id} missing dimension decisions")
        dimensions = [str(decision.get("dimension", "")) for decision in decisions]
        if set(dimensions) != ADAPTATION_DIMENSIONS or len(dimensions) != len(
            ADAPTATION_DIMENSIONS
        ):
            raise ValueError(f"{policy_id} dimension decisions are incomplete or duplicated")
        for decision in decisions:
            dimension = str(decision["dimension"])
            context = f"{policy_id}/{dimension}"
            value = decision.get("decision")
            if value not in ADAPTATION_DECISIONS:
                raise ValueError(f"{context} has invalid adaptation decision")
            requirement_refs = set(
                map(str, _require_list(decision, "requirement_refs", context))
            )
            if not requirement_refs.issubset(requirement_ids):
                raise ValueError(f"{context} references unknown UI/VIS requirement")
            if value in {"adapt", "add", "omit"}:
                cited_sources = set(map(str, decision.get("source_refs", [])))
                if not cited_sources.issubset(source_ids):
                    raise ValueError(f"{context} references unknown source")
                if not cited_sources and not decision.get("hard_constraint_refs"):
                    raise ValueError(
                        f"{context} must cite source evidence or a target hard constraint"
                    )
            if value in {"clarify", "blocked"}:
                _require_blocker(decision, context)
            if decision.get("hard_constraint_conflict") and value not in {
                "adapt",
                "add",
                "omit",
                "blocked",
            }:
                raise ValueError(
                    f"{context} lets lower-priority evidence override a hard constraint"
                )

        has_blocked_decision = any(_blocked(decision) for decision in decisions)
        if has_blocked_decision and not _blocked(policy):
            raise ValueError(f"{policy_id} must be BLOCKED while a decision is blocked")
        if _blocked(policy) and not has_blocked_decision:
            raise ValueError(f"{policy_id} BLOCKED policy has no blocked decision")

        if mode == "framework-equivalent":
            divergent = [
                decision["dimension"]
                for decision in decisions
                if decision["decision"] not in {"preserve", "clarify", "blocked"}
            ]
            if divergent:
                raise ValueError(
                    f"{policy_id} framework-equivalent diverges at {divergent[0]}"
                )

        if target_platform_normalized in {"android", "ios", "ipados"}:
            by_dimension = {
                decision["dimension"]: decision["decision"] for decision in decisions
            }
            for invariant in (
                "content-and-information-hierarchy",
                "task-flow-and-navigation",
                "ui-state-and-feedback",
                "color-effects-and-brand",
            ):
                if by_dimension[invariant] not in {"preserve", "blocked", "clarify"}:
                    raise ValueError(
                        f"{policy_id} native target fails to preserve {invariant}"
                    )


def validate_ui_specification_contract(payload: dict[str, Any]) -> None:
    """Validate source-backed UI, restoration, pixel, and adaptation structures."""

    requirements = payload.get("requirements")
    sources = payload.get("sources")
    if not isinstance(requirements, list) or not requirements:
        raise ValueError("UI specification must include requirements")
    if not isinstance(sources, list) or not sources:
        raise ValueError("UI specification must include sources")

    requirement_ids = {
        str(requirement.get("id", "")) for requirement in requirements
    }
    all_spec_requirement_refs = payload.get("all_spec_requirement_refs")
    if not isinstance(all_spec_requirement_refs, list) or not all_spec_requirement_refs:
        raise ValueError(
            "UI specification must include all_spec_requirement_refs"
        )
    all_requirement_ids = list(map(str, all_spec_requirement_refs))
    if _duplicates(all_requirement_ids):
        raise ValueError("all_spec_requirement_refs contains duplicates")
    if not requirement_ids.issubset(set(all_requirement_ids)):
        raise ValueError(
            "all_spec_requirement_refs omits a UI/VIS requirement"
        )
    sources_by_id = _validate_sources(sources, set(all_requirement_ids))
    _validate_requirements(requirements, sources_by_id)
    _validate_restoration(payload, requirement_ids, sources_by_id)
    _validate_pixel_profiles(payload, requirement_ids, sources_by_id)
    _validate_adaptation(payload, requirement_ids, set(sources_by_id))
