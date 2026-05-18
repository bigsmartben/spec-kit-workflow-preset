# Workflow Preset Merge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Merge the plan-design-artifacts preset and orchestrated implement preset into one replacement community preset named `workflow-preset`.

**Architecture:** Keep planning and task generation as core-template wrappers, but make `/speckit.implement` a replacement command that runs the orchestrated workflow. The orchestrator scripts generate scoped handoffs whose context digest includes the plan design artifacts.

**Tech Stack:** Spec Kit preset YAML, Markdown command templates, Python unittest, Python stdlib scripts.

---

### Task 1: Contract Tests

**Files:**
- Modify: `tests/test_preset_contract.py`

- [ ] Update manifest expectations to `workflow-preset`, merged command/template providers, workflow provider, and merged tags.
- [ ] Add command tests requiring `/speckit.implement` to call `.specify/presets/workflow-preset/workflows/speckit-orchestrated-implement/workflow.yml`.
- [ ] Add shard builder tests proving `class-diagram.md`, `contracts/sequences.md`, and `test-plan.md` are indexed and summarized in handoff context.
- [ ] Run `python3 -m unittest tests/test_preset_contract.py` and verify the new tests fail before implementation.

### Task 2: Preset Files

**Files:**
- Modify: `preset.yml`
- Modify: `commands/speckit.implement.md`
- Create: `workflows/speckit-orchestrated-implement/workflow.yml`
- Create: `scripts/build-task-shards.py`
- Create: `scripts/run-orchestrated-implement.py`

- [ ] Update `preset.yml` to define one preset id `workflow-preset`.
- [ ] Keep `plan-template`, `speckit.plan`, and `speckit.tasks` as `wrap`.
- [ ] Replace `speckit.implement` with orchestrated implementation command.
- [ ] Copy orchestrator scripts and workflow from `spec-kit-implement-preset`.
- [ ] Change installed preset paths from `.specify/presets/implement/` to `.specify/presets/workflow-preset/`.
- [ ] Extend context indexing to include `class-diagram.md` and `test-plan.md`.

### Task 3: Documentation

**Files:**
- Modify: `README.md`
- Modify: `CHANGELOG.md`

- [ ] Rewrite README around the unified workflow: plan, tasks, orchestrated implement.
- [ ] Document release and local install under `workflow-preset`.
- [ ] Document written artifacts, handoffs, and safety boundaries.
- [ ] Update changelog for `1.0.0` as the merged replacement preset.

### Task 4: Verification

**Files:**
- Test: `tests/test_preset_contract.py`

- [ ] Run `python3 -m unittest tests/test_preset_contract.py`.
- [ ] Run `git status --short --branch`.
- [ ] Review final diff for accidental generated files or stale preset ids.
