---
description: Run orchestrated implementation or execute a single handoff shard.
---

## Input

```text
$ARGUMENTS
```

## Mode

- Handoff mode: `$ARGUMENTS` contains a `.json` handoff path or `Use handoff JSON <path>`.
- Orchestration mode: no handoff JSON is present.

## Orchestration

```sh
uv run .specify/presets/workflow-preset/scripts/run-orchestrated-implement.py --project-root . --integration __AGENT__ --args="$ARGUMENTS"
```

Do not manually invoke `/speckit.implement` from orchestration mode.

## Subagent Matrix

The orchestrator classifies upstream tasks and writes the authoritative
subagent assignment into each handoff JSON. Use the matrix below only as the
human-readable execution policy:

- setup -> setup-worker
- test -> test-worker
- implementation -> implementation-worker
- integration -> integration-worker
- validation -> validation-worker
- cleanup -> cleanup-worker

Each shard must run with a fresh process and fresh context. Shards are
dispatched sequentially; parallelism is none. Do not reuse a previous shard's
session, memory, prompt context, or task assumptions.

## Handoff

1. Read the handoff JSON file.
2. Verify `contract_type` is `speckit.implement.handoff.v2`.
3. Verify `task_type`, `shard_type`, `executor_type`, `executor_profile`, `task_classification`, `isolation`, `execution_body`, `lifecycle`, and `scope` are present.
4. Execute exactly one shard; do not reuse this context for another shard.
5. Load `context_digest_path`.
6. Treat digest content from `class-diagram.md`, `contracts/sequences.md`, and `test-plan.md` as implementation constraints when present.
7. Do not read full `spec.md`, `plan.md`, `contracts/`, `class-diagram.md`, or `test-plan.md`.
8. If `context_gaps` is not empty, stop before editing.
9. Use `context_index_path` only for headings and digest source refs.
10. Execute only `task_ids` using the declared `executor_profile`.
11. Write only `allowed_write_paths`.
12. Follow `forbidden_actions`.
13. Mark only completed listed tasks in `tasks.md`.
14. Run `validation_commands` and focused validation for changed files.

Do not run `specify workflow run` in handoff mode.
