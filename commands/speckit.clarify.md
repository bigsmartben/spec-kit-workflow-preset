---
description: Resolve shared product root causes and synchronize spec.md with the one Requirement Gate.
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
`/speckit.specify`; do not create a specification here.

## Two-File Ownership

Clarify may update only:

1. `FEATURE_SPEC`: accepted product decisions, their stable semantic refs, and
   Clarification history;
2. the existing `FEATURE_DIR/checklists/requirements.md`: current Check
   evaluations/evidence, shared Blocker lifecycle, Spec Revision, Six-Gate
   Summary, and Planning Readiness.

The Gate must identify `Stage: requirements` and
`Contract: speckit.requirement-gate.v1`. Clarify does not create a missing Gate
or repair malformed Canonical Layout. Before any Gate update, validate exact
lowercase SHA-256 metadata, unique/resolvable Semantic Group, Rule key, Check,
Spec and Blocker refs, shared-Blocker affected refs, and the six unique Summary
rows. A structural failure preserves the Gate byte-for-byte and routes to
Checklist. It never writes Plan, Architecture,
contracts, Test artifacts, Tasks, `planning-readiness.md`, advisory files, or
obsolete Domain checklist files.

`spec.md` remains the only product-requirement truth. The Gate stores questions,
references, evaluations, evidence, and root-cause Blockers, never accepted
answer prose as a second copy.

External source-evidence Blockers stay outside the product-decision loop.
Clarify does not dereference a locator, acquire evidence, change the Blocker
class/owner, or require external
write-back or synchronization.

## Shared-Root Ambiguity Map

Read `spec.md` and only the canonical `requirements.md`. Inventory Semantic
Requirement Groups once. Build one candidate per OPEN
`class: product-decision` Blocker ID:

```text
Blocker ID | primary Spec ref | minimal missing/conflicting meaning
| all affected Check IDs/Gates | impact × uncertainty
```

Three Gate Checks referencing one Blocker produce one question. Two distinct
Blockers under the same Spec ref remain two candidates. Similar topics under
different Spec refs do not merge automatically. Source-evidence,
template-structure, malformed-Gate, and legacy-layout Blockers retain their
existing routes and are not product questions.

Prioritize by `impact × uncertainty`; do not use a UI-first fixed order.
Exclude already answered decisions, low-impact style preferences, and
implementation choices owned by Plan.

## Question Loop

Ask at most five high-impact questions, exactly one at a time. Never reveal the
future queue. Use either 2–5 mutually exclusive options with
`**Recommended:** Option X - ...`, or a short answer constrained to `<=5 words`
with `**Suggested:** ...`. Accept `yes`, `recommended`, or `suggested` for the
displayed recommendation.

For each accepted answer:

1. ensure `## Clarifications` and `### Session YYYY-MM-DD` exist;
2. append exactly one `- Q: ... -> A: ...` entry;
3. update the existing stable Spec semantic ref that owns the decision;
4. preserve that ID for meaning-preserving wording changes; when meaning
   splits, merges, retires, or becomes N/A, record explicit successor refs and
   reasons rather than silently renumbering;
5. replace the ambiguity instead of duplicating it, preserve the originating `SRC-*` provenance,
   validate the Spec locally, and atomically save `spec.md`;
6. compute SHA-256 over the new exact Spec bytes;
7. re-evaluate every affected Check in the semantic group against current
   Spec evidence; one answer may pass Checks in several Gates;
8. update shared Blocker affected refs/status, then strictly rederive all six
   Gate Summary rows and Planning Readiness;
9. atomically save only the canonical `requirements.md`.

If the second write fails, report the Spec write as completed and the Gate as
stale/unsynchronized. Never report Planning Readiness PASS. The next Clarify
run recovers deterministically from the current Spec plus existing Gate; do not
create a transaction file, journal, manifest, or third coordination artifact.

## Local Validation After Every Spec Write

Check:

- one history bullet per accepted answer and no more than five;
- the accepted answer appears once in its owning stable semantic ref;
- the targeted ambiguity is removed without contradiction or terminology drift;
- ID lifecycle and replacement refs remain traceable;
- Markdown structure and template-owned headings remain valid;
- no product-requirement artifact other than `spec.md` changed.

These are local write-safety checks, not cross-command consistency analysis.

## Mandatory Closeout Reconciliation

Run this closeout after partial clarification, full clarification, and zero
questions:

1. compute the current exact Spec SHA-256;
2. require the one existing canonical `requirements.md`;
3. if its Canonical Layout is malformed, preserve it unchanged and route
   `REQUIREMENT_GATE_MALFORMED` to Checklist;
4. if structurally valid, re-evaluate every Semantic Requirement Group—not
   only groups asked about—against the current Spec;
5. require every PASS evidence ref to resolve as
   `spec.md#<Spec semantic ref>` against the current Spec; refresh every PASS
   evidence ref, every OPEN/RESOLVED shared Blocker and its
   affected Check refs, the file Revision, all six derived Summary rows, and
   derived Planning Readiness;
6. preserve unresolved groups after the five-question limit and preserve
   source-evidence Blockers with their class and owner;
7. ignore every other checklist path byte-for-byte.

Zero questions never means zero work: a stale Revision, an interrupted prior
sync, or independently updated valid Spec still requires full reconciliation.
Do not rerun Checklist merely to refresh evaluation state or Revision.

If re-evaluation finds a Check with neither current Spec evidence nor an
existing root-cause Blocker, do not invent a Blocker or publish a malformed
current Gate. Preserve the existing Gate as stale, report
`REQUIREMENT_GATE_RECONCILIATION_BLOCKER_REQUIRED`, and route the missing
Checklist-owned question structure to Checklist.

## Missing, Malformed, And Legacy Inputs

| Input | Action |
|---|---|
| canonical `requirements.md` missing | stop Gate work; route to Checklist; do not create it |
| malformed Canonical Layout | preserve unchanged; route to Checklist |
| stale but structurally valid Revision | perform full closeout reconciliation |
| advisory/focus checklist | ignore and preserve byte-for-byte |
| obsolete six-file Domain layout | ignore and preserve; report `REQUIREMENT_GATE_LEGACY_LAYOUT` |

Never import product answers from a legacy or advisory checklist.

## Completion Report

Report question groups, decisions, updated Spec refs, affected Gates/Checks,
remaining shared Blockers by owner, current Revision, Planning Readiness,
two-file synchronization status, ignored legacy paths, and hook status.
