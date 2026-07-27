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
    -> plan artifacts + BDD/UIF/validation design
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
| Clarify | accepted decisions in `spec.md` | checklist recomputation, provider intake, cross-artifact checks |
| Checklist | `checklists/<focus>.md` questions | answers, spec repair, readiness aggregation |

The full-spectrum `spec-template` supplies optional carriers for functional,
NFR, UX, UI, visual, security/privacy, data/integration, dependency, boundary,
assumption, exclusion, source, unresolved-decision, provider-gap, and measurable
outcome content. A carrier's presence is not a completeness claim.

Specify and Clarify are replacement commands because active Core side effects
would otherwise create or re-evaluate `checklists/requirements.md`. Their
replacement contracts preserve user input, feature/path resolution, extension
hooks, local write safety, and completion reporting. Checklist remains a Core
wrapper and produces only unanswered question-form checks.

Examples:

- A UI state in `spec.md` and `contracts/uif/` becomes a concrete UI
  implementation task plus a UI acceptance task.
- A real-system path in `quickstart.md` becomes an integration/e2e task with
  environment and evidence expectations.
- A persistence change becomes implementation and data-side-effect validation
  tasks, followed by the final review scope.

## Final Code Review Gate

`/speckit.tasks` MUST append Final Code Review as the last mandatory phase of
`tasks.md`. It is an ordinary ordered task phase executed by the standard core
implementation command, not an independent runtime.

The phase must cover each applicable scope:

- planned `M + U` boundary;
- interface contracts;
- behavior contracts;
- UI state, viewport, and visual/IR consistency;
- data side effects;
- sequence consistency;
- asset bindings;
- integration/e2e evidence and unresolved blockers.

Completion requires the review tasks themselves to pass. No separate worker
result file or orchestration layer is required.

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

## Planning Artifact Boundaries

Keep `/speckit.plan` and `/speckit.tasks` as core-template wrappers unless an
intentional contract change says otherwise.

Optional contextual design artifacts include:

- `class-diagram.md`
- `contracts/sequences.md`

Validation decisions stay in `research.md`, executable paths stay in
`quickstart.md`, and BDD Plan closeout maps them into
`behavior/behavior-testability.md`. `/speckit.tasks` derives unit, contract,
integration, UI acceptance, real-system e2e, and review tasks from that mapping.
Do not add a standalone `test-plan.md`.

## External Intake Boundary

External source capture, provider access, rendered HTML, structured IR,
screenshots, authentication, and provider evidence generation belong to
extensions. This preset only consumes confirmed refs already projected into
requirements and readiness artifacts.

Provider evidence gaps remain intake blockers. Product decision gaps return to
clarification. Neither planning nor implementation may silently manufacture
missing evidence.

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
