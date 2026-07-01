# Behavior Testability Checklist

## User Story Readiness
- [ ] Each applicable user story has observable acceptance behavior.
- [ ] Each story identifies the actor or system responsible for the behavior.
- [ ] Each story has enough context to distinguish primary, alternate, and exception behavior when applicable.

## Acceptance Criteria Quality
- [ ] Acceptance criteria are observable and verifiable from `spec.md`.
- [ ] Acceptance criteria avoid implementation-only wording.
- [ ] Business rules include precise success, rejection, validation, permission, boundary, and state_conflict outcomes when applicable.

## Scenario Coverage
- [ ] Primary success behavior is covered.
- [ ] Alternate and exception behavior is covered when applicable.
- [ ] Boundary, permission, validation, and state_conflict behavior is covered when applicable.

## Case Coverage Matrix
For each user story or capability, record one row per story or capability case type. Status: Required|Not Applicable|Unknown.

| Case ID | Story/Capability | Case Type | Status | Source `spec.md` section | Blocking Item ID | Rationale |
| --- | --- | --- | --- | --- | --- | --- |
| CASE-PERMISSION-001 | Example | permission | Required | `spec.md#...` |  | reason |
| CASE-BOUNDARY-001 | Example | boundary | Not Applicable | `spec.md#...` |  | reason |
| CASE-VALIDATION-001 | Example | validation | Unknown | `spec.md#...` | BI-... | missing rule |

- [ ] Required case type must cite the source `spec.md` section.
- [ ] Each row must have a stable Case ID.
- [ ] Scenario IDs and `case_coverage_blockers` are assigned during `/speckit.plan`.
- [ ] Not Applicable requires rationale.
- [ ] Unknown must appear in Blocking Items.

## Given Readiness
- [ ] Required roles and permissions are explicit.
- [ ] Required starting state, entity state, and data are explicit enough for later fixture setup.
- [ ] Required data does not depend on production-only records.

## When Readiness
- [ ] Each trigger is an executable user action, request case, or system trigger.
- [ ] Required inputs, selections, uploads, and submitted values are explicit.

## Then Readiness
- [ ] Each outcome maps to user feedback, business state, error semantics, or assertion intent.
- [ ] Failure outcomes include precise feedback or error semantics.

## Non-Functional Requirement Readiness
- [ ] Performance - Status: Required|Not Applicable|Unknown; requirement or rationale is explicitly declared in `spec.md`.
- [ ] Security and Privacy - Status: Required|Not Applicable|Unknown; requirement or rationale is explicitly declared in `spec.md`.
- [ ] Reliability and Recovery - Status: Required|Not Applicable|Unknown; requirement or rationale is explicitly declared in `spec.md`.
- [ ] Accessibility - Status: Required|Not Applicable|Unknown; requirement or rationale is explicitly declared in `spec.md`.
- [ ] Compliance and Auditability - Status: Required|Not Applicable|Unknown; requirement or rationale is explicitly declared in `spec.md`.
- [ ] Observability - Status: Required|Not Applicable|Unknown; requirement or rationale is explicitly declared in `spec.md`.
- [ ] Compatibility - Status: Required|Not Applicable|Unknown; requirement or rationale is explicitly declared in `spec.md`.
- [ ] Data Lifecycle - Status: Required|Not Applicable|Unknown; requirement or rationale is explicitly declared in `spec.md`.
- [ ] Cost and Operational Constraints - Status: Required|Not Applicable|Unknown; requirement or rationale is explicitly declared in `spec.md`.
- [ ] Required NFR entries have verifiable product-level criteria without prescribing architecture.
- [ ] Unknown NFR entries that affect downstream design are listed as blocking items.

## Visual Fidelity Readiness
- [ ] Apply this section when `spec.md` contains `Visual & UI Specification`, visual requirements, visual SSOT refs, HTML SSOT refs, structured IR refs, external intake refs, provider evidence blockers, or provider-specific evidence requests. Also apply it when `spec.md` contains product-side visual requirements such as pixel-perfect, brand-critical, responsive visual, or UI visual acceptance requirements.
- [ ] `Visual & UI Specification` exists when a visual or UI surface applies; otherwise `spec.md` records a Not Applicable rationale.
- [ ] Every identified visual/UI requirement uses status `Required`, `Not Applicable`, `Unknown`, or `[BLOCKED: PROVIDER_EVIDENCE]`.
- [ ] Unknown visual/UI coverage status appears in Blocking Items when it affects downstream behavior projection or design.
- [ ] Required visual/UI requirements have observable requirement text in `spec.md`.
- [ ] Design-derived requirements identify the design source, provider source refs, and required fidelity.
- [ ] Visual requirements record external intake readiness status when cited, visual SSOT refs, HTML SSOT refs, structured IR refs, other evidence refs, and provider blocker status when provider evidence is required.
- [ ] Visual Fidelity Evidence Matrix rows cite source `spec.md` sections, traceability refs, readiness inputs, blocking item IDs, and accepted exception refs.
- [ ] Visual Fidelity Evidence Matrix is the only artifact that records visual planning readiness, provider blocker status, traceability refs, accepted exception refs, Gate Status, and Blocking Items.
- [ ] Visual Fidelity Evidence Matrix reads visual facts from `spec.md` and cited evidence refs; it does not call provider tools, re-extract external intake evidence, parse HTML SSOT bundles, re-parse structured IR artifacts, rebuild provider matrices, define visual validation work, or create another visual readiness path.
- [ ] Use one Visual Fidelity Evidence Matrix as the single visual readiness record; do not duplicate visual evidence decisions outside the matrix and Blocking Items.
- [ ] Do not add historical visual rules or alternate visual decision paths.

## Visual Fidelity Evidence Matrix

| Visual Item ID | Source `spec.md` section | Requirement Status | Depends on Provider Evidence | HTML SSOT Refs | Structured IR Refs | Other Evidence Refs | Readiness Input | Blocking Item ID | Accepted Exception Refs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| VIS-001 | `spec.md#...` | Required|Not Applicable|Unknown|[BLOCKED: PROVIDER_EVIDENCE] | yes|no | html-ssot/... or none | ir/... or none | provider/screenshot refs or none | ready|blocked|not-applicable | BI-... or none | EX-... or none |

- [ ] Requirement Status is declared for each visual requirement.
- [ ] Provider-dependent rows cite HTML SSOT refs, structured IR refs, visual SSOT refs, or other external intake artifact refs when available.
- [ ] Missing required provider or intake evidence sets Gate Status: BLOCKED, uses `[BLOCKED: PROVIDER_EVIDENCE]`, and lists the item in Blocking Items.
- [ ] Rows that do not depend on HTML SSOT, structured IR, or provider evidence are marked `Not Applicable` with rationale.
- [ ] Product decision gaps use `Unknown` or `[NEEDS CLARIFICATION]` only when product requirements are missing, not when provider evidence is unavailable.
- [ ] Responsive visual requirements block PASS only when required source-backed state or viewport evidence is missing for a feature that depends on provider evidence.
- [ ] Layout, spacing, typography, colors, effects, assets, and clipping requirements are explicit.
- [ ] Required client visual assets have source refs, asset source strategy, required variants, fallback policy, and blocker status.
- [ ] Required component mappings and variant coverage are explicit or marked as blocking clarification items.
- [ ] Default, hover, focus, active, disabled, loading, empty, and error states are explicit or marked as missing.
- [ ] Required breakpoints, reflow rules, scrolling, minimum widths, safe areas, and responsive behavior is explicit.
- [ ] Copy, icons, images, fonts, numeric formats, and placeholder content are explicit.
- [ ] Keyboard, focus, semantics, contrast, ARIA, form error behavior, and accessibility requirements are explicit.
- [ ] Accepted exceptions are defined as traceable exception refs and rationale.

## Gate Status
Gate Status: PASS|BLOCKED
Blocking Items:
- none
