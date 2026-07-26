# Behavior Testability / Task Readiness

**Stage**: plan
**Behavior Testability Status**: READY | BLOCKED
**Spec Revision**: sha256:[SPEC_CONTENT_HASH]
**Plan Revision**: sha256:[PLAN_CONTENT_HASH]

## Input Revisions

| Input | Revision / Reference |
|---|---|
| `spec.md` | sha256:[SPEC_CONTENT_HASH] |
| `plan.md` | sha256:[PLAN_CONTENT_HASH] |
| Requirement gates | [paths and revisions] |
| Behavior drafts | [paths] |
| Formal contracts | [paths] |
| `research.md` | [reference] |
| `quickstart.md` | [reference] |

## Task Derivation Matrix

One row per Required Case. Every row must either map to a complete task
derivation path or name a blocker.

| Case ID | Scenario ID | BDD Ref | UIF Ref | Fixture Ref | Assertion Ref | Validation Level | Research Ref | Quickstart Path | Visual/NFR Refs | Blocker ID |
|---|---|---|---|---|---|---|---|---|---|---|
| CASE-001 | SCN-001 | contracts/bdd/example.feature | N/A: non-UI behavior | FIX-001 | AST-001 | unit | research.md#decision | quickstart.md#path | checklists/nfr.md#NFR-001 | none |

Validation Level is one of `unit`, `contract`, `integration`, or `e2e`.
UIF may be `N/A` only with a reason. NFR or visual references may point to an
explicit Not Applicable gate result.

## Blocking Items

- none

## Task Readiness Decision

- READY only when every Required Case has a Scenario ID, formal BDD/behavior
  contract, fixture, assertion, validation decision, and quickstart path, plus
  UIF and Visual/NFR references when applicable.
- BLOCKED when any Required Case lacks that mapping or any referenced planning
  input is missing or stale.

<!-- Recompute generated sections from stable Case IDs. Do not copy the legacy
     checklists/behavior-testability.md file or retain resolved blockers. -->
