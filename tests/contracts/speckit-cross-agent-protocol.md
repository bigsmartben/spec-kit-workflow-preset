# Spec Kit Cross-Agent Protocol

## Purpose
Constrain observable workflow behavior with small stage protocols instead of long global agent memory rules. The protocol constrains inputs, outputs, file access, readiness gates, stop conditions, and fallback behavior. It does not constrain internal reasoning.

## BaseSubagentProtocol
Every command profile defines these fields:

- `stage`: command-local lifecycle stage.
- `owner_agent`: agent role that owns final writes and readiness decisions.
- `input_scope`: exact artifacts, sections, IDs, or path families assigned to the stage.
- `allowed_reads`: files, directories, or scoped excerpts the role may inspect.
- `allowed_writes`: files, directories, or artifact families the role may create or update.
- `output_contract`: draft, finding, blocker, receipt, manifest, or final artifact shape.
- `validation_gate`: schema, validator, checklist, or blocker-code gate before the next stage.
- `stop_conditions`: deterministic blockers that stop the current role.
- `fallback`: sequential simulation or manual queue behavior when delegated agents are unavailable.

## Command Profiles

### `speckit.specify.single_core`
- `stage`: requirement projection.
- `owner_agent`: Specify Core Agent.
- `input_scope`: user prompt, product notes, confirmed external intake refs, visual SSOT refs, screenshots, and visual proof refs.
- `allowed_reads`: command inputs and existing requirement context selected by core Spec Kit behavior.
- `allowed_writes`: `spec.md` only.
- `output_contract`: stakeholder-readable requirements with explicit source-backed facts, assumptions, visual/UI status, and provider blockers.
- `validation_gate`: specification quality validation in `/speckit.specify`.
- `stop_conditions`: missing feature description, unsupported inference, or provider evidence treated as product semantics.
- `fallback`: single-core execution; no persistent handoff, receipt, or worker queue.

### `speckit.plan.stage_local_planning`
- `stage`: Phase 0 behavior projection and Phase 1 planning.
- `owner_agent`: Plan Core Agent.
- `input_scope`: checklist-approved requirement sections, behavior readiness rows, planning inputs, and assigned artifact families.
- `allowed_reads`: scoped planning inputs declared per delegated payload.
- `allowed_writes`: final planning artifacts owned by `/speckit.plan`.
- `output_contract`: draft behavior artifacts, formal contract drafts, design artifact drafts, blockers, and `context_gaps`.
- `validation_gate`: checklist PASS preflight, matching behavior schemas, and planning blocker report.
- `stop_conditions`: failed checklist gate, required case projection gaps, or unresolved planning `context_gaps`.
- `fallback`: Plan Core Agent sequentially simulates each assigned scope and preserves final-write ownership.

### `speckit.tasks.stage_local_derivation`
- `stage`: task derivation.
- `owner_agent`: Tasks Core Agent.
- `input_scope`: user stories, behavior contracts, interface contracts, research decisions, quickstart validation paths, visual readiness rows, and review scopes.
- `allowed_reads`: scoped derivation payloads; no full artifact tree unless the payload explicitly lists it.
- `allowed_writes`: `tasks.md` only.
- `output_contract`: task candidates, evidence refs, source refs, blockers, and `context_gaps`.
- `validation_gate`: task-derivation blocker aggregation and existing checklist format.
- `stop_conditions`: missing Required case coverage, missing visual readiness evidence, or unresolved task-derivation `context_gaps`.
- `fallback`: Tasks Core Agent processes one assigned scope at a time; no handoff, receipt, write-path metadata, or worker dispatch.

### `speckit.analyze.read_only_parallel_review`
- `stage`: vertical consistency analysis.
- `owner_agent`: Analyze Core Agent.
- `input_scope`: existing planning artifacts and stable IDs such as `CASE-`, `SCN-`, `UIF-`, `FIX-`, `AST-`, and `BLK-`.
- `allowed_reads`: bounded artifact inventory, ID maps, and surrounding prose only when an ID link is missing or ambiguous.
- `allowed_writes`: none.
- `output_contract`: findings, blockers, warnings, and closed-chain summary.
- `validation_gate`: read-only consistency checks by source artifact and target artifact.
- `stop_conditions`: missing source artifact, broken traceability, or first blocker that proves a downstream link cannot close.
- `fallback`: sequential read-only review; no durable artifact writes.

### `speckit.implement.persistent_handoff_orchestration`
- `stage`: implement lifecycle from context indexing through closeout.
- `owner_agent`: Core Agent for orchestration and task commit; Vertical Planner Agent for drafts; Worker Agent for one handoff.
- `input_scope`: incomplete `tasks.md` items, context index, planner outputs, handoffs, context digests, receipts, and validation evidence.
- `allowed_reads`: role-scoped handoff inputs and digest paths.
- `allowed_writes`: Core writes manifest and task status; planners write drafts; workers write only authorized implementation paths and receipts.
- `output_contract`: manifest, shard handoffs, context digests, worker receipts, code review receipts, visual review receipts, and closeout.
- `validation_gate`: `validate_manifest_structure()`, `validate_handoff_structure()`, `validate_dispatch_ready()`, `validate_receipt_structure()`, and `validate_commit_ready()`.
- `stop_conditions`: schema mismatch, unlisted handoff, non-empty dispatch `context_gaps`, or current role writing outside authorized paths.
- `fallback`: when isolated subagents are unavailable, Core emits a `Manual Worker Queue` ordered by manifest `dispatch_order`.

## Permission Boundary
Profiles inherit the scheduling protocol, not execution permissions. A command must reference only its own profile. Persistent handoff orchestration, handoff manifests, receipts, allowed write paths, and manual worker queues belong only to `speckit.implement.persistent_handoff_orchestration`.
