# Chronicle Stack v1.23.0 Release Status

Related: `docs/adr/0042-local-ai-index-detail-structured-i18n.md`, `docs/release-status-v1.22.0.md`

`v1.23.0` is the repository-side local AI-index-detail structured-i18n release after the published `v1.22.0` baseline.

- Latest published release: `v1.22.0`
- Release URL: `https://github.com/zyx-corporation/chronicle-stack/releases/tag/v1.22.0`
- Current repository-side release target: `v1.23.0`
- Lane scope: AI-index vector-entry and graph-node detail structured i18n contracts only

## Current repository-side progress

Planned `v1.23.0` release progress includes:

- accepted ADR scope for AI-index-detail structured i18n
- stable `message_key` fields for vector-entry detail wording
- stable `counts_summary_key` fields for vector-entry text/metadata counts
- stable `message_key` fields for graph-node detail wording
- stable `counts_summary_key` fields for graph-node label/property/neighbor counts
- stable `boundary_note_key` fields for derived/read-only detail wording
- smoke/test coverage for explicit AI-index-detail presentation-contract fields
- version bump and release-readiness documents for `1.23.0`

## Boundary notes

Planned `v1.23.0` preserves:

- local-first single-operator scope
- read-only derived-surface discipline
- i18n presentation-only boundary
- primary Chronicle record authority over derived index detail wording

`v1.23.0` still must not imply:

- hosted auth or multi-user authority
- translated machine-readable status codes or ids
- broader GUI mutation authority
- correctness proof or security certification
