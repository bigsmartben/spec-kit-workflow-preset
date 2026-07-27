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

## Authorized Source Input Contract

Treat natural-language direction and every user-provided or explicitly
authorized external reference through the same local Source Reference Contract:

```text
SRC ref | role | opaque locator/description | revision/identity
| authorized scope/facts | projected requirement refs | status/blocker
```

1. Read only the current conversation and sources the user explicitly
   authorizes. A locator, directory, repository, provider, or neighboring file
   does not expand that scope.
2. Record every used source as one unique `SRC-*` row with exactly one role:
   `requirement-input`, `visual-input`, `technical-evidence`, or `context-only`.
3. Establish the current feature slice before projecting a broad source.
   Project only facts inside the explicit slice. When no safe slice exists,
   record `[NEEDS CLARIFICATION: ...]` or a stable local source blocker and do
   not import the complete source.
4. Keep confirmed facts, assumptions, clarification needs, unavailable
   evidence, and informative context distinguishable.
5. `requirement-input` may authorize applicable WHAT/WHY requirement carriers.
   `visual-input` may authorize only `UI-*` and `VIS-*`.
   `technical-evidence` may be cited as evidence but does not become a product
   requirement. `context-only` authorizes no normative requirement.

Opaque identity is optional provenance. Preserve a supplied URI, path,
revision, digest, conversation reference, or description, but do not interpret
or validate its external meaning. The presence of a reference MUST NOT cause
this command to invoke a provider tool, dereference or execute a locator,
inspect adjacent source scope, validate authenticity/freshness/publication
state, or create an import manifest, handoff package, adapter, provider-specific
schema, or external synchronization record. Intake is not an SDD stage.

## Full-Spectrum Projection

Project confirmed facts from the Authorized Source Input Contract into the
resolved template. Keep the result stakeholder-readable, technology-agnostic,
and focused on WHAT users need and WHY.

Populate applicable carriers for:

- product goals, actors, journeys, observable behavior, edge/failure cases;
- functional requirements (`FR-*`);
- non-functional outcomes (`NFR-*`);
- UX journeys and interaction expectations (`UX-*`);
- UI surfaces, states, feedback, and responsive behavior (`UI-*`);
- visual requirements and confirmed source refs (`VIS-*`);
- security/privacy, data/integration, dependencies, boundaries;
- assumptions, exclusions, measurable success criteria;
- source references, unresolved product decisions, source-evidence blockers, and
  clarification history.

Optional domains remain optional. Use a specific `Not Applicable` statement only
when the supplied feature context establishes non-applicability; absence alone
is not proof. The template is a carrier, not a completeness result.

Make informed, documented assumptions for low-impact gaps. Use at most three
`[NEEDS CLARIFICATION: ...]` markers for high-impact product decisions with no
safe default. Missing external evidence is a stable source blocker, not a
product decision.

Visual, HTML, structured IR, executable, document, and technical-evidence
inputs use the same `SRC-*` row shape. Preserve only their authorized opaque
provenance and projected local refs. Do not execute or certify them, or invent
DOM/CSS structure, framework components, code props, local asset paths, hashes,
or implementation strategies.

After projection, `spec.md` is the feature-local WHAT/WHY SSOT. Downstream
commands consume its local requirements and blockers, not the external source
format or workflow.

## Local Write Safety

Before finishing, check only the artifact this command owns:

- the resolved template headings remain structurally valid;
- the feature description was projected into user scenarios, applicable
  requirement carriers, and measurable outcomes;
- every used source has one allowed role, an explicit authorized scope, local
  projection refs or a reason for none, and a local status/blocker;
- assumptions and unresolved decisions are not presented as confirmed facts;
- no implementation design or foreign-stage artifact was written.

Do not compute completeness, PASS/BLOCKED readiness, ID uniqueness, numbering
gaps, stale refs, cross-artifact coverage, or cross-command consistency.

## Completion Report

Report the `spec.md` path, populated specification areas, assumptions, unresolved
product decisions, source-evidence blockers, and hook status. Suggest
`/speckit.clarify` for product decisions or `/speckit.checklist` for independent
requirement-writing questions. Do not declare Planning Readiness.
