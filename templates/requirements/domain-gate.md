# Requirement Domain Gate Rule Fragment

This parameterized fragment supplies Checklist assembly rules for
`requirements`, `ux`, and `security`. It never becomes
`checklists/<domain>.md`.

| Rule key | Allowed Gate | Atomic concern / question pattern |
|---|---|---|
| DOM-SCOPE | requirements / ux / security | Is the applicable product scope explicit for this Spec semantic ref? |
| DOM-ACTOR-STATE | requirements / ux / security | Are actors, states, permissions, failures, and boundaries unambiguous? |
| DOM-MEASURE | requirements / ux / security | Is the observable outcome measurable without implementation detail? |
| DOM-COVERAGE | requirements / ux / security | Are assumptions, dependencies, exclusions, and edge cases stated or explicitly N/A? |

Instantiate a cross-Gate Check only under a stable Spec semantic ref. A passing
Check cites current `spec.md` evidence; a blocked Check cites exactly one shared
root-cause Blocker.
