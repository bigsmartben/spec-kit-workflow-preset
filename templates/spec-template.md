{CORE_TEMPLATE}

## Specification Spectrum

This section is a content carrier, not a completeness checklist. Populate only
applicable domains and retain a concrete `Not Applicable: <reason>` when
non-applicability is confirmed.

### Functional Requirements

- **FR-001**: [Observable product behavior.]

### Non-Functional Requirements

- **NFR-001**: [Measurable quality outcome, constraint, or explicit N/A.]

### UX Journeys and Interaction Expectations

- **UX-001**: [Actor goal, journey, feedback, recovery, and accessibility expectation.]

### UI Surfaces and States

- **UI-001**: [Surface, loading/empty/error/success/disabled/focus states, feedback, and responsive behavior.]

### Visual Requirements and Sources

- **VIS-001**: [Observable visual requirement, applicable SRC/UI refs, viewport/state refs, or source-evidence blocker.]

### Security and Privacy

- [Requirement, constraint, assumption, or specific N/A reason.]

### Data and Integration Constraints

- [Data semantics, external dependency, boundary, failure, compatibility, or specific N/A reason.]

### Dependencies and Boundaries

- [Owned/non-owned scope and external dependency.]

## Assumptions

- [Documented default that is not presented as confirmed fact.]

## Exclusions

- [Explicitly out-of-scope outcome.]

## Source References

This table is the feature-local Source Reference Contract. A source identity is
opaque provenance: retain a supplied URI, path, revision, digest, conversation
reference, or human description without interpreting or validating its external
meaning or state.

| SRC ref | Role | Opaque locator / description | Revision / identity | Authorized scope / facts | Projected requirement refs | Status / blocker |
|---|---|---|---|---|---|---|
| SRC-001 | requirement-input | [Conversation direction, document, reference, or description.] | [Optional supplied identity or `Not supplied`.] | [Current feature slice and authorized WHAT/WHY facts.] | [FR/NFR/UX/UI/VIS refs, or `None`.] | [projected / retained / NEEDS CLARIFICATION / BLOCKED with reason.] |

Allowed roles are exactly `requirement-input`, `visual-input`,
`technical-evidence`, and `context-only`. `context-only` and
`technical-evidence` do not authorize normative `FR/NFR/UX/UI/VIS` projection.
`visual-input` may project only `UI-*` and `VIS-*`. A broad source without a
safe feature slice stays blocked or needs clarification; it is not imported in
full.

## Unresolved Product Decisions

- [NEEDS CLARIFICATION: high-impact product decision, or `None`.]

## Source Evidence Blockers

- [SRC ref + missing evidence + affected local refs, or `None`. The matching
  Source References row remains the canonical status.]

## Clarifications

### Session YYYY-MM-DD

- Q: [Question] -> A: [Accepted answer]
