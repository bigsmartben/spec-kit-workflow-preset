# Workflow Preset

This Spec Kit community preset combines design-aware planning with orchestrated implementation.

It keeps `/speckit.plan` and `/speckit.tasks` compatible with the core workflow while adding optional design artifacts for internal object design, service sequencing, and test strategy. It replaces `/speckit.implement` with an orchestrated implementation command that splits incomplete `tasks.md` items into scoped handoff shards and dispatches each shard through an integration CLI.

## Goal

`workflow-preset` turns a Spec Kit feature from a single broad implementation prompt into a staged workflow with stable design context and scoped execution boundaries.

The preset has two goals:

- Preserve richer planning intent so downstream tasks and implementation do not lose object design, service-flow, or validation decisions.
- Execute implementation through bounded handoff shards so each implementation run has explicit task IDs, context, read/write paths, validation commands, and post-dispatch scope checks.

The intended result is a community preset that supports larger Spec Kit features without forcing all design detail into `plan.md` or all implementation work into one high-context `/speckit.implement` run.

## Capabilities

Planning capabilities:

- Wraps `/speckit.plan` to produce optional/contextual design artifacts when useful.
- Keeps `plan.md` focused on technical decisions and navigation.
- Adds plan-template navigation to the core plan output.
- Stores internal object design in `class-diagram.md`.
- Stores service, command, event, async, retry, rollback, and failure-path flows in `contracts/sequences.md`.
- Stores validation strategy and scenario planning in `test-plan.md`.

Task generation capabilities:

- Wraps `/speckit.tasks` so task generation can consume the design artifacts.
- Uses design artifacts to derive implementation, integration, orchestration, failure-handling, and validation tasks.
- Preserves the existing checklist format and user-story organization.

Implementation capabilities:

- Replaces `/speckit.implement` with an orchestrated implementation command.
- Builds handoff shards from incomplete `tasks.md` items.
- Classifies shards as setup, test, implementation, integration, validation, or cleanup.
- Assigns each shard to a matching subagent profile with a fresh process and fresh context.
- Writes one handoff JSON, context digest, and context index per shard.
- Dispatches shards through the configured integration CLI.
- Supports direct single-shard execution with `Use handoff JSON <path>`.
- Supports `dry_run=true` for install and workflow wiring checks.
- Blocks dispatch when generated context has unresolved `context_gaps`.
- Verifies after each shard that file changes and task status changes stay inside the handoff scope.

## Workflow

1. `/speckit.plan` keeps the core planning outputs and adds design artifacts when they help implementation.
2. `/speckit.tasks` reads the core plan outputs plus the design artifacts and produces executable tasks.
3. `/speckit.implement` runs the orchestrator instead of implementing directly.
4. The orchestrator resolves the active feature, parses incomplete tasks, creates scoped handoffs, and dispatches each shard.
5. Each shard runs with its handoff JSON and digest as primary context.
6. The orchestrator stops on failed dispatch, blocking context gaps, out-of-scope file changes, or out-of-scope task status changes.

## Non-Goals

- It does not make every feature produce large diagrams or test matrices.
- It does not move product requirements out of `spec.md`.
- It does not move API or message schemas out of `contracts/`.
- It does not replace `data-model.md`, `research.md`, or `quickstart.md`.
- It does not parallelize shard dispatch; dispatch is intentionally sequential for deterministic long-running execution and easier scope verification.
- It does not allow shard agents to freely expand context by reading full planning documents when the digest is insufficient.

## Install

Release install:

```bash
specify preset add workflow-preset --from https://github.com/bigsmartben/spec-kit-workflow-preset/archive/refs/tags/v1.0.0.zip
```

Local development install:

```bash
specify preset add --dev /path/to/workflow-preset
```

## Usage

Run the normal planning and task generation commands:

```text
/speckit.plan
/speckit.tasks
```

Then run orchestrated implementation:

```text
/speckit.implement
```

The implementation command runs the workflow YAML installed at `.specify/presets/workflow-preset/workflows/speckit-orchestrated-implement/workflow.yml`. For install or wiring checks without invoking an agent, run the workflow with `-i dry_run=true -i run_id=manual`.

Run a single shard directly:

```text
/speckit.implement Use handoff JSON specs/001-demo/handoffs/implement/<run-id>/S01-implement-01.json
```

## Files Written

The core planning workflow still owns its normal artifacts:

- `specs/<feature>/plan.md`
- `specs/<feature>/research.md`
- `specs/<feature>/data-model.md`
- `specs/<feature>/contracts/`
- `specs/<feature>/quickstart.md`
- `specs/<feature>/tasks.md`

This preset adds optional/contextual planning artifacts:

- `specs/<feature>/class-diagram.md`
- `specs/<feature>/contracts/sequences.md`
- `specs/<feature>/test-plan.md`

Orchestrated implementation writes handoff files:

- `specs/<feature>/handoffs/implement/<run-id>/*.json`
- `specs/<feature>/handoffs/implement/<run-id>/*.context.md`
- `specs/<feature>/handoffs/implement/<run-id>/context-index.json`

## Artifact Roles

`class-diagram.md` captures internal implementation object structure: classes, interfaces, abstract types, composition, dependencies, references, and design pattern participants.

`contracts/sequences.md` captures service-call, command, event, external-system, retry, rollback, compensation, async, and failure-path sequencing. Sequences always live at this path, even when there are no other contract files.

`test-plan.md` captures validation intent: test objectives, in/out of scope, test levels, data strategy, requirement traceability, and scenario matrix.

The shard context digest includes these design artifacts when present, so implementation shards can preserve object boundaries, service flows, and validation intent without reading full planning documents by default.

## Subagent Matrix

The implementation orchestrator classifies upstream tasks from `tasks.md` and records the authoritative assignment in each handoff JSON:

- `setup` -> `setup-worker`
- `test` -> `test-worker`
- `implementation` -> `implementation-worker`
- `integration` -> `integration-worker`
- `validation` -> `validation-worker`
- `cleanup` -> `cleanup-worker`

Every shard runs sequentially in its own fresh process and fresh context. The matrix controls the role and lifecycle metadata; it does not imply parallel execution.

## Safety Boundaries

Planning artifacts are optional/contextual. Simple features may produce concise files or `N/A` sections with concrete reasons. The command should avoid large placeholder artifacts and should not move product requirements out of `spec.md`, interface schemas out of `contracts/`, or quick validation instructions out of `quickstart.md`.

Shard agents should treat the handoff JSON and its digest as the primary context. They should not read full `spec.md`, `plan.md`, `contracts/`, `class-diagram.md`, or `test-plan.md` by default. If the digest contains `context_gaps`, the shard must stop instead of expanding context on its own.

Shard agents must honor the handoff `executor_profile`, `task_classification`, `isolation`, and `lifecycle` fields. A shard must not reuse another shard's session, context, or assumptions.

After each successful shard dispatch, the orchestrator compares the workspace against a pre-dispatch snapshot. It fails the run if a shard modifies files outside `allowed_write_paths` or changes `tasks.md` statuses outside its listed `task_ids`.

Completed `[x]` tasks are not scheduled into new implementation shards.

## Development

Runtime requirements:

- Spec Kit CLI `>=0.8.10.dev0`
- Python 3.10 or newer
- `uv` available on `PATH` for workflow shell execution
- A configured Spec Kit integration CLI for shard dispatch, such as `copilot`

Development and release tooling:

- Python 3.10 or newer
- PyYAML for contract tests
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

Validate local installation:

```bash
specify preset add --dev /path/to/workflow-preset
specify preset info workflow-preset
specify preset remove workflow-preset
```

After tagging a release, validate archive installation:

```bash
specify preset add workflow-preset --from https://github.com/bigsmartben/spec-kit-workflow-preset/archive/refs/tags/v1.0.0.zip
```

## Source Rationale

See `2026-05-15-plan-design-artifacts-proposal.md` for the design artifact proposal that this preset incorporates.
