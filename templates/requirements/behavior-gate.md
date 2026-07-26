# Behavior Requirement Gate

**Purpose**: Validate observable behavior and case coverage before behavior projection
**Stage**: requirements
**Domain**: behavior
**Gate**: planning-readiness
**Applicability**: APPLICABLE
**Status**: PASS | BLOCKED
**Spec Revision**: sha256:[SPEC_CONTENT_HASH]

## User Story Readiness

- [ ] CHK-BEH-001 [blocker:product-decision] [spec:STORY] Does each applicable story define observable acceptance behavior?

## Given / When / Then Readiness

- [ ] CHK-BEH-002 [blocker:product-decision] [spec:SECTION] Are roles, permissions, starting state, and required data explicit?
- [ ] CHK-BEH-003 [blocker:product-decision] [spec:SECTION] Is each trigger an executable user action, request case, or system event?
- [ ] CHK-BEH-004 [blocker:product-decision] [spec:SECTION] Does each outcome define feedback, business state, error semantics, or assertion intent?

## Case Coverage Matrix

One row per story or capability case type. Status:
`Required|Not Applicable|Unknown`. Each row has a stable Case ID. A Required
case cites its source `spec.md` section. Not Applicable requires rationale.
Unknown appears in Blocking Items.

| Case ID | Story/Capability | Case Type | Status | Source `spec.md` section | Blocking Item ID | Rationale |
|---|---|---|---|---|---|---|
| CASE-[STORY]-POS-001 | [story] | positive | Required | [section] | none | [reason] |
| CASE-[STORY]-NEG-001 | [story] | negative | Unknown | [section] | BLK-BEH-001 | [reason] |

Evaluate positive, negative, boundary, permission, validation, and
state_conflict case types. Scenario IDs and `case_coverage_blockers` are
assigned during `/speckit.plan`.

## Blocking Items

- none

<!-- Recompute by stable CASE/CHK ID. Never append stale blockers or duplicate
     Gate Status sections. -->
