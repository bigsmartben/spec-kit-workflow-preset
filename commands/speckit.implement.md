---
description: Run implement orchestration.
---
## Input
`$ARGUMENTS`; runtime hint: `agent-runtime=<spec-kit-integration-key>`.
## Mode
- Core mode: no handoff JSON path in `$ARGUMENTS`.
- Worker mode: `.json` handoff path in `$ARGUMENTS` or `Use handoff JSON <path>`.
- Forbidden: dispatch scripts, workflow runners, inline worker execution.
## Authority
- Core Agent: build `context-index.json` and `handoff-manifest.json`; dispatch, review receipts,
  update `tasks.md`, verify integration.
- Vertical Planner Agent: plan one `vertical_capability`, draft shard plans and handoff/context digests, never execute.
- Worker Agent: execute exactly one handoff; never edit `tasks.md`, create handoffs, or dispatch workers.
## Core Agent
- Follow cross-agent protocol profile: `speckit.implement.persistent_handoff_orchestration`.
- Use only this command, implement schemas, and implement validators as runtime contract sources.
- Map planned `U` design objects to concrete source, test, fixture, configuration, and receipt paths.
- Use `isolated_subagent` only with isolated subagent/subsession execution; otherwise use `manual_fresh_worker_session`.
- If isolation is unavailable or unknown, write the manifest and handoffs, then stop with `Manual Worker Queue` entries:
  `1. /speckit.implement Use handoff JSON <path>`.
- Consume planner outputs and worker receipts, not worker conversation history.
## Visual Implementation Boundary
- Visual Fidelity Readiness `Requirement Status` is `Required` or `Required` plus an accepted exception.
  This is the `/speckit.tasks` visual task input filter.
- Do not create handoffs or worker instructions for visual rows with `Requirement Status`
  `Not Applicable`, `Unknown`, or `[BLOCKED: PROVIDER_EVIDENCE]`.
- Route `Unknown` visual rows back to `/speckit.clarify`.
- Route `[BLOCKED: PROVIDER_EVIDENCE]` visual rows to the external intake extension;
  do not repair provider evidence in `/speckit.implement`.
- `/speckit.implement` must not discover visual requirements, repair Visual Fidelity Readiness evidence,
  or edit upstream artifacts for execution.
- Visual worker receipts must reference the relevant Visual Item ID, `Requirement Status`, and evidence refs.
## Vertical Planner Agent
- Read only `tasks.md`, `context-index.json`, and allowed planning artifacts.
- Preserve order, dependencies, capability boundaries, and Change Scope Granularity.
- Put unresolved shard, context, asset, path, visual status, evidence, or fallback gaps into `context_gaps`.
- Emit drafts that validate against the handoff schema before Core assembly.
## Worker Agent
- Reject non-existent handoff paths.
- Reject handoffs not listed in `handoff-manifest.json`.
- Verify `contract_type` is `speckit.implement.handoff.v2`; load `context_digest_path`; stop on `context_gaps`.
- Execute only `task_ids`; read only `allowed_read_paths`; write only `allowed_write_paths`.
- Select Implementation Worker or Code Review Worker by `task_type`.
- Visual/UI implementation is implementation work; UI consistency review is code review.
- Write `task_status_update.receipt_path` as `speckit.implement.receipt.v1`.
- For visual/UI handoffs, validate task text and preserve visual/IR traceability refs.
- Use empty `completed_task_ids` when required provider evidence is unavailable.
- Do not edit `tasks.md`.
## Contract References
- Runtime, shard, digest, path, asset binding, dispatch, Worker Prompt, and receipt rules are source-owned here.
- Schemas: `schemas/speckit.implement.manifest.v1.schema.json`,
  `schemas/speckit.implement.handoff.v2.schema.json`,
  `schemas/speckit.implement.receipt.v1.schema.json`.
- Gates in `validators/speckit_implement_contract.py`: `validate_manifest_structure()`,
  `validate_handoff_structure()`, `validate_dispatch_ready()`, `validate_receipt_structure()`,
  `validate_commit_ready()`.
## Runtime Stops
- Stop on missing handoff files, unlisted handoffs, non-empty `context_gaps`, schema mismatch,
  current-role writes outside `allowed_write_paths`, or planning artifact updates.
- Stop instead of inventing validation strategy, roles, requirements, contract updates, wider scope,
  or validation planning artifacts.
