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
- `input_scope`: current natural-language direction plus explicitly authorized,
  feature-sliced sources recorded through one local `SRC-*` role.
- `allowed_writes`: `spec.md` only.
- `output_contract`: source-neutral rows plus local product, behavior, visual,
  and UI/UX requirement projections or stable blockers.
- `stop_conditions`: a broad source without a safe feature slice does not
  authorize full import.
- `fallback`: single-core execution.

### `speckit.plan.stage_local_planning`

- `stage`: X0–X4 milestones nested in Core Plan.
- `owner_agent`: Plan Core Agent.
- `assigned_scope`: one bounded X1, X2-A, X2-B, X2-C, X3, or X4 derivation
  unit; never an implementation unit.
- `input_scope`: local Spec facts/blockers, Constitution, current repository
  facts, applicable Architecture refs, and assigned X1/X2/X3/X4 artifact
  families. External `SRC-*` locators are not allowed reads.
- `allowed_reads`: authoritative upstream inputs, current repository facts,
  packaged Plan templates/schemas, and already-produced Plan artifacts named by
  the assigned scope.
- `allowed_writes`: final planning artifacts owned by `/speckit.plan`.
- `required_outputs`: lane-qualified decisions, X2-A/X2-B/X2-C designs,
  `TC-*`, `VAL-*`, or independent readiness content explicitly named by the
  assigned scope.
- `output_contract`: required outputs plus `blockers` and `context_gaps`.
- `validation_gate`: `PLAN_OUTPUT_READY` over Plan outputs and internal refs
  only, with a lane-local Gate on each assignment.
- `stop_conditions`: an unmet entry Gate, an out-of-scope read/write, an
  unresolved required ref, or a blocker owned by another lane.
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
- `stop_conditions`: `PLAN_OUTPUT_INCOMPLETE`, an unresolved Plan blocker,
  unresolved derivation context, or an attempted source-acquisition,
  locator-execution, external-state-validation, or visual-fidelity task derived
  from a `SRC-*`.
- `fallback`: the Tasks Core Agent processes one scope at a time.

### `speckit.analyze.read_only_parallel_review`

- `stage`: cross-command consistency analysis.
- `owner_agent`: Analyze Core Agent.
- `input_scope`: local Source References → Plan/UIF, Constitution/Architecture
  → Spec/Plan, Spec → Plan, Architecture → X1/X2/X3, Plan → Tasks, and M + U
  preservation. External locators are never accessed.
- `allowed_writes`: none.
- `output_contract`: stable-code findings, blockers, warnings, closed-chain
  summary, and implementation readiness.
- `fallback`: sequential read-only review.

## Permission Boundary

Profiles share only the stage-local delegation shape. They do not grant
implementation permissions and do not define persistent execution artifacts.
The implementation command and its execution behavior are owned exclusively by
the current Spec Kit core.
