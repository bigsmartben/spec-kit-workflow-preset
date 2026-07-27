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

- `stage`: X0–X4 milestones nested in Core Plan.
- `owner_agent`: Plan Core Agent.
- `input_scope`: accepted Spec facts, current repository facts, applicable
  Architecture refs, and assigned X1/X2/X3/X4 artifact families.
- `allowed_writes`: final planning artifacts owned by `/speckit.plan`.
- `output_contract`: lane-qualified decisions, X2-A/X2-B/X2-C designs,
  `TC-*`, `VAL-*`, independent readiness products, blockers, and
  `context_gaps`.
- `validation_gate`: `PLAN_OUTPUT_READY` over Plan outputs and internal refs
  only.
- `fallback`: the Plan Core Agent processes one assigned scope at a time and
  preserves final-write ownership.

### `speckit.tasks.stage_local_derivation`

- `stage`: upstream-artifact-to-checklist mapping.
- `owner_agent`: Tasks Core Agent.
- `input_scope`: `PLAN_OUTPUT_READY`, Design Object, UI/UX Delivery, Test
  Readiness, contracts, and `VAL-*` paths.
- `allowed_reads`: only the scoped inputs declared for each derivation unit.
- `allowed_writes`: `tasks.md` only.
- `output_contract`: concrete path bindings, dependency-ordered implementation,
  required functional validation/evidence, and last-phase Final Code Review
  items, plus blockers and `context_gaps`.
- `validation_gate`: source/evidence binding, dependency ordering, final review
  placement, and blocker aggregation.
- `stop_conditions`: `PLAN_OUTPUT_INCOMPLETE`, unresolved Plan blocker, or
  unresolved derivation context.
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
