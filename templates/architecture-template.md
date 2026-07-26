# Project Architecture: [PROJECT]

**Architecture Goal**: [State the project-level architecture outcome this artifact guides.]

**Project Mode**: [greenfield | brownfield | amendment]

**Last Updated**: [DATE]

**Authorized Sources**:

- [Source and its agreed role]

**Excluded Sources**:

- [Source or `None`]

## Architecture Overview

[Summarize the target architecture, the current-to-target distinction when applicable, and the reasoning scope. Do not include an implementation plan.]

## System Boundary

| Boundary | Owns | Does Not Own | External Relationship / Dependency Direction | Source |
|----------|------|--------------|----------------------------------------------|--------|
| [At least one explicit boundary] | [Responsibility] | [Explicit non-responsibility] | [Inbound/outbound relationship] | [Authorized source] |

## Conceptual Model

| Concept | Stable Meaning | Owner | Relationships | Lifecycle | Invariants | Source |
|---------|----------------|-------|---------------|-----------|------------|--------|

## Technical Decisions & Evidence

| Decision / Candidate | Scope | Conclusion | Consequence | Evidence Or Explicit Gap | Revisit Condition | Validation |
|----------------------|-------|------------|-------------|--------------------------|-------------------|------------|

Use `MUST_VALIDATE` in the Validation column only when planning depends on evidence that is not yet sufficient. Such a row requires a current conclusion and either available evidence or an explicit validation gap.

## Planning Guardrails & Gaps

### Constraints

| Constraint | Applies To | Planning Implication | Source |
|------------|------------|----------------------|--------|

### Unresolved Gaps

| Gap | Planning Impact | Resolution Owner / Trigger | Source |
|-----|-----------------|----------------------------|--------|

Optional tables may remain empty when they are not applicable. Do not add placeholder facts or invented records.
