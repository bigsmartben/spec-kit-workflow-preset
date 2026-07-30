---
description: Map completed Plan products to concrete paths, dependencies, and executable checklist tasks.
strategy: wrap
---

Follow cross-agent protocol profile: `speckit.tasks.stage_local_derivation`.

## Core Precedence And Ownership

Preserve Core input/path resolution, task format, story organization, parallel
markers, dependency sections, and completion behavior.

The completed Plan is authoritative for test requirements:

```text
Required TC-* in Test Readiness
  => corresponding fixture/test/validation work is required
```

Core's generic “tests are optional” rule applies only when the completed Plan
contains no Required Test Condition for the slice. Tasks MUST NOT drop or
optionalize a required Plan Test Condition.

Tasks owns task IDs, concrete paths, checklist formatting, dependency order,
story/capability grouping, `[P]` markers, and compact task boundaries. It does
not choose Architecture, design objects, test level/type/technique/priority,
fixture strategy, execution mode, oracle, evidence, or UI/UX ownership.

## T0 — Plan Handoff Preflight

Before writing `tasks.md`, require the current Plan handoff:

```text
PLAN_OUTPUT_READY
├── plan.md + Design Object Derivation Index
├── research.md
├── X2-A artifacts when active
├── ui-ux-design.md + UI/UX Delivery Readiness when active
├── contracts/test/test-conditions.json when Test is active
├── technique-specific contracts when selected
├── quickstart.md VAL-* paths
└── test-readiness.md when Test is active
```

Verify only immediate handoff completeness and Tasks' own output contract:

- `PLAN_OUTPUT_READY: READY`;
- current Plan/artifact revisions, including the revision named by the Tasks
  handoff;
- Design, UI/UX, and Test readiness independently present or explicitly N/A;
- the complete X2-B mapping inventory has only `Required`, `N/A`, or `Blocked`
  rows and uses current `X2B-UI-*`, `X2B-PX-*`, and `X2B-ADP-*` IDs;
- every Required mapping resolves to declared `UI-*`, `VIS-*`, `PXT-*`,
  `PEX-*`, or `ADP-*` Plan refs;
- every Required mapping is classified as an implementation mapping or as a
  review-method-only mapping with an explicit no-task rationale;
- stable Plan blockers and runtime prerequisites remain distinguishable.

Missing information produces `PLAN_OUTPUT_INCOMPLETE`; stop before writing
complete-looking tasks. Do not recover by treating Spec/Checklist as direct
strategy inputs, reconstructing missing Plan decisions, or performing
Analyze-owned cross-command conformance.

A `Blocked` mapping keeps its blocker visible and produces no normal task.
Stale mappings, missing UI/UX Delivery Readiness rows, or suppressed blockers
also make the handoff incomplete.

## T1 — Concrete Path Binding

Bind each populated Plan record to the smallest relevant set of concrete source,
test, fixture, configuration, migration, and asset paths. Preserve the planned
`M + U` scope and responsibility. Exact paths are a Tasks output; Plan does not
own them.

Examples:

```text
PaymentCoordinator -> backend/src/checkout/payment_coordinator.py
PaymentFeedbackPanel -> frontend/src/checkout/PaymentFeedbackPanel.tsx
TC-PAYMENT-DECLINED -> tests/contract/checkout/test_payment_declined.py
```

Changing object ownership, test level, or sandbox to mock is re-planning and is
forbidden.

For active X2-B delivery, route every Required implementation mapping without
duplicate path/dimension coverage:

| Mapping class | Concrete task responsibility |
|---|---|
| `X2B-UI-*` | component, state, interaction, navigation, responsive, accessibility |
| `X2B-PX-*` | geometry, sizing, spacing, alignment, flow, overflow, clipping, typography, text metrics, color, gradient, border, radius, shadow, opacity, effects, asset preparation/binding/crop/aspect/fitting, layering/stacking/fixed-sticky/occlusion |
| `X2B-ADP-*` | target component, navigation, presentation, input modality, gestures, system UI, safe regions, adaptive layout, accessibility scaling, localization, layout direction |

Each emitted task names its mapping ID, covered implementation dimensions,
declared traceability refs, and exact file/configuration/asset paths. A
review-method-only row emits no task and retains its Plan-authored rationale.

Example:

```text
X2B-PX-004 asset-preparation -> T041 prepare assets/refund-panel.svg
X2B-PX-004 asset-binding     -> T042 bind it in src/ui/RefundPanel.tsx
T042 depends on T041
```

## T2 — Dependency Graph

Build dependencies from Plan refs, shared paths, fixtures, contracts, and
execution boundaries. X2-A/X2-B/X2-C are parallel; never impose a fixed
`data -> UI -> test` lane order. Add `[P]` only when tasks touch independent
paths and have no unresolved dependency.

For X2-B, preserve mapping-to-mapping dependencies and derive task edges from:

- shared source/configuration/asset paths;
- `X2B-*` mapping dependencies and declared `DEC-UI-*` decision refs;
- asset preparation before asset binding;
- component availability before state/interaction binding;
- target-component availability before platform-specific behavior;
- accessibility or responsive prerequisites recorded by the Plan mapping.

Do not emit normal tasks for N/A, intentionally minimal, placeholder, or blocked
records.

## T3 — Story / Capability Derivation

Use user stories or deliverable/capability slices as phase boundaries. Map only
populated Plan products:

| Plan product | Tasks result |
|---|---|
| scope / `M + U` | task scope and phase boundary |
| technical decisions | setup/configuration/dependency tasks |
| Design Object Derivation Index | implementation object paths |
| data model | domain/persistence/migration/invariant work |
| interface contracts | contract tests and interface implementation |
| sequences | orchestration/retry/rollback/compensation dependencies |
| `X2B-UI-*` | component/state/interaction/navigation/responsive/accessibility implementation |
| `X2B-PX-*` | geometry/typography/appearance/asset/layering/overflow/clipping implementation |
| `X2B-ADP-*` | platform component/navigation/input/system/safe-region/adaptive/accessibility/localization implementation |
| Test Readiness | fixture, test-first, validation, evidence work |
| `VAL-*` paths | runnable integration/e2e/evidence work |

Do not emit a task because a file merely exists. Keep tasks compact and split
only at meaningful path ownership, dependency, execution-command, or evidence
boundaries.

## T4 — Functional Validation And Evidence

For each Required `TC-*`, preserve the Plan-selected level, type, technique,
fixture/data decision, environment/mode, oracle, evidence, related refs, and
`VAL-*` path. Generate the smallest meaningful chain:

```text
fixture/environment -> test skeleton or Red -> implementation
  -> runnable validation/evidence
```

Do not force four tasks when one command naturally owns validation and evidence.
Unit/component/contract/integration/system/e2e work is emitted only when Test
Readiness requires it. Functional UI, accessibility, responsive behavior, and
user-journey tests are generated only from Required Test Conditions.

UI/UX Delivery Readiness is implementation readiness only. It may generate:

- view/component and state implementation;
- loading/empty/error/success/permission/disabled/focus behavior;
- functional responsive, navigation, interaction, and accessibility work;
- geometry, sizing, spacing, alignment, flow, overflow, and clipping;
- typography and text-metric implementation;
- color, gradient, border, radius, shadow, opacity, and effects;
- asset preparation, variants, binding, crop, aspect, fitting, authorization
  refs, and fallback;
- layering, stacking, fixed/sticky positioning, and occlusion;
- target-platform component, navigation, presentation, input, gesture, system
  UI, safe-region, adaptive-layout, accessibility-scaling, localization, and
  layout-direction implementation.

Local `UI-*`, `VIS-*`, `PXT-*`, `PEX-*`, and `ADP-*` refs guide only the
implementation dimensions already mapped in X2-B. `PXT-*` and `PEX-*` are
traceability inputs, not authority to copy the Spec-owned baseline locator,
fidelity mode, acceptance envelope, exception bound, or adaptation decision.
The external locator remains opaque and does not create
acceptance/verification work.

### Forbidden task scope

Never generate:

- `visual_acceptance` or `pixel_fidelity_review`;
- screenshot capture, screenshot comparison, screenshot diff, visual diff, or
  baseline production or baseline capture;
- pixel comparison, perceptual comparison, threshold evaluation, visual
  acceptance, or acceptance-envelope/fidelity-mode evaluation;
- visual restoration, rendered-fidelity judgment, final visual review, or
  final rendered visual review;
- pixel-level layout/style assertions or perceptual assertions;
- screenshot-based evidence requirements;
- source dereference, execution, authenticity/freshness/revision/publication
  checks, or external-source validation;
- provider-tool, source acquisition, external baseline certification, or
  locator-availability tasks;
- an automatic UI acceptance phase;
- a Final Code Review scope that judges rendered fidelity.

Tasks MAY implement pixel-target dimensions such as spacing, typography,
effects, asset fitting, layering, overflow, and clipping. It MUST NOT execute
the visual method used to judge those dimensions. For example, “set the mapped
8 px spacing in `RefundPanel.tsx`” is implementation; “capture a screenshot and
compare it to the baseline” is forbidden visual execution.

Functional UI tests remain derived only from Required `TC-*` rows in Test
Readiness. An `X2B-PX-*` or `X2B-ADP-*` mapping never invents a test condition.

## Stable Tasks Contract Errors

The pure in-memory Tasks contract validator uses these stable error codes:

- `TASK_X2B_MAPPING_UNMAPPED`;
- `TASK_X2B_MAPPING_DUPLICATE`;
- `TASK_X2B_REF_UNKNOWN`;
- `TASK_X2B_BLOCKER_SUPPRESSED`;
- `TASK_X2B_IMPLEMENTATION_DIMENSION_UNCOVERED`;
- `TASK_X2B_ADAPTATION_UNCOVERED`;
- `TASK_SPEC_OWNERSHIP_LEAK`;
- `TASK_VISUAL_EXECUTION_LEAK`;
- `TASK_FINAL_REVIEW_MAPPING_MISSING`.

The validator supports tests and static conformance only. It is not a runtime,
execution manifest, transfer protocol, worker result format, dispatcher, or
replacement for Core `/speckit.implement`.

## Task-Derivation Delegation

When the runtime supports bounded derivation subagents, the Tasks Core Agent
remains the sole writer. Partition by story/capability, Plan record group, or
review scope. Payloads declare assigned scope, exact allowed reads/sections, and
an output contract containing task candidates, source refs, blockers, and
`context_gaps`. A derivation unit that needs undeclared context returns
`TASK_DERIVATION_CONTEXT_GAP`; it does not widen its own reads.

Allowed derivation roles are Story/Capability Mapping, Contract/Test Mapping,
UI Implementation Mapping, and Final Review Mapping. They do not implement,
write upstream artifacts, invent strategy, or define a persistent transfer
protocol.

## T5 — Final Code Review

When generating `tasks.md`, append the final phase after user-story tasks. It is
mandatory and no phase may follow it. Core `/speckit.implement` executes it as
ordinary ordered checklist work.

Applicable review scopes and sources:

| Scope | Plan source |
|---|---|
| boundary | `plan.md` M + U |
| design object | derivation index and class diagram |
| interface contract | interface contracts |
| behavior/test contract | Test Readiness and optional technique contracts |
| data side effect | data model, sequences, invariants, oracles |
| sequence consistency | sequence contracts |
| X2-B component/state/interaction | `X2B-UI-*`, UI/UX design, and UIF |
| X2-B geometry/typography/appearance | `X2B-PX-*` implementation mappings |
| X2-B asset/layering/overflow/clipping | `X2B-PX-*` implementation mappings |
| X2-B platform navigation/input/system/safe-region/adaptive/accessibility/localization | `X2B-ADP-*` implementation mappings |
| evidence completeness | Test Readiness and `VAL-*` paths |

Each review task names concrete source artifacts, implementation surfaces, and
functional evidence. It covers every Required X2-B implementation mapping and
checks mapping-to-code conformance, unresolved blockers, and Plan revision
drift. Review-method-only rows remain no-task rationales. UI review is
code/design-contract review only; it MUST NOT
judge rendered visual fidelity, evaluate an acceptance envelope, or require
screenshot/pixel evidence.

Review may authorize bounded implementation repair and affected-test reruns. If
repair requires changing Spec, Architecture, Plan, research, contracts,
readiness products, or quickstart, keep the task open and report an upstream
blocker.

Do not add an implementation reviewer runtime, receipt, manifest, worker
protocol, dispatch script, or preset-owned Implement command.

{CORE_TEMPLATE}

## Preset Completion Addition

Report handoff revision, mapped/blocked Plan records, concrete path groups,
Required Test Condition coverage, dependency/parallel summary, and confirmation
that Final Code Review is the last mandatory phase. Do not declare
cross-command consistency.
