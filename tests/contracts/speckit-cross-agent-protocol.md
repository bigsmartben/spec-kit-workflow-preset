# Spec Kit Cross-Agent Protocol

## Purpose

Constrain stage-local delegation without defining a second implementation
runtime. The protocol covers bounded inputs, outputs, readiness gates, stop
conditions, and sequential fallback.

## BaseSubagentProtocol

Every preset-owned command profile defines:

- `stage`
- `owner_agent`
- `input_scope`
- `allowed_reads`
- `allowed_writes`
- `output_contract`
- `validation_gate`
- `stop_conditions`
- `fallback`

## Command Profiles

### `speckit.specify.single_core`

- `stage`: requirement projection.
- `owner_agent`: Specify Core Agent.
- `allowed_writes`: `spec.md` only.
- `output_contract`: source-aware product, behavior, visual, and UI/UX
  requirements.
- `fallback`: single-core execution.

### `speckit.plan.stage_local_planning`

- `stage`: Phase 0 behavior projection and Phase 1 planning.
- `owner_agent`: Plan Core Agent.
- `input_scope`: checklist-approved requirements and assigned planning artifact
  families.
- `allowed_writes`: final planning artifacts owned by `/speckit.plan`.
- `output_contract`: behavior drafts, formal contracts, design drafts,
  validation design, blockers, and `context_gaps`.
- `validation_gate`: checklist PASS, matching behavior schemas, and planning
  blocker aggregation.
- `fallback`: the Plan Core Agent processes one assigned scope at a time and
  preserves final-write ownership.

### `speckit.tasks.stage_local_derivation`

- `stage`: upstream-artifact-to-checklist mapping.
- `owner_agent`: Tasks Core Agent.
- `input_scope`: user stories, behavior and interface contracts, research
  decisions, quickstart paths, UI/visual readiness, and review scopes.
- `allowed_reads`: only the scoped inputs declared for each derivation unit.
- `allowed_writes`: `tasks.md` only.
- `output_contract`: ordered implementation, validation, integration/e2e, and
  Final Code Review checklist items, plus blockers and `context_gaps`.
- `validation_gate`: source/evidence binding, dependency ordering, final review
  placement, and blocker aggregation.
- `stop_conditions`: missing required case coverage, missing provider evidence,
  or unresolved derivation context.
- `fallback`: the Tasks Core Agent processes one scope at a time.

### `speckit.analyze.read_only_parallel_review`

- `stage`: vertical consistency analysis.
- `owner_agent`: Analyze Core Agent.
- `allowed_writes`: none.
- `output_contract`: findings, blockers, warnings, and closed-chain summary.
- `fallback`: sequential read-only review.

## Permission Boundary

Profiles share only the stage-local delegation shape. They do not grant
implementation permissions and do not define persistent execution artifacts.
The implementation command and its execution behavior are owned exclusively by
the current Spec Kit core.
