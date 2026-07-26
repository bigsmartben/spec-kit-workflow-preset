---
description: Wrap core checklist generation with multi-domain requirement gates.
strategy: wrap
---

## Multi-Domain Requirement Gate

This wrapper extends the core spec-only checklist contract. It must not read
`plan.md` or `tasks.md`, create planning artifacts, redefine extension hooks,
or introduce a new command.

Use `$ARGUMENTS` only to prioritize requirement-quality focus. The standard
domain evaluation is always:

| Domain | Output | Template |
|---|---|---|
| requirements | `checklists/requirements.md` | core baseline |
| behavior | `checklists/behavior.md` | `requirement-behavior-gate-template` |
| UX | `checklists/ux.md` | `requirement-domain-gate-template` |
| security | `checklists/security.md` | `requirement-domain-gate-template` |
| NFR | `checklists/nfr.md` | `requirement-nfr-gate-template` |
| visual | `checklists/visual.md` | `requirement-visual-gate-template` |

Every standard domain must be written as `APPLICABLE` or
`NOT_APPLICABLE` with a concrete reason. Every file uses the core
`Stage/Domain/Gate/Applicability/Status/Spec Revision` metadata contract.
Planning Readiness is aggregated in memory; do not create
`planning-readiness.md`.

The legacy `checklists/behavior-testability.md` is not an input or output of
this command. Preserve an existing legacy file for migration history but never
update it or treat it as a current Gate.

## Behavior Requirement Gate

Write behavior requirement quality and the Case Coverage Matrix to
`checklists/behavior.md`.

- Evaluate user-story readiness, observable acceptance behavior, and Given,
  When, and Then requirement readiness.
- Use one row per story/capability and case type.
- Cover positive, negative, boundary, permission, validation, and
  state_conflict.
- Use stable Case IDs.
- Status is `Required|Not Applicable|Unknown`.
- Required rows cite a `spec.md` section.
- Not Applicable requires rationale.
- Unknown becomes `[blocker:product-decision]` and blocks PASS.
- Scenario IDs and `case_coverage_blockers` remain `/speckit.plan` outputs.

This gate checks whether behavior requirements are projectable. It does not
decide test level, fixtures, assertions, contracts, or Task Readiness.

## NFR Requirement Gate

Write NFR readiness to `checklists/nfr.md`. Evaluate performance, security and
privacy, reliability and recovery, accessibility, compliance and auditability,
observability, compatibility, data lifecycle, and cost or operational
constraints.

Each dimension is `Required`, `Not Applicable`, or `Unknown`. Required items
need verifiable product-level criteria. Not Applicable needs a rationale.
Unknown items affecting planning are product-decision blockers. Do not require
technical designs or invent architecture.

## Visual Requirement Gate

Write visual readiness and the only Visual Fidelity Evidence Matrix to
`checklists/visual.md`.

Apply the gate when `spec.md` contains a Visual & UI Specification, visual
requirements, visual/HTML/structured-IR SSOT refs, external intake refs,
provider blockers, pixel-perfect/brand-critical requirements, responsive
visual requirements, or UI visual acceptance requirements.

Every visual item is `Required`, `Not Applicable`, `Unknown`, or
`[BLOCKED: PROVIDER_EVIDENCE]`.

- Unknown product semantics become `[blocker:product-decision]`.
- Missing provider proof remains `[blocker:provider-evidence] [return:intake]`.
- Provider blockers must not be converted into clarify questions.
- Required items need source traceability and observable requirement text.
- The matrix records source refs, provider dependency, visual SSOT refs, HTML
  SSOT refs, structured IR refs, other evidence refs, readiness input,
  accepted exceptions, and blocker IDs.
- Responsive visual requirements block PASS only when required source-backed
  state or viewport evidence is missing for a feature that depends on provider
  evidence.

Do not call provider tools, rebuild intake evidence, parse provider or HTML
artifacts, define screenshot comparison, visual diff, baseline capture, or
final visual review.

## Recompute and Reporting

Recompute generated sections using stable CHK/CASE/NFR/VIS IDs. Never append
duplicate status blocks, stale blockers, or repeated matrix rows. Preserve
unrelated manual notes.

Report per-domain applicability/status, current spec revision, the in-memory
Planning Readiness aggregate, product-decision blockers, and provider-evidence
blockers separately.

{CORE_TEMPLATE}
