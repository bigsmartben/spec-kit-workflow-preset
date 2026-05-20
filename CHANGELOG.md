# Changelog

## 1.0.1

- Updated preset and orchestrated workflow version metadata for the 1.0.1 release.
- Updated release install examples to use the `v1.0.1` archive.

## 1.0.0

- Merged the plan design artifacts preset and orchestrated implement preset into `workflow-preset`.
- Kept `/speckit.plan`, `/speckit.tasks`, and `plan-template` as design-aware wrappers.
- Replaced `/speckit.implement` with orchestrated handoff shard dispatch.
- Added workflow and scripts for scoped implementation handoff generation, dispatch, and post-dispatch scope verification.
- Included `class-diagram.md`, `contracts/sequences.md`, and `test-plan.md` in implementation shard context digests.
- Added the subagent profile matrix for setup, test, implementation, integration, validation, and cleanup shards.
- Added fresh process and fresh context isolation metadata to implementation handoffs.
- Reduced unmatched `spec.md` and `plan.md` digest content to outlines plus blocking clarification context.
- Allowed directory-scoped handoffs to create, update, or delete descendant files while preserving scope verification.
- Declared packaged scripts and the orchestrated workflow as preset support files.
