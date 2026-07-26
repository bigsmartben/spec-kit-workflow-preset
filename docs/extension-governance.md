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

| Stage | Owner | Durable output |
|---|---|---|
| `/speckit.constitution` | preset wrapper | Constitution and project Architecture |
| `/speckit.specify` | preset wrapper | requirement and UI/UX intent in `spec.md` |
| `/speckit.clarify` | preset wrapper | clarified requirement decisions |
| `/speckit.checklist` | preset wrapper | requirement-readiness gates |
| `/speckit.plan` | preset wrapper | design, behavior contracts, and validation design |
| `/speckit.tasks` | preset wrapper | executable checklist in `tasks.md` |
| `/speckit.analyze` | preset wrapper | read-only consistency findings |
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
spec.md + requirement gates
    -> plan artifacts + BDD/UIF/validation design
    -> tasks.md implementation and validation checklist
    -> core /speckit.implement execution
```

Tasks maps upstream artifacts into checklist items. It must not create another
planning system or execution protocol.

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
