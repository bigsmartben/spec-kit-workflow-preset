---
description: Create one full-spectrum WHAT/WHY specification without generating readiness artifacts.
strategy: replace
---

Follow cross-agent protocol profile: `speckit.specify.single_core`.

## User Input

```text
$ARGUMENTS
```

The arguments are the feature description. If empty, stop with
`No feature description provided`.

## Extension Hooks

Read `.specify/extensions.yml` when present. Run enabled, unconditional
`hooks.before_specify` entries before creating the specification and
`hooks.after_specify` entries after the write but before reporting. Invoke and
await mandatory hooks; condition evaluation remains the HookExecutor's
responsibility.

## Feature Path And Template

1. Generate a concise 2–4 word action/noun short name.
2. If a successful pre-hook provides feature metadata, retain it without using
   the branch name as the specification directory identity.
3. Resolve `SPECIFY_FEATURE_DIRECTORY` from explicit input first. Otherwise use
   `.specify/init-options.json` feature numbering and create one directory under
   `specs/`.
4. Resolve the active `spec-template` through the preset resolution stack.
5. Materialize exactly one `spec.md` from that resolved template.
6. Persist the actual directory in `.specify/feature.json`.

This command writes only the feature directory bootstrap, `.specify/feature.json`,
and `spec.md`. It MUST NOT create, read, evaluate, or modify
`checklists/requirements.md` or any other checklist, Plan, Tasks, Architecture,
contract, test-design, or implementation artifact.

## Bounded Supplied Input Contract

This command starts when bounded content or source-backed facts have already
been supplied. Treat the current feature direction and each supplied evidence
packet through one local Source Reference Contract:

```text
SRC ref | role | opaque locator/description | revision/identity
| bounded feature scope | supplied content/facts
| projected requirement refs | status/blocker
```

1. Use only content and facts present in the bounded supplied input. An opaque
   locator without supplied content or source-backed facts is provenance only.
   Record `SRC_EVIDENCE_MISSING` and do not project a requirement from it.
2. Record every used source as one unique `SRC-*` row with exactly one role:
   `requirement-input`, `visual-input`, `technical-evidence`, or `context-only`.
3. Establish the current feature slice before projecting a broad source.
   Project only facts inside that explicit slice. When no safe slice exists,
   record `[NEEDS CLARIFICATION: ...]` or `SRC_FEATURE_SLICE_MISSING` and do not
   import the complete source.
4. Keep observed, derived, assumed, unresolved, and conflicting statements
   distinguishable. An unresolved or conflicting statement carries a stable
   blocker and is not presented as a requirement ready for downstream use.
5. `requirement-input` may support applicable WHAT/WHY requirement carriers.
   `visual-input` may support only `UI-*` and `VIS-*`.
   `technical-evidence` may be cited as evidence but does not become a product
   requirement. `context-only` supports no normative requirement.

Opaque identity is optional provenance. Preserve a supplied URI, path,
revision, digest, conversation reference, or description as written. The
source row's supplied content/facts and evidence locators are the only basis
for local projection.

## Full-Spectrum Projection

Project supported facts from the Bounded Supplied Input Contract into the
resolved template. Keep the result stakeholder-readable, technology-agnostic,
and focused on WHAT users need and WHY.

Populate applicable carriers for:

- product goals, actors, journeys, observable behavior, edge/failure cases;
- functional requirements (`FR-*`);
- non-functional outcomes (`NFR-*`);
- UX journeys and interaction expectations (`UX-*`);
- UI surfaces, states, feedback, responsive behavior, and target-platform
  outcomes (`UI-*`);
- observable visual and restoration-equivalence requirements (`VIS-*`);
- security/privacy, data/integration, dependencies, boundaries;
- assumptions, exclusions, measurable success criteria;
- source references, unresolved product decisions, source-evidence blockers, and
  clarification history.

Optional domains remain optional. Use a specific `Not Applicable` statement only
when the supplied feature context establishes non-applicability; absence alone
is not proof. The template is a carrier, not a completeness result.

Apply the UI Evidence Projection Rules and the stable UI Specification
structures in the resolved template whenever supplied HTML, CSS, rendered
state, interaction, asset, responsive, accessibility, or restoration evidence
applies. Every applicable `UI-*`/`VIS-*` row records its kind, observable
statement, `SRC-*` refs, evidence locator, surface, state, viewport, derivation
classification, measurable acceptance condition, and status/blocker.

For UI restoration, classify every applicable equivalence dimension and every
required `surface x state x viewport` target. A pixel-restoration request is
actionable only when its profile and complete target matrix identify baseline
evidence, rendering context, fidelity mode, measurable acceptance envelope,
and stable accepted-exception policy. Otherwise retain the request with
`PIXEL_PROFILE_INCOMPLETE` or a more specific stable blocker.

For cross-platform restoration, record the source platform, concrete target
platform, one allowed adaptation mode, target contexts, and one allowed
per-dimension decision. Apply the precedence declared by the UI Specification
contract. `Swift` alone is not a target platform. Mixed policies are expressed
per dimension, never as a free-form mode.

Make informed, documented `assumed` classifications only for low-impact gaps.
Use at most three `[NEEDS CLARIFICATION: ...]` markers for high-impact product
decisions with no safe default. Missing evidence is a stable source blocker,
not a product decision.

Visual, HTML, structured IR, executable, document, and technical-evidence
inputs use the same `SRC-*` row shape. Preserve their opaque provenance,
bounded supplied facts, evidence locators, and projected local refs. Do not
invent unobserved DOM/CSS structures, UI states, responsive behavior, assets,
product intent, framework components, code properties, local asset paths,
hashes, capture/comparison procedures, or implementation strategies.

After projection, `spec.md` is the feature-local WHAT/WHY SSOT. Downstream
commands consume its local requirements and blockers, not the external source
format or workflow.

## Local Write Safety

Before finishing, check only the artifact this command owns:

- the resolved template headings remain structurally valid;
- the feature description was projected into user scenarios, applicable
  requirement carriers, and measurable outcomes;
- every used source has one allowed role, an explicit bounded feature scope,
  supplied content/facts or `SRC_EVIDENCE_MISSING`, local projection refs or a
  reason for none, and a local status/blocker;
- every projected `UI-*`/`VIS-*` row resolves its source and evidence locators,
  uses one derivation classification, and contains an observable acceptance
  condition or stable blocker;
- every applicable restoration, pixel-profile, and cross-platform adaptation
  structure is complete or carries its owning stable blocker;
- assumptions and unresolved decisions are not presented as confirmed facts;
- no implementation design or foreign-stage artifact was written.

Do not compute completeness, PASS/BLOCKED readiness, ID uniqueness, numbering
gaps, stale refs, cross-artifact coverage, or cross-command consistency.

## Completion Report

Report the `spec.md` path, populated specification areas, assumptions, unresolved
product decisions, source-evidence blockers, and hook status. Suggest
`/speckit.clarify` for product decisions or `/speckit.checklist` for independent
requirement-writing questions. Do not declare Planning Readiness.
