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

## Full-Spectrum Projection

Project confirmed natural-language input and authorized source facts into the
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
- source references, unresolved product decisions, provider-evidence gaps, and
  clarification history.

Optional domains remain optional. Use a specific `Not Applicable` statement only
when the supplied feature context establishes non-applicability; absence alone
is not proof. The template is a carrier, not a completeness result.

Make informed, documented assumptions for low-impact gaps. Use at most three
`[NEEDS CLARIFICATION: ...]` markers for high-impact product decisions with no
safe default. Missing external/provider evidence is
`[BLOCKED: PROVIDER_EVIDENCE]`, not a product decision.

Preserve confirmed visual SSOT, HTML SSOT, structured IR, evidence, state,
viewport, visual proof, and Client Asset Contract refs without re-running
provider intake. Do not invent DOM/CSS structure, framework components, code
props, local asset paths, hashes, or implementation strategies.

## Local Write Safety

Before finishing, check only the artifact this command owns:

- the resolved template headings remain structurally valid;
- the feature description was projected into user scenarios, applicable
  requirement carriers, and measurable outcomes;
- assumptions and unresolved decisions are not presented as confirmed facts;
- no implementation design or foreign-stage artifact was written.

Do not compute completeness, PASS/BLOCKED readiness, ID uniqueness, numbering
gaps, stale refs, cross-artifact coverage, or cross-command consistency.

## Completion Report

Report the `spec.md` path, populated specification areas, assumptions, unresolved
product decisions, provider-evidence gaps, and hook status. Suggest
`/speckit.clarify` for product decisions or `/speckit.checklist` for independent
requirement-writing questions. Do not declare Planning Readiness.
