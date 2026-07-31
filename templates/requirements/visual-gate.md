# Visual and UI Gate Rule Fragment

This fragment contributes Visual/UX/Requirements concerns to Semantic
Requirement Groups in the one canonical Gate. It is never emitted as
`checklists/visual.md`.

| Rule key | Gate | Atomic concern / question pattern |
|---|---|---|
| UI-STATES | ux | Are critical surfaces, loading/empty/error/success/disabled/focus states, and recovery feedback specified? |
| UX-JOURNEY | ux | Are journeys, navigation, keyboard/accessibility behavior, and responsive outcomes observable? |
| VIS-TRACE | visual | Does every `UI-*`/`VIS-*` row identify kind, observable statement, `SRC-*`, evidence locator, surface, state, viewport/context, derivation, measurable acceptance, and status/blocker? |
| VIS-SOURCE | visual | Does visual input have the right role, bounded feature slice, supplied facts, and only allowed projections? |
| UI-EVIDENCE | visual | Are state, viewport, responsive, asset, accessibility, long-copy, and safe-region claims supported or blocked? |
| UI-INFERENCE | visual | Are observed, derived, assumed, unresolved, and conflicting statements distinguishable? |
| RST-COVERAGE | visual | When restoration applies, are all required equivalence dimensions classified? |
| PXR-PROFILE | visual | Does each pixel profile cover its target matrix, baseline, rendering context, fidelity, envelope, and exception policy? |
| PXR-EXCEPTION | visual | Is every accepted exception bounded while unrelated regions retain the profile rule? |
| ADP-COVERAGE | visual | Does cross-platform scope identify platforms, adaptation mode, target contexts, and every applicable dimension? |
| ADP-TRACE | visual | Do adapt/add/omit decisions cite affected UI/VIS refs and evidence or hard constraints? |
| UI-BOUNDARY | requirements | Are observable outcomes kept in `spec.md` while components and delivery methods remain downstream? |

Examples of generated Check families include `CHK-UI-003`, `CHK-RST-001`,
`CHK-PXR-001`, `CHK-PXR-002`, `CHK-ADP-001`, `CHK-ADP-002`, and
`CHK-BND-001`; final IDs also bind the owning Spec semantic ref. Do not acquire
external evidence or answer product questions while assembling these rules.
