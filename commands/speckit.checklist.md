---
description: Build the one canonical requirements.md Gate from stable Spec semantic refs.
strategy: wrap
---

## Preset Checklist Ownership

This wrapper keeps Core user input, official read-only feature/path resolution,
before/after hooks, and completion behavior. It intentionally narrows Core's
write target:

```text
any $ARGUMENTS focus
  -> exactly FEATURE_DIR/checklists/requirements.md
  -> no other checklist output
```

`$ARGUMENTS` changes only concern priority and checking depth inside that file.
It never selects a filename or creates an advisory/focus/Domain checklist.
Within the embedded Core template, instructions to write
`checklists/<domain>.md`, `checklists/<focus>.md`, advisory files, or multiple
Planning Readiness files are superseded by this single-output contract. If the
installed Core cannot honor that override while retaining its lifecycle, stop
with `REQUIREMENT_GATE_CORE_WRAPPER_INCOMPATIBLE`; do not generate extra files
and ignore them afterward.

Checklist reads current `spec.md` and writes only the canonical Requirement
Gate. It MUST NOT modify `spec.md`, accept product decisions, ask clarification
questions, call Clarify or Plan, or read Plan/Tasks as strategy inputs.

## Canonical Execution

1. Use Core's official path-only mechanism to resolve `FEATURE_DIR` and
   `FEATURE_SPEC`; require the current Spec and stop if Plan already exists.
2. Compute SHA-256 over the exact `spec.md` bytes as
   `sha256:<lowercase-hex>`.
3. Inventory every active, replaced, retired, or explicitly N/A stable Spec
   semantic ref. Product semantics come only from `spec.md`.
4. Load `templates/requirements/*.md` as rule fragments for the six logical
   Gates: `requirements`, `behavior`, `ux`, `security`, `nfr`, and `visual`.
   Fragments never become runtime files.
5. Rebuild template-owned content in the one canonical file by stable Spec ref,
   Check ID, Blocker ID, and lifecycle relation. Preserve clearly delimited
   manual notes byte-for-byte; notes never affect a Check, Gate, or readiness
   result.
6. Derive Six-Gate Summary from Check/Blocker records, then derive Planning
   Readiness from the current Revision, all six Gate results, and the current
   open Blocker inventory.
7. Atomically replace only
   `FEATURE_DIR/checklists/requirements.md`.

Regeneration is idempotent recomputation, not append. Remove duplicate/stale
template-owned records. A wording-only Spec change preserves IDs. Spec or
Blocker split/merge/retirement follows explicit replacement relations; never
silently reassign an old ID to a different meaning.

## Canonical Document Contract

The physical document has exactly this owner structure:

```text
File Metadata
  Contract: speckit.requirement-gate.v1
  Stage: requirements
  Spec Revision: sha256:<current exact Spec bytes>
  Planning Readiness: PASS | BLOCKED
Semantic Requirement Groups
  <stable Spec semantic ref>
    cross-Gate Check records
    shared root-cause Blocker records
Six-Gate Summary
Planning Readiness
```

Each Check record contains:

```text
Check ID | template Rule key | Gate | atomic concern | Spec refs
| PASS + current spec.md evidence as spec.md#<Spec semantic ref>
  OR BLOCKED + exactly one shared Blocker ref
```

The Rule key is the stable origin from `templates/requirements/*.md`; it makes
fragment-to-Check mapping auditable without copying fragment text into the
Summary. Every PASS evidence ref resolves each Spec ref owned by the Check.

Each Blocker record contains:

```text
Stable ID | primary Spec ref | minimal semantic root cause
| semantic key | affected Check IDs | class | owner/route
| OPEN / RESOLVED / RETIRED / SUPERSEDED | replacement refs
```

Never derive one `BLK-*` mechanically from each `CHK-*`. One root cause may be
referenced by Requirements, Behavior, and Security Checks. Two different gaps
under the same Spec ref remain two Blockers, and similarly named gaps under
different Spec refs remain separate. `product-decision`, `source-evidence`,
`template-structure`, and `legacy-layout` classes never silently convert or
merge.

The six Gate Summary rows contain only:

```text
Gate | Applicability | current Spec-backed N/A reason naming a stable Spec ref
| Status | Check refs/count | open Blocker refs/count
```

Check questions and product content appear only in Semantic Requirement Groups,
never again in the summary. All six rows exist exactly once even when focus was
supplied. `NOT_APPLICABLE` requires a concrete current Spec reason; absence is
not N/A.

Planning Readiness is `PASS` only when the file Revision is current, all
references resolve uniquely, all applicable Gates are `PASS`, every N/A has a
current reason, every passing Check has current Spec evidence, and the open
Blocker inventory is empty. It is stored once as strictly derived state. Do not
create `planning-readiness.md`.

“Zero Blocker” means zero `OPEN` current root causes. `RESOLVED`, `RETIRED`, and
`SUPERSEDED` rows are lifecycle history, not current Blocker inventory, and
cannot be referenced by a current BLOCKED Check.

## Legacy Boundary

Preserve existing advisory checklists and the obsolete six-file Domain layout
byte-for-byte. Do not read, merge, delete, rewrite, or import answers from them.
Report obsolete `behavior.md`, `ux.md`, `security.md`, `nfr.md`, or `visual.md`
as `REQUIREMENT_GATE_LEGACY_LAYOUT`; the new canonical
`requirements.md` remains the only authority.

External locators are opaque. Checklist MUST NOT dereference a locator or validate external
meaning. A source-evidence gap preserves its class and original route.

{CORE_TEMPLATE}

## Authoritative Core Conflict Resolution

The Preset Checklist Ownership and Canonical Execution sections are the
effective write policy after Core merge. Execute Core hooks, input handling,
path resolution, and completion around that policy, but do not execute any
embedded Core step that creates Domain/advisory/focus checklist files or
aggregates multiple runtime files.

## Preset Completion Addition

Report the canonical path, focus, semantic-group/Check/Blocker counts, six Gate
results, Spec Revision, Planning Readiness, preserved legacy paths, and any
wrapper compatibility blocker. Do not claim product completeness or modify the
Spec.
