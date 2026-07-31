# NFR Gate Rule Fragment

This is a logical-Gate rule fragment assembled into the one canonical
`checklists/requirements.md`; it is not an independent file contract.

| Rule key | Gate | Atomic concern / question pattern |
|---|---|---|
| NFR-MEASURE | nfr | Are applicable quality expectations measurable on named observable paths? |
| NFR-COVERAGE | nfr | Are reliability, recovery, security/privacy, accessibility, and compatibility outcomes specified or concretely N/A? |
| NFR-CONTEXT | nfr | Are thresholds, populations, environments, and observation windows unambiguous? |
| NFR-ABSTRACTION | nfr | Does the requirement avoid prescribing implementation unless it is an authorized constraint? |

Generate stable Checks by Spec ref plus concern. Reuse a shared Blocker when
multiple Gates expose the same missing product fact.
