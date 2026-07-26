# Workflow Preset

This Spec Kit community preset combines behavior-first specification, design-aware planning, scoped change governance, and agent-native handoff orchestration.

It wraps `/speckit.specify`, `/speckit.checklist`, `/speckit.clarify`,
`/speckit.constitution`, `/speckit.plan`, `/speckit.tasks`, and
`/speckit.analyze` with multi-domain requirement gates, Change Scope
Granularity and Architecture SSOT governance, Phase 0 behavior projection,
formal behavior contracts, plan-stage Behavior Testability, optional design
artifacts, and task-time validation derivation. It replaces
`/speckit.implement` with a Core Agent, Vertical Planner Agent, and Worker Agent
orchestration contract that writes handoffs to disk.

## Goal

`workflow-preset` turns a Spec Kit feature from a single broad implementation prompt into a staged workflow with stable design context and explicit worker boundaries.

The preset has six goals:

- Make requirements, behavior, UX, security, NFR, and visual readiness explicit
  before planning without creating a Planning Readiness summary file.
- Project accepted requirements into BDD, UIF intent, and fixture intent drafts during `/speckit.plan` Phase 0.
- Close planning with `behavior/behavior-testability.md`, which maps Required
  Cases and formal planning decisions into Task Readiness.
- Preserve richer planning intent so downstream tasks and implementation do not lose object design, service-flow, or validation decisions.
- Keep implementation scope explicit by applying Change Scope Granularity from planning onward: M + U boundaries are locked before execution maps them to concrete paths and O-level edits.
- Execute implementation through agent-native handoff orchestration so each worker receives explicit task IDs, lifecycle stage, vertical capability, context, read/write paths, validation commands, and receipt requirements.

## Problem Addressed

Large Spec Kit features can overload the implementation phase. A single `/speckit.implement` run may need to keep product requirements, technical decisions, domain details, interface contracts, object design, service flows, test strategy, task ordering, and current code changes in one prompt. As the context grows, the agent is more likely to drift from earlier design decisions, blur task boundaries, read unrelated documents, update the wrong files, or mark tasks complete without enough validation evidence.

`workflow-preset` reduces that failure mode in three complementary ways:

- Requirement enhancement keeps product requirements in `spec.md` and gates
  planning with metadata-bearing domain checklists.
- Scope governance keeps broad repository context from becoming implementation scope by applying the R/M/U/O model once planning begins.
- Plan enhancement projects accepted behavior drafts, then gives object design, service sequencing, and validation intent stable homes before tasks are generated.
- Implement handoff orchestration slices work by lifecycle and vertical capability, then gives each Worker Agent a compact digest, scoped paths, validation commands, and a receipt contract instead of the full planning corpus.

The intent is not to add ceremony to simple features. The intent is to preserve reasoning quality when the feature is large enough that a single implementation context becomes a source of drift.

## Capabilities

Requirement capabilities:

- Wraps `/speckit.specify` so it produces or updates `spec.md` only.
- Wraps `/speckit.clarify` so it resolves product-decision blockers in
  `spec.md`, recomputes affected gates, and leaves provider evidence with
  intake.
- Consumes confirmed product facts, external intake facts, visual SSOT refs, HTML SSOT refs, structured IR refs, and evidence refs when projecting requirements into `spec.md`.
- When external intake evidence or visual SSOT refs have already been projected into `spec.md`, `/speckit.clarify` clarifies evidence-derived gaps already written in `spec.md` and does not call provider tools.
- Wraps `/speckit.checklist` to generate `requirements.md`, `behavior.md`,
  `ux.md`, `security.md`, `nfr.md`, and `visual.md` requirement gates.
- Checks user stories, acceptance criteria, Given/When/Then readiness, roles, permissions, states, data, validation, boundary, exception, state_conflict behavior, and non-functional requirements directly from `spec.md`.
- Adds a Case Coverage Matrix with one row per story or capability case type so positive, negative, boundary, permission, validation, and state_conflict cases are marked Required, Not Applicable, or Unknown before planning.
- Checks visual requirements for source traceability, external intake readiness status when cited, HTML SSOT refs, structured IR refs, evidence refs, provider blocker status, and visual fidelity scope before planning.
- Preserves stable visual SSOT refs, HTML SSOT refs, structured IR refs, and evidence refs through `spec.md` and the Visual Fidelity Evidence Matrix.
- Records Client Asset Contract facts in `spec.md` for asset source strategy, required variants, fallback policy, and blocker status.
- Requires NFR dimensions to be marked Required, Not Applicable, or Unknown in product language before planning.
- Blocks planning when readiness gaps or missing or unverifiable NFR assumptions must return to `/speckit.clarify` or `/speckit.specify`.

Governance capabilities:

- Wraps `/speckit.constitution` and the constitution template with Change Scope Granularity and Architecture SSOT governance.
- Defines the fixed R/M/U/O model: R is Repository / Workspace, M is Module / Capability, U is Unit / Design Object, and O is Operation / Detail. These letters must not be renamed or expanded with alternate nouns.
- Blocks constitution writes when a generated draft changes the fixed R/M/U/O mapping.
- Routes architecture decisions, domain facts, object design, flows, and interface contracts to architecture SSOT artifacts instead of embedding concrete implementation content in ratified constitution principles.
- Requires planning to lock M + U before execution maps units to concrete paths.
- Treats unresolved U -> path mapping as a context gap instead of widening execution to repository-wide or broad module scope.

Planning capabilities:

- Wraps `/speckit.plan` to run Phase 0 preflight, Phase 0 behavior projection, and optional/contextual design artifacts when useful.
- Requires the runtime Planning Readiness aggregate to pass before planning;
  no `planning-readiness.md` is generated.
- Treats Phase 0 preflight failures as report-only/no-write failures.
- Writes `behavior/bdd.draft.feature`, `behavior/behavior-scenarios.draft.json`, `behavior/uif.intent.json`, and `behavior/data-fixtures.intent.json` during Phase 0 behavior projection.
- Projects Required case coverage into `behavior/behavior-scenarios.draft.json` instead of allowing Required cases to disappear behind positive-only drafts.
- Consumes Phase 0 behavior drafts and must formalize them into
  `contracts/bdd/`, `contracts/uif/`, and `contracts/behavior/` after the
  multi-domain Planning Readiness aggregate passes.
- Requires failure scenarios in `contracts/behavior/` to carry an explicit trigger, case kind, error code, failure feedback, and state invariant, rollback, or compensation assertion reference.
- Records `N/A or blocker` and `case_coverage_blockers` when behavior drafts cannot be formalized.
- Keeps `plan.md` focused on technical decisions and navigation.
- Adds plan-template navigation to the core plan output.
- Stores internal object design in `class-diagram.md`.
- Stores service, command, event, async, retry, rollback, and failure-path flows in `contracts/sequences.md`.
- Records validation decisions in `research.md` and validation paths in `quickstart.md`.
- Generates `behavior/behavior-testability.md` at BDD Plan closeout with a Task
  Derivation Matrix and READY/BLOCKED status.
- When visual requirements are in scope, research.md carries forward visual/IR source refs, readiness inputs, accepted exceptions, related contract paths, and unresolved blockers; contracts formalize visual interaction and state constraints; contracts/sequences.md records visual state flow only when it affects cross-boundary sequencing.
- For visual restoration work, visual SSOT refs carry requirement traceability while Client Asset Contract entries carry local asset binding expectations.
- Keeps product requirements in `spec.md`, domain facts in `data-model.md`, interface schemas in `contracts/`, and executable validation guidance in `quickstart.md`.

Task generation capabilities:

- Wraps `/speckit.tasks` so task generation requires READY
  `behavior/behavior-testability.md` and consumes its Case mappings.
- Uses formal BDD, UIF, and behavior contracts to derive test-first fixture, acceptance test, implementation, and verification tasks.
- Treats missing Required failure behavior scenarios as blockers instead of generating complete-looking happy-path-only tasks.
- Performs test strategy derivation from BDD contracts, Expected UIF contracts, behavior contracts, interface contracts, `research.md`, and `quickstart.md` without writing a separate strategy artifact.
- Derives paired UI implementation and acceptance tasks when UIF contracts, Visual Fidelity Readiness rows, visual acceptance requirements, or Client Asset Contract entries apply.
- Preserves visual/IR traceability refs on UI implementation, asset binding, and non-visual acceptance tasks without generating visual validation, screenshot comparison, visual diff, baseline capture, or final visual review work.
- Uses design artifacts to derive implementation, integration, orchestration, failure-handling, and validation tasks.
- Adds Final Code Review tasks for boundary, interface contract, visual, data side-effect, behavior contract, sequence consistency, and asset binding scopes when applicable.
- Preserves the existing checklist format and user-story organization.

Analysis capabilities:

- Wraps `/speckit.analyze` to check vertical consistency from `spec.md` through BDD/UIF intent, formal contracts, and `tasks.md`.
- Checks that user stories, Given/When/Then steps, UIF API calls, behavior contracts, tasks, and quickstart validation paths remain traceable.
- Adds case coverage checks so Required case types remain traceable through behavior drafts, formal contracts, tasks, and quickstart validation paths.
- Treats UIF as a requirement behavior projection, formalized during planning as Expected UIF contracts.

Implementation capabilities:

- Replaces `/speckit.implement` with an agent-native handoff orchestration command.
- Uses Core Agent mode to own lifecycle state, create the context index, assemble the final manifest, dispatch Worker Agent runs, review receipts, update `tasks.md`, and run integration verification.
- Uses Vertical Planner Agent mode to plan one `vertical_capability`, produce shard plans, create handoff drafts, create context digest drafts, and derive allowed paths.
- Uses Worker Agent mode to execute exactly one `speckit.implement.handoff.v2` handoff.
- Writes `handoff-manifest.json`, one handoff JSON, one context digest, a context index, and one worker receipt per shard.
- Defines deterministic shard, context digest, and allowed path derivation rules.
- Uses the cross-agent protocol profile `speckit.implement.persistent_handoff_orchestration`; `/speckit.plan`, `/speckit.tasks`, and `/speckit.analyze` use their own stage-local profiles without inheriting implement execution permissions.
- Keeps manifest, handoff, and receipt JSON contracts in standalone schema files.
- Splits implement gates into manifest structure, handoff structure, dispatch readiness, receipt structure, and commit readiness validation.
- Requires behavior-linked `validation_evidence` in worker receipts when behavior contracts are in handoff context.
- Requires Final Code Review receipts to include post-implementation data side-effect review, visual consistency review, and asset binding review of actual implementation diffs before task status commit when those scopes apply.
- Requires Final Code Review receipts to reconcile implemented UI states, viewport behavior, visual/IR traceability refs, and Client Asset Contract bindings when UI or asset scopes apply.
- Assigns every handoff a lifecycle stage and vertical capability such as `domain-model`, `api-contract`, `persistence`, `service-flow`, `ui`, `test-validation`, `documentation`, `integration`, or `cleanup`.
- Supports direct single-shard execution with `Use handoff JSON <path>`.
- Blocks worker execution when generated context has unresolved `context_gaps`.
- Commits completed task statuses from `speckit.implement.receipt.v1` receipts so the Core Agent is the only `tasks.md` writer.

Context-load controls:

- `context-index.json` records the available planning and implementation context without requiring every worker to read every source document.
- Context digests include only assigned task text, relevant headings, referenced sections, applicable `class-diagram.md` or `contracts/sequences.md` constraints, relevant `research.md` validation decisions, and relevant `quickstart.md` validation paths.
- `context_gaps` are explicit blockers. A Worker Agent stops instead of guessing or expanding into full `spec.md`, `plan.md`, `research.md`, `contracts/`, `class-diagram.md`, or `quickstart.md`.
- `allowed_read_paths` and `allowed_write_paths` make each handoff auditable and prevent broad implementation runs from silently crossing capability boundaries.
- Worker receipts separate execution evidence from task status commits, so the Core Agent can review validation evidence before updating `tasks.md`.
- Final Code Review analyzes implementation data side effects after Worker Agents finish and before task status commit.
- When isolated subagents are unavailable, Core Agent writes the manifest and handoffs, then reports a `Manual Worker Queue` of `/speckit.implement Use handoff JSON <path>` entries in dispatch order.

## Workflow

1. `/speckit.constitution` preserves Change Scope Granularity and Architecture SSOT governance when the project constitution is created or updated.
2. `/speckit.specify` keeps the core requirements output in `spec.md`.
3. `/speckit.clarify` resolves requirement ambiguity in `spec.md`.
4. `/speckit.checklist` evaluates requirements, behavior, UX, security, NFR,
   and visual readiness directly from `spec.md`; `/speckit.clarify` repairs
   product-decision blockers and re-evaluates affected gates.
5. `/speckit.plan` applies Change Scope Granularity, runs Phase 0 preflight, performs Phase 0 behavior projection, formalizes behavior drafts into contracts, and adds design artifacts when they help implementation.
6. `/speckit.tasks` reads the core plan outputs, optional design artifacts, behavior contracts, interface contracts, `research.md`, and `quickstart.md`, then produces executable tasks with inline test level, data strategy, visual/IR traceability refs, asset binding, non-visual acceptance, and evidence requirements.
7. `/speckit.analyze` checks vertical consistency across requirements, behavior drafts, contracts, and tasks.
8. `/speckit.implement` enters Core Agent mode when no handoff path is provided.
9. The Core Agent writes `context-index.json` and dispatches one Vertical Planner Agent per active vertical capability.
10. Vertical Planner Agents produce shard plans, handoff drafts, context digest drafts, and allowed path derivations.
11. The Core Agent assembles final handoffs and writes `handoff-manifest.json`.
12. Worker Agents run only from persisted handoff JSON files and write receipts.
13. Final Code Review checks boundary, contract, visual, asset binding, sequence, implementation data side effects, and real e2e readiness.
14. The Core Agent reviews receipts, updates `tasks.md`, runs integration verification, and reports closeout status.

## Non-Goals

- It does not make every feature produce large diagrams or test matrices.
- It does not move product requirements out of `spec.md`.
- It does not move API or message schemas out of `contracts/`.
- It does not replace `data-model.md`, `research.md`, or `quickstart.md`.
- It does not infer UIF from built code; UIF remains a requirement and planning contract.
- It does not provide a Python orchestration script, workflow shell runner, or integration adapter layer.
- It does not allow Worker Agents to freely expand context by reading full planning documents when the digest is insufficient.

## Install

Release install:

```bash
specify preset add workflow-preset --from https://github.com/bigsmartben/spec-kit-workflow-preset/releases/download/v1.4.0/spec-kit-workflow-preset-v1.4.0.zip
```

Local development install:

```bash
specify preset add --dev /path/to/workflow-preset
```

## Usage

Run the behavior-first workflow:

```text
/speckit.constitution
/speckit.specify
/speckit.clarify
/speckit.checklist
/speckit.plan
/speckit.tasks
/speckit.analyze
```

### External Intake And Visual SSOT

Source capture and provider-specific intake are owned by the separate `spec-kit-intake`
extension. Install or run that extension when PRD, design, provider design, rendered HTML,
or test-case evidence must be captured or validated before this preset projects
requirements.

```text
external intake evidence + visual SSOT refs + HTML SSOT refs + structured IR refs -> /speckit.specify -> baseline spec.md
```

`/speckit.specify` does not perform intake, call provider tools, parse HTML SSOT bundles, re-parse structured IR artifacts, or decide provider source readiness. It consumes confirmed source-backed facts and preserves visual SSOT refs, HTML SSOT refs, structured IR refs, evidence refs, state/viewport refs,
screenshots, visual proof refs, and Client Asset Contract facts in `spec.md`.
Missing product decisions become `[NEEDS CLARIFICATION]`; missing provider or intake evidence for a feature that depends on that evidence becomes `[BLOCKED: PROVIDER_EVIDENCE]`; features that do not depend on HTML SSOT, structured IR, or provider evidence are `Not Applicable`.

### Provider Evidence Refs

Screenshots, visual proof refs, HTML SSOT refs, structured IR refs, and provider artifacts are evidence refs, not intake execution. This preset only references them through `spec.md` visual requirements and the Visual Fidelity Evidence Matrix.

Evidence refs can support layout, density, state, viewport, asset, and visual facts when source-backed. They cannot upgrade product semantics such as permissions, business effects, validation rules, or data ownership into confirmed requirements.

The Visual Fidelity Evidence Matrix is the single visual readiness record. It records requirement status, source refs, HTML SSOT refs, structured IR refs, other evidence refs, provider blocker status, accepted exception refs, Gate Status, and Blocking Items. It does not define visual validation work, screenshot comparison, visual diff, baseline capture, or final visual review.

### Provider Design And HTML SSOT Input

Use the `spec-kit-intake` extension for provider design, HTML SSOT, or structured IR capture:

```text
/speckit.intake.visual-design <source>
/speckit.intake.figma2htmlssot <source-or-intake-dir>
```

The intake extension owns source capture, provider evidence, raw provider metadata,
node inventory parity, rendered HTML visual SSOT bundles, structured IR artifacts,
source-side readiness, and blocker codes. This preset consumes only the confirmed
artifact refs, readiness inputs, blocker status, and traceability refs written or cited in `spec.md`.

Then run agent-native orchestrated implementation:

```text
/speckit.implement
```

Run a single worker handoff directly:

```text
/speckit.implement Use handoff JSON specs/001-demo/handoffs/implement/<run-id>/S01-service-flow-01.json
```

## Files Written

The core governance and planning workflow still owns its normal artifacts:

- `.specify/memory/constitution.md`
- `specs/<feature>/plan.md`
- `specs/<feature>/research.md`
- `specs/<feature>/data-model.md`
- `specs/<feature>/contracts/`
- `specs/<feature>/quickstart.md`
- `specs/<feature>/tasks.md`

This preset adds requirement-stage checklist artifacts:

- `specs/<feature>/checklists/behavior.md`
- `specs/<feature>/checklists/ux.md`
- `specs/<feature>/checklists/security.md`
- `specs/<feature>/checklists/nfr.md`
- `specs/<feature>/checklists/visual.md`

Source intake artifacts and provider artifact instances are written by
`spec-kit-intake` or another external intake extension. This preset consumes the
qualified evidence refs from `spec.md` after `/speckit.specify` writes confirmed
requirements or records `[BLOCKED: PROVIDER_EVIDENCE]`; it does not define or
generate the artifact instances. Provider evidence blockers do not become
`[NEEDS CLARIFICATION]`.

This preset adds Phase 0 behavior artifacts:

- `specs/<feature>/behavior/bdd.draft.feature`
- `specs/<feature>/behavior/behavior-scenarios.draft.json`
- `specs/<feature>/behavior/uif.intent.json`
- `specs/<feature>/behavior/data-fixtures.intent.json`

This preset adds planning-phase formal behavior contracts:

- `specs/<feature>/contracts/bdd/`
- `specs/<feature>/contracts/uif/`
- `specs/<feature>/contracts/behavior/`

This preset adds the plan-stage task-readiness artifact:

- `specs/<feature>/behavior/behavior-testability.md`

This preset adds optional/contextual planning artifacts:

- `specs/<feature>/class-diagram.md`
- `specs/<feature>/contracts/sequences.md`

Agent-native handoff orchestration writes implementation artifacts:

- `specs/<feature>/handoffs/implement/<run-id>/handoff-manifest.json`
- `specs/<feature>/handoffs/implement/<run-id>/planner-outputs/`
- `specs/<feature>/handoffs/implement/<run-id>/*.json`
- `specs/<feature>/handoffs/implement/<run-id>/*.context.md`
- `specs/<feature>/handoffs/implement/<run-id>/context-index.json`
- `specs/<feature>/handoffs/implement/<run-id>/results/*.json`

Contract files packaged by the preset:

- `schemas/speckit.behavior.scenarios.draft.v1.schema.json`
- `schemas/speckit.behavior.uif.intent.v1.schema.json`
- `schemas/speckit.behavior.data-fixtures.intent.v1.schema.json`
- `schemas/speckit.behavior.uif.expected.v1.schema.json`
- `schemas/speckit.behavior.scenario-instances.v1.schema.json`
- `schemas/speckit.behavior.data-fixtures.v1.schema.json`
- `schemas/speckit.behavior.assertions.v1.schema.json`
- `schemas/speckit.implement.manifest.v1.schema.json`
- `schemas/speckit.implement.handoff.v2.schema.json`
- `schemas/speckit.implement.receipt.v1.schema.json`

Governance templates packaged by the preset:

- `templates/constitution-template.md`

Packaged contract validators:

- `validators/speckit_implement_contract.py`

Source intake templates, provider design contracts, visual requirements schemas, HTML SSOT bundle contracts, structured IR contracts, and source-side validators live in the `spec-kit-intake` extension.

## Artifact Roles

`checklists/behavior.md` owns observable behavior and the Case Coverage Matrix;
`checklists/nfr.md` owns product-level non-functional readiness; and
`checklists/visual.md` owns the single Visual Fidelity Evidence Matrix.
Together with requirements, UX, and security gates they produce the runtime
Planning Readiness aggregate. Missing product decisions return to clarify;
provider evidence remains an intake blocker.

`behavior/bdd.draft.feature` captures Phase 0 behavior projection in readable Given/When/Then form. `behavior/behavior-scenarios.draft.json`, `behavior/uif.intent.json`, and `behavior/data-fixtures.intent.json` make the same draft behavior machine-readable enough for planning formalization.

`contracts/bdd/`, `contracts/uif/`, and `contracts/behavior/` contain planning-phase formal behavior contracts. They are generated from Phase 0 drafts after planning has resolved fixture strategy, data model, interface contracts, and validation paths, unless planning records `N/A or blocker` for missing planning input. `contracts/behavior/scenario-instances.json` carries `case_coverage_blockers` for Required cases that cannot be formalized. Failure scenarios must be structured enough to constrain implementation, including error code, failure feedback, and state invariant, rollback, or compensation assertion references.

`behavior/behavior-testability.md` is generated at plan closeout. It maps every
Required Case to its Scenario, BDD/UIF contract, fixture, assertion, validation
level, research decision, quickstart path, and visual/NFR refs. `/speckit.tasks`
stops unless this artifact is current and READY.

`class-diagram.md` captures internal implementation object structure: classes, interfaces, abstract types, composition, dependencies, references, and design pattern participants. It is the object design map that helps implementation preserve boundaries between services, adapters, repositories, strategies, factories, controllers, coordinators, and extension points.

`contracts/sequences.md` captures service-call, command, event, external-system, retry, rollback, compensation, async, and failure-path sequencing. It is the flow design map that helps implementation preserve call order, service boundaries, async behavior, idempotency, compensation, and error propagation. Sequences always live at this path, even when there are no other contract files.

For visual planning, research.md carries forward visual/IR source refs, readiness inputs, accepted exception refs, unresolved blocker refs, related contracts, and quickstart paths. contracts formalize visual interaction and state constraints by linking accepted visual items to Expected UIF, behavior scenarios, assertions, and supporting API/data schemas. contracts/sequences.md records visual state flow only when it affects cross-boundary sequencing, async results, retries, rollback, compensation, or error propagation; it does not redefine layout, tokens, screenshot matrices, visual readiness, or visual validation strategy.

Test strategy derivation happens during `/speckit.tasks`. The command derives unit, contract, integration, and end-to-end validation work from BDD contracts, Expected UIF contracts, behavior contracts, interface contracts, `research.md`, and `quickstart.md`, then writes the strategy inline on the relevant `tasks.md` checklist items. It also defines UI implementation, non-visual acceptance, contract validation, data-side-effect validation, integration/e2e validation, and scope-aware code review tasks in `tasks.md`; `/speckit.implement` executes those tasks and records receipt evidence without inventing validation strategy, changing requirements, updating contracts, or widening scope.

The handoff context digest includes relevant design constraints, visual fidelity requirements, visual SSOT refs, HTML SSOT refs, structured IR refs, external evidence refs, readiness inputs, quickstart paths, and behavior contracts when present, so Worker Agents can preserve object boundaries, service flows, visual intent, and validation intent without reading full planning documents by default.

See `commands/speckit.implement.md` for runtime handoff orchestration rules, and `schemas/` plus `validators/speckit_implement_contract.py` for the machine-checked manifest, handoff, receipt, dispatch, and commit contracts.

## Agent Topology

The Core Agent is the lifecycle orchestrator. It owns context indexing, manifest assembly, worker dispatch, receipt review, task status commit, integration verification, and closeout. It does not directly produce shard plans or context digest drafts.

Vertical Planner Agent runs are planners. A Vertical Planner Agent handles one `vertical_capability`, produces shard plans, handoff drafts, context digest drafts, and allowed path derivations, and does not execute implementation, write the final manifest, dispatch workers, or edit `tasks.md`.

Worker Agent runs are executors. A Worker Agent handles one persisted handoff, writes only `allowed_write_paths`, does not edit `tasks.md`, does not dispatch additional workers, and writes a `speckit.implement.receipt.v1` receipt.

Worker mode rejects handoff paths that do not exist or are not listed in `handoff-manifest.json`.

Only Vertical Planner Agents may produce shard plans and digest drafts.

Only Core Agent may write final `handoff-manifest.json` and commit `tasks.md`.

Only Worker Agents may execute implementation handoffs.

## Lifecycle

Core Agent mode proceeds through these stages:

- `intake`
- `context_indexing`
- `vertical_planning`
- `manifest_assembly`
- `worker_dispatch`
- `worker_execution`
- `receipt_review`
- `code_review`
- `task_commit`
- `integration_verification`
- `closeout`

Every worker handoff records its `lifecycle_stage`, `vertical_capability`, `agent_topology`, `capability_boundary`, `planner_outputs`, and `draft_source`.

## Vertical Capability

Worker handoffs should stay inside one vertical capability:

- `domain-model`
- `api-contract`
- `persistence`
- `service-flow`
- `ui`
- `cli`
- `test-validation`
- `documentation`
- `integration`
- `cleanup`

When a task spans capabilities, the Core Agent should split it into dependent handoffs instead of assigning broad cross-cutting work to one Worker Agent.

## Safety Boundaries

Planning artifacts are optional/contextual. Simple features may produce concise files or `N/A` sections with concrete reasons. The command should avoid large placeholder artifacts and should not move product requirements out of `spec.md`, interface schemas out of `contracts/`, validation decisions out of `research.md`, or quick validation instructions out of `quickstart.md`.

Vertical Planner Agents may read only the planning artifacts required to produce their capability-local shard plan and digest drafts. Worker Agents should treat the final handoff JSON and its digest as the primary context. They should not read full `spec.md`, `plan.md`, `research.md`, `contracts/`, `class-diagram.md`, or `quickstart.md` by default. If the digest contains `context_gaps`, the Worker Agent must stop instead of expanding context on its own.

Completed `[x]` tasks are not scheduled into new implementation handoffs.

## Development

Runtime requirements:

- Spec Kit CLI `>=0.8.10.dev0`
- An agent environment capable of running `/speckit.implement` in Core Agent, Vertical Planner Agent, and Worker Agent modes

Development and release tooling:

- Python 3.10 or newer
- PyYAML and jsonschema for contract tests
- Git
- GitHub CLI `gh` for repository and release publishing

Install development test dependencies:

```bash
python3 -m pip install -r requirements-dev.txt
```

Run the contract tests:

```bash
python3 -m unittest tests/test_preset_contract.py
```

## Preset CI Boundary

This repository owns preset artifact health:

- run `tests/test_preset_contract.py`;
- build `spec-kit-workflow-preset-v<version>.zip`;
- smoke-install this checkout on an Ubuntu GitHub runner with a `specify` CLI built from `bigsmartben/spec-kit`;
- publish or confirm the release artifact for a tag or manual release run;
- create or update a `workflow-preset-release-v<version>` integration PR in `bigsmartben/spec-kit` on tag releases or manual runs with `create_integration_pr=true`.

Manual release runs default to the next patch version when `version` is omitted. For example, a `preset.yml` version of `1.4.0` defaults to release version `1.4.1`.

The integration PR step requires a repository secret named `SPEC_KIT_FORK_PR_TOKEN` with permission to push branches and open pull requests in `bigsmartben/spec-kit`. If a tag release or manual `create_integration_pr=true` run reaches that step without the secret, the workflow fails fast instead of skipping integration PR creation.

This repository owns the release artifact and the fork integration PR. It does not open pull requests to `github/spec-kit`. The `bigsmartben/spec-kit` fork owns downstream integration validation, core workflow fixes, catalog resolver checks, and any later community catalog PR flow.

Optional local CLI sanity check:

```bash
specify preset add --dev /path/to/workflow-preset
specify preset info workflow-preset
specify preset remove workflow-preset
```

Release install smoke validation is intentionally owned by GitHub Actions, not by a local WSL environment.

After tagging a release, validate archive installation:

```bash
specify preset add workflow-preset --from https://github.com/bigsmartben/spec-kit-workflow-preset/releases/download/v1.4.0/spec-kit-workflow-preset-v1.4.0.zip
```

## Source Rationale

See `2026-05-15-plan-design-artifacts-proposal.md` for the design artifact proposal that this preset incorporates.
