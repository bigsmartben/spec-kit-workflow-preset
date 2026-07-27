---
description: Wrap Core Plan with X0–X4 feature control, parallel design lanes, and test-first acceptance contracts.
strategy: wrap
---

Follow cross-agent protocol profile: `speckit.plan.stage_local_planning`.

## Core Compatibility

The X labels are preset-internal milestones nested inside the official Core
Plan lifecycle:

```text
Core setup + plan-template materialization -> X0
Core Phase 0 Outline & Research           -> X1
Core Phase 1 Design & Contracts           -> X2 and X3
Core post-design Constitution re-check    -> unchanged
Preset closeout before completion report  -> X4
```

Preserve Core user input, setup scripts, Technical Context, Constitution Check,
pre/post hooks, Phase 0, Phase 1, and completion behavior in their official
order. Do not add, remove, rename, reorder, duplicate, or reinterpret a Core
phase or gate. Do not re-run Checklist or aggregate Planning Readiness.

## Deterministic Execution Spine

Run this preset-internal spine inside the unchanged Core lifecycle:

```text
Core setup
  -> X0 scope/lane control
  -> X1 decisions
  -> X2-A / X2-B / X2-C active lanes
  -> X2 cross-lane reconciliation
  -> X3 VAL paths
  -> refresh affected X2 reconciliation checks
  -> unchanged Core post-design Constitution re-check
  -> X4 closeout
  -> derive PLAN_OUTPUT_READY
```

For every internal milestone or active lane, use exactly this Gate loop:

| Gate step | Required action |
|---|---|
| Entry conditions | Confirm every dependency Gate is `READY` or explicitly `N/A`; otherwise stop the dependent scope. |
| Bounded reads | Read only the upstream inputs, packaged templates/schemas, repository facts, and already-produced Plan artifacts needed by this scope. |
| Owned writes | Write only the artifacts owned by the current milestone/lane. |
| Validation | Check required outputs, conditional decisions, stable refs, placeholders, ownership, and lane-specific prohibitions. |
| Evidence | Record `READY`, `BLOCKED: <ID>`, or `N/A: <reason>` plus concrete artifact/section/ID evidence in `plan.md`. |
| Failure handling | Keep the owning lane blocked, record the smallest actionable blocker or context gap, and do not enter a dependent milestone. |

File existence, prose confidence, or a summary statement is never Gate
evidence. A Gate is `READY` only when all of its required checks pass. An
inactive lane is `N/A` only through the decision rules below. Any unresolved
required check makes the Gate `BLOCKED`; do not continue into a scope that
depends on it.

## External Input Boundary

Authoritative upstream inputs are limited to `spec.md`,
`.specify/memory/constitution.md`, `.specify/memory/architecture.md`, and
current repository facts. “Read only” does not prohibit reading packaged
templates/schemas or the current Plan stage's already-generated artifacts for
validation and reconciliation. Planning has one strategy for every repository:

```text
current repository facts
  -> applicable Architecture constraints
  -> repository-grounded technical design
  -> Plan outputs
```

Treat empty/minimal repositories as observed fact. Do not invent an existing
module, path, dependency, or implementation surface. Architecture IDs and
revision are provenance inputs. Plan never amends Architecture or declares
cross-command conformance. If required design cannot fit Architecture, record a
blocker routed to `/speckit.constitution`.

Consume confirmed local WHAT/WHY requirements, local blockers, and Architecture
records. `SRC-*` locators are opaque provenance, not automatic read or
execution targets. Do not rewrite Spec, invoke Clarify/Checklist, acquire
external evidence, dereference or execute a source locator, or validate source
authenticity, revision, digest, freshness, publication state, or availability.
Unavailable evidence remains the blocker already projected into Spec or
Architecture.

Apply Change Scope Granularity: lock planned `M + U`; `plan.md` may record
repository/module directory topology required by Core, but no task IDs,
per-task paths, operation-level changes, or implementation order.

## Ownership And Conditional Artifact Decisions

| Scope | Sole final writer | Owned outputs | Must not absorb |
|---|---|---|---|
| X0/X4 control | Plan Core Agent | `plan.md` control, Gate evidence, derivation index, closeout | complete designs, Test Conditions, tasks |
| X1 decisions | Plan Core Agent | `research.md` `DEC-*` records | complete designs, runnable paths, cross-command audit |
| X2-A | Plan Core Agent | `data-model.md`, contextual class/sequence artifacts, interface contracts | UI delivery detail, fixtures, assertions, task paths |
| X2-B | Plan Core Agent | `ui-ux-design.md`, `contracts/uif/` | API payload schemas, pixel tests, external-source certification |
| X2-C | Plan Core Agent | Test Conditions and selected technique children | UI styling/fidelity, validation run guidance, tasks |
| X3 | Plan Core Agent | `quickstart.md` `VAL-*` paths | test design decisions, implementation bodies, results |

Use this decision table; never infer N/A merely because an artifact is absent:

| Artifact/lane | Required when | N/A allowed when | Blocked when |
|---|---|---|---|
| `class-diagram.md` | multiple cooperating objects, dependency direction, patterns, or object ownership must be designed | one object or responsibilities are fully expressed without an object relationship view; record the concrete reason | trigger applies but responsibilities/relationships cannot yet be resolved |
| interface contracts | an externally observable protocol, input/output, error, compatibility/versioning, or state-effect boundary must be designed | X2-A is pure domain/internal-object design with no externally observable interface contract; record the concrete reason | an interface trigger applies but its observable contract cannot yet be resolved |
| `contracts/sequences.md` | observable cross-boundary order, async callback, retry, rollback, compensation, or failure propagation exists | no observable ordering or failure-flow design exists; record the concrete reason | trigger applies but participants/order/failure path is unresolved |
| X2-B + `ui-ux-design.md`/UIF | any `UX-*`, `UI-*`, `VIS-*`, interactive surface/state, responsive, asset, or accessibility delivery applies | feature has no user-visible or interactive delivery; cite the scoped Spec evidence | applicable UI/visual refs lack a local delivery mapping or stable blocker |
| BDD/scenario child | parent `TC-*` selects BDD/scenario technique | no parent selects that technique | selected technique lacks its parent-linked child |
| fixture child | a parent `TC-*` requires reusable/formal setup data | every applicable condition records a fixture-free rationale | required reusable setup is unresolved or missing |
| assertion child | a parent `TC-*` selects structured scenario/assertion technique | no parent selects a structured assertion technique and each oracle remains complete in its parent | selected technique lacks outcome assertions |

A blocked applicable lane remains `Blocked`; never relabel it `N/A`. During a
resume, preserve each independently verified `Required` output and mark only
the affected output `Blocked`. In particular, X2-C does not require Test
Conditions, Quickstart, and Test Readiness to become blocked as a group.

## Stage-Local Work Units

If bounded subagents are available, the Plan Core Agent may assign independent
X1/X2/X3 derivation units. Every transient assignment must contain:

```text
assigned_scope
allowed_reads
allowed_writes
required_outputs
validation_gate
blockers
context_gaps
```

The assignment is runtime context only, not a file, manifest, queue, handoff
protocol, or worker result. The Plan Core Agent remains the sole final writer
and sole Gate decision owner. It validates returned content before incorporating
it. If delegation is unavailable or a unit is blocked, process one assigned
scope at a time with the same fields and Gate loop.

## X0 — Feature Plan Control

Run after Core setup has materialized `plan.md`, before detailed research.
Populate the control sections supplied by `plan-template`:

- feature goal and exclusions;
- repository-grounded planned `M + U`;
- Spec and applicable Architecture revision/ID refs;
- X2-A, X2-B, X2-C applicability (`Required`, `Not Applicable: <reason>`, or
  `Blocked: <ID>`);
- declared independent artifact outputs and internal gates;
- cross-lane dependencies;
- navigation without broken placeholder links.

`X0_CONTROL_READY` passes only when goal/scope, lane applicability, outputs,
dependencies, Core Technical Context, and Constitution Check are explicit and
no detailed design/test artifact is duplicated into `plan.md`.

## X1 — Research & Decisions

Within Core Phase 0, use `research.md` as a shared decision record. Every
material decision has:

```text
Decision ID | source/constraint refs | decision | rationale | alternatives
| affected outputs | status
```

Use `DEC-TECH-*`, `DEC-DATA-*`, `DEC-IF-*`, `DEC-UI-*`, and `DEC-TEST-*`.
Record applicable decisions for technical topology/runtime, data
consistency/migration/retry/rollback, interface ownership/compatibility, UI/UX
state/responsive/token/asset/accessibility delivery, and Test risk/level/type/
technique/fixture/environment/oracle/evidence.

`research.md` records decisions, not complete designs, Test Conditions, tasks,
results, or cross-command audits. `X1_DECISIONS_READY` requires Core technical
unknowns and active-lane decisions to be decided, routed upstream, or retained
as stable runtime prerequisites. “Use E2E/BDD” alone is incomplete.

## X2 — Parallel Design & Contracts

X2-A, X2-B, and X2-C are parallel and mutually constraining. A lane returns a
bounded gap to the owning lane; it never silently owns another lane's schema.

### X2-A Domain / Object / Interface / Sequence

- `data-model.md` owns domain concepts, fields, relationships, lifecycle,
  invariants, validation, ownership, and persistence semantics. Test fixtures,
  scenario instances, UIF paths, feedback views, assertions, DTO schemas, and
  task paths are not domain entities unless genuinely part of the product.
- `class-diagram.md` follows the stable template and owns implementation object
  responsibilities and relationships. Trigger it for multiple cooperating
  objects, dependency direction, patterns, or ownership that `plan.md` cannot
  express; otherwise record a specific N/A reason.
- interface contracts own externally observable protocol, input/output,
  errors, compatibility/versioning, and state effects.
- `contracts/sequences.md` owns cross-boundary order, async callbacks, retry,
  rollback, compensation, and failure propagation when order is observable;
  otherwise record a specific N/A reason.

`X2A_DESIGN_READY` requires every triggered artifact populated or explicitly
N/A, non-overlapping ownership, resolved internal refs, and no placeholder
presented as a decision.

### X2-B UI/UX Delivery

When UI/UX or visual delivery applies, create `ui-ux-design.md` from its stable
template. It owns surfaces, components, composition, state, navigation/events,
viewports/responsive behavior, tokens/themes/variants, assets/fallbacks,
accessibility implementation, opaque accepted-source provenance, local delivery
method, and UI/UX Delivery Readiness.

`contracts/uif/*.expected.json` is a UI/UX interaction contract: start view,
events, routes, observable states/feedback, API call refs, and transitions. It
maps applicable `source_refs` plus local `requirement_refs` (`UI-*`/`VIS-*`) and
may carry `visual_item_refs`, `viewport_matrix_refs`, `state_matrix_refs`,
`visual_proof_refs`, and `accepted_exception_refs` as declared schema fields. It
does not own pixel comparison, styling, or API payload schemas.

Do not produce `behavior/uif.intent.json` as a mandatory parent or second SSOT.
Formal UIF derives from accepted Spec refs plus `ui-ux-design.md`.

`X2B_UIUX_READY` requires each applicable `SRC-* + UI/VIS-*` pair to map to
surface/component/state, viewport/responsive/accessibility, asset/variant/
fallback, accepted-source/delivery-method, and UIF records or a stable local
blocker. X2-B preserves opaque provenance but MUST NOT open, run, inspect,
compare, or certify an external source or its fidelity/state as part of the
local gate. Local pixel delivery ownership stays in UI/UX, never Test
Conditions.

### X2-C Test & Acceptance

Create `contracts/test/test-conditions.json` from its schema/template. One
`TC-*` represents one required condition and records source, risk/priority,
level, type, technique, execution mode, fixture decision, environment,
oracle, evidence, related design/UIF/interface refs, X3 path/blocker, and status.

BDD drafts/contracts and structured behavior scenario/fixture/assertion
artifacts are optional children only when selected techniques require them:

- BDD/scenario artifacts must reference their parent `TC-*`;
- non-UI scenarios omit `uif_path_id` with `non_ui_rationale`;
- fixture-free scenarios omit fixture refs with `no_fixture_rationale`;
- non-UI/non-message oracles do not require feedback;
- formal fixtures exist only when a Test Condition requires reusable setup;
- assertions may express state, error, invariant, threshold, accessibility,
  security, reliability, recovery, or data-side-effect outcomes.

Reject pixel-perfect comparison, screenshot diff, baseline capture, pixel-level
layout/style assertions, visual restoration, and final pixel review from Test
Conditions or Test Readiness.

`X2C_TEST_DESIGN_READY` requires all TC dimensions and internal refs, every
technique-triggered child or stable blocker, and zero pixel-level Test entries.

## X2 — Cross-Lane Reconciliation

After all active X2 lanes have reached `READY`, and before entering X3, the Plan
Core Agent performs one explicit reconciliation pass. Do not delegate the final
judgment. Inventory each declared `DEC-*`, design/interface/sequence ID, UIF,
`TC-*`, and requested `VAL-*` mapping once, then check:

1. every consumed ref resolves to exactly one producer and uses one stable ID or
   name; report missing, duplicate, renamed, and stale refs;
2. every material `DEC-*` reaches each affected active-lane output;
3. every UIF API/design ref resolves in X2-A and every applicable UI/VIS source
   pair resolves in X2-B;
4. every `TC-*` resolves its requirement, design/UIF/interface refs and every
   technique-triggered child;
5. every condition needing execution declares the expected `VAL-*` mapping or
   a stable X3 blocker;
6. content remains with its sole owner; record misplaced domain, interface, UI,
   Test, or validation-path content;
7. each blocker is recorded against its real owning lane, and every dependent
   lane points to that blocker instead of copying or relabeling it.

Record the inventory, findings, blocker owners, and evidence in the
`X2_RECONCILIATION_READY` section of `plan.md`. Any unresolved finding blocks
X3. After X3 writes `VAL-*`, refresh all reconciliation rows affected by
created, renamed, blocked, or removed paths; a requested mapping is not closed
until the actual `VAL-*` or blocker resolves.

## X3 — Integration & Validation Paths

Within Core Phase 1, populate `quickstart.md` using stable `VAL-*` records:

```text
VAL ID | covered TC/design/contract refs | purpose and level/type
| prerequisites/environment/mode | actor/journey | fixture/data
| systems/boundaries | ordered actions | oracle | evidence | cleanup | blocker
```

Unit/component/contract conditions may share a command path when their oracle
and evidence remain identifiable. Integration/system/e2e and real-system
conditions require explicit journey/environment paths. Do not embed suites,
implementation bodies, migrations, task IDs/order, or fabricated results.

`X3_VALIDATION_PATHS_READY` requires each condition needing a runnable path to
map to a complete `VAL-*` or stable runtime blocker.

## Continuation And Resume

Treat the `plan.md` Internal Gate Summary and its evidence as the resume index:

1. validate the recorded evidence rather than trusting the status text;
2. preserve an already-verified artifact when its bounded inputs and stable refs
   are unchanged;
3. resume at the first Gate whose evidence is absent, invalid, `BLOCKED`, or
   affected by changed input;
4. re-run that Gate and every downstream reconciliation/Gate that consumes the
   changed artifact or ref;
5. never unconditionally overwrite a verified upstream artifact, and never
   preserve a downstream `READY` status after an input/ref it depends on changed.

No `PENDING` state is introduced. A Gate without closed evidence is simply not
ready and is treated as the first resume candidate.

## X4 — Independent Closeout

After Core design and its post-design Constitution re-check:

1. Finalize `plan.md` Design Object Derivation Index:
   `source refs | Architecture provenance | M | U/design object | data-model |
   class | interface/sequence | blocker`.
2. Finalize UI/UX Delivery Readiness in `ui-ux-design.md` or explicit N/A.
3. Create `test-readiness.md` as the only Test/Tasks readiness SSOT, one row per
   required `TC-*`. Each row is `READY` with evidence or `BLOCKED` with a
   blocker; any blocked row blocks `PLAN_OUTPUT_READY`. Do not create/retain authoritative
   `behavior/behavior-testability.md`, `planning-readiness.md`, or
   `test-plan.md`.
4. Re-run the final cross-lane reference and ownership checks, then summarize
   Gate status and lane-owned blockers in `plan.md`.

Derive `PLAN_OUTPUT_READY`; never set it independently. It is `READY` if and
only if X0 + X1 + `X2_RECONCILIATION_READY` + every applicable X2 Gate +
applicable X3 + complete Design/UI/UX/Test readiness are evidenced, every
conditional artifact is Required/READY or has a valid N/A reason, all
Plan-internal refs resolve, all blockers are lane-owned, and no placeholder is
presented as a decision. Otherwise it is `BLOCKED` with the failed Gate and
blocker evidence. It validates Plan outputs only.

{CORE_TEMPLATE}

## Preset Completion Addition

Report each X0–X4 gate, active/N/A lanes, artifacts created or omitted with
reasons, readiness products, Architecture revision refs, runtime prerequisites,
lane-owned blockers, and `PLAN_OUTPUT_READY`. Do not report Tasks, execution
results, or cross-command consistency.
