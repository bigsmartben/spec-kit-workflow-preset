---
description: Generate question-form unit tests for requirement writing without evaluating or repairing the specification.
strategy: wrap
---

## Preset Checklist Ownership

`$ARGUMENTS` is an optional focus. Generate either a broad requirements
checklist or a focused domain checklist under `checklists/<focus>.md`.

Checklist reads the current `spec.md` and writes only the selected checklist.
It MUST NOT modify `spec.md`, answer its own questions, ask clarification
questions, invoke Specify/Clarify, aggregate Planning Readiness, compute
PASS/BLOCKED, route blockers, validate IDs/numbering/references, or read Plan and
Tasks as strategy inputs.

Every checklist item is a question-form “unit test for requirements writing”.
Use checklist-local `CHK-*` IDs as formatting, not as a global consistency
claim. Cite a relevant spec section or append `[Gap]` when the expected
requirement text cannot be located.

For broad scope, cover completeness, clarity, consistency, measurability,
scenarios, edge/failure cases, NFRs, security/privacy, data/integration,
dependencies, assumptions, exclusions, and success criteria. For focused scope,
generate domain-aware questions without inventing a second specification
schema.

Source-focused questions may ask whether each `SRC-*` is clearly identified,
feature-scoped, assigned one allowed role, and connected to observable local
requirements or an explicit blocker. Checklist MUST NOT dereference a locator,
acquire missing evidence, validate authenticity/freshness/publication state, or
answer whether an external source is correct.

Examples:

```markdown
- [ ] CHK-UX-001 Are empty, loading, error, and recovery states specified for each critical journey? [Completeness] [Spec § UX]
- [ ] CHK-VIS-001 Is “brand-consistent” grounded in an explicit source or observable criterion? [Clarity] [Gap]
- [ ] CHK-NFR-001 Are user-visible performance expectations measurable for the critical path? [Measurability] [Spec § NFR]
```

Generated items remain unchecked questions. If gaps are exposed, recommend that
the user independently rerun Specify or Clarify with the relevant focus.

{CORE_TEMPLATE}

## Preset Completion Addition

Report the checklist path, focus, and item count. Do not report a readiness
status or mutate the specification.
