# Chronicle Stack v1.21.0 Release Status

Related: `docs/adr/0040-local-graph-summary-structured-i18n.md`, `docs/release-status-v1.20.0.md`

`v1.21.0` is the repository-side local graph-summary structured-i18n release after the published `v1.20.0` baseline.

- Latest published release: `v1.20.0`
- Release URL: `https://github.com/zyx-corporation/chronicle-stack/releases/tag/v1.20.0`
- Current repository-side release target: `v1.21.0`
- Lane scope: graph-summary structured i18n contracts only

## Current repository-side progress

Planned `v1.21.0` release progress includes:

- accepted ADR scope for graph-summary structured i18n
- stable `message_key` fields for graph-summary availability wording
- stable `counts_summary_key` fields for graph node/edge count wording
- stable `boundary_note_key` fields for derived/read-only graph boundary wording
- endpoint and overview payload exposure for structured graph-summary fields
- smoke/test coverage for explicit graph-summary presentation-contract fields
- version bump and release-readiness documents for `1.21.0`

## Boundary notes

Planned `v1.21.0` preserves:

- local-first single-operator scope
- read-only derived-surface discipline
- i18n presentation-only boundary
- primary Chronicle record authority over graph-summary wording

`v1.21.0` still must not imply:

- hosted auth or multi-user authority
- translated machine-readable status codes or ids
- broader GUI mutation authority
- correctness proof or security certification
