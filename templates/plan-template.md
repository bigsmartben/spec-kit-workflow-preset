{CORE_TEMPLATE}

## X0 Feature Plan Control

### Feature Goal And Exclusions

- **Goal**: [Feature outcome.]
- **Exclusions**: [Explicit non-goals.]
- **Planned M + U**: [Module/capability + design object.]
- **Repository Topology**: [Core-required source/test directory topology only.]

### Upstream References

- **Spec**: [path + revision]
- **Spec Source Contract**: [Applicable local SRC refs and blockers; locators remain opaque.]
- **Architecture Revision**: [revision]
- **Applicable Architecture IDs**: [BND/CON/DEC/CST/GAP refs]

### Active Lane Matrix

| Lane | Applicability | Source refs | Declared outputs | Dependencies | Internal gate |
|---|---|---|---|---|---|
| X2-A Domain/Object/Interface | Required / N/A: reason / Blocked: ID | [refs] | [paths] | [lane refs] | X2A_DESIGN_READY |
| X2-B UI/UX Delivery | Required / N/A: reason / Blocked: ID | [SRC + UI/VIS refs] | [paths] | [lane refs] | X2B_UIUX_READY |
| X2-C Test & Acceptance | Required / N/A: reason / Blocked: ID | [refs] | [paths] | [lane refs] | X2C_TEST_DESIGN_READY |

### Cross-Lane Dependency Register

| ID | Producer | Consumer | Required contract/decision | Status/blocker |
|---|---|---|---|---|

### Internal Gate Summary

| Gate | READY / BLOCKED / N/A | Evidence / blocker |
|---|---|---|
| X0_CONTROL_READY | [status] | [ref] |
| X1_DECISIONS_READY | [status] | [ref] |
| X2A_DESIGN_READY | [status] | [ref] |
| X2B_UIUX_READY | [status] | [ref] |
| X2C_TEST_DESIGN_READY | [status] | [ref] |
| X2_RECONCILIATION_READY | [status] | [inventory/findings/blocker refs] |
| X3_VALIDATION_PATHS_READY | [status] | [ref] |

Each status is derived from the cited evidence. File existence alone is not
evidence. A missing or invalid evidence cell means the Gate is not ready.

### X2 Cross-Lane Reconciliation

| Ref / mapping | Producer / owner | Consumers | Resolved target | Drift / ownership finding | Status / blocker |
|---|---|---|---|---|---|
| [DEC/UIF/TC/VAL/design ref] | [lane + artifact] | [lane artifacts] | [stable ID/path] | [none or finding] | [READY/BLOCKED: ID] |

### Resume Checkpoint

- **First unclosed/affected Gate**: [Gate ID]
- **Verified artifacts preserved**: [paths + evidence refs]
- **Changed inputs/refs**: [refs or none]
- **Downstream Gates/reconciliation to rerun**: [Gate IDs]

## Artifact Navigation

- Shared decisions: `./research.md`
- Domain model: `./data-model.md`
- Object responsibilities: `./class-diagram.md`
- Interface contracts: `./contracts/`
- Cross-boundary sequences: `./contracts/sequences.md`
- UI/UX delivery design: `./ui-ux-design.md`
- UI interaction contracts: `./contracts/uif/`
- Test Conditions: `./contracts/test/test-conditions.json`
- Optional technique contracts: `./contracts/bdd/`, `./contracts/behavior/`
- Validation paths: `./quickstart.md`
- Test readiness: `./test-readiness.md`

Remove links for explicitly N/A artifacts; do not leave broken placeholders.

## X4 Design Object Derivation Index

| Source refs | Architecture refs | M | U / design object | Data-model ref | Class ref | Interface/sequence refs | Blocker |
|---|---|---|---|---|---|---|---|

No task IDs, exact per-task paths, or implementation order belong here.

## X4 Closeout Summary

- **Design Readiness**: [READY/BLOCKED + index link]
- **UI/UX Delivery Readiness**: [READY/BLOCKED/N/A + link/reason]
- **Test Readiness**: [READY/BLOCKED/N/A + link/reason]
- **X3 Validation Paths**: [READY/BLOCKED/N/A]
- **Blockers by lane**: [IDs]
- **PLAN_OUTPUT_READY**: READY | BLOCKED

`PLAN_OUTPUT_READY` is derived from the Internal Gate Summary, reconciliation,
conditional artifact decisions, readiness products, resolved refs, and
placeholders. Do not mark it READY from file presence or prose summary alone.
