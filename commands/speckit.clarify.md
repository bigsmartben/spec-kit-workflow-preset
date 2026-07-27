---
description: Resolve high-impact product ambiguity and record accepted decisions only in spec.md.
strategy: replace
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --paths-only
  ps: scripts/powershell/check-prerequisites.ps1 -Json -PathsOnly
---

## User Input

```text
$ARGUMENTS
```

Use optional arguments only as focus for this clarification run.

## Extension Hooks And Path Resolution

Run enabled, unconditional `hooks.before_clarify` before analysis and
`hooks.after_clarify` after successful writes. Invoke and await mandatory hooks.

Run `{SCRIPT}` once from the repository root and read `FEATURE_DIR` and
`FEATURE_SPEC`. If resolution fails or `spec.md` is missing, stop and recommend
running `/speckit.specify`; do not create a specification here.

## Ownership

Read and write only `FEATURE_SPEC` aside from official path/hook mechanics.
Do not read blocked checklists as a queue. Do not create, recompute, answer,
toggle, or mutate checklist files. Do not aggregate readiness, revise gates,
validate IDs/numbering/references, create external-source artifacts, or modify Plan,
Tasks, Architecture, contracts, or tests.

External source-evidence blockers remain in their canonical `SRC-*` rows and
stay outside the product-decision question loop. Do not dereference a locator,
acquire missing evidence, validate external state, or require external
write-back or synchronization.

## Cross-Domain Ambiguity Map

Build an in-memory map across:

- scope and observable behavior;
- roles, permissions, security/privacy, and compliance;
- domain/data semantics and lifecycle;
- UX journeys, UI states, accessibility, and failure recovery;
- NFRs and measurable completion signals;
- integrations, dependency failures, boundaries, constraints, and terminology.

Prioritize candidates by `impact × uncertainty`. Do not use a UI-first fixed
order. Exclude decisions already answered, low-impact stylistic preferences,
source-evidence gaps, and implementation choices better owned by Plan.

## Question Loop

Ask at most five high-impact questions, exactly one at a time. Never reveal the
future queue. Use either 2–5 mutually exclusive options with
`**Recommended:** Option X - ...`, or a short answer constrained to `<=5 words`
with `**Suggested:** ...`. Accept `yes`, `recommended`, or `suggested` for the
displayed recommendation.

After each accepted answer:

1. ensure `## Clarifications` and `### Session YYYY-MM-DD` exist;
2. append exactly one `- Q: ... -> A: ...` entry;
3. update the existing canonical section that owns the decision;
4. replace the ambiguous statement rather than duplicating it;
5. preserve the originating `SRC-*` provenance and clarification history while
   making the accepted local decision current;
6. atomically save `spec.md`.

The accepted answer is owned locally by `spec.md` and may supersede an
ambiguous projected statement. Do not present the superseded statement as the
current decision, erase its provenance, or require a change to the external
source.

## Local Validation After Every Write

Check only:

- one history bullet per accepted answer and no more than five;
- the targeted ambiguity is removed;
- the accepted answer appears once in its owning section;
- no contradiction or terminology drift was introduced;
- Markdown structure and template-owned headings remain valid;
- no artifact other than `spec.md` was changed.

These are local write-safety checks, not requirement completeness or
cross-artifact validation.

## Completion Report

Report questions asked, decisions recorded, sections updated, remaining product
ambiguities, source-evidence blockers, and hook status. Recommend independently
rerunning Checklist when requirement-writing quality should be reassessed.
