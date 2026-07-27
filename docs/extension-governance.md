# Preset Extension Governance

This document defines the ownership boundaries for `workflow-preset`.

## Source Of Truth

- `preset.yml` declares every packaged command, template, and schema.
- `commands/` contains stage-local instructions.
- `templates/` contains stable artifact shapes.
- `schemas/` contains machine-readable behavior contracts.
- `validators/speckit_behavior_contract.py` contains pure in-memory behavior
  cross-field checks.
- `tests/test_preset_contract.py` is the executable preset contract.

## Preset Boundary

The preset enriches existing Spec Kit stages. It does not own execution
orchestration or add a second implementation engine.

## Authority And Gate Ownership

| Concern | Single owner |
|---|---|
| SDD workflow governance | `.specify/memory/constitution.md` |
| repository technical truth | `.specify/memory/architecture.md` |
| one command's output quality | the producing command |
| official workflow gates | Spec Kit Core, unchanged |
| cross-command consistency | `/speckit.analyze`, read-only |

Intake is external evidence acquisition, not an SDD stage. Constitution does
not contain concrete repository Architecture. Architecture does not contain
command procedures, gate definitions, product requirements, task derivation, or
downstream conformance conclusions.

`/speckit.constitution` is an enforceable replacement command so the authorized
source agreement can suppress unapproved repository inference. It preserves
user input, hooks, independent write scopes, validation, and completion
reporting.

The Constitution command owns two independent internal gates:

- `CONSTITUTION_OUTPUT_READY` validates SDD governance only.
- `ARCHITECTURE_OUTPUT_READY` validates the technical Architecture contract,
  including intent-first Greenfield and repo-first Brownfield generation.

Neither gate checks downstream artifacts. Constitution → Spec/Plan,
Architecture → Plan, Spec → Plan, and Plan → Tasks consistency belong only to
Analyze.

## Analyze Cross-Command Audit

Analyze is the only owner of cross-command consistency:

```text
Constitution -> Spec / Plan
Architecture -> research / data-model / contracts / plan / quickstart
Spec -> X0 / X1 / X2 / X3 / X4
Plan readiness products -> Tasks
Constitution M + U -> Plan / Tasks
```

It inventories once, uses stable IDs first, stops a branch at the first
conclusive blocker, separates blockers from warnings, and writes no artifact.
It audits one repo-first, Architecture-constrained Plan strategy for every
repository; Greenfield/Brownfield remain Constitution-only Architecture
generation modes.

The concrete #24 idempotency, provider binding/lock, retry context, provider
switching recovery, and `ready`/`completed` lifecycle cases are Analyze
fixtures. They are required only when applicable Architecture/Spec refs demand
them, and they do not become a Plan-local conformance gate.

| Stage | Owner | Durable output |
|---|---|---|
| `/speckit.constitution` | preset replacement | independently authorized Constitution and project Architecture outputs |
| `/speckit.specify` | preset replacement | full-spectrum WHAT/WHY content in `spec.md` |
| `/speckit.clarify` | preset replacement | accepted product decisions in `spec.md` |
| `/speckit.checklist` | preset wrapper | unanswered requirement-writing questions |
| `/speckit.plan` | preset wrapper | design, behavior contracts, and validation design |
| `/speckit.tasks` | preset wrapper | executable checklist in `tasks.md` |
| `/speckit.analyze` | preset wrapper | read-only cross-command consistency findings |
| `/speckit.implement` | Spec Kit core | execution of `tasks.md` |

`workflow-preset` MUST NOT declare, package, copy, or replace
`speckit.implement`. The active Spec Kit core version is the single source of
truth for the implementation command. A core implementation change therefore
requires no preset release.

The preset MUST NOT introduce an implementation-specific reviewer command,
runtime role, persistent transfer protocol, execution manifest, worker result
protocol, manual execution queue, or implementation validator.

## Artifact Pipeline

The workflow is a producer-to-consumer pipeline:

```text
spec.md + optional independent requirement-writing checklists
    -> X0 plan control
    -> X1 shared decisions
    -> X2-A domain/object/interface + X2-B UI/UX + X2-C Test contracts
    -> X3 VAL paths + X4 independent readiness
    -> tasks.md implementation and validation checklist
    -> core /speckit.implement execution
```

Tasks maps upstream artifacts into checklist items. It must not create another
planning system or execution protocol.

## Requirement Command Independence

Specify, Clarify, and Checklist are independent:

| Command | Writes | Does not own |
|---|---|---|
| Specify | one `spec.md` plus official feature bootstrap metadata | checklists, completeness/readiness, ID validation |
| Clarify | accepted decisions in `spec.md` | checklist recomputation, source acquisition, cross-artifact checks |
| Checklist | `checklists/<focus>.md` questions | answers, spec repair, readiness aggregation |

The full-spectrum `spec-template` supplies optional carriers for functional,
NFR, UX, UI, visual, security/privacy, data/integration, dependency, boundary,
assumption, exclusion, source, unresolved-decision, source-blocker, and
measurable outcome content. A carrier's presence is not a completeness claim.

Specify and Clarify are replacement commands because active Core side effects
would otherwise create or re-evaluate `checklists/requirements.md`. Their
replacement contracts preserve user input, feature/path resolution, extension
hooks, local write safety, and completion reporting. Checklist remains a Core
wrapper and produces only unanswered question-form checks.

Examples:

- A UI state in `ui-ux-design.md` and `contracts/uif/` becomes concrete UI
  implementation work. Functional tests exist only when Test Readiness contains
  a Required Test Condition.
- A real-system path in `quickstart.md` becomes an integration/e2e task with
  environment and evidence expectations.
- A persistence change becomes implementation and data-side-effect validation
  tasks, followed by the final review scope.

## Source Reference Contract

Authorized external material is an input to existing commands, not an SDD stage
or runtime dependency. `spec.md` carries one canonical, source-neutral shape:

```text
SRC ref | role | opaque locator/description | revision/identity
| authorized scope/facts | projected requirement refs | status/blocker
```

The allowed roles are exactly:

| Role | Local authority |
|---|---|
| `requirement-input` | confirmed, feature-scoped WHAT/WHY facts |
| `visual-input` | feature-scoped `UI-*` and `VIS-*` facts |
| `technical-evidence` | citable evidence that does not become a product requirement |
| `context-only` | informative context with no normative projection authority |

Every used source has one role and a feature slice. A broad source without a
safe slice remains blocked or needs clarification instead of being imported in
full. Supplied URI/path/revision/digest/description values are opaque
provenance; the preset does not infer adjacent scope or validate their external
meaning, authenticity, freshness, publication state, availability, or
fidelity.

After authorized projection, `spec.md` is the feature-local WHAT/WHY SSOT.
Clarify may make a user-accepted local decision current while retaining the
originating `SRC-*` and clarification history; no external write-back or
synchronization is required.

Architecture reuses the four role meanings inside its existing explicit source
agreement without merging Architecture and Specify. Only authorized
`technical-evidence` supports observed or inferred technical records.
Product-facing sources do not become technical decisions automatically.

Plan reads only local Spec, Constitution, Architecture, and current repository
facts. `SRC-*` locators are provenance, not read or execution targets.
Applicable visual projection follows:

```text
SRC-* + UI/VIS-* -> ui-ux-design.md -> UIF source_refs + requirement_refs
```

Tasks uses that local mapping for implementation guidance only. Analyze checks
local source existence, uniqueness, role compatibility, projection targets,
orphans, contradictions, and X2-B/UIF mappings. Neither command acquires,
dereferences, executes, compares, or certifies an external source.

## Final Code Review Gate

`/speckit.tasks` MUST append Final Code Review as the last mandatory phase of
`tasks.md`. It is an ordinary ordered task phase executed by the standard core
implementation command, not an independent runtime.

The phase must cover each applicable scope:

- planned `M + U` boundary;
- interface contracts;
- behavior and Test contracts;
- UI component/state, responsive/accessibility behavior, and asset contracts;
- data side effects;
- sequence consistency;
- asset bindings;
- integration/e2e evidence and unresolved blockers.

Completion requires the review tasks themselves to pass. No separate worker
result file or orchestration layer is required.

UI review is code/design-contract review. Tasks and Final Code Review never
create or evaluate visual acceptance, pixel fidelity, screenshot comparison,
visual diff, baseline capture, visual restoration, or final rendered-visual
review. Visual/IR/source refs may guide implementation but do not create a
validation task.

## Tasks As A Pure Plan Mapper

`/speckit.tasks` starts from `PLAN_OUTPUT_READY`, not Spec or Checklist strategy.
Its lifecycle is:

```text
T0 handoff preflight
  -> T1 concrete path binding
  -> T2 dependency graph
  -> T3 story/capability mapping
  -> T4 required functional validation/evidence
  -> T5 Final Code Review (last mandatory phase)
```

Tasks owns exact paths, task IDs, dependency order, `[P]`, and checklist shape.
It preserves Plan-selected design/test/UI decisions. Missing mappings produce
`PLAN_OUTPUT_INCOMPLETE`; Tasks does not reconstruct them.

A Required `TC-*` overrides Core's generic optional-test wording. UI,
accessibility, responsive, and journey tests exist only when Test Readiness
requires them. UI/UX Delivery Readiness otherwise maps only to component, state,
interaction, accessibility, responsive, asset, variant, and fallback
implementation work.

## Structured Artifact Rules

Machine-readable JSON artifacts are contracts, not prose examples. Stable
behavior JSON artifacts require schemas in `schemas/` and focused coverage in
`validators/speckit_behavior_contract.py` when cross-field rules matter.

Every packaged schema and validator must be covered by
`tests/test_preset_contract.py`.

## Cross-Agent Rules

Planning and task derivation may use bounded, stage-local subagents when the
runtime supports them. The owning command remains the sole final writer for its
stage. Delegation metadata is transient derivation context and must not become
an implementation transfer format.

Shared stage-local behavior is documented in
`tests/contracts/speckit-cross-agent-protocol.md`. Commands may reference only
their own stage profile. Commands must not use `tests/` or `docs/` paths as
runtime sources.

## X0–X4 Planning Artifact Boundaries

Keep `/speckit.plan` and `/speckit.tasks` as core-template wrappers unless an
intentional contract change says otherwise.

The X labels are preset-internal milestones nested inside unchanged Core Plan
setup, Phase 0, Phase 1, post-design Constitution Check, hooks, and completion:

| Milestone/lane | Owning artifact |
|---|---|
| X0 Feature Plan Control | `plan.md` |
| X1 Research & Decisions | `research.md` |
| X2-A Domain/Object/Interface | `data-model.md`, contextual `class-diagram.md`, interface contracts, contextual `contracts/sequences.md` |
| X2-B UI/UX Delivery | `ui-ux-design.md`, `contracts/uif/` |
| X2-C Test & Acceptance | `contracts/test/test-conditions.json`, optional technique children |
| X3 Validation Paths | `quickstart.md` `VAL-*` paths |
| X4 Design Readiness | `plan.md` derivation index |
| X4 UI/UX Delivery Readiness | `ui-ux-design.md` |
| X4 Test Readiness | `test-readiness.md` |

X2-A, X2-B, and X2-C are parallel and mutually constraining. BDD is an optional
Test technique, not the parent of planning. Test Conditions may cover
functional, accessibility, security, performance, reliability, recovery,
compatibility, and data-side-effect concerns across unit/component/contract/
integration/system/e2e levels.

Pixel-fidelity delivery and review belong only to UI/UX Delivery Readiness.
Pixel, screenshot, diff, baseline, restoration, and rendered-visual-review work
is rejected from Test Conditions and Test Readiness.

Validation decisions stay in `research.md`, executable paths stay in
`quickstart.md`, and `test-readiness.md` is the single Test/Tasks handoff. Do
not restore `behavior/behavior-testability.md`, create a generic
`planning-readiness.md`, or add a standalone `test-plan.md`.

## External Source Boundary

External source capture, access, authentication, rendering, and evidence
generation remain outside this preset. The preset does not require an upstream
workflow, directory convention, provider, artifact format, publication state,
import manifest, handoff package, adapter runtime, orchestration script, or
provider-specific schema.

Missing source evidence remains a local `SRC-*` blocker. Product decision gaps
return to clarification. Planning, Tasks, and Analyze do not acquire or repair
either kind of gap, and Intake is not added as an SDD stage.

## Release And Integration Boundary

The source repository owns development, tests, tags, releases, and release
artifacts. The Spec Kit fork owns only a reproducible bundled snapshot and
catalog metadata.

Integration must use an immutable release:

1. publish a new source version;
2. record the source repository, version, commit SHA, artifact URL, and artifact
   SHA-256;
3. extract the bundled snapshot without edits;
4. verify every bundled file hash against the release manifest;
5. ensure bundled and `--from <version>` installations are identical.

Never change a published version in place or modify the bundled snapshot after
integration.

## Validation

Run:

```bash
python3 -m unittest tests/test_preset_contract.py
```

Release preparation must also run the install smoke checks in
`.github/workflows/preset-artifact.yml`.
