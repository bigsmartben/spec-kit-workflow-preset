# Codex Project Instructions

This repository is a Spec Kit community preset named `workflow-preset`.

## Project Shape

- `preset.yml` is the preset manifest and should stay aligned with the files it declares.
- `commands/` contains Spec Kit command templates.
- `templates/` contains wrapped Spec Kit templates.
- `workflows/speckit-orchestrated-implement/workflow.yml` runs the orchestrated implementation workflow.
- `scripts/build-task-shards.py` builds scoped implementation handoff files.
- `scripts/run-orchestrated-implement.py` dispatches those handoffs and verifies shard scope.
- `tests/test_preset_contract.py` is the main contract test suite.

## Development Rules

- Preserve the preset contract tested by `tests/test_preset_contract.py`.
- Keep `/speckit.plan` and `/speckit.tasks` as core-template wrappers.
- Keep `/speckit.implement` as a replacement command that runs the orchestrated workflow or executes exactly one handoff shard.
- Planning design artifacts are optional and contextual:
  - `class-diagram.md`
  - `contracts/sequences.md`
  - `test-plan.md`
- Do not move product requirements out of `spec.md`, domain model details out of `data-model.md`, interface schemas out of `contracts/`, or validation run guidance out of `quickstart.md`.

## Handoff Boundaries

When working from a generated handoff JSON:

- Treat the handoff JSON and its `context_digest_path` as primary context.
- Verify `contract_type` is `speckit.implement.handoff.v2`.
- Stop before editing if `context_gaps` is not empty.
- Execute only the listed `task_ids`.
- Write only paths listed in `allowed_write_paths`.
- Mark only completed listed tasks in `tasks.md`.
- Do not read full `spec.md`, `plan.md`, `contracts/`, `class-diagram.md`, or `test-plan.md` unless the handoff explicitly allows it.

## Validation

Run the focused contract tests after changes:

```bash
python3 -m unittest tests/test_preset_contract.py
```

For local preset installation checks, the `specify` CLI must be available on `PATH`.
