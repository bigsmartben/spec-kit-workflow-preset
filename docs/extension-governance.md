# Preset Extension Governance
This document is the repository-level rule set for extending `workflow-preset`.
It exists to keep preset changes aligned with Spec Kit's preset model and this
repository's contract tests.

## Source Of Truth
- `preset.yml` declares every packaged command, template, schema, and script.
- `commands/` contains stage-local LLM instructions.
- `templates/` contains stable artifact shapes.
- `schemas/` contains machine-readable JSON contracts.
- `validators/` contains pure in-memory cross-field contract checks.
- `tests/test_preset_contract.py` is the executable contract for this preset.

## Preset Boundaries

Presets customize existing Spec Kit workflows by overriding or composing
commands, templates, and scripts. Use extensions, not presets, for new tooling,
external integrations, static analyzers, workflow runners, or commands that add
a new capability outside the existing Spec Kit workflow.

Do not reintroduce Python orchestration, workflow shell dispatch, integration
adapter scripts, or worker dispatch from scripts.

Source intake artifacts belong in an extension, not this preset. External intake owns source capture, provider evidence, provider metadata, rendered HTML SSOT bundles, structured IR artifacts,
source-side readiness, and blocker codes. This preset may consume confirmed
external intake artifact refs, visual SSOT refs, HTML SSOT refs, structured IR refs,
source refs, coverage gaps, readiness inputs, accepted exception refs, and provider blockers already cited in `spec.md`.
External evidence refs are consumed as source, readiness, blocker, and traceability inputs only. Provider tools, provider execution, hooks, adapter scripts,
and authentication are external integration concerns and remain outside this
preset.

## Template And Command Ownership

- templates own stable artifact shapes.
- commands own stage-local generation instructions.
- Commands may name the inputs they consume, the outputs they write, and the
  local update rules for their own phase.
- Do not put downstream prohibitions in upstream commands.
- Do not encode full output structures only inside command text when the output
  is intended to be durable or reused by later phases.

Stage ownership:

- `/speckit.constitution`: constitution governance and project principles only.
- `/speckit.specify`: requirement artifacts only.
- `/speckit.clarify`: product-decision clarification and affected requirement-gate recomputation only.
- `/speckit.checklist`: requirements, behavior, UX, security, NFR, and visual requirement gates only.
- `/speckit.plan`: Phase 0 behavior projection, planning artifacts, formal contracts, and BDD Plan closeout.
- `/speckit.tasks`: `tasks.md` only.
- `/speckit.analyze`: vertical consistency checks across requirements, behavior drafts, contracts, and tasks only.
- `/speckit.implement`: implementation handoff execution only.

`/speckit.tasks` owns implementation, non-visual acceptance, contract validation, data-side-effect validation, integration/e2e validation, and code review task definition in `tasks.md`. `/speckit.implement` may execute those tasks and record receipt evidence, but it must not invent validation strategy, visual validation work, lifecycle roles, requirements, contract updates, or wider scope during execution.

When external intake evidence or visual SSOT refs have already been projected into `spec.md`, `/speckit.clarify` may clarify those requirement gaps from `spec.md`, but extraction remains outside clarification.
External design extraction is not a clarification responsibility.

Visual Fidelity readiness applies to external-intake-derived and product-side
visual requirements. `checklists/visual.md` and its Visual Fidelity Evidence
Matrix are the single visual requirement-readiness record. Provider evidence
gaps remain intake blockers. The matrix must not define visual validation work,
screenshot comparison, visual diff, baseline capture, or final visual review.

## Structured Artifact Rules

Machine-readable JSON artifacts are contracts, not prose examples. Stable
structured JSON artifacts require schemas in `schemas/` and focused validator
coverage in `validators/` when cross-field rules matter.

Every schema or validator added for a preset artifact must be covered by
`tests/test_preset_contract.py`.

## Cross-Agent Protocol Rules

Shared multi-agent runtime behavior belongs in command source, schemas, and validators.
Test coverage for shared multi-agent behavior belongs in `tests/contracts/speckit-cross-agent-protocol.md`.
Commands may reference only their own profile. A profile inherits scheduling
protocol fields, not execution permissions from another command.
Commands must not reference `tests/` or `docs/` paths as runtime contract sources.

Persistent handoff orchestration belongs only to `/speckit.implement`.
Manifest files, handoff files, receipts, `allowed_write_paths`, dispatch
readiness, commit readiness, and manual worker queues must not be introduced
into `/speckit.specify`, `/speckit.plan`, `/speckit.tasks`, or
`/speckit.analyze`.

The implement handoff runtime profile lives in `commands/speckit.implement.md`;
test coverage lives in `tests/contracts/speckit-cross-agent-subagents.md`.
Both must stay aligned with the implement schemas and validator gates.

## Behavior-first extension rule

BDD and UIF artifacts need independent templates. A behavior-first extension
must not rely only on command prose to define:

- BDD draft files.
- UIF intent files.
- data fixture intent files.
- behavior scenario draft files.
- formal BDD contracts.
- Expected UIF contracts.
- behavior scenario, fixture, and assertion contracts.

Phase 0 behavior drafts and planning-phase formal contracts must be separate
artifacts with separate owners. If they are JSON, they also need schemas and
validator coverage.

## Planning Artifact Boundaries

Keep `/speckit.plan` and `/speckit.tasks` as core-template wrappers unless the
contract tests are intentionally updated to change that rule.

Planning design artifacts remain optional and contextual:

- `class-diagram.md`
- `contracts/sequences.md`

Validation decisions are recorded in `research.md`, executable paths in
`quickstart.md`, and the BDD Plan closeout maps them to Required Cases in
`behavior/behavior-testability.md`. `/speckit.tasks` derives concrete tasks from
that READY mapping. Do not add a standalone `test-plan.md`.

Planning Readiness is aggregated at runtime from metadata-bearing requirement
gates. It is not a durable artifact and must never be written as
`planning-readiness.md`.

`behavior/behavior-testability.md` is a permitted planning artifact, not a test
strategy document. It contains the task-derivation matrix and READY/BLOCKED
decision; it must not duplicate requirement prose, provider intake, or
clarification.

Keep product requirements in `spec.md`, including explicit NFR assumptions;
NFR readiness belongs in `spec.md` product requirements rather than downstream
planning guesses. Keep domain model details in `data-model.md`, interface
schemas in `contracts/`, and validation run guidance in `quickstart.md`.

For visual planning, research.md records visual/IR source refs, readiness inputs, accepted exception refs, related contract paths, and unresolved blocker refs only; it must not duplicate the Visual Fidelity Evidence Matrix or define visual validation strategy, screenshot comparison, visual diff, baseline capture, or final visual review. contracts formalize visual interaction and state constraints by referencing accepted visual items, source refs, structured IR refs, and accepted exception refs; contracts/sequences.md records visual state flow only when it affects cross-boundary sequencing, async callbacks, retry, rollback, compensation, or error propagation, and must not define visual style, tokens, layout breakpoints, screenshot matrices, or validation commands.

## Handoff Extension Rules

Handoff extensions must update schema, validator, command, and cross-agent documentation together.
Any new implementation-stage artifact that Worker
Agents may read or write must be reflected in:

- `schemas/speckit.implement.*.schema.json` when the JSON contract changes.
- `validators/speckit_implement_contract.py` when cross-field validation changes.
- `commands/speckit.implement.md` when Core, Vertical Planner, or Worker
  behavior changes.
- `tests/contracts/speckit-cross-agent-protocol.md` when shared profile behavior changes.
- `tests/contracts/speckit-cross-agent-subagents.md` when implement worker prompts,
  context digest rules, shard rules, or path rules change.
- `tests/test_preset_contract.py` for all of the above.

## Release Discipline

Do not bump preset version or release archive URLs until release preparation.
Unreleased behavior belongs under `## Unreleased` in `CHANGELOG.md`.

## Verification

After changing preset commands, templates, schemas, validators, governance docs,
or public documentation, run:

```bash
python3 -m unittest tests/test_preset_contract.py
```

If the system Python lacks development dependencies, use a local virtual
environment and the same unittest command from that environment.
