# Preset Extension Governance

This document defines the ownership boundaries for `workflow-preset`.

## Source Of Truth

- `preset.yml` declares every packaged command, template, and schema.
- `commands/` contains stage-local instructions.
- `templates/` contains stable artifact shapes.
- `schemas/` contains machine-readable behavior contracts.
- `validators/speckit_behavior_contract.py` contains pure in-memory behavior
  cross-field checks.
- `validators/speckit_requirement_gate_contract.py` contains pure in-memory
  canonical Requirement Gate, Clarify reconciliation, and Plan preflight checks.
- `tests/test_preset_contract.py` is the executable preset contract.

## Preset Boundary

The preset enriches existing Spec Kit stages. It does not own execution
orchestration or add a second implementation engine.

## Authority And Gate Ownership

| Concern | Single owner |
|---|---|
| SDD workflow governance | `.specify/memory/constitution.md` |
| repository technical truth | `.specify/memory/architecture.md` |
| one command's output quality | the producing command |
| official workflow gates | Spec Kit Core, unchanged |
| cross-command consistency | `/speckit.analyze`, read-only |

Intake is external evidence acquisition, not an SDD stage. Constitution does
not contain concrete repository Architecture. Architecture does not contain
command procedures, gate definitions, product requirements, task derivation, or
downstream conformance conclusions.

`/speckit.constitution` is an enforceable replacement command so the authorized
source agreement can suppress unapproved repository inference. It preserves
user input, hooks, independent write scopes, validation, and completion
reporting.

The Constitution command owns two independent internal gates:

- `CONSTITUTION_OUTPUT_READY` validates SDD governance only.
- `ARCHITECTURE_OUTPUT_READY` validates the technical Architecture contract,
  including intent-first Greenfield and repo-first Brownfield generation.

Neither gate checks downstream artifacts. Constitution → Spec/Plan,
Architecture → Plan, Spec → Plan, and Plan → Tasks consistency belong only to
Analyze.

## Analyze Cross-Command Audit

Analyze is the only owner of cross-command consistency:

```text
Constitution -> Spec / Plan
Architecture -> research / data-model / contracts / plan / quickstart
Spec -> X0 / X1 / X2 / X3 / X4
Plan readiness products -> Tasks
Constitution M + U -> Plan / Tasks
```

It inventories once, uses stable IDs first, stops a branch at the first
conclusive blocker, separates blockers from warnings, and writes no artifact.
It audits one repo-first, Architecture-constrained Plan strategy for every
repository; Greenfield/Brownfield remain Constitution-only Architecture
generation modes.

The concrete #24 idempotency, provider binding/lock, retry context, provider
switching recovery, and `ready`/`completed` lifecycle cases are Analyze
fixtures. They are required only when applicable Architecture/Spec refs demand
them, and they do not become a Plan-local conformance gate.

| Stage | Owner | Durable output |
|---|---|---|
| `/speckit.constitution` | preset replacement | independently authorized Constitution and project Architecture outputs |
| `/speckit.specify` | preset replacement | full-spectrum WHAT/WHY content and stable semantic IDs in `spec.md` |
| `/speckit.clarify` | preset replacement | accepted product decisions in `spec.md`; current evaluation/derived state in the one Requirement Gate |
| `/speckit.checklist` | preset wrapper | one semantic-grouped `checklists/requirements.md` containing six logical Gates |
| `/speckit.plan` | preset wrapper | design, behavior contracts, and validation design |
| `/speckit.tasks` | preset wrapper | executable checklist in `tasks.md` |
| `/speckit.analyze` | preset wrapper | read-only cross-command consistency findings |
| `/speckit.implement` | Spec Kit core | execution of `tasks.md` |

`workflow-preset` MUST NOT declare, package, copy, or replace
`speckit.implement`. The active Spec Kit core version is the single source of
truth for the implementation command. A core implementation change therefore
requires no preset release.

The preset MUST NOT introduce an implementation-specific reviewer command,
runtime role, persistent transfer protocol, execution manifest, worker result
protocol, manual execution queue, or implementation validator.

## Artifact Pipeline

The workflow is a producer-to-consumer pipeline:

```text
spec.md with stable semantic refs
    -> one checklists/requirements.md with six logical Gates
    -> Clarify decision write + gate reconciliation
    -> zero-write Plan requirement-gate preflight
    -> X0 plan control
    -> X1 shared decisions
    -> X2-A domain/object/interface + X2-B UI/UX + X2-C Test contracts
    -> X3 VAL paths + X4 independent readiness
    -> tasks.md implementation and validation checklist
    -> core /speckit.implement execution
```

Tasks maps upstream artifacts into checklist items. It must not create another
planning system or execution protocol.

## Requirement Command Ownership

Specify owns product projection, Checklist owns the question set, and Clarify
owns accepted product decisions plus post-decision gate reconciliation:

| Command | Writes | Does not own |
|---|---|---|
| Specify | one `spec.md` plus official feature bootstrap metadata; stable semantic IDs and their replacement/retirement relations | checklists, completeness/readiness, Check/Blocker evaluation |
| Checklist | one canonical `checklists/requirements.md` | answers, spec repair, other checklist files, downstream design |
| Clarify | accepted decisions in `spec.md`; current Check evidence, shared Blockers, Revision, Summary, and readiness in existing canonical `requirements.md` | new checklist questions, malformed-layout repair, source acquisition, downstream design |

The full-spectrum `spec-template` supplies optional, stable-ID carriers for
functional, NFR, UX, UI, visual, security/privacy, data/integration,
dependency, boundary, assumption, exclusion, source, unresolved-decision,
source-blocker, and measurable outcome content. IDs follow product meaning:
wording-only edits preserve them; split, merge, retirement, and N/A retain
explicit lifecycle records. A carrier's presence is not a completeness claim.

Specify and Clarify are replacement commands because active Core side effects
would otherwise create or re-evaluate `checklists/requirements.md` outside the
preset contract. Their replacement contracts preserve user input, feature/path
resolution, extension hooks, local write safety, and completion reporting.
Checklist remains a Core wrapper but supersedes Core's multi-file write target.
With or without focus it atomically rebuilds only
`checklists/requirements.md`. The physical main structure is keyed by stable
Spec semantic ref. Cross-Gate Check records and shared root-cause Blockers live
only inside those groups. Every Check retains its template Rule key, and PASS
evidence resolves its current Spec refs as `spec.md#<Spec semantic ref>`. The
six logical Gates are `requirements`, `behavior`,
`ux`, `security`, `nfr`, and `visual`; their Summary carries only
applicability/status, refs, and counts, never duplicated questions or product
answers.

One semantic root cause can block several Checks and Gates. A Spec ref can also
have multiple distinct root causes. Check IDs and Blocker IDs are therefore
many-to-one, not mechanically paired. Blockers retain class, owner, affected
Checks, and split/merge/retirement history. Clarify asks once per OPEN
`product-decision` Blocker, updates the Spec first, then synchronizes the
canonical Gate. Even a zero-question closeout re-evaluates all groups and
refreshes the exact Spec SHA-256. Missing/malformed Gate structure is preserved
and routed to Checklist; source-evidence Blockers retain their original owner.
This closes state directly without a `Clarify -> Checklist -> Clarify` loop.

Plan runs a read-only path resolver and consumes only current `spec.md` plus the
one canonical `requirements.md`. Before hooks, template materialization, X0, or
any Plan write, it recomputes Revision, references, all six Summary rows, and
Planning Readiness. Any mismatch emits
`REQUIREMENT_GATE_PREFLIGHT_BLOCKED` and produces zero Plan writes. Plan never
repairs upstream state or calls an upstream command. No `planning-readiness.md`
exists.

Existing advisory files and the obsolete six-file Domain layout are preserved
byte-for-byte but ignored by Checklist, Clarify, Plan, and Planning Readiness.
They are never answer sources or fallback authority.

“Zero Blocker” in Planning Readiness means no `OPEN` current root cause.
Resolved, retired, and superseded Blocker rows are traceability history; no
current BLOCKED Check may reference them.

Examples:

- A UI state in `ui-ux-design.md` and `contracts/uif/` becomes concrete UI
  implementation work. Functional tests exist only when Test Readiness contains
  a Required Test Condition.
- A real-system path in `quickstart.md` becomes an integration/e2e task with
  environment and evidence expectations.
- A persistence change becomes implementation and data-side-effect validation
  tasks, followed by the final review scope.

## Source Reference Contract

Bounded supplied material is an input to existing commands, not an SDD stage or
runtime dependency. `/speckit.specify` begins only after applicable content or
source-backed facts have been supplied. It owns no source-access,
authentication, provider, locator-resolution, adapter, or synchronization
responsibility. `spec.md` carries one canonical, source-neutral shape:

```text
SRC ref | role | opaque locator/description | revision/identity
| bounded feature scope | supplied content/facts
| projected requirement refs | status/blocker
```

The allowed roles are exactly:

| Role | Local authority |
|---|---|
| `requirement-input` | supplied, feature-scoped WHAT/WHY facts |
| `visual-input` | supplied, feature-scoped `UI-*` and `VIS-*` evidence/facts |
| `technical-evidence` | citable evidence that does not become a product requirement |
| `context-only` | informative context with no normative projection authority |

Every used source has one role and a feature slice. A broad source without a
safe slice remains blocked or needs clarification instead of being imported in
full. A URI/path/revision/digest/description is opaque provenance; without
supplied content/facts it records `SRC_EVIDENCE_MISSING` and projects no local
requirement. The preset does not infer adjacent scope or validate external
meaning, authenticity, freshness, publication state, availability, or fidelity.

After source-backed projection, `spec.md` is the feature-local WHAT/WHY SSOT.
Clarify may make a user-accepted local decision current while retaining the
originating `SRC-*` and clarification history; no external write-back or
synchronization is required.

Architecture reuses the four role meanings inside its existing explicit source
agreement without merging Architecture and Specify. Only authorized
`technical-evidence` supports observed or inferred technical records.
Product-facing sources do not become technical decisions automatically.

Plan reads only local Spec, Constitution, Architecture, and current repository
facts. `SRC-*` locators are provenance, not read or execution targets.
Applicable visual projection follows:

```text
SRC-* + UI/VIS/RST/PXR/PXT/PEX/ADP refs
  -> ui-ux-design.md Spec UI Input Inventory
  -> X2B-* delivery mappings + UIF source_refs/requirement_refs
  -> UI/UX Delivery Readiness
```

Tasks uses that local mapping for implementation guidance only. Analyze checks
local source existence, uniqueness, role compatibility, projection targets,
orphans, contradictions, and X2-B/UIF mappings. Neither command acquires,
dereferences, executes, compares, or certifies an external source.

## Feature-Local UI Specification Contract

`spec.md` remains the only product-requirement SSOT. Its stable UI
Specification structure makes every applicable `UI-*`/`VIS-*` row identify:

- stable identity and kind;
- observable statement;
- `SRC-*` refs and locators inside the bounded supplied input;
- surface/region, state/preconditions, and viewport/target context;
- one of `observed`, `derived`, `assumed`, `unresolved`, or `conflicting`;
- measurable acceptance condition;
- `specified` or a stable blocker.

HTML, CSS, rendered-state, interaction, asset, responsive, and accessibility
evidence projects only outcomes directly supported by cited observations or
deterministically derived from them. For example, one desktop rendering may
support the cited desktop geometry but cannot support an unevidenced mobile
layout. An `assumed` low-impact default is labeled as such; `unresolved` and
`conflicting` rows remain blocked.

Restoration additionally classifies content, information structure, visual
appearance, interaction/feedback, UI states, responsive viewports,
accessibility, and asset identity/substitution. Pixel restoration uses stable
`PXR-*` profiles, `PXT-*` surface × state × viewport targets, and `PEX-*`
accepted exceptions. Each unblocked target identifies one baseline,
rendering-context constraints, one of `pixel-exact`, `pixel-tolerant`,
`perceptual-equivalent`, or `structural-only`, and a measurable acceptance
envelope. Missing/conflicting inputs remain blocked; Specify owns no baseline
production, comparison execution, implementation method, or review result.

Cross-platform restoration records one policy per applicable scope:

```text
UI ref | source platform | concrete target platform | adaptation mode
| preserve/adapt/add/omit decisions | target contexts | SRC refs
| status/blocker
```

Allowed modes are `framework-equivalent`, `native-adaptive`,
`brand-preserving-native`, and `visual-equivalent-native`; `hybrid` is invalid.
Each applicable dimension resolves to `preserve`, `adapt`, `add`, `omit`,
`clarify`, or `blocked`. `Swift` is an implementation language rather than a
concrete target platform.

Conflicts use this precedence:

```text
target-platform hard constraints and accessibility requirements
  > explicit product requirements
  > declared adaptation policy and per-dimension decisions
  > source-backed observable UI evidence
  > target-platform defaults
  > implementation preference
```

Specify owns target outcomes. X2-B owns concrete components, unit conversions,
navigation/presentation mechanisms, safe-region implementation, accessibility
mapping, adaptive-layout strategy, and delivery/review methods. Pixel scope
must not enter Test Conditions or Test Readiness.

### Plan-Internal UI Contract Consumption

Plan consumes the UI Specification through reference-only, rebuildable X2-B
delivery mappings. X0 and `ui-ux-design.md` record the same current local
`spec.md` SHA-256. The digest detects local same-ID semantic changes; it does
not certify any external source, revision, locator, or baseline. A mismatch
invalidates affected X2-B, reconciliation, X4, and `PLAN_OUTPUT_READY`
evidence.

`ui-ux-design.md` inventories every applicable `UI/VIS/RST/PXR/PXT/PEX/ADP`
ref exactly once, then maps it through stable Plan-owned `X2B-*` records:

- general UI delivery maps UI/visual/restoration refs to regions, components,
  state, navigation, input, responsive, and accessibility design;
- pixel-target delivery maps profile/target/exception refs to target-region,
  style/token/asset/layering/overflow responsibilities and a local X2-B method;
- platform-adaptation delivery maps one policy/dimension ref to target-context
  component, navigation, input, layout, and accessibility design.

The inventory and mappings reference but never copy Spec-owned statements,
baseline identity/locator, state/viewport, rendering context, fidelity mode,
acceptance envelope, exception bound, or adaptation decision. Every required
mapping has one UI/UX Delivery Readiness row. A Spec blocker propagates with
the same ID and cannot become `READY` or `N/A`.

## Final Code Review Gate

`/speckit.tasks` MUST append Final Code Review as the last mandatory phase of
`tasks.md`. It is an ordinary ordered task phase executed by the standard core
implementation command, not an independent runtime.

The phase must cover each applicable scope:

- planned `M + U` boundary;
- interface contracts;
- behavior and Test contracts;
- UI component/state, responsive/accessibility behavior, and asset contracts;
- data side effects;
- sequence consistency;
- asset bindings;
- integration/e2e evidence and unresolved blockers.

Completion requires the review tasks themselves to pass. No separate worker
result file or orchestration layer is required.

UI review is code/design-contract review. Tasks and Final Code Review never
create or evaluate visual acceptance, screenshot/baseline production,
pixel/perceptual comparison, visual diff, acceptance-envelope thresholds, or
final rendered-visual review. `X2B-PX-*` may still produce geometry,
typography, appearance, asset, layering, overflow, and clipping implementation
work. Visual/IR/source refs remain traceability and do not create a validation
task.

## Tasks As A Pure Plan Mapper

`/speckit.tasks` starts from `PLAN_OUTPUT_READY`, not Spec or Checklist strategy.
Its lifecycle is:

```text
T0 handoff preflight
  -> T1 concrete path binding
  -> T2 dependency graph
  -> T3 story/capability mapping
  -> T4 required functional validation/evidence
  -> T5 Final Code Review (last mandatory phase)
```

Tasks owns exact paths, task IDs, dependency order, `[P]`, and checklist shape.
It preserves Plan-selected design/test/UI decisions. Missing mappings produce
`PLAN_OUTPUT_INCOMPLETE`; Tasks does not reconstruct them.

A current, closed X2-B handoff routes mappings as follows:

| Mapping | Tasks responsibility |
|---|---|
| `X2B-UI-*` | component, state, interaction, navigation, responsive, accessibility |
| `X2B-PX-*` | geometry, typography, color/effects, assets, layering, overflow, clipping |
| `X2B-ADP-*` | target-platform system, navigation, input, layout, accessibility, localization |

Every Required implementation mapping names concrete paths. A
review-method-only mapping may omit tasks only with its explicit Plan rationale.
Blocked mappings emit no normal tasks and keep `PLAN_OUTPUT_INCOMPLETE`.
Dependencies come from mapping/`DEC-UI-*` refs, shared paths, interface/UIF
boundaries, asset preparation/binding, and accessibility/adaptive constraints;
independent lanes retain parallel eligibility.

A Required `TC-*` overrides Core's generic optional-test wording. UI,
accessibility, responsive, and journey tests exist only when Test Readiness
requires them. UI/UX Delivery Readiness otherwise maps only to component, state,
interaction, accessibility, responsive, geometry/style, asset/layering, and
platform-adaptation implementation work.

`validators/speckit_tasks_contract.py` is a pure in-memory test helper. Its
stable surfaces include `TASK_X2B_MAPPING_UNMAPPED`,
`TASK_X2B_MAPPING_DUPLICATE`, `TASK_X2B_REF_UNKNOWN`,
`TASK_X2B_BLOCKER_SUPPRESSED`,
`TASK_X2B_IMPLEMENTATION_DIMENSION_UNCOVERED`,
`TASK_X2B_ADAPTATION_UNCOVERED`, `TASK_SPEC_OWNERSHIP_LEAK`,
`TASK_VISUAL_EXECUTION_LEAK`, and `TASK_FINAL_REVIEW_MAPPING_MISSING`. It is
not an execution runtime, manifest, transfer protocol, worker format, or
Implement override.

## Structured Artifact Rules

Machine-readable JSON artifacts are contracts, not prose examples. Stable
behavior JSON artifacts require schemas in `schemas/` and focused coverage in
`validators/speckit_behavior_contract.py` when cross-field rules matter.

Every packaged schema and validator must be covered by
`tests/test_preset_contract.py`.

The UI Specification validator's in-memory bundle keeps
`all_spec_requirement_refs` separate from its `UI-*`/`VIS-*` requirement
records. This lets one canonical `SRC-*` row project both general product refs
and UI refs without moving `FR-*`/`NFR-*` content into the UI contract.

The Tasks validator's in-memory candidates use transient `action_classes` to
separate implementation, functional validation, forbidden visual execution,
and Final Code Review. This metadata exists only for contract tests; it is not
written to `tasks.md` and is not an execution manifest or transfer protocol.

`validators/speckit_requirement_gate_contract.py` is likewise a pure in-memory
test helper. It models the one canonical bundle, stable Spec/Check/Blocker
references, shared root causes, strictly derived Six-Gate Summary and Planning
Readiness, partial/full/zero-question clarification, stale Revision
replacement, ID lifecycle, legacy selection, and read-only Plan preflight
without parsing or writing Markdown. Stable findings include
`REQUIREMENT_GATE_SPEC_REF_UNKNOWN`,
`REQUIREMENT_GATE_SPEC_REF_MISSING`,
`REQUIREMENT_GATE_LAYOUT_EXTRA_FIELD`,
`REQUIREMENT_GATE_CHECK_EVIDENCE_INVALID`,
`REQUIREMENT_GATE_BLOCKER_CROSS_GROUP`,
`REQUIREMENT_GATE_BLOCKER_AFFECTED_CHECK_MISMATCH`,
`REQUIREMENT_GATE_SUMMARY_DRIFT`,
`PLANNING_READINESS_DERIVATION_INVALID`, and
`REQUIREMENT_GATE_PREFLIGHT_BLOCKED`.

## Cross-Agent Rules

Planning and task derivation may use bounded, stage-local subagents when the
runtime supports them. The owning command remains the sole final writer for its
stage. Delegation metadata is transient derivation context and must not become
an implementation transfer format.

Shared stage-local behavior is documented in
`tests/contracts/speckit-cross-agent-protocol.md`. Commands may reference only
their own stage profile. Commands must not use `tests/` or `docs/` paths as
runtime sources.

## X0–X4 Planning Artifact Boundaries

Keep `/speckit.plan` and `/speckit.tasks` as core-template wrappers unless an
intentional contract change says otherwise.

The X labels are preset-internal milestones nested inside unchanged Core Plan
setup, Phase 0, Phase 1, post-design Constitution Check, hooks, and completion:

| Milestone/lane | Owning artifact |
|---|---|
| X0 Feature Plan Control | `plan.md` |
| X1 Research & Decisions | `research.md` |
| X2-A Domain/Object/Interface | `data-model.md`, contextual `class-diagram.md`, interface contracts, contextual `contracts/sequences.md` |
| X2-B UI/UX Delivery | `ui-ux-design.md`, `contracts/uif/` |
| X2-C Test & Acceptance | `contracts/test/test-conditions.json`, optional technique children |
| X3 Validation Paths | `quickstart.md` `VAL-*` paths |
| X4 Design Readiness | `plan.md` derivation index |
| X4 UI/UX Delivery Readiness | `ui-ux-design.md` |
| X4 Test Readiness | `test-readiness.md` |

X2-A, X2-B, and X2-C are parallel and mutually constraining. BDD is an optional
Test technique, not the parent of planning. Test Conditions may cover
functional, accessibility, security, performance, reliability, recovery,
compatibility, and data-side-effect concerns across unit/component/contract/
integration/system/e2e levels.

Pixel-fidelity delivery and review belong only to UI/UX Delivery Readiness.
Pixel, screenshot, diff, baseline, restoration, and rendered-visual-review work
is rejected from Test Conditions and Test Readiness.

Plan internal milestones use one evidence-bearing loop: entry conditions,
bounded reads, owned writes, validation, `READY/BLOCKED/N/A` evidence, and stop
handling. A dependent milestone cannot start before its dependency Gate closes.
After active X2 lanes, Plan performs a cross-lane reconciliation over stable
`DEC-*`, design/interface/sequence, UIF, `TC-*`, and requested `VAL-*` refs;
X3 refreshes every affected reconciliation row after producing validation
paths.

Conditional artifacts are decided by explicit triggers rather than file
presence. Class diagrams are triggered by cooperating-object responsibility or
dependency design; interface contracts by an externally observable boundary;
sequences by observable cross-boundary order/failure flow; X2-B by user-visible
or interactive delivery; and BDD/scenario/fixture/assertion children by their
parent Test Condition techniques. Pure domain/internal-object X2-A therefore
does not require an interface contract. Each non-triggered artifact has a
concrete N/A reason.

Blocked applicability is never rewritten as N/A. During continuation, artifact
decisions remain independent: preserve verified Required outputs and block only
affected outputs. X2-C does not force Test Conditions, Quickstart, and Test
Readiness to share one Blocked decision. Every required Test Readiness row is
READY with evidence or BLOCKED with a blocker, and any blocked row prevents
`PLAN_OUTPUT_READY`.

`plan.md` Gate evidence is also the continuation index. A rerun preserves
verified artifacts whose inputs and refs are unchanged, resumes at the first
unclosed or affected Gate, and revalidates its downstream consumers. No
`PENDING` state or persistent execution/transfer artifact is introduced.
`PLAN_OUTPUT_READY` is derived only from evidenced internal Gates,
reconciliation, readiness products, conditional decisions, resolved refs, and
the absence of decision placeholders.

Validation decisions stay in `research.md`, executable paths stay in
`quickstart.md`, and `test-readiness.md` is the single Test/Tasks handoff. Do
not restore `behavior/behavior-testability.md`, create a generic
`planning-readiness.md`, or add a standalone `test-plan.md`.

## External Source Boundary

External source capture, access, authentication, rendering, and evidence
generation remain outside this preset. The preset does not require an upstream
workflow, directory convention, provider, artifact format, publication state,
import manifest, handoff package, adapter runtime, orchestration script, or
provider-specific schema.

Missing source evidence remains a local `SRC-*` blocker. Product decision gaps
return to clarification. Planning, Tasks, and Analyze do not acquire or repair
either kind of gap, and Intake is not added as an SDD stage.

## Release And Integration Boundary

The source repository owns development, tests, tags, releases, and release
artifacts. The Spec Kit fork owns only a reproducible bundled snapshot and
catalog metadata.

Integration must use an immutable release:

1. publish a new source version;
2. record the source repository, version, commit SHA, artifact URL, and artifact
   SHA-256;
3. extract the bundled snapshot without edits;
4. verify every bundled file hash against the release manifest;
5. ensure bundled and `--from <version>` installations are identical.

Never change a published version in place or modify the bundled snapshot after
integration.

## Validation

Run:

```bash
python3 -m unittest tests/test_preset_contract.py
```

Release preparation must also run the install smoke checks in
`.github/workflows/preset-artifact.yml`.
