{CORE_TEMPLATE}

## Specification Spectrum

This section is a content carrier, not a completeness checklist. Populate only
applicable domains and retain a concrete `Not Applicable: <reason>` when
non-applicability is confirmed.

### Functional Requirements

- **FR-001**: [Observable product behavior.]

### Non-Functional Requirements

- **NFR-001**: [Measurable quality outcome, constraint, or explicit N/A.]

### UX Journeys and Interaction Expectations

- **UX-001**: [Actor goal, journey, feedback, recovery, and accessibility expectation.]

### UI Specification Contract

This is the feature-local UI requirement source of truth inside `spec.md`.
Rows specify observable outcomes, not delivery components, capture/comparison
procedures, or implementation choices.

| Requirement ref | Kind | Observable statement | SRC refs | Evidence locator(s) within supplied input | Evidence support | Surface / region | State / preconditions | Viewport / target context | Derivation | Measurable acceptance condition | Status / blocker |
|---|---|---|---|---|---|---|---|---|---|---|---|
| UI-001 | interaction | [Observable surface, state, feedback, responsive, or accessibility outcome.] | [SRC-001] | [Supplied HTML fragment, rendered-state frame, fact ID, or `None` only when blocked.] | [Supported dimensions such as surface, state, viewport, interaction.] | [Named surface/region.] | [State and content/data preconditions.] | [Width × height, range, platform context, or explicit N/A reason.] | [observed / derived / assumed / unresolved / conflicting] | [Measurable observable result, or blocker.] | [specified / BLOCKED: stable ID] |
| VIS-001 | visual | [Observable geometry, typography, appearance, asset, layering, overflow, or clipping outcome.] | [SRC-001] | [Exact locator inside the supplied evidence.] | [Supported dimensions such as surface, state, viewport, visual.] | [Named surface/region.] | [State and content/data preconditions.] | [Applicable viewport/context.] | [observed / derived / assumed / unresolved / conflicting] | [Measurable observable result, or blocker.] | [specified / BLOCKED: stable ID] |

Stable kinds are `content`, `structure`, `interaction`, `state`, `responsive`,
`accessibility`, `visual`, `asset`, and `restoration`. Every `UI-*`/`VIS-*`
row has exactly one kind and one derivation classification.

### UI Evidence Projection Rules

Apply these deterministic rules only to content/facts actually present in the
bounded supplied input:

| Evidence class | Supported local projection | Unsupported projection example |
|---|---|---|
| HTML / semantic markup | Observed content, hierarchy, control role, attributes, and states explicitly present in the supplied fragment. | A hidden error state is not inferred because a form exists. |
| CSS / computed-style facts | Observed selectors/properties and derived visual outcomes whose cited values deterministically imply them. | A framework component name or design token is not inferred from a color value. |
| Rendered-state evidence | Visible content, geometry, typography, appearance, asset crop, layering, overflow, clipping, and evidenced state at the cited viewport/context. | DOM nesting and off-screen states are not inferred from one image. |
| Interaction evidence | Observed trigger, transition, feedback, focus, keyboard, pointer, or gesture outcome for the evidenced state/context. | Hover behavior is not inferred for a touch-only target. |
| Asset evidence | Observed asset identity/variant/crop/aspect/fitting facts that the supplied evidence identifies. | A local file path or substitution is not invented. |
| Responsive evidence | Only the states or rules supported by cited viewports, breakpoints, constraints, or supplied facts. | Mobile behavior is unresolved when only one desktop viewport is supplied. |
| Accessibility evidence | Only supplied semantic, focus, scaling, contrast, motion, input, or assistive-technology outcomes. | Compliance or screen-reader behavior is not claimed from appearance alone. |

Derivation classifications have exact meanings:

| Classification | Contract meaning |
|---|---|
| `observed` | The statement is directly present at the cited evidence locator. |
| `derived` | The statement follows deterministically from cited observations; record those observation refs/locators in the row. |
| `assumed` | A documented low-impact default; it is never presented as observed and its acceptance condition exposes the default. |
| `unresolved` | Required evidence is absent; the row remains `BLOCKED` with a stable blocker. |
| `conflicting` | Supplied evidence disagrees across sources, states, or viewports; the row remains `BLOCKED` and cites each conflicting locator. |

A state, responsive, viewport, asset, or accessibility claim names that
dimension in Evidence support and cites corresponding evidence. A locator
without supplied content/facts records
`SRC_EVIDENCE_MISSING` and projects no `UI-*`/`VIS-*` requirement.

### Restoration Equivalence

When restoration applies, classify every dimension below for the applicable
scope. Use `required`, `not-applicable: <reason>`, or `BLOCKED: <stable ID>`;
absence is not a classification.

| Restoration scope | Dimension | UI/VIS refs | SRC refs / evidence locators | Expected observable equivalence | Acceptance condition | Status / blocker |
|---|---|---|---|---|---|---|
| RST-001 | content | [UI/VIS refs] | [SRC refs + locators] | [Required content outcome.] | [Measurable condition.] | [required / N/A reason / BLOCKED] |

Required dimensions are `content`, `information-structure`,
`visual-appearance`, `interaction-feedback`, `ui-states`,
`responsive-viewports`, `accessibility`, and `asset-identity-substitution`.

### Pixel-Restoration Profiles

Pixel-level restoration is an observable outcome contract. It does not define
how baselines are produced, comparisons are run, or delivery is implemented.

| Profile ID | Scope | UI refs | VIS refs | SRC refs | Target matrix refs | Fidelity semantics | Accepted-exception policy | Status / blocker |
|---|---|---|---|---|---|---|---|---|
| PXR-001 | [Exact surface/region boundary.] | [UI-*] | [VIS-*] | [SRC-*] | [PXT-* refs covering every applicable surface × state × viewport.] | [pixel-exact / pixel-tolerant / perceptual-equivalent / structural-only] | [Stable PEX-* refs, or `None`.] | [specified / BLOCKED: stable ID] |

A `BLOCKED` profile retains its requirement/source/target traceability and
stable blocker. Fidelity semantics or accepted-exception policy that constitute
the unresolved input may remain absent until clarification; they are mandatory
for `specified`.

The profile's target refs are the declared applicable matrix; each ref resolves
to exactly one unique surface × state × viewport row:

| Target ref | Profile ID | Surface / exact region | State and content/data preconditions | Viewport width × height | Device-pixel ratio | Baseline SRC ref + evidence locator | Rendering context | Required visual dimensions | Fidelity mode | Measurable acceptance envelope | Accepted-exception refs | Derivation | Status / blocker |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PXT-001 | PXR-001 | [Surface and included/excluded region.] | [Deterministic state/data.] | [1280 × 720] | [Value or `N/A: immaterial`.] | [Exactly one SRC-* + supplied baseline locator.] | [Fonts/fallbacks, color mode, locale, scale, and material platform/browser constraints.] | [Geometry/spacing/alignment/flow/overflow/clipping; typography; colors/borders/radius/shadows/effects; assets/crop/fitting; layering/stacking/fixed/sticky/occlusion.] | [Allowed fidelity mode.] | [Exact equality boundary, explicit channel/aggregate tolerance, declared perceptual threshold, or structural metric.] | [PEX-* refs or `None`.] | [observed / derived / unresolved / conflicting] | [specified / BLOCKED: stable ID] |

Accepted exceptions do not weaken unlisted regions:

| Exception ref | Profile / target refs | Exact dynamic or divergent region | Reason | Allowed divergence and bound | Unaffected regions remain governed by | SRC / requirement refs |
|---|---|---|---|---|---|---|
| PEX-001 | [PXR/PXT refs] | [Exact region.] | [Why divergence is intentional/dynamic.] | [Explicit permitted difference and threshold.] | [Profile fidelity/envelope.] | [SRC-* + UI/VIS refs] |

`pixel-exact` requires equality inside the declared envelope.
`pixel-tolerant` requires explicit per-pixel/channel or aggregate thresholds.
`perceptual-equivalent` requires a named metric and threshold.
`structural-only` requires geometry/content structure and explicitly excludes
pixel fidelity. Record acceptance envelopes structurally as `kind`, `metric`
when applicable, and `threshold`; for example, a pixel-tolerant target can use
`kind: per-channel, threshold: 1`. A “pixel-perfect” request without a baseline, complete target
matrix, rendering context, measurable envelope, and exception policy remains
`BLOCKED: PIXEL_PROFILE_INCOMPLETE`.

### Cross-Platform Restoration Adaptation

Every applicable cross-platform restoration scope has one policy row:

| UI ref / scope | Source platform | Concrete target platform | Adaptation mode | Preserve dimensions | Adapt dimensions | Required additions | Permitted omissions | Prohibited divergences | Target contexts | SRC refs | Status / blocker |
|---|---|---|---|---|---|---|---|---|---|---|---|
| UI-001 | [HTML/Web.] | [HTML/Web, Android, iOS, iPadOS, or another concrete platform; `Swift` is invalid.] | [framework-equivalent / native-adaptive / brand-preserving-native / visual-equivalent-native] | [Dimension refs.] | [Dimension refs.] | [Dimension refs.] | [Dimension refs.] | [Explicit outcomes.] | [Window/device/input/accessibility/locale contexts.] | [SRC-*] | [specified / BLOCKED: stable ID] |

Target contexts explicitly cover window/device class, input modalities,
accessibility/user scaling, and locale/layout direction, or carry a stable
blocker for the missing category.

Resolve every applicable dimension through exactly one decision:

| Policy / dimension ref | Dimension | Decision | Observable target outcome | Affected UI/VIS refs | SRC refs / target hard-constraint refs | Conflict / rationale | Acceptance condition | Status / blocker |
|---|---|---|---|---|---|---|---|---|
| ADP-001/content | content-and-information-hierarchy | [preserve / adapt / add / omit / clarify / blocked] | [Target outcome.] | [UI/VIS refs] | [SRC-* and/or hard-constraint refs.] | [Conflict and selected precedence, if any.] | [Measurable condition.] | [specified / BLOCKED: stable ID] |

Apply decisions to at least: `content-and-information-hierarchy`,
`task-flow-and-navigation`, `surface-and-component-role`,
`ui-state-and-feedback`, `geometry-and-composition`, `typography`,
`color-effects-and-brand`, `assets-and-variants`,
`input-modality-and-gestures`, `responsive-adaptive-layout`,
`system-ui-and-safe-regions`, `accessibility-and-user-scaling`, and
`localization-and-layout-direction`.

Allowed decisions are `preserve`, `adapt`, `add`, `omit`, `clarify`, and
`blocked`. Mixed behavior is expressed per dimension; `hybrid` is not a mode.
Every `adapt`, `add`, or `omit` cites affected `UI-*`/`VIS-*` plus `SRC-*`
evidence or a target hard constraint.

HTML-to-Android, iOS, and iPadOS use `brand-preserving-native` unless the
policy records an explicit reason for another allowed native mode.

Resolve conflicts in this exact order:

```text
target-platform hard constraints and accessibility requirements
  > explicit product requirements
  > declared adaptation policy and per-dimension decisions
  > source-backed observable UI evidence
  > target-platform defaults
  > implementation preference
```

For example, a source icon may preserve its visible size while an Android or
iOS target adds the larger interaction area required by accessibility. Record
that as `adapt`/`add`; do not silently change source geometry.

`framework-equivalent` preserves declared rendered outcomes for every target
while allowing internal framework, DOM, style organization, and state
management differences. Native targets preserve product/state/brand semantics
and explicitly classify target-required system, accessibility, input, and
adaptive-layout differences. Concrete widgets, classes, code properties,
navigation containers, unit conversions, and resource paths belong to X2-B
UI/UX delivery design, not this specification.

### Security and Privacy

- **SEC-001**: [Observable security/privacy requirement, constraint, or specific N/A reason.]

### Data and Integration Constraints

- **DAT-001**: [Data semantics, lifecycle, failure, compatibility, or specific N/A reason.]

### Dependencies and Boundaries

- **DEP-001**: [External dependency, observable failure behavior, or explicit N/A.]
- **BND-001**: [Owned/non-owned product boundary and observable responsibility.]

## Assumptions

- **ASM-001**: [Documented default that is not presented as confirmed fact.]

## Exclusions

- **EXC-001**: [Explicitly out-of-scope outcome.]

## Semantic ID Lifecycle

Stable refs follow product meaning rather than wording, heading, or line
position. List only changed/non-active identities; an unchanged active ref
remains in its owning section.

| Semantic ref | Lifecycle | Successor/current refs | Concrete reason | Last applicable meaning |
|---|---|---|---|---|
| FR-000 | [REPLACED / RETIRED / NOT_APPLICABLE] | [One or more current refs, or `None`.] | [Split, merge, retirement, or N/A reason.] | [Prior atomic WHAT/WHY meaning.] |

Meaning-preserving wording changes keep the same ID. A split preserves the old
ID with every successor; a merge chooses one current ID and maps the others to
it. Retired or N/A refs remain traceable with a reason. Never silently reuse an
old ID for different semantics.

## Source References

This table is the feature-local Source Reference Contract. A source identity is
opaque provenance. Requirement projection depends on bounded supplied
content/facts and cited evidence locators, never on the locator alone.

| SRC ref | Role | Opaque locator / description | Revision / identity | Bounded feature scope | Supplied content / facts | Projected requirement refs | Status / blocker |
|---|---|---|---|---|---|---|---|
| SRC-001 | requirement-input | [Conversation direction, document, reference, or description.] | [Optional supplied identity or `Not supplied`.] | [Current feature slice.] | [Supplied WHAT/WHY facts, evidence packet refs, or `None`.] | [FR/NFR/UX/UI/VIS/SEC/DAT/DEP/BND/ASM/EXC refs, or `None`.] | [projected / retained / NEEDS CLARIFICATION / BLOCKED with stable reason.] |

Allowed roles are exactly `requirement-input`, `visual-input`,
`technical-evidence`, and `context-only`. `context-only` and
`technical-evidence` do not support normative stable requirement projection.
`visual-input` may project only `UI-*` and `VIS-*`; the other requirement
families require `requirement-input`. A broad source without a
safe feature slice stays blocked or needs clarification; it is not imported in
full. A row with no supplied content/facts stays
`BLOCKED: SRC_EVIDENCE_MISSING` and has no projected requirement refs.

## Unresolved Product Decisions

- **Affected refs: FR-001** — [NEEDS CLARIFICATION: high-impact product
  decision, or `None`. Every item names its current stable semantic refs.]

## Source Evidence Blockers

- **Affected refs: UI-001** — [SRC ref + missing evidence + affected stable
  local refs, or `None`. The matching Source References row remains the
  canonical status.]

## Clarifications

### Session YYYY-MM-DD

- Q: [Question] -> A: [Accepted answer]
