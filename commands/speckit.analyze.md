---
description: Read-only cross-command consistency audit across Constitution, Architecture, Spec, Plan, and Tasks.
strategy: wrap
---

Follow cross-agent protocol profile: `speckit.analyze.read_only_parallel_review`.

## Exclusive Ownership And Read-Only Boundary

Analyze exclusively owns Cross-Command Consistency Gates. Producing commands own
their own output quality; official Core gates remain unchanged.

Analyze may read available Constitution, Architecture, repository facts, Spec,
Plan outputs, and Tasks. It MUST NOT modify or repair any artifact, generate a
receipt/compliance matrix/audit file, invoke another command, inspect
post-implementation code as proof of design, or promote a finding into a new
Plan/Tasks gate.

Run against artifacts currently available. Missing later-stage artifacts limit
the relevant audit rather than authorizing invention.

## One-Pass Inventory

Build one in-memory inventory before deep reading:

- Constitution revision, SDD authority statements, exact R/M/U/O model;
- Architecture Revision plus `BND-*`, `CON-*`, `DEC-*`, `CST-*`, `GAP-*`;
- Spec `SRC-*` rows with role, scope, projection, and blocker plus
  `FR/NFR/UX/UI/VIS` and other stable refs;
- X0–X4 gates, decisions, design/readiness products, `TC-*`, `VAL-*`;
- Tasks IDs, concrete paths, dependencies, Test Condition refs, Final Code
  Review position.

Use stable IDs as the primary consistency surface. Read surrounding prose only
when an ID, source, mapping, or blocker is missing/ambiguous. Stop expanding one
branch after the first blocker that proves the downstream link cannot close.
Separate blockers from warnings.

## Audit Chain S — Local Source Reference Integrity

Audit only the local Source Reference Contract and its local projections:

- every referenced `SRC-*` exists exactly once in the Spec carrier;
- every source has exactly one allowed role, opaque locator/description,
  explicit authorized scope/facts, projection refs or a reason for none, and a
  status/blocker;
- every projected requirement ref exists locally and is compatible with the
  role: `requirement-input` may project WHAT/WHY refs, `visual-input` only
  `UI-*`/`VIS-*`, while `technical-evidence` and `context-only` authorize no
  normative requirement;
- a broad source without a safe feature slice remains blocked or needs
  clarification instead of projecting unrelated facts;
- orphan, contradictory, missing, role-invalid, and projection-invalid refs
  produce stable findings;
- every applicable `SRC-* + UI/VIS-*` pair reaches X2-B UI/UX Delivery records
  and, when an interaction contract is required, UIF `source_refs` plus
  `requirement_refs`.

Use stable codes including `SRC_REF_MISSING`, `SRC_REF_DUPLICATE`,
`SRC_FIELD_INVALID`, `SRC_ROLE_INVALID`, `SRC_ROLE_PROJECTION_INVALID`,
`SRC_PROJECTED_REF_MISSING`, `SRC_FEATURE_SLICE_MISSING`, `SRC_ORPHAN`,
`SRC_STATUS_CONTRADICTORY`, `SRC_UIUX_MAPPING_MISSING`, and
`SRC_UIF_MAPPING_MISSING`.

Do not open, run, inspect, compare, fetch, or otherwise dereference an external
locator. Do not decide source authenticity, availability, revision/digest
freshness, fidelity, or publication state. Analyze writes no persistent audit
artifact and does not acquire missing evidence.

## Audit Chain A — Constitution To Spec / Plan

Check cross-artifact effects only:

- Spec/Plan do not claim Constitution or Architecture authority;
- Plan/Tasks preserve the exact planned `M + U` boundary and do not widen to R;
- command outputs do not introduce Intake as an SDD stage;
- Plan does not create a cross-command Architecture Conformance Gate;
- Tasks does not perform upstream consistency repair;
- downstream authority does not contradict Constitution's command ownership.

Do not re-run `CONSTITUTION_OUTPUT_READY`.

## Audit Chain B — Architecture To Plan Products

For every repository, audit one strategy:

```text
repo-first planning within Architecture constraints
```

Do not classify Plan as Greenfield/Brownfield. Check that current repository
facts ground planned modules/paths/dependencies, planned creation is explicit,
and Plan does not silently amend Architecture.

Check:

| Architecture source | Required downstream projection |
|---|---|
| `DEC-*` | `research.md` decision and affected X2/X3 refs |
| `CON-*` | `data-model.md` meaning, ownership, lifecycle, invariants |
| `BND-*` | interface contracts and dependency direction |
| `CST-*` | applicable `plan.md`, design, and `quickstart.md` constraints |
| `GAP-*` | stable blocker/prerequisite without fake evidence |
| Architecture Revision | current refs in `plan.md` and readiness products |

Report omitted IDs, contradictions, stale revision, repository-grounding gaps,
unauthorized authority promotion, or an Architecture change that should return
to `/speckit.constitution`. Do not run a Plan-internal Architecture gate.

### #24 concrete data-model projection

When applicable Architecture/Spec refs require them, verify the domain/design
chain explicitly represents:

- idempotency record/key composition and create uniqueness;
- provider task binding to clip/shot/render plan;
- provider configuration/version lock;
- retry/force-retry retention of entitlement, SKU, language, render plan,
  provider lock, and attempt history;
- provider switching as an explicit recovery decision, not ordinary retry;
- lifecycle separation among entitlement readiness, provider completion, and
  client availability (`ready` versus `completed`).

Use source → target blocker codes such as
`ARCH_DATA_MODEL_IDEMPOTENCY_MISSING`,
`ARCH_PROVIDER_BINDING_MISSING`, `ARCH_PROVIDER_LOCK_MISSING`,
`ARCH_RETRY_CONTEXT_MISSING`, `ARCH_RECOVERY_DECISION_MISSING`, and
`ARCH_LIFECYCLE_PROJECTION_MISSING`. These are Analyze findings, not business
fields mandated for unrelated features.

## Audit Chain C — Spec To X0/X1/X2/X3/X4

Check applicable Spec refs project without contradiction:

- goals/exclusions and requirement refs into X0;
- product constraints into X1 decisions;
- domain/interface requirements into X2-A;
- UX/UI/VIS into UI/UX Design and Delivery Readiness;
- functional/NFR/security/accessibility/recovery/data-side-effect acceptance
  into `TC-*` and Test Readiness;
- Test Conditions needing execution into `VAL-*`;
- blockers retain their actual owning lane.

BDD/fixtures/assertions are required only when the parent Test Condition selects
that technique. Pixel delivery/readiness stays in UI/UX and is absent from Test
Conditions/Test Readiness.

## Audit Chain D — Plan To Tasks

Check every populated Plan record maps to concrete Tasks work or an explicit
blocker:

- Design Object rows → implementation paths;
- interface/sequence refs → contract/orchestration dependencies;
- UI/UX Delivery rows → component/state/responsive/accessibility/asset
  implementation only;
- Required `TC-*` → required fixture/test/validation/evidence tasks;
- `VAL-*` → runnable environment/integration/e2e/evidence work;
- Plan blockers → blocked task scope, never complete-looking work;
- Final Code Review covers applicable Plan sources and is the last phase.

Detect Tasks-side strategy invention and missing Plan-to-Tasks mappings.
Required Test Conditions must not be dropped by Core optional-test prose.

Assert #37's downstream visual boundary: no screenshot comparison, visual diff,
baseline, restoration, pixel assertion, visual acceptance, or rendered-fidelity
review task. Visual refs may guide UI implementation only.

## Finding Format And Implementation Readiness

For each finding output:

```text
severity | stable code | source artifact + ID/location
| target artifact + expected mapping | evidence | owning command / next action
```

Recommended top-level summary:

```text
Source References -> Local Projections: PASS | BLOCKED
Constitution -> Spec/Plan: PASS | BLOCKED
Architecture -> Plan Products: PASS | BLOCKED
Spec -> Plan Products: PASS | BLOCKED
Plan -> Tasks: PASS | BLOCKED
M + U Preservation: PASS | BLOCKED
Implementation Readiness: PASS | BLOCKED
```

`Implementation Readiness: BLOCKED` prevents proceeding to Core Implement. A
PASS means the available cross-command chains close; it does not replace any
producing command's output gate or prove implementation results.

{CORE_TEMPLATE}

## Preset Completion Addition

Report the inventory, chain summaries, blockers, warnings, and implementation
readiness. Confirm no files were written.
