# Figma Evidence Packet Input Design

Date: 2026-06-16

## Objective

Allow users to pass a Figma URL directly to `/speckit.specify` while keeping
`workflow-preset` within preset boundaries.

The runtime agent may use Figma MCP when available. The preset does not install,
authenticate, call, wrap, or dispatch Figma MCP. The preset only defines the
evidence format that a runtime agent must produce before `/speckit.specify`
turns design evidence into `spec.md` requirements.

## Boundary

The intended boundary is:

```text
Runtime agent calls Figma MCP.
Preset defines the evidence format.
/speckit.specify consumes evidence and writes spec.md.
```

This keeps external integration outside the preset while still supporting the
user workflow:

```text
/speckit.specify <Figma URL>
-> runtime agent extracts Figma design evidence when Figma MCP is available
-> runtime agent prepares a Figma Evidence Packet
-> /speckit.specify writes spec.md from that packet
-> /speckit.clarify resolves non-Figma requirements
-> /speckit.checklist gates requirement quality
-> /speckit.plan
```

## Artifact Design

Add one packaged Markdown template:

```text
templates/figma-evidence-packet-template.md
```

The first version should be Markdown, not JSON. The packet is an input evidence
contract for an LLM command, not a machine-executed downstream contract. Markdown
also avoids introducing schema and validator ownership before there is a proven
need for machine-readable packet processing.

The template must include these sections:

- Figma Source
- Extraction Context
- Observed from Figma
- Inferred from Structure
- Missing / Needs Clarification
- Out of Scope
- Endpoint / Client Requirements
- Component Mapping
- Acceptance Criteria
- Open Questions

Each extracted fact should preserve traceability through frame, node, component,
or screenshot references where the runtime agent can provide them.

## Command Changes

Update `commands/speckit.specify.md` with a Figma URL input policy:

- If the raw input is a Figma URL and the runtime agent has Figma MCP access,
  first collect design facts and normalize them into the Figma Evidence Packet
  format.
- If the runtime agent lacks Figma MCP access, write an explicit
  `[NEEDS CLARIFICATION]` item requesting either a filled packet, screenshots,
  or design facts.
- Only use reliable Figma evidence as observed requirements.
- Label structural interpretations as inferred.
- Mark business semantics, permissions, validation rules, dynamic UI states,
  responsive behavior, error handling, data semantics, and analytics as
  `[NEEDS CLARIFICATION]` unless the packet provides explicit evidence.
- Continue to write only `spec.md`.

Do not add planning outputs, implementation outputs, runners, hooks, scripts, or
external integration logic to `/speckit.specify`.

## Checklist Changes

Update `commands/speckit.checklist.md` so the existing requirement-quality gate
can check visual fidelity readiness when `spec.md` contains Figma-derived
requirements.

The checklist remains a requirements checklist. It must not become an
implementation test checklist. It should check whether the specification defines:

- visual layout, spacing, typography, colors, effects, assets, and clipping;
- component mappings and variant coverage;
- default, hover, focus, active, disabled, loading, empty, and error states;
- breakpoints, reflow, scrolling, minimum widths, and safe areas;
- copy, icons, images, fonts, numeric formats, and placeholders;
- keyboard, focus, semantics, contrast, ARIA, and form error requirements;
- Figma source links, node IDs, screenshots, mapping evidence, and exception
  rules.

Blockers should prevent entry to planning. Minor gaps may be recorded as
follow-up improvements when they do not affect implementation or validation.

## Manifest And Tests

Update `preset.yml` to package the new Markdown template.

Update `tests/test_preset_contract.py` to verify:

- the manifest includes the Figma Evidence Packet template;
- the template file exists and contains the required evidence sections;
- `/speckit.specify` defines the Figma URL and packet policy while preserving
  spec-only ownership;
- `/speckit.checklist` includes visual fidelity readiness checks as requirement
  quality checks;
- no scripts, workflow runners, or external integration adapters are added.

The existing focused verification command remains:

```bash
python3 -m unittest tests/test_preset_contract.py
```

## Documentation Changes

Update public documentation to explain that direct Figma URL input is supported
only when the runtime agent has Figma MCP access. The preset defines the
required packet shape and command behavior, but does not provide the Figma MCP
runtime integration.

Update extension governance to make the distinction explicit:

- packaged evidence templates are allowed preset artifacts;
- Figma MCP execution, hooks, adapter scripts, and authentication are external
  integration concerns and remain outside this preset.

## Non-Goals

- Do not add Python orchestration.
- Do not add workflow shell dispatch.
- Do not add Figma MCP adapter scripts.
- Do not add hook execution.
- Do not move product requirements out of `spec.md`.
- Do not create implementation tests from `/speckit.checklist`.
- Do not introduce JSON schema or validators for the packet in the first
  version.

## Risks

The main risk is that users interpret a Figma URL as a complete product
requirement. The packet and command policy must make the evidence boundary
visible: Figma can provide design facts, but business semantics and endpoint
behavior still require product clarification unless explicitly provided.

Another risk is weakening existing preset stage ownership. Tests should assert
that `/speckit.specify` still writes only `spec.md` and that checklist changes
remain requirement-quality gates.
