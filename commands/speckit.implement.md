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
specify workflow run .specify/presets/workflow-preset/workflows/speckit-orchestrated-implement/workflow.yml -i integration=__AGENT__ -i args="$ARGUMENTS"
```

Do not manually invoke `/speckit.implement` from orchestration mode.

## Handoff

1. Read the handoff JSON file.
2. Verify `contract_type` is `speckit.implement.handoff.v2`.
3. Verify `task_type`, `executor_type`, `execution_body`, `lifecycle`, and `scope` are present.
4. Execute exactly one shard; do not reuse this context for another shard.
5. Load `context_digest_path`.
6. Treat digest content from `class-diagram.md`, `contracts/sequences.md`, and `test-plan.md` as implementation constraints when present.
7. Do not read full `spec.md`, `plan.md`, `contracts/`, `class-diagram.md`, or `test-plan.md`.
8. If `context_gaps` is not empty, stop before editing.
9. Use `context_index_path` only for headings and digest source refs.
10. Execute only `task_ids`.
11. Write only `allowed_write_paths`.
12. Follow `forbidden_actions`.
13. Mark only completed listed tasks in `tasks.md`.
14. Run `validation_commands` and focused validation for changed files.

Do not run `specify workflow run` in handoff mode.
