# Codex Project Instructions

This repository is a Spec Kit community preset named `workflow-preset`.

## Project Shape

- `preset.yml` is the preset manifest and should stay aligned with the files it declares.
- `commands/` contains Spec Kit command templates.
- `templates/` contains wrapped Spec Kit templates.
- `schemas/` contains decoupled JSON schema contracts.
- `validators/` contains pure in-memory contract validators for tests.
- `tests/test_preset_contract.py` is the main contract test suite.

## Development Rules

- Preserve the preset contract tested by `tests/test_preset_contract.py`.
- Follow the Extension Governance in `docs/extension-governance.md` before adding or changing preset commands, templates, schemas, validators, or behavior-first artifacts.
- Keep `/speckit.plan` and `/speckit.tasks` as core-template wrappers.
- Do not declare, copy, or replace `/speckit.implement`; implementation execution
  belongs to the currently installed Spec Kit core command.
- Keep Final Code Review as the last mandatory phase generated in `tasks.md`.
- Do not introduce an implementation reviewer runtime, persistent transfer
  protocol, execution manifest, worker result protocol, Python orchestration,
  workflow shell dispatch, integration adapter scripts, or script-based worker
  dispatch.
- Planning design artifacts are optional and contextual:
  - `class-diagram.md`
  - `contracts/sequences.md`
- Validation decisions stay in `research.md` and executable paths in
  `quickstart.md`; plan closeout maps them into
  `behavior/behavior-testability.md`, and `/speckit.tasks` derives concrete
  tasks. Do not add standalone `test-plan.md`.
- Do not move product requirements out of `spec.md`, domain model details out of `data-model.md`, interface schemas out of `contracts/`, or validation run guidance out of `quickstart.md`.

## Integration Boundary

- This repository owns the `workflow-preset` source, tests, release artifact,
  and source documentation.
- Do not open pull requests from this repository directly to `github/spec-kit`.
- Do not push branches to `github/spec-kit` or add workflow automation that
  targets `github/spec-kit` for pull requests, repository dispatches, or direct
  writes.
- If a Spec Kit catalog or bundled snapshot update is needed, target the
  `bigsmartben/spec-kit` integration fork first. The integration fork owns any
  downstream pull request to `github/spec-kit`.
- Source releases must provide source-backed metadata for the integration fork:
  repository URL, release version, source commit SHA, download URL, and
  validation evidence.

## Validation

Run the focused contract tests after changes:

```bash
python3 -m unittest tests/test_preset_contract.py
```

For local preset installation checks, the `specify` CLI must be available on `PATH`.
