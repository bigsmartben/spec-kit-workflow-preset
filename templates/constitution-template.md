{CORE_TEMPLATE}

## Change Scope Granularity

Spec Kit planning and execution MUST use R/M/U/O scope granularity:

- R: Repository / Workspace. Environment only; too broad for scoped changes.
- M: Module / Capability. Hard outer boundary.
- U: Unit / Design Object. Primary planning boundary.
- O: Operation / Detail. Execution detail.

The mapping is fixed and MUST NOT be renamed, translated, or substituted.
Planning locks M + U. Tasks binds U to concrete paths; implementation performs
O-level changes. Requirement commands MUST NOT infer M/U/O boundaries.

## SDD Workflow Governance

The Constitution is the sole governance SSOT for the SDD workflow:

| Command | Owns | Durable write boundary |
|---|---|---|
| Constitution | workflow governance and repository Architecture generation contracts | `constitution.md`, independently authorized `architecture.md` |
| Specify | WHAT/WHY requirements | `spec.md` |
| Clarify | accepted product decisions | `spec.md` |
| Checklist | requirement-writing quality questions | `checklists/<focus>.md` |
| Plan | feature technical, UI/UX, and Test design | feature Plan artifacts |
| Tasks | concrete path binding and ordered checklist work | `tasks.md` |
| Analyze | read-only cross-command consistency | none |
| Core Implement | execution of `tasks.md` | implementation surfaces named by Tasks |

Intake is external evidence acquisition, not an SDD stage. A command may consume
an upstream artifact but MUST NOT rewrite it, emulate another command, or decide
cross-command consistency.

## Gate Ownership

| Gate category | Owner | Meaning |
|---|---|---|
| Command Internal Gate | producing command | its output satisfies its own contract |
| Official Core Gate | Spec Kit Core | unchanged official workflow gate |
| Cross-Command Consistency Gate | Analyze exclusively | artifacts from different commands agree and are current |

Commands MUST NOT copy, broaden, reorder, or reinterpret official Core gates.
Analyze is read-only and routes conflicts to the command that owns the affected
artifact.

## Constitution and Architecture Authority

- `.specify/memory/constitution.md` contains only durable SDD governance.
- `.specify/memory/architecture.md` contains only repository technical facts,
  abstractions, decisions, evidence, constraints, risks, and gaps.
- Constitution MUST NOT duplicate concrete Architecture facts.
- Plan is repo-first and Architecture-constrained; it never amends Architecture.
- Tasks maps completed Plan products; it never reinterprets Architecture.
- Cross-artifact Architecture projection is verified only by Analyze.
