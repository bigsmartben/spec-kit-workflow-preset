# Project Architecture: [PROJECT]

**Architecture Goal**: [Repository-level technical outcome.]

**Architecture Revision**: [ARCH-REV-YYYYMMDD-N]

**Generation Mode**: [greenfield | brownfield | amendment]

**Repository Revision / Snapshot**: [Commit, tag, snapshot ID, or N/A with reason.]

**Authorized Sources**:

| Source ref | Role | Opaque locator / identity | Authorized technical scope / facts | Affected Architecture IDs | Status / gap |
|---|---|---|---|---|---|
| SRC-ARCH-001 | technical-evidence | [Repository snapshot, supplied reference, or description.] | [Explicit technical evidence scope.] | [BND/CON/DEC/CST/GAP refs] | [retained / verified locally / GAP ref] |

Allowed roles use the source-neutral Spec semantics: `requirement-input`,
`visual-input`, `technical-evidence`, and `context-only`. Only
`technical-evidence` supports observed or inferred technical records.
Product-facing sources may establish approved target context but do not become
technical decisions automatically. Locator identity stays opaque.

**Excluded Sources**:

- [Source or `None`.]

## Architecture Overview

[Summarize current technical state, approved target, and migration delta when
applicable. Do not include product requirements, SDD procedures, or tasks.]

## System Boundary

| ID | State | Owns | Does Not Own | Dependency Direction | Evidence | Evidence Status |
|---|---|---|---|---|---|---|
| BND-001 | observed-current | [Responsibility] | [Non-responsibility] | [Inbound/outbound] | [Revision + path/source] | verified |

Allowed `State` values: `observed-current`, `inferred`, `approved-target`,
`migration-gap`. An inferred record is never treated as an approved target.

## Conceptual Model

| ID | State | Stable Meaning | Owner | Relationships | Lifecycle | Invariants | Evidence |
|---|---|---|---|---|---|---|---|
| CON-001 | observed-current | [Meaning] | [Boundary ID] | [Related IDs] | [States/transitions] | [Invariant] | [Revision + path/source] |

## Technical Decisions & Evidence

| ID | State | Scope | Decision / Candidate | Technical Consequence | Evidence | Evidence Status | Revisit Condition | Supersedes |
|---|---|---|---|---|---|---|---|---|
| DEC-001 | approved-target | [BND/CON refs] | [Conclusion] | [Technical effect] | [Stable ref] | verified | [Trigger] | [DEC ID or None] |

Allowed `Evidence Status` values: `verified`, `partial`, `unverified`,
`contradictory`. A decision with insufficient evidence remains a candidate or
has a `GAP-*`; it is not silently ratified.

## Technical Constraints & Gaps

### Technical Constraints

| ID | State | Applies To | Constraint | Technical Consequence | Evidence | Revisit Condition |
|---|---|---|---|---|---|---|
| CST-001 | approved-target | [BND/CON/DEC refs] | [Constraint] | [Technical effect] | [Stable ref] | [Trigger] |

### Unresolved Technical Gaps

| ID | State | Gap | Technical Risk | Resolution Owner / Trigger | Evidence | Supersedes |
|---|---|---|---|---|---|---|
| GAP-001 | migration-gap | [Unknown or contradiction] | [Risk] | [Owner/trigger] | [Stable ref] | [GAP ID or None] |

Optional tables may be empty only with a concrete `Not Applicable` reason.
Do not add placeholder facts, command names, downstream gate instructions,
feature task paths, or implementation operations.
