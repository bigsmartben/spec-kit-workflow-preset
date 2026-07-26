{CORE_TEMPLATE}

## Change Scope Granularity

Spec Kit planning and execution MUST use R/M/U/O scope granularity:

- R: Repository / Workspace. Environment only; too broad for scoped changes.
- M: Module / Capability. Hard outer boundary.
- U: Unit / Design Object. Primary planning boundary.
- O: Operation / Detail. Execution detail.

The R/M/U/O letter mapping is fixed. Do not paraphrase, expand, rename, translate, or substitute these letters with other nouns.

Planning locks M + U.
Execution maps U -> concrete paths -> O-level changes.
If U -> concrete paths cannot be determined, report a context gap. Do not widen scope to R or broad M.

This principle applies from planning onward. Requirement specification, clarification, and checklist readiness MUST NOT infer M/U/O boundaries.

## Constitution And Architecture Boundary

The Constitution stage maintains separate project-memory artifacts:

- `.specify/memory/constitution.md` contains durable governance principles.
- `.specify/memory/architecture.md` contains project-level boundaries, concepts, technical direction, evidence, constraints, and gaps.

Ratified Constitution principles MUST NOT copy concrete Architecture facts. Feature-local planning artifacts may refine Architecture for one feature, but MUST NOT silently replace project Architecture.

## Architecture-Guided Planning

`/speckit.plan` MUST read `.specify/memory/architecture.md` before producing planning artifacts.

- `research.md` MUST follow established technical decisions and evidence, unless an Architecture revisit condition is met.
- `data-model.md` MUST preserve defined concepts, ownership, relationships, lifecycle, and invariants.
- `contracts/` MUST preserve system boundaries, responsibilities, interface ownership, and dependency direction.
- `plan.md` and `quickstart.md` MUST carry forward applicable Architecture constraints, gaps, and validation implications.

If any planning artifact conflicts with or requires changing the Architecture, planning MUST stop and return to the Constitution stage.
