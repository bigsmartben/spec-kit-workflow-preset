---
description: Wrap core planning with project Architecture consumption, Phase 0 behavior projection, formal contracts, and BDD Plan closeout.
strategy: wrap
---

## Change Scope Granularity

Apply the constitution's Change Scope Granularity principle.

During planning, lock the change scope to `M + U`: module/capability plus design object. Do not lock operation-level implementation details or concrete write paths.

## Architecture-Guided Planning

Before Phase 0 preflight or any planning write, read:

```text
.specify/memory/constitution.md
.specify/memory/architecture.md
```

If `architecture.md` is missing, uses the retired 4+1 or nine-section planning-contract format, lacks an Architecture goal or authorized sources, or has no explicit system boundary with ownership and non-responsibility, stop with a report-only/no-write failure and return to `/speckit.constitution`.

Consume applicable Architecture content through the normal planning artifacts:

- `research.md` MUST follow established technical decisions and evidence. If a documented revisit condition is met, record the evidence that triggered it; do not silently replace the Architecture decision.
- `data-model.md` MUST preserve defined concepts, ownership, relationships, lifecycle, and invariants.
- `contracts/` MUST preserve system boundaries, responsibilities, interface ownership, and dependency direction.
- `plan.md` and `quickstart.md` MUST carry forward applicable Architecture constraints, unresolved gaps, revisit conditions, and validation implications.

An Architecture gap may shape or block planning, but must not be converted into an invented decision. If any planning artifact conflicts with or requires changing `.specify/memory/architecture.md`, stop planning and return to the Constitution stage. Do not repair or rewrite project Architecture from `/speckit.plan`.

Planning artifacts demonstrate Architecture consumption in their normal content. Do not create a compliance matrix, consumption report, audit receipt, or separate traceability artifact.

## Plan Agent Topology

Follow cross-agent protocol profile: `speckit.plan.stage_local_planning`.

Plan Core Agent owns requirement-gate consumption, stage-local delegation,
conflict resolution, BDD Plan closeout, and final writes to planning artifacts.
Delegated agents return bounded drafts, source refs, blockers, and
`context_gaps`; Plan Core Agent consumes those outputs rather than subagent conversation history.

Use only planning-local roles: Behavior Projection Agent, Formal Contract Agent, Design Artifact Agent, Validation Planning Agent, and Visual Planning Agent. Each payload declares assigned scope, allowed reads, allowed sections, and output contract. If runtime subagents are unavailable, Plan Core Agent processes one assigned scope at a time with the same boundaries and final-write ownership.

## Design Artifact Policy

Core planning remains authoritative. Optional design artifacts carry structured details that do not belong in `plan.md`.

Generate design artifacts only when the feature requires internal object design or cross-boundary sequence constraints:

- `class-diagram.md`: internal implementation object structure.
- `contracts/sequences.md`: service-call, command, event, and integration sequencing.

For simple features, keep artifacts concise. `N/A` sections require a concrete rationale, for example "No service boundary exists for this static documentation change." Do not create large placeholder files.

Keep `plan.md` as summary/navigation. It must link generated design artifacts and must not embed complete class diagrams or complete sequence diagrams.

Store service sequences only at `contracts/sequences.md`, even when there are no other contract files. Do not create a root-level `sequences.md`.

Validation strategy is not a standalone planning document. Planning-time
validation decisions belong in `research.md`; executable validation paths belong in `quickstart.md`; BDD Plan closeout maps those decisions into
`behavior/behavior-testability.md`; concrete tasks belong in `tasks.md`.

## Phase 0 Gate Consumption

Use the core plan command's read-only Planning Readiness preflight before any
planning write. This wrapper consumes:

- `checklists/requirements.md`
- `checklists/behavior.md`
- `checklists/ux.md`
- `checklists/security.md`
- `checklists/nfr.md`
- `checklists/visual.md`

All standard domains must be evaluated, metadata must match the current spec
revision, and every applicable gate must PASS. Do not accept the legacy
`checklists/behavior-testability.md` as evidence. Missing, BLOCKED, malformed,
or stale gates produce the core report-only/no-write failure. Return product
decisions to `/speckit.clarify` and provider evidence to intake.

## Phase 0 Behavior Projection

After Phase 0 preflight passes and before core research or design work, project the accepted `spec.md` requirements into behavior drafts:

- `behavior/bdd.draft.feature`: readable BDD draft scenarios.
- `behavior/behavior-scenarios.draft.json`: structured draft scenario IDs, Given inputs, When actions, Then outcomes, and source.
- `behavior/uif.intent.json`: interaction intent extracted from accepted requirements.
- `behavior/data-fixtures.intent.json`: data setup intent required by draft scenarios.

Required case types from `checklists/behavior.md` must project into
`behavior/behavior-scenarios.draft.json`. Do not continue with only positive
scenarios when Required case types exist. If a Required case type cannot be
projected without inventing requirements, stop without partial behavior writes
and return to `/speckit.checklist` or `/speckit.clarify`.

Phase 0 behavior projection is a projection step, not a new requirement-discovery step:

- Do not discover new requirement problems.
- Do not ask clarification questions.
- Do not modify `spec.md`.
- Do not generate formal contracts.
- Do not decide test level, fixture strategy, external-system strategy, interface design, or validation commands.

Structured JSON draft artifacts must follow their matching `schemas/speckit.behavior.*.schema.json` contracts.

If Phase 0 cannot generate behavior drafts from a `spec.md` that passed checklist, stop with a report-only/no-write failure. Do not create or update partial behavior artifacts. The remedy is to return to `/speckit.checklist` or `/speckit.clarify`; do not invent missing requirements during planning.

## Additional Phase 1 Design Outputs

During Phase 1, after Phase 0 behavior projection and core research have resolved planning unknowns and while producing design/contracts, create or update these artifacts only when their trigger conditions are met:

1. `class-diagram.md`
   - Capture key classes, interfaces, abstract types, services, repositories, adapters, factories, strategies, controllers, and coordinators.
   - Explain each core type's responsibility and the relationships that constrain implementation: inheritance, composition, aggregation, dependency, and references.
   - Format must be Mermaid, PlantUML, or structured table; selected format must expose type responsibilities and relationships.
   - Do not define API request/response fields, domain business fields, test cases, task IDs, private helpers, or method-level implementation details.

2. `contracts/sequences.md`
   - Capture the observable flow of API requests, commands, events, callbacks, async workers, external systems, retries, compensation, rollback, and failure branches.
   - Include participants, service boundaries, main success paths, important alternate paths, and failure handling that affects implementation or testing.
   - Format must be Mermaid sequence diagram or structured text; selected format must expose participants, boundaries, success paths, and failure paths.
   - Do not define field schemas, internal class inheritance, test matrices, or user-facing run instructions.

When `plan.md` has a design artifact/navigation section, include links to:

- Internal object design: `./class-diagram.md`
- Service sequences: `./contracts/sequences.md`
- Behavior draft: `./behavior/bdd.draft.feature`
- BDD contracts: `./contracts/bdd/`
- Expected UIF contracts: `./contracts/uif/`
- Behavior contracts: `./contracts/behavior/`
- Data model: `./data-model.md`
- Interface contracts: `./contracts/`
- Validation path: `./quickstart.md`
- Behavior testability: `./behavior/behavior-testability.md`

When visual requirements are in scope, keep `plan.md` navigation linked to visual fidelity scope, source refs, visual SSOT refs, HTML SSOT refs, structured IR refs, screenshot refs, visual proof refs, and other external evidence refs already accepted by `spec.md` and the readiness checklist.

## Visual Planning Responsibilities

When visual requirements are in scope, planning must keep
`checklists/visual.md` and its Visual Fidelity Evidence Matrix as the upstream
readiness record and split visual carry-forward across the existing planning
outputs.

Use the Visual Fidelity Evidence Matrix `Requirement Status` as the visual planning input filter. Carry forward only visual rows with status `Required` or an accepted exception rule. Rows with status `Unknown` or `[BLOCKED: PROVIDER_EVIDENCE]` must already have blocked checklist PASS; if encountered during planning, stop with a report-only/no-write upstream gate failure and return to `/speckit.checklist`, `/speckit.clarify`, or the external intake extension as appropriate. Do not project `Not Applicable` rows into visual planning outputs.

- `research.md`: carry forward visual and IR planning inputs for each relevant Visual Item ID or visual SSOT ref. Record source refs, HTML SSOT refs, structured IR refs, readiness status, accepted exception refs, unresolved blocker refs, external evidence refs, related quickstart path, and related UIF or behavior contract path. Do not define visual validation strategy, screenshot comparison, visual diff, baseline capture, or final visual review work; do not copy the Visual Fidelity Evidence Matrix into `research.md`, create new visual requirements, call provider tools, rebuild external intake evidence, or rebuild provider evidence matrices.
- `contracts/uif/` and `contracts/behavior/`: formalize accepted visual interaction and state constraints only when they affect observable behavior. Expected UIF contracts may carry visual_item_refs, viewport_matrix_refs, state_matrix_refs, visual_proof_refs, and accepted_exception_refs. Behavior contracts may reference visual assertion IDs or blockers when a visual state cannot be formalized without inventing requirements. Interface contracts in `contracts/` may model only API or data fields needed to support UI states, assets, or feedback; they must not contain layout rules or screenshot proof decisions.
- `contracts/sequences.md`: add UI interaction sequence, visual state handoff points, responsive branch trigger refs, and visual proof references only when visual states affect cross-boundary order, async callbacks, retries, rollback, compensation, or error propagation. Keep visual style, tokens, layout breakpoints, screenshot matrices, and validation commands out of `contracts/sequences.md`.

## Behavior-First Planning Inputs

Use the Phase 0 behavior projection drafts as planning inputs:

- `behavior/bdd.draft.feature`
- `behavior/behavior-scenarios.draft.json`
- `behavior/uif.intent.json`
- `behavior/data-fixtures.intent.json`

Phase 1 outputs must cite applicable draft scenario IDs or record `N/A or blocker`.

During Phase 1, if behavior drafts exist and the requirement gates have passed,
you must formalize them into formal behavior contracts:

- `contracts/bdd/`: acceptance-level BDD contracts.
- `contracts/uif/`: Expected UIF contracts.
- `contracts/behavior/`: scenario instance, fixture, and assertion contracts.

Required case types from `checklists/behavior.md` must formalize into
`contracts/behavior/scenario-instances.json`. Do not continue with only positive
scenarios when Required case types exist. Map each Required Case ID to a
Scenario ID or `case_coverage_blockers` entry. When a Required case type cannot
be formalized, write `case_coverage_blockers` in
`contracts/behavior/scenario-instances.json` and record `N/A or blocker` with
the Case ID, missing planning input, and downstream contract path.

When formalizing BDD Draft into `contracts/bdd/*.feature`:

- Preserve scenario intent and business outcome from the draft.
- Convert ambiguous Given steps into formal fixture, actor, state, permission, or start-view conditions.
- Convert When steps into formal user events, request cases, or system triggers aligned with UIF/API contracts.
- Convert Then steps into formal feedback, response, business state, or assertion expectations.
- If a step cannot be formalized without inventing information, record `N/A or blocker` instead of guessing.
- Do not introduce independent traceability mechanisms for BDD formalization.

If behavior drafts exist but cannot be formalized, write `N/A or blocker` in the affected planning artifact with the source draft path, the missing planning input, and the downstream contract path that could not be produced. Do not silently skip behavior draft formalization.

BDD draft reasoning must feed the normal planning outputs:

- `research.md`: record the selected test level, fixture strategy, mock/external-system strategy, and error-branch validation decisions for each behavior scenario type that affects implementation.
- `data-model.md`: model formal behavior entities referenced by behavior contracts, including `BehaviorScenarioInstance`, `DataFixture`, `UIFPath`, `FeedbackView`, and `BehaviorAssertion`.
- `contracts/`: align interface contracts with BDD When steps, Expected UIF `api_call` steps, and behavior assertions.
- `quickstart.md`: include validation paths that exercise the formal BDD/UIF/behavior contracts.

Keep `plan.md` as summary/navigation for these formal behavior contracts. Product requirements stay in `spec.md`, domain details stay in `data-model.md`, interface schemas stay in `contracts/`, and validation run guidance stays in `quickstart.md`.

## BDD Plan / Behavior Testability Closeout

After Phase 1 contracts, `research.md`, and `quickstart.md` are complete,
generate `behavior/behavior-testability.md` from the
`behavior-testability-template`.

Compute and record the current spec and plan SHA-256 revisions. Build one Task
Derivation Matrix row for every Required Case from `checklists/behavior.md`.
Each row maps:

`Case ID → Scenario ID → BDD ref → UIF ref → fixture ref → assertion ref →
validation level → research decision → quickstart path → visual/NFR refs`.

- UIF may be `N/A` only with a concrete non-UI reason.
- Visual or NFR may be N/A only by referencing the corresponding requirement
  gate and rationale.
- Validation level is `unit`, `contract`, `integration`, or `e2e`.
- Every missing mapping gets a stable blocker ID.
- `Behavior Testability Status: READY` requires every Required Case to have a
  complete derivation row and no blocking items.
- Otherwise set `Behavior Testability Status: BLOCKED`.

Recompute generated sections by stable Case ID. Do not append duplicate Gate
Status blocks, retain resolved blockers, copy the legacy
`checklists/behavior-testability.md`, re-check requirement prose, call provider
intake, or ask product clarification.

{CORE_TEMPLATE}

## Design Artifact Reporting

Before finishing, the final report must list generated artifacts and state whether each is populated or intentionally minimal:

- `class-diagram.md`: populated, intentionally minimal, or not applicable with reason.
- `contracts/sequences.md`: populated, intentionally minimal, or not applicable with reason.

Also report where validation decisions were recorded:

- `research.md`: selected test level, fixture strategy, mock/external-system strategy, and error-branch validation decisions required by behavior contracts.
- `quickstart.md`: executable validation paths for the planned behavior contracts.
- `behavior/behavior-testability.md`: READY or BLOCKED, with Required Case
  coverage and blocker IDs.

Report unresolved design gaps separately from downstream tasks. Do not mark the planning run complete if a design artifact contains unresolved `NEEDS CLARIFICATION` items that block task generation.
