# Behavior Gate Rule Fragment

This is a Checklist assembly fragment, not a standalone checklist and not a
runtime artifact. Apply its rules inside the matching Spec semantic group in
`checklists/requirements.md`.

| Rule key | Gate | Atomic concern / question pattern |
|---|---|---|
| BEH-CASES | behavior | Are primary, alternate, negative, boundary, permission, validation, and state-conflict outcomes explicit when applicable? |
| BEH-OBSERVABLE | behavior | Does the behavior identify actor, trigger, observable outcome, and failure feedback? |
| BEH-LIFECYCLE | behavior | Are lifecycle, retry, recovery, and terminal outcomes internally consistent? |
| BEH-SCOPE | behavior | Are behavior exclusions, assumptions, and boundary effects explicit? |

Generate one stable Check per applicable Spec ref and atomic concern. Several
Checks may share one semantic root-cause Blocker; never create a Blocker merely
because a Rule key exists.
