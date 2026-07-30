# UI/UX Delivery Design: [FEATURE]

**Consumed Spec SHA-256**: [sha256:<64 lowercase hexadecimal characters>]

The digest is local `spec.md` freshness evidence only. It does not certify an
external source, locator, revision, or baseline.

## Spec UI Input Inventory

Inventory every applicable Spec-owned UI contract ref exactly once. This table
contains refs and statuses only; it does not copy requirement statements,
baseline locators, rendering contexts, fidelity modes, acceptance envelopes,
exception bounds, or adaptation decisions.

| Spec ref | Contract class | Spec status | X2-B applicability | X2-B mapping ref or propagated blocker |
|---|---|---|---|---|
| UI-001 | UI | specified / BLOCKED | Required / Blocked | X2B-UI-001 / stable upstream blocker |
| RST-001/content | RST | specified / BLOCKED | Required / Blocked | X2B-UI-001 / stable upstream blocker |
| PXT-001 | PXT | specified / BLOCKED | Required / Blocked | X2B-PX-001 / stable upstream blocker |
| ADP-001/accessibility-and-user-scaling | ADP | specified / BLOCKED | Required / Blocked | X2B-ADP-001 / stable upstream blocker |

Allowed contract classes are exactly `UI`, `VIS`, `RST`, `PXR`, `PXT`, `PEX`,
and `ADP`. Blocked Spec applicability remains blocked with the same stable
blocker; it is never relabeled `N/A` or replaced by a Plan decision.

## General UI Delivery Mappings

| X2B mapping ref | UI/VIS/RST refs | SRC refs | Surface / region binding | Component responsibility / composition / state ownership | Navigation / input / responsive / accessibility delivery | DEC-UI refs | UIF / interface / asset refs | Status / blocker |
|---|---|---|---|---|---|---|---|---|
| X2B-UI-001 | [UI/VIS/RST refs] | [SRC refs] | [Exact delivery binding.] | [Plan-owned component and state delivery design.] | [Plan-owned navigation/input/layout/accessibility delivery.] | [DEC-UI refs] | [Resolved refs or explicit N/A.] | [READY / BLOCKED: stable ID] |

## Pixel-Target Delivery Mappings

| X2B mapping ref | PXR ref | PXT ref | UI/VIS refs | SRC refs | Exact target-region binding | Component / style / token / asset / layering / overflow delivery mapping | PEX refs | Local delivery/review method | DEC-UI / UIF / interface / asset refs | Status / blocker |
|---|---|---|---|---|---|---|---|---|---|---|
| X2B-PX-001 | [PXR-*] | [PXT-*] | [UI/VIS refs] | [SRC refs] | [Exact component/region ownership.] | [Plan-owned delivery design.] | [PEX refs or None.] | [Local X2-B method.] | [Resolved refs.] | [READY / BLOCKED: stable ID] |

The pixel row references its Spec-owned baseline, target state/viewport,
rendering context, fidelity mode, acceptance envelope, and exception bounds.
It must not repeat or weaken those values.

## Platform-Adaptation Delivery Mappings

| X2B mapping ref | ADP policy/dimension ref | UI/VIS refs | SRC refs | Target-context binding | Target component / navigation / input / layout / accessibility delivery design | DEC-UI refs | UIF / interface / asset refs | Status / blocker |
|---|---|---|---|---|---|---|---|---|---|
| X2B-ADP-001 | [ADP policy/dimension ref] | [UI/VIS refs] | [SRC refs] | [Window/device/input/accessibility/locale context binding.] | [Plan-owned target delivery design.] | [DEC-UI refs] | [Resolved refs.] | [READY / BLOCKED: stable ID] |

The mapping implements the referenced Spec decision; it does not copy,
reinterpret, or replace `preserve`, `adapt`, `add`, `omit`, `clarify`, or
`blocked`.

## UIF Contracts

| X2B mapping refs | SRC + UI/VIS refs | UIF path | Start view / events / routes | Observable states/feedback | API/interface refs | Blocker |
|---|---|---|---|---|---|---|
| [X2B refs] | [SRC + UI/VIS refs] | [contracts/uif/*.expected.json] | [UIF delivery path.] | [Referenced observable outcomes.] | [Resolved refs.] | [None / stable ID] |

UIF references interface schemas; it does not duplicate API payloads.

## X4 UI/UX Delivery Readiness

Every required `X2B-*` mapping has exactly one closed row.

| X2B mapping ref | Mapping class | Required Spec refs | Resolved DEC-UI / UIF / interface / asset / exception refs | Status | Local evidence | Blocker |
|---|---|---|---|---|---|---|
| X2B-UI-001 | general-ui | [refs] | [resolved refs] | READY / BLOCKED | [Local delivery evidence.] | [None / stable ID] |

`X2B_UIUX_READY` is READY only when the recorded Spec digest is current, the
inventory and delivery mappings are complete and unique, every internal ref
resolves, every readiness row is closed, no Spec-owned value is duplicated,
and no X2-B/reconciliation finding remains.

Pixel delivery/review is owned here, never by Test Conditions. This artifact
contains no BDD strategy, general test levels, task IDs, implementation
results, pixel comparison execution, screenshot capture/diff, visual
acceptance, or final visual review. Source locators are provenance only: X2-B
does not dereference, execute, inspect, compare against, or certify an external
source, its fidelity, freshness, revision, availability, or publication state.
