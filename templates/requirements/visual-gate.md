# Visual Requirement Gate

**Purpose**: Validate visual/UI requirements and cited evidence before planning
**Stage**: requirements
**Domain**: visual
**Gate**: planning-readiness
**Applicability**: APPLICABLE | NOT_APPLICABLE
**Status**: PASS | BLOCKED
**Spec Revision**: sha256:[SPEC_CONTENT_HASH]
**Applicability Reason**: [Required when NOT_APPLICABLE]

## Visual Fidelity Readiness

Every identified visual/UI requirement uses `Required`, `Not Applicable`,
`Unknown`, or `[BLOCKED: PROVIDER_EVIDENCE]`. Required items need observable
requirement text. Unknown items become product-decision blockers. Provider
evidence gaps remain intake blockers and are never converted to clarification.

## Visual Fidelity Evidence Matrix

This is the single visual planning-readiness record.

| Visual Item ID | Source `spec.md` section | Requirement Status | Provider Evidence Dependency | Visual SSOT Refs | HTML SSOT Refs | Structured IR Refs | Other Evidence Refs | Readiness Input | Blocking Item ID | Accepted Exception Refs |
|---|---|---|---|---|---|---|---|---|---|---|
| VIS-001 | [section] | [status] | [yes/no] | [refs] | [refs] | [refs] | [refs] | [input] | [id/none] | [refs/none] |

Record state, responsive, accessibility, component mapping, asset/fallback, and
accepted-exception coverage when applicable. Responsive visual requirements
block PASS only when required source-backed state or viewport evidence is
missing for a feature that depends on provider evidence.

Do not call provider tools, re-parse provider artifacts, define screenshot
comparison, visual diff, baseline capture, or final visual review.

## Blocking Items

- none
