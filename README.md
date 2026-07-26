# Workflow Preset

`workflow-preset` extends Spec Kit with Constitution-managed project
Architecture, behavior-first requirements and planning, UI/UX delivery
contracts, and an execution-ready task mapping.

It deliberately does **not** provide `speckit.implement`. After installation,
`/speckit.implement` always resolves to the implementation command supplied by
the currently installed Spec Kit core.

## Ownership Model

| Stage | What this preset adds | Primary output |
|---|---|---|
| Specify | behavior, visual, and UI/UX requirement ownership | `spec.md` |
| Checklist | requirement-domain readiness gates | `checklists/*.md` |
| Plan | Architecture consumption, BDD/UIF contracts, validation design | `plan.md`, `research.md`, `quickstart.md`, `contracts/`, behavior artifacts |
| Tasks | mapping of upstream artifacts to ordered implementation, validation, e2e, and review work | `tasks.md` |
| Implement | no preset override; standard core behavior | execution of `tasks.md` |

The lifecycle is:

```text
spec requirements and UI/UX intent
    -> requirement readiness gates
    -> plan, behavior/UI contracts, and validation design
    -> tasks.md execution checklist
    -> standard core implement
```

## Commands

The preset packages seven command wrappers:

1. `/speckit.specify`
2. `/speckit.clarify`
3. `/speckit.checklist`
4. `/speckit.constitution`
5. `/speckit.plan`
6. `/speckit.tasks`
7. `/speckit.analyze`

`speckit.implement` is intentionally absent from `preset.yml` and `commands/`.
This prevents the preset from freezing or shadowing a core implementation
command.

## UI/UX From Specify

UI/UX is a requirement concern before it is an implementation concern.
`/speckit.specify` records applicable visual and interaction needs in
`spec.md`, including states, viewport behavior, source/evidence refs, and Client
Asset Contract expectations. `/speckit.checklist` decides whether those
requirements are ready for planning.

External provider capture stays outside the preset. Confirmed visual SSOT refs,
HTML SSOT refs, structured IR refs, screenshots, and visual proof refs may be
consumed after an intake extension has projected them into the specification.
Missing provider evidence remains an intake blocker; it is not converted into a
product clarification.

Example:

```text
Requirement: Checkout shows loading, success, validation-error, and
payment-declined states at desktop and mobile viewports.
```

The Visual Fidelity Evidence Matrix in `checklists/visual.md` records the
planning-readiness status of that requirement. It does not define screenshot
comparison, visual diff, baseline capture, or final visual review work.

## Validation Design From Plan

`/speckit.plan` consumes checklist-approved requirements and creates the
technical and validation contracts required for task derivation:

- `research.md` records validation decisions, test levels, fixture strategy,
  and external-system strategy.
- `quickstart.md` records executable validation paths and real-system
  integration/e2e scenarios.
- `behavior/bdd.draft.feature`, `behavior/uif.intent.json`, and
  `behavior/data-fixtures.intent.json` provide Phase 0 projections.
- `contracts/bdd/`, `contracts/uif/`, and `contracts/behavior/` contain formal
  behavior contracts.
- `behavior/behavior-testability.md` closes the BDD Plan with a READY or
  BLOCKED decision.
- `class-diagram.md` and `contracts/sequences.md` are optional contextual design
  artifacts.

This is broader than unit testing. Applicable plans cover unit, contract,
integration, UI acceptance, and real-system e2e validation.

Example:

```text
quickstart.md: a buyer submits a refund against a sandbox payment service and
observes the persisted refund plus the user-visible confirmation state.
```

That path is a source for integration/e2e tasks, not an implementation detail
invented later by Tasks or Implement.

## Tasks Is A Mapping Stage

`/speckit.tasks` produces only `tasks.md`. It maps upstream deliverables into
the core checklist format and user-story organization.

For each applicable story, it derives:

- fixtures and environment setup;
- unit and contract validation;
- UI implementation and UI acceptance;
- implementation work;
- data-side-effect validation;
- integration and real-system e2e validation;
- evidence collection and blocker reporting.

Task text binds the work to concrete source, test, fixture, configuration, and
asset paths plus upstream scenario, contract, visual/IR, or quickstart refs.
Tasks does not create a second plan, execution manifest, transfer file, worker
result file, write-path protocol, or execution queue.

Example mapping:

| Upstream product | `tasks.md` result |
|---|---|
| `SCN-ERR-001` permission failure | fixture + BDD/contract test + implementation + evidence tasks |
| Expected UIF submit event and error feedback | UI implementation + UI acceptance tasks |
| `quickstart.md` sandbox refund path | integration/e2e environment + execution + evidence tasks |
| persistence update rules | implementation + data-side-effect validation tasks |

## Mandatory Final Code Review

Tasks appends **Final Code Review** after all user-story, integration, and
validation work. It is a mandatory final phase in `tasks.md`, so the standard
core implementation command executes it in normal checklist order.

The phase includes applicable checks for:

- the planned `M + U` boundary;
- interface and behavior contracts;
- implemented UI states and viewport behavior;
- visual/IR traceability refs and Client Asset Contract bindings;
- field-level and runtime data side effects;
- cross-boundary sequence consistency;
- integration/e2e evidence and unresolved blockers.

Code Review is not a separate command, reviewer runtime, or orchestration
protocol. Completion means the review checklist items pass; failures remain
open tasks or explicit blockers.

## Architecture And Scope

`/speckit.constitution` manages separate project-level artifacts:

- `.specify/memory/constitution.md`
- `.specify/memory/architecture.md`

The Architecture follows the System Boundary -> Conceptual Model -> Technical
Decisions & Evidence -> Planning Guardrails & Gaps chain.

Change Scope Granularity uses the fixed R/M/U/O model: R is Repository / Workspace, M is Module / Capability, U is Unit / Design Object, and O is Operation / Detail. Planning locks `M + U`; Tasks maps those design objects to concrete executable paths without widening the planned boundary.

## Behavior Contracts

The preset packages separate templates and JSON schemas for behavior drafts,
Expected UIF, scenario instances, fixtures, and assertions.
`validators/speckit_behavior_contract.py` checks cross-field relationships such
as scenario-to-fixture references, exception-case structure, Expected UIF
steps, and required-case coverage.

The behavior validator is independent of implementation execution. There are no
implementation manifest, transfer, or worker-result schemas in this package.

## Install

Development checkout:

```bash
specify preset add --dev /path/to/spec-kit-workflow-preset
```

Published release:

```bash
specify preset add --from https://github.com/bigsmartben/spec-kit-workflow-preset/releases/download/v3.0.0/spec-kit-workflow-preset-v3.0.0.zip
```

After installation, resolve a preset-owned wrapper:

```bash
specify preset resolve speckit.tasks
```

Resolve implementation through the normal command surface. Because the preset
does not declare it, `speckit.implement` comes from the active Spec Kit core.

## Release Integrity

A source release is immutable. The integration fork must record:

- source repository URL;
- release version;
- source commit SHA;
- release download URL;
- release artifact SHA-256;
- per-file hashes from the release manifest.

The fork extracts the release snapshot without edits. Bundled installation and
installation from the same release must produce identical preset files and
manifest content. Any functional change requires a new source version; a
published version is never modified in place.

## Development

Install test requirements and run the contract suite:

```bash
python3 -m pip install -r requirements-dev.txt
python3 -m unittest tests/test_preset_contract.py
```

Repository extension rules are in
[`docs/extension-governance.md`](docs/extension-governance.md).
