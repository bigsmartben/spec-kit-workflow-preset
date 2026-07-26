---
description: Wrap core constitution updates with change scope granularity and Constitution-managed architecture governance.
strategy: wrap
---

## Constitution Stage Input Agreement

Before writing either project-memory artifact, establish an explicit input agreement with the user:

- project mode: `greenfield`, `brownfield`, or `amendment`;
- the goal of this Constitution-stage run;
- which user-selected sources are authoritative and the role of each source;
- which candidate sources are excluded;
- whether repository inspection is authorized and its exact scope;
- whether this run may update Constitution, Architecture, or both.

Conversation input, UC/PRD/product documents, an existing Constitution or Architecture, repository evidence, and external constraints are all possible sources. No conventional path is mandatory. In particular, `uc.md`, `inception/product/uc.md`, `.specify/memory/uc.md`, README files, source code, tests, configuration, and directory names are candidate sources only until the user authorizes their role.

If the agreement is absent, ambiguous, or insufficient for the requested update, stop and confirm it with the user before writing. Do not silently discover an input and promote it to authority.

## Project Mode

Apply the source rules for the agreed mode:

- `greenfield`: derive prospective governance and Architecture from confirmed intent and selected project/product sources. Do not infer target Architecture from scaffolding.
- `brownfield`: inspect only the authorized repository scope. Keep observed current state, approved governance, target Architecture, and migration or unresolved gaps distinct. Existing code is evidence, not automatically a ratified principle or target decision.
- `amendment`: update the existing Constitution and/or Architecture baseline within the agreed scope. Preserve unaffected content and record the reason for each material Architecture change.

If an existing `.specify/memory/architecture.md` uses the retired 4+1 or nine-section planning-contract format, report `ARCH_LEGACY_FORMAT`. Rewrite it only when the input agreement authorizes an Architecture update; never silently migrate it.

## Change Scope Granularity

Always preserve the Change Scope Granularity principle in `.specify/memory/constitution.md`.

Constitution updates must not remove, weaken, or contradict the principle's R/M/U/O model, boundary timing, or context-gap rule. Keep the principle normative, including `Planning locks M + U`.

The R/M/U/O letter mapping is fixed and MUST remain exact:

- R: Repository / Workspace. Environment only; too broad for scoped changes.
- M: Module / Capability. Hard outer boundary.
- U: Unit / Design Object. Primary planning boundary.
- O: Operation / Detail. Execution detail.

Do not paraphrase, expand, rename, translate, or substitute these letters with other nouns such as Requirement, Model, User/API Interface, or Operations.

If a drafted constitution changes this mapping, discard the draft and report blocker code `CONSTITUTION_RMUO_MAPPING_DRIFT` instead of writing `.specify/memory/constitution.md`.

When producing the Sync Impact Report, report template or command file status only after checking the actual path. If a path cannot be checked, report `CONSTITUTION_TEMPLATE_STATUS_UNCHECKED`; do not report it as missing.
If the root `.specify/templates/constitution-template.md` is still the core placeholder, do not treat that as the workflow-preset template being absent. Resolve or check `.specify/presets/workflow-preset/templates/constitution-template.md` before reporting preset template status.

## Separate Artifact Ownership

The Constitution stage manages two independent project-memory files:

```text
.specify/memory/constitution.md
.specify/memory/architecture.md
```

- `constitution.md` stores durable governance principles.
- `architecture.md` stores project-level boundaries, concepts, technical direction, constraints, evidence, revisit conditions, and unresolved gaps.
- Architecture facts must not be embedded in ratified Constitution principles.
- Feature-local `research.md`, `data-model.md`, `contracts/`, `plan.md`, and `quickstart.md` consume and refine the project Architecture for one feature; they do not replace it.

## Architecture Lifecycle

When the input agreement authorizes an Architecture update, load the workflow-preset `architecture-template.md` and write exactly one Architecture artifact: `.specify/memory/architecture.md`.

Use one sequential reasoning chain, without 4+1:

```text
System Boundary
  -> Conceptual Model
  -> Technical Decisions & Evidence
  -> Planning Guardrails & Gaps
```

Render exactly these five top-level sections:

1. `Architecture Overview`
2. `System Boundary`
3. `Conceptual Model`
4. `Technical Decisions & Evidence`
5. `Planning Guardrails & Gaps`

Technical validation is evidence registration only. Record a candidate, conclusion, available evidence, and an explicit evidence gap or revisit condition when validation is still required. Do not create PoC code, application source, tests, migrations, build changes, deployment changes, secondary Architecture models, view files, or receipts.

An Architecture update is ready only when it:

- states the Architecture goal, authorized sources, and at least one explicit boundary with ownership and non-responsibility;
- defines applicable core concepts with stable meaning, ownership, relationships, lifecycle, and invariants;
- records established technical decisions with scope, consequence, evidence, and revisit conditions;
- gives every item marked `MUST_VALIDATE` a conclusion plus evidence or an explicit validation gap;
- states applicable planning constraints and unresolved gaps without requiring downstream inference;
- contains no invented product requirement, implementation plan, task breakdown, or unresolved ambiguity presented as fact.

Optional tables may be empty when they are genuinely not applicable. Do not manufacture extension points, decisions, or open questions to fill the template.

When the agreement excludes an Architecture update, do not modify `architecture.md`. Report whether the existing file is missing, legacy, ready, or blocked so the user understands whether `/speckit.plan` can proceed.

## Architecture-Guided Planning

Always preserve the Architecture-Guided Planning principle in `.specify/memory/constitution.md`.

`/speckit.plan` MUST read `.specify/memory/architecture.md` before producing planning artifacts.

- `research.md` MUST follow established technical decisions and evidence, unless an Architecture revisit condition is met.
- `data-model.md` MUST preserve defined concepts, ownership, relationships, lifecycle, and invariants.
- `contracts/` MUST preserve system boundaries, responsibilities, interface ownership, and dependency direction.
- `plan.md` and `quickstart.md` MUST carry forward applicable Architecture constraints, gaps, and validation implications.

If any planning artifact conflicts with or requires changing the Architecture, planning MUST stop and return to the Constitution stage.

{CORE_TEMPLATE}

## Constitution Stage Reporting

Before finishing, report:

- the agreed project mode, goal, authorized and excluded sources, repository-inspection scope, and update scope;
- whether `constitution.md` preserves Change Scope Granularity, `Planning locks M + U`, and preserves the exact R/M/U/O letter mapping;
- whether Constitution facts and Architecture facts remain in their separate files;
- whether `architecture.md` was created, updated, preserved, missing, legacy, ready, or blocked;
- unresolved governance or Architecture gaps without presenting them as ratified facts.
