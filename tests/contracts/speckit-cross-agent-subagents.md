# Spec Kit Implement Handoff Profile

## Purpose
Follow cross-agent protocol profile: `speckit.implement.persistent_handoff_orchestration`.
Reduce implementation-stage context load and reasoning drift by turning broad `/speckit.implement` work into persisted, capability-scoped handoffs. Workers receive only task-local context, allowed paths, validation commands, and receipt obligations.

## Files, Schemas, and Gates
- `handoffs/implement/<run-id>/handoff-manifest.json`, `planner-outputs/`, `context-index.json`, `<shard>.json`, `<shard>.context.md`, `results/<shard>.json`
- schemas: `schemas/speckit.implement.manifest.v1.schema.json`, `schemas/speckit.implement.handoff.v2.schema.json`, `schemas/speckit.implement.receipt.v1.schema.json`
- validators: `validate_manifest_structure()`, `validate_handoff_structure()`, `validate_dispatch_ready()`, `validate_receipt_structure()`, `validate_commit_ready()`
- Handoff records `planner_outputs` and `draft_source` fields.

## Authority
- Only Vertical Planner Agents may produce shard plans and digest drafts.
- Only Core Agent may write final `handoff-manifest.json` and commit `tasks.md`.
- Only Worker Agents may execute implementation handoffs.
- The protocol constrains observable workflow behavior, not internal reasoning.

## Lifecycle
`intake` -> `context_indexing` -> `vertical_planning` -> `manifest_assembly` -> `worker_dispatch` -> `worker_execution` -> `receipt_review` -> `code_review` -> `task_commit` -> `integration_verification` -> `closeout`

## Runtime Isolation Mapping
Use `agent-runtime=<spec-kit-integration-key>` as a prompt hint. The manifest records only `isolated_subagent` or `manual_fresh_worker_session`.

| Runtime key | Isolated execution | Planner dispatch | Worker dispatch |
| --- | --- | --- | --- |
| codex (Codex) | isolated subagent/subsession | one planner per `vertical_capability` | one worker per handoff |
| claude (Claude Code) | subagent | planner subagent | worker subagent |
| gemini (Gemini CLI) | `@subagent` | `@speckit_planner` | `@speckit_worker` |
| copilot (GitHub Copilot) | subagent/task agent | planner task agent | worker task agent |
| opencode | agent context | planner agent | worker agent |
| cursor-agent, devin, windsurf, kiro-cli, junie | runtime-managed isolated agent | planner role | worker role |
| generic | not assumed | write planner prompts only | manual fresh Worker-mode sessions |

## Dispatch Payloads
- Vertical Planner payload: planner prompt, one `vertical_capability`, `context-index.json`, allowed planning artifact paths.
- Worker payload: one of the Worker prompts, one handoff JSON path, no full `spec.md`, `plan.md`, `research.md`, `contracts/`, `quickstart.md`.
- Core consumes planner outputs and worker receipts, not worker conversation history.
- If isolation is unavailable or unknown, Core writes manifest and handoffs, then reports `Manual Worker Queue` ordered by manifest `dispatch_order`; same-layer entries may say `can run in parallel manually`.

## Core Agent
- read `tasks.md`
- write `context-index.json`
- dispatch Vertical Planner Agents
- collect planner drafts
- assemble final handoffs
- write `handoff-manifest.json`
- dispatch Worker Agent runs only for isolated execution
- review receipts with `validate_receipt_structure()` and `validate_commit_ready()`
- commit `tasks.md`
- during task_commit, mark `[x]` only for receipt completed_task_ids that passed receipt review, required code review, and integration verification with no deferred_validation_todos
- run integration verification and report closeout

## Vertical Planner Agent
- one `vertical_capability`
- produce shard plans, handoff drafts, context digest drafts
- derive `allowed_read_paths`, `allowed_write_paths`
- mark final review handoffs with `task_type: code_review`
- must not execute implementation, write final `handoff-manifest.json`, dispatch workers, edit `tasks.md`

## Worker Agent
- execute exactly one handoff
- Reject non-existent handoff paths
- Reject handoffs not listed in `handoff-manifest.json`
- Verify contract_type == speckit.implement.handoff.v2
- Load context_digest_path before editing
- Stop if dispatch gate has non-empty `context_gaps`
- Execute only task_ids
- Read only allowed_read_paths
- Write only allowed_write_paths; directory authorization includes files below the directory
- Do not edit tasks.md
- Do not dispatch workers
- write receipt_path as speckit.implement.receipt.v1 with validation_evidence references to relevant BDD scenario, behavior assertion, API contract, quickstart path, Visual Item ID, Requirement Status, UIF path, screenshot ref, visual proof ref, Client Asset Contract entry, quickstart validation path, or captured command output
- use empty completed_task_ids when the handoff is blocked, validation is deferred, required evidence is missing, or code review status is not approved

## Worker Prompts
```text
Implementation Worker.
Handoff JSON: <path>
- Verify contract_type == speckit.implement.handoff.v2
- Load context_digest_path before editing
- Stop if context_gaps is not empty at dispatch
- Execute only implementation task_ids
- Read only allowed_read_paths
- Write only allowed_write_paths
- Do not perform code review or final_visual_review
- Do not edit tasks.md
- Do not dispatch workers
- Follow Worker Agent receipt rules
```

```text
Code Review Worker.
Handoff JSON: <path>
- Require task_type: code_review
- Review actual implementation diff, data side effects, runtime database writes, and field-level update/delete behavior
- Include review_conclusion.checked_sources, data_side_effect_review, consistency_repairs, deferred_validation_todos, and quickstart/contract validation command evidence
- Repair only authorized implementation drift against existing design, sequence, or contract constraints inside allowed_write_paths
- Record upstream requirement, contract, checklist, planning artifact, or real e2e gaps as blockers or todos
- Do not edit tasks.md, create handoffs, or dispatch workers
```

```text
Visual Review Worker.
Handoff JSON: <path>
- Use for final_visual_review tasks
- Verify implemented UI states, viewport behavior, Visual Fidelity Readiness, UIF paths, screenshot refs, visual proof refs, and Client Asset Contract bindings
- Reference Visual Item ID and Requirement Status in validation_evidence
- Do not discover visual requirements, repair Visual Fidelity Readiness evidence, or edit spec.md, contracts, readiness checklists, or planning artifacts
- Do not edit tasks.md, create handoffs, or dispatch workers
```

## Planner Prompt
```text
Vertical Planner Agent.
vertical_capability: <capability>
- Produce shard plans
- Produce handoff drafts
- Produce context digest drafts
- Derive allowed_read_paths
- Derive allowed_write_paths
- Do not execute implementation
- Do not write final handoff-manifest.json
- Do not dispatch workers
- Do not edit tasks.md
```

## Shard Rules
- one incomplete `tasks.md` checklist item maps to one candidate shard
- ignore completed `[x]` checklist items
- preserve `tasks.md` order
- visual shard candidates must come only from `tasks.md` visual task types `visual_setup`, `visual_validation`, `visual_implementation`, `visual_evidence`, `ui_acceptance`, `visual_verification`, `asset_binding`, or `final_visual_review`; preserve the Visual Fidelity Readiness `Requirement Status` filter from `/speckit.tasks`: only `Required` or `Required` plus an accepted exception is executable; do not create visual shards for `Not Applicable`, `Unknown`, or `[BLOCKED: PROVIDER_EVIDENCE]`; route `Unknown` back to `/speckit.clarify` and `[BLOCKED: PROVIDER_EVIDENCE]` to the external intake extension
- infer `vertical_capability` from task section heading, task text, referenced paths
- group candidates only when lifecycle dependencies, vertical_capability, and allowed_write_paths match
- serial shards with explicit dependencies may declare shared write paths; same dispatch layer must not overlap allowed_write_paths
- shard IDs use `S<2-digit-sequence>-<vertical_capability>-<2-digit-sequence>`

## Context Digest Rules
- include task text for assigned `task_ids`
- include document headings from `context-index.json`
- include only sections referenced by assigned task paths or vertical_capability
- include relevant `class-diagram.md`, `contracts/sequences.md`, `contracts/bdd/`, `contracts/uif/`, and `contracts/behavior/` constraints, plus research.md validation decisions and quickstart.md validation paths from `research.md` and `quickstart.md`
- include behavior contract constraints, visual fidelity requirements, Visual Item ID, Requirement Status, accepted exception rule, screenshot refs, visual proof refs, visual SSOT refs, external evidence refs, and Client Asset Contract entries
- asset binding maps only executable Required or accepted-exception Client Asset Contract items to local asset paths or code asset mappings; missing required client visual assets, mappings, variants, or fallbacks become `context_gaps`
- visual `Requirement Status` mismatches, `Unknown`, `[BLOCKED: PROVIDER_EVIDENCE]`, missing visual proof refs, missing screenshot refs, missing asset variants, or missing fallback policy become `context_gaps`, not implementation scope
- record unresolved required context as `context_gaps`

## Path and Receipt Rules (Path Rules)
- derive `allowed_write_paths` from paths referenced by assigned task text, planned `U` design object, and specific source, test, fixture, configuration, or receipt paths
- include receipt path in `allowed_write_paths`
- derive `allowed_read_paths` from allowed write parents, validation files, context digest, and context index
- exclude `tasks.md` from `allowed_write_paths`
- receipt changed_paths may equal an allowed write path or be inside an allowed directory
- implementation changed_paths require at least one Code Review Receipt before task_commit
- code review uses the union of all Code Review Receipts to cover implementation changed_paths
- Receipt Rejection: mismatched `shard_id`; `task_ids` outside handoff; `completed_task_ids` outside handoff; non-empty `completed_task_ids` with `deferred_validation_todos`; non-empty `completed_task_ids` on Code Review Receipts whose `review_conclusion.status` is not approved; empty `validation_evidence` or missing relevant BDD scenario, behavior assertion, API contract, quickstart path, Visual Item ID, Requirement Status, UIF path, screenshot ref, visual proof ref, Client Asset Contract entry, quickstart/contract validation command evidence; receipt path not equal to handoff `task_status_update.receipt_path`; missing `task_type: code_review`, `review_conclusion.checked_sources`, `data_side_effect_review`, `consistency_repairs`, or needed `deferred_validation_todos`
