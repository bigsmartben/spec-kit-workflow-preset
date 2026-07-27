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

## External Input Boundary

Read only `spec.md`, `.specify/memory/constitution.md`,
`.specify/memory/architecture.md`, and current repository facts. Planning has
one strategy for every repository:

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

## X4 — Independent Closeout

After Core design and its post-design Constitution re-check:

1. Finalize `plan.md` Design Object Derivation Index:
   `source refs | Architecture provenance | M | U/design object | data-model |
   class | interface/sequence | blocker`.
2. Finalize UI/UX Delivery Readiness in `ui-ux-design.md` or explicit N/A.
3. Create `test-readiness.md` as the only Test/Tasks readiness SSOT, one row per
   required `TC-*`. Do not create/retain authoritative
   `behavior/behavior-testability.md`, `planning-readiness.md`, or
   `test-plan.md`.
4. Summarize gate status and lane-owned blockers in `plan.md`.

`PLAN_OUTPUT_READY` equals X0 + X1 + applicable X2 gates + applicable X3 +
complete Design/UI/UX/Test readiness + resolved Plan-internal refs + no
placeholder presented as a decision. It validates Plan outputs only.

{CORE_TEMPLATE}

## Preset Completion Addition

Report each X0–X4 gate, active/N/A lanes, artifacts created or omitted with
reasons, readiness products, Architecture revision refs, runtime prerequisites,
lane-owned blockers, and `PLAN_OUTPUT_READY`. Do not report Tasks, execution
results, or cross-command consistency.
