---
description: Manage SDD governance and repository technical Architecture as separate project-memory contracts.
strategy: replace
---

## User Input

```text
$ARGUMENTS
```

You MUST consider the user input before proceeding.

## Pre-Execution Hooks

Read `.specify/extensions.yml` when it exists and run enabled, unconditional
`hooks.before_constitution` entries. Mandatory hooks MUST be invoked and awaited;
conditional hooks remain the HookExecutor's responsibility. Invalid or absent
hook configuration is skipped without changing this command's ownership.

## Explicit Input Agreement

Before writing, confirm and retain an in-memory agreement containing:

- Architecture generation mode: `greenfield`, `brownfield`, or `amendment`;
- run goal;
- every authorized source, one allowed role, opaque identity, and explicit
  technical scope;
- excluded candidate sources;
- repository inspection authorization and exact scope;
- write scope: Constitution only, Architecture only, or both.

No conventional file is authoritative by default. Conversation input, product
documents, an existing Constitution or Architecture, repository code, tests,
configuration, documentation, and directory names are candidate sources until
the user authorizes their role. Core-style repository inference MUST NOT expand
the agreement. If the agreement is missing or ambiguous, stop before writing.

Use the source-neutral roles `requirement-input`, `visual-input`,
`technical-evidence`, and `context-only`. Only explicitly authorized
`technical-evidence` may support observed or inferred technical records.
Product-facing `requirement-input` or `visual-input` may establish approved
target context but does not become a technical decision merely because it is
available; `context-only` authorizes no normative Architecture fact. A source
locator remains opaque and authorizes neither adjacent repository inspection
nor external execution, authenticity/freshness checks, or publication-state
validation.

## Independent Write Scopes

This command owns two independent files:

```text
.specify/memory/constitution.md
.specify/memory/architecture.md
```

- Constitution-only changes MUST NOT modify Architecture.
- Architecture-only changes MUST NOT modify Constitution.
- Combined changes validate and report each output independently.
- Never create a second Architecture artifact, conformance receipt, audit file,
  compliance matrix, implementation manifest, or task artifact.

Resolve the active `constitution-template` through the preset resolution stack.
Resolve the workflow-preset `architecture-template` only when Architecture is in
the authorized write scope. Preserve unaffected content during amendments.

## Constitution Contract

Constitution is the sole SSOT (single source of truth) for SDD workflow
governance. It owns:

- command responsibilities and artifact authority;
- allowed read/write/block boundaries;
- the distinction among Command Internal Gates, official Core Gates, and
  Cross-Command Consistency Gates;
- conflict routing to the command that owns the affected artifact;
- Architecture's role as repository technical SSOT;
- the rule that Plan, Tasks, and Core Implement respect Architecture;
- Analyze's exclusive ownership of cross-command consistency.

Constitution MUST NOT contain concrete frameworks, databases, services, modules,
directory facts, dependency directions, CI details, product requirements,
feature-local mappings, task details, or Intake as an SDD stage.

Always preserve the exact Change Scope Granularity model:

- R: Repository / Workspace. Environment only; too broad for scoped changes.
- M: Module / Capability. Hard outer boundary.
- U: Unit / Design Object. Primary planning boundary.
- O: Operation / Detail. Execution detail.

The mapping MUST NOT be renamed or paraphrased. Preserve `Planning locks M + U`.
If it drifts, do not write Constitution; report
`CONSTITUTION_RMUO_MAPPING_DRIFT`.

### `CONSTITUTION_OUTPUT_READY`

PASS only when the Constitution:

- contains SDD Workflow Governance and Gate Ownership;
- preserves the exact R/M/U/O mapping;
- assigns command output quality to the producing command;
- leaves official Core gates unchanged;
- assigns cross-command consistency exclusively to Analyze;
- contains no concrete repository Architecture or Intake stage.

This is a command-internal output gate. It does not evaluate downstream
artifacts.

## Architecture Contract

Architecture is the repository technical SSOT. It contains only:

- revision identity and authorized evidence scope;
- technical boundaries and dependency direction (`BND-*`);
- stable technical concepts, relationships, lifecycle, and invariants (`CON-*`);
- technical decisions, status, evidence, consequence, revisit condition, and
  supersession (`DEC-*`);
- technical constraints and risks (`CST-*`);
- unresolved technical gaps and triggers (`GAP-*`).

It MUST NOT contain command names, SDD gate definitions, planning consumption
instructions, task derivation, compliance matrices, product requirements, or
implementation operations.

### Mode-specific generation

`greenfield` is intent-first. Derive target Architecture only from confirmed
intent and authorized constraints. Empty scaffolding and directory names do not
establish target technical choices; unresolved choices remain candidates or
`GAP-*`.

`brownfield` is repo-first:

```text
authorized repository snapshot
  -> repository technical facts
  -> stable boundaries and concepts
  -> established decisions
  -> contradictions and technical gaps
  -> repository Architecture SSOT
```

Every core abstraction needs repository evidence or an explicit gap. Distinguish
`observed-current`, `inferred`, `approved-target`, and `migration-gap`. External
direction may define a target change but cannot overwrite observed facts
silently.

`amendment` starts from the current Architecture, preserves unaffected records,
and records reason, effect, supersession, and revision change for every material
update.

### `ARCHITECTURE_OUTPUT_READY`

PASS only when:

- Architecture Revision and source scope are explicit;
- all records use the correct stable ID and defined status;
- Greenfield is intent-first or Brownfield is repo-first, as agreed;
- evidence is precise enough to distinguish fact, inference, approved target,
  and gap;
- decisions include consequence, revisit condition, and supersession;
- no SDD governance, product requirement, task, or downstream conformance
  conclusion is present.

This is a command-internal output gate. It does not check whether Plan or Tasks
has consumed Architecture correctly.

## Update Procedure

1. Establish the explicit input agreement.
2. Read only authorized sources.
3. Load only artifacts in the authorized write scope plus their resolved
   templates.
4. Draft Constitution and Architecture independently.
5. Preserve template headings and existing ratification metadata where
   applicable.
6. Run `CONSTITUTION_OUTPUT_READY` and/or `ARCHITECTURE_OUTPUT_READY`.
7. Write only outputs whose internal gate passes. Use atomic replacement.
8. Never repair or analyze downstream Spec, Plan, Tasks, or implementation.

Do not create a separate source manifest, import/handoff package, adapter, or
provider-specific schema. Source authorization is carried only by the existing
input agreement and Architecture artifact.

## Post-Execution Hooks

After successful authorized writes, run enabled, unconditional
`hooks.after_constitution` entries before the completion report. Mandatory hooks
MUST be invoked and awaited. A failed mandatory hook is reported as a blocker.

## Completion Report

Report:

- mode, goal, authorized/excluded sources, inspection scope, and write scope;
- each artifact path and whether it was created, updated, preserved, or blocked;
- `CONSTITUTION_OUTPUT_READY` and `ARCHITECTURE_OUTPUT_READY` independently;
- Architecture Revision when applicable;
- unresolved governance or technical gaps without promoting them to facts;
- whether mandatory post-hooks completed.
