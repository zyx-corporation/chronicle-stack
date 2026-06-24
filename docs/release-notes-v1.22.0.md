# Chronicle Stack v1.22.0 Release Notes

Chronicle Stack `v1.22.0` is a local AI-index-status structured-i18n release over the published `v1.21.0` baseline.

## Added

`v1.22.0` includes:

- structured AI-index-status `message_key` contracts for availability wording
- structured vector `counts_summary_key` contracts inside AI-index-status
- structured graph `counts_summary_key` contracts inside AI-index-status
- structured AI-index-status `boundary_note_key` contracts for derived/read-only wording

## Verified

`v1.22.0` includes:

- updated UI i18n catalog coverage for AI-index-status contracts
- read-endpoint tests for structured AI-index-status fields
- UI smoke checks for AI-index-status structured contracts
- full `ruff`, `pytest`, and `ui-smoke` verification before release

## Boundaries

`v1.22.0` does not add:

- hosted auth or broader mutation authority
- changed vector/graph index semantics or authority
- translated ids, paths, or persisted index payloads
- new durable storage for presentation-only wording
