# Visual and UI Requirements Writing Checklist: [FEATURE]

- [ ] CHK-UI-001 Are critical surfaces, loading/empty/error/success/disabled/focus states, and recovery feedback specified? [Completeness]
- [ ] CHK-UX-001 Are journeys, navigation, keyboard/accessibility behavior, and responsive expectations observable? [Clarity]
- [ ] CHK-VIS-001 Does every `UI-*`/`VIS-*` row identify its kind, observable statement, `SRC-*`, evidence locator, surface, state, viewport/context, derivation classification, measurable acceptance condition, and status/blocker? [Traceability]
- [ ] CHK-VIS-002 Does each visual source have the `visual-input` role, a bounded feature slice, supplied content/facts, and only `UI-*`/`VIS-*` projections? [Consistency]
- [ ] CHK-UI-002 Are state, viewport, responsive, asset, accessibility, long-copy, and safe-region claims backed by corresponding supplied evidence or an explicit blocker? [Evidence]
- [ ] CHK-UI-003 Are `observed`, `derived`, `assumed`, `unresolved`, and `conflicting` statements distinguishable without presenting an assumption or gap as observed? [Inference]
- [ ] CHK-RST-001 When restoration applies, are content, information structure, appearance, interaction/feedback, UI states, responsive viewports, accessibility, and asset identity/substitution each required, N/A with reason, or blocked? [Coverage]
- [ ] CHK-PXR-001 Does every pixel-restoration profile cover the complete applicable surface × state × viewport matrix with one baseline, rendering context, fidelity mode, measurable envelope, and stable accepted-exception policy per target? [Measurability]
- [ ] CHK-PXR-002 Does each accepted exception have a stable `PEX-*` ref, exact region and bound, while unrelated regions retain the profile fidelity rule? [Containment]
- [ ] CHK-ADP-001 Does each cross-platform scope name source/target platforms, an allowed adaptation mode, target contexts, and one allowed decision for every applicable equivalence dimension? [Completeness]
- [ ] CHK-ADP-002 Do `adapt`, `add`, and `omit` decisions cite affected `UI-*`/`VIS-*` plus `SRC-*` evidence or a target hard constraint, with the declared conflict precedence preserved? [Traceability]
- [ ] CHK-BND-001 Are observable UI outcomes kept in `spec.md` while concrete components, capture/comparison methods, and implementation choices remain downstream? [Ownership]

Use citations or `[Gap]`. Do not dereference or validate external sources,
acquire evidence, answer these questions, or modify `spec.md`.
