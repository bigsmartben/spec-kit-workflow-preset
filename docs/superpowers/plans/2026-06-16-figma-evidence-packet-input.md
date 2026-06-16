# Figma Evidence Packet Input Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Support direct Figma URL input to `/speckit.specify` by defining a preset-packaged Figma Evidence Packet format and command policies without making the preset execute Figma MCP.

**Architecture:** The runtime agent remains responsible for calling Figma MCP when available. The preset adds a Markdown evidence template, teaches `/speckit.specify` how to consume Figma-derived evidence while still writing only `spec.md`, and extends the existing checklist gate with visual-fidelity requirement readiness checks. Contract tests protect the manifest, template shape, command ownership, documentation, and governance boundary.

**Tech Stack:** Spec Kit preset YAML, Markdown command/template files, Python `unittest` contract tests, PyYAML.

---

## File Structure

- Modify `tests/test_preset_contract.py`: add failing contract coverage for the manifest entry, packet template, command policy, checklist readiness wording, README wording, and governance wording.
- Create `templates/figma-evidence-packet-template.md`: stable Markdown input evidence template for Figma-derived design facts.
- Modify `preset.yml`: package the new template as a preset template entry.
- Modify `commands/speckit.specify.md`: add a Figma URL input policy that requires packet normalization before spec writing.
- Modify `commands/speckit.checklist.md`: add visual fidelity readiness as requirement-quality checks.
- Modify `templates/behavior/behavior-testability-checklist.md`: add optional visual fidelity readiness checklist sections for Figma-derived requirements.
- Modify `README.md`: document direct Figma URL input boundary and usage.
- Modify `docs/extension-governance.md`: clarify evidence templates are preset artifacts while Figma MCP execution remains external integration.
- Modify `CHANGELOG.md`: add an Unreleased entry.

## Task 1: Add Failing Contract Tests

**Files:**
- Modify: `tests/test_preset_contract.py`
- Test: `tests/test_preset_contract.py`

- [ ] **Step 1: Add the packet template path constant**

Add this constant after `PLAN_TEMPLATE_PATH`:

```python
FIGMA_EVIDENCE_PACKET_TEMPLATE_PATH = (
    REPO_ROOT / "templates" / "figma-evidence-packet-template.md"
)
```

- [ ] **Step 2: Extend the manifest contract test**

In `test_preset_manifest_contract`, change the provide count from `30` to `31`.

Add this block after the `constitution_template` assertions:

```python
        figma_packet_template = entries["figma-evidence-packet-template"]
        self.assertEqual("template", figma_packet_template["type"])
        self.assertEqual(
            "templates/figma-evidence-packet-template.md",
            figma_packet_template["file"],
        )
        self.assertEqual(
            "figma-evidence-packet-template",
            figma_packet_template["replaces"],
        )
        self.assertEqual("replace", figma_packet_template["strategy"])
        self.assertIn("Figma Evidence Packet", figma_packet_template["description"])
```

- [ ] **Step 3: Add a template contract test**

Add this test method near `test_behavior_first_templates_exist_and_are_decoupled`:

```python
    def test_figma_evidence_packet_template_contract(self) -> None:
        self.assertTrue(FIGMA_EVIDENCE_PACKET_TEMPLATE_PATH.exists())
        document = FIGMA_EVIDENCE_PACKET_TEMPLATE_PATH.read_text(encoding="utf-8")

        required_terms = [
            "Figma Evidence Packet",
            "Figma Source",
            "Extraction Context",
            "Observed from Figma",
            "Inferred from Structure",
            "Missing / Needs Clarification",
            "Out of Scope",
            "Endpoint / Client Requirements",
            "Component Mapping",
            "Acceptance Criteria",
            "Open Questions",
            "Frame / Node IDs",
            "Required fidelity",
            "[NEEDS CLARIFICATION]",
        ]
        for term in required_terms:
            self.assertIn(term, document)

        forbidden_terms = [
            "Figma MCP authentication",
            "run a script",
            "implementation test",
            "test-plan.md",
        ]
        for term in forbidden_terms:
            self.assertNotIn(term, document)
```

- [ ] **Step 4: Extend command wrapper assertions**

In `test_behavior_first_command_wrapper_contracts`, add these specify assertions after the existing specify `assertIn` checks:

```python
        for term in (
            "Figma URL Input Policy",
            "Figma Evidence Packet",
            "runtime agent has Figma MCP access",
            "Observed from Figma",
            "Inferred from Structure",
            "Missing / Needs Clarification",
            "Out of Scope",
            "[NEEDS CLARIFICATION]",
            "Continue to write only `spec.md`",
        ):
            self.assertIn(term, specify)
```

Add these checklist assertions after the existing checklist section assertions:

```python
        for term in (
            "Visual Fidelity Readiness",
            "Figma-derived requirements",
            "layout, spacing, typography, colors, effects, assets, and clipping",
            "component mappings and variant coverage",
            "default, hover, focus, active, disabled, loading, empty, and error states",
            "breakpoints, reflow, scrolling, minimum widths, and safe areas",
            "Figma source links, node IDs, screenshots, mapping evidence, and exception rules",
        ):
            self.assertIn(term, checklist)
```

- [ ] **Step 5: Extend behavior checklist template assertions**

In `test_behavior_first_templates_exist_and_are_decoupled`, after the existing NFR assertions, add:

```python
        self.assertIn("Visual Fidelity Readiness", behavior_checklist_template)
        self.assertIn("Figma-derived requirements", behavior_checklist_template)
        self.assertIn("component mappings and variant coverage", behavior_checklist_template)
        self.assertIn("responsive behavior is explicit", behavior_checklist_template)
        self.assertIn("accessibility requirements are explicit", behavior_checklist_template)
```

- [ ] **Step 6: Extend README and governance assertions**

In `test_readme_contract`, add:

```python
        self.assertIn("Figma Evidence Packet", readme)
        self.assertIn("direct Figma URL input", readme)
        self.assertIn("runtime agent has Figma MCP access", readme)
        self.assertIn("does not provide Figma MCP connection, authentication, or execution", readme)
```

In `test_extension_governance_document_contract`, add these required terms:

```python
            "packaged evidence templates are allowed preset artifacts",
            "Figma MCP execution, hooks, adapter scripts, and authentication",
```

- [ ] **Step 7: Run focused tests and verify RED**

Run:

```bash
python3 -m unittest \
  tests.test_preset_contract.PresetContractTests.test_preset_manifest_contract \
  tests.test_preset_contract.PresetContractTests.test_figma_evidence_packet_template_contract \
  tests.test_preset_contract.PresetContractTests.test_behavior_first_command_wrapper_contracts \
  tests.test_preset_contract.PresetContractTests.test_behavior_first_templates_exist_and_are_decoupled \
  tests.test_preset_contract.PresetContractTests.test_readme_contract \
  tests.test_preset_contract.PresetContractTests.test_extension_governance_document_contract
```

Expected: FAIL. The failure should mention the provide count, missing `figma-evidence-packet-template`, missing template file, or missing Figma policy terms.

## Task 2: Add Packet Template And Manifest Entry

**Files:**
- Create: `templates/figma-evidence-packet-template.md`
- Modify: `preset.yml`
- Test: `tests/test_preset_contract.py`

- [ ] **Step 1: Create the packet template**

Create `templates/figma-evidence-packet-template.md` with:

```markdown
# Figma Evidence Packet

## Figma Source
- File URL:
- Page / Frame / Node IDs:
- Design version / timestamp:
- Target platform:
- Required fidelity:

## Extraction Context
- Runtime agent:
- Figma MCP availability:
- Screenshots captured:
- Variables / styles captured:
- Component metadata captured:

## Observed from Figma
- Layout hierarchy:
- Spacing / sizing / grid:
- Typography:
- Colors / tokens:
- Effects:
- Assets:
- Components / variants:
- Prototype links:

## Inferred from Structure
- Likely navigation:
- Likely grouping:
- Likely content priority:
- Confidence notes:

## Missing / Needs Clarification
- Business semantics:
- Dynamic states:
- Responsive behavior:
- Permissions:
- Validation:
- Error handling:
- Data source:
- Analytics / tracking:
- Items marked `[NEEDS CLARIFICATION]`:

## Out of Scope
- Figma content not included in this extraction:
- Runtime behavior not represented by the selected frames:
- Explicit exclusions:

## Endpoint / Client Requirements
- Required breakpoints:
- Scroll behavior:
- Safe area:
- Text overflow:
- Long data:
- Loading / empty / error:
- Accessibility:
- Localization:

## Component Mapping
- Figma component -> code component:
- Variant coverage:
- Missing mappings:

## Acceptance Criteria
- Visual tolerance:
- Required screenshots:
- Required states:
- Required responsive matrix:
- Required accessibility checks:
- Traceability evidence:

## Open Questions
- [NEEDS CLARIFICATION]
```

- [ ] **Step 2: Add the manifest entry**

In `preset.yml`, add this entry after `constitution-template`:

```yaml
    - type: "template"
      name: "figma-evidence-packet-template"
      file: "templates/figma-evidence-packet-template.md"
      description: "Define the Figma Evidence Packet input format for Figma-derived specifications"
      replaces: "figma-evidence-packet-template"
      strategy: "replace"
```

- [ ] **Step 3: Run focused tests**

Run the same focused command from Task 1.

Expected: manifest and packet template failures should pass. Command, README, governance, and checklist wording failures should remain.

## Task 3: Update Specify And Checklist Policies

**Files:**
- Modify: `commands/speckit.specify.md`
- Modify: `commands/speckit.checklist.md`
- Modify: `templates/behavior/behavior-testability-checklist.md`
- Test: `tests/test_preset_contract.py`

- [ ] **Step 1: Add Figma URL input policy to specify**

Insert this section before `{CORE_TEMPLATE}` in `commands/speckit.specify.md`:

```markdown
## Figma URL Input Policy

If the raw request is a Figma URL and the runtime agent has Figma MCP access,
first collect design facts and normalize them into a Figma Evidence Packet
before writing requirements.

Use packet facts as follows:

- Treat `Observed from Figma` as design evidence.
- Treat `Inferred from Structure` as interpretation, not confirmed product intent.
- Treat `Missing / Needs Clarification` as unresolved requirements.
- Treat `Out of Scope` as excluded evidence.
- Mark business semantics, permissions, validation rules, dynamic UI states,
  responsive behavior, error handling, data semantics, and analytics as
  `[NEEDS CLARIFICATION]` unless explicit packet evidence confirms them.

If Figma MCP access is unavailable, Continue to write only `spec.md` and add a
`[NEEDS CLARIFICATION]` item requesting a filled Figma Evidence Packet,
screenshots, or design facts.
```

- [ ] **Step 2: Add visual fidelity readiness policy to checklist**

Insert this section before the NFR paragraph in `commands/speckit.checklist.md`:

```markdown
Check Visual Fidelity Readiness when `spec.md` contains Figma-derived
requirements. Require requirement-level clarity for layout, spacing,
typography, colors, effects, assets, and clipping; component mappings and
variant coverage; default, hover, focus, active, disabled, loading, empty, and
error states; breakpoints, reflow, scrolling, minimum widths, and safe areas;
copy, icons, images, fonts, numeric formats, and placeholders; keyboard, focus,
semantics, contrast, ARIA, and form error requirements; and Figma source links,
node IDs, screenshots, mapping evidence, and exception rules.
```

- [ ] **Step 3: Extend the behavior checklist template**

Insert this section before `## Gate Status` in `templates/behavior/behavior-testability-checklist.md`:

```markdown
## Visual Fidelity Readiness
- [ ] Figma-derived requirements identify the source Figma URL, frame or node IDs, and required fidelity.
- [ ] Layout, spacing, typography, colors, effects, assets, and clipping requirements are explicit.
- [ ] Component mappings and variant coverage are explicit or marked as blocking clarification items.
- [ ] Default, hover, focus, active, disabled, loading, empty, and error states are explicit or marked as missing.
- [ ] Required breakpoints, reflow rules, scrolling, minimum widths, safe areas, and responsive behavior is explicit.
- [ ] Copy, icons, images, fonts, numeric formats, and placeholder content are explicit.
- [ ] Keyboard, focus, semantics, contrast, ARIA, form error behavior, and accessibility requirements are explicit.
- [ ] Visual differences that may be accepted are defined as traceable exception rules.
```

- [ ] **Step 4: Run focused tests**

Run the focused command from Task 1.

Expected: command and checklist failures should pass. README and governance wording failures should remain.

## Task 4: Update Public Docs, Governance, And Changelog

**Files:**
- Modify: `README.md`
- Modify: `docs/extension-governance.md`
- Modify: `CHANGELOG.md`
- Test: `tests/test_preset_contract.py`

- [ ] **Step 1: Add README Figma usage section**

Add this section after the Usage command list:

```markdown
### Figma Input

`/speckit.specify` supports direct Figma URL input when the runtime agent has
Figma MCP access:

```text
/speckit.specify <Figma URL>
```

The runtime agent should extract design evidence into a Figma Evidence Packet
before writing `spec.md`. The preset defines the packet format and requirement
ownership rules; it does not provide Figma MCP connection, authentication, or
execution.
```

- [ ] **Step 2: Add README file-role note**

In the "Contract files packaged by the preset" area, add:

```markdown
Input evidence template packaged by the preset:

- `templates/figma-evidence-packet-template.md`
```

In "Artifact Roles", add:

```markdown
`templates/figma-evidence-packet-template.md` defines how Figma-derived design
facts are normalized before `/speckit.specify` writes requirements. It separates
observed design facts, structural inferences, missing requirements, and excluded
scope so Figma evidence does not get treated as complete product behavior.
```

- [ ] **Step 3: Update extension governance**

Add this paragraph under "Preset Boundaries":

```markdown
Packaged evidence templates are allowed preset artifacts when they define input
shape without executing an external system. Figma MCP execution, hooks, adapter
scripts, and authentication are external integration concerns and remain outside
this preset.
```

Confirm the file remains at or below 140 lines.

- [ ] **Step 4: Update changelog**

Under `## Unreleased`, add:

```markdown
- Added a Figma Evidence Packet input template and requirement-stage policies for Figma-derived specifications without adding Figma MCP execution to the preset.
```

- [ ] **Step 5: Run focused tests**

Run the focused command from Task 1.

Expected: all focused tests pass.

## Task 5: Full Verification And Commit

**Files:**
- Verify all modified files.
- Commit all implementation changes.

- [ ] **Step 1: Run the full contract suite**

Run:

```bash
python3 -m unittest tests/test_preset_contract.py
```

Expected: PASS with zero failures.

- [ ] **Step 2: Inspect git diff**

Run:

```bash
git diff --check
git status --short
git diff --stat
```

Expected: no whitespace errors. Status should show only the planned files.

- [ ] **Step 3: Commit implementation**

Run:

```bash
git add preset.yml commands/speckit.specify.md commands/speckit.checklist.md templates/figma-evidence-packet-template.md templates/behavior/behavior-testability-checklist.md README.md docs/extension-governance.md CHANGELOG.md tests/test_preset_contract.py
git commit -m "feat: add figma evidence packet input"
```

- [ ] **Step 4: Final status check**

Run:

```bash
git status --short
git log -2 --oneline
```

Expected: clean working tree, with the implementation commit above the design-doc commit.

## Self-Review

- Spec coverage: The plan covers the packet template, direct Figma URL policy, observed/inferred/missing/out-of-scope classification, `[NEEDS CLARIFICATION]` handling, checklist visual fidelity readiness, docs, governance, changelog, and tests.
- Placeholder scan: No planned task contains placeholder work. Every file change has explicit text or exact assertions.
- Type and name consistency: The template name is consistently `figma-evidence-packet-template`; the file path is consistently `templates/figma-evidence-packet-template.md`; the command strings are matched by the tests.
