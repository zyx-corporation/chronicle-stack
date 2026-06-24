# Chronicle Stack v1.21.0 Release Notes

Chronicle Stack `v1.21.0` is a local graph-summary structured-i18n release over the published `v1.20.0` baseline.

## Added

`v1.21.0` includes:

- structured graph-summary `message_key` contracts for availability wording
- structured graph-summary `counts_summary_key` contracts for node/edge count wording
- structured graph-summary `boundary_note_key` contracts for derived/read-only/non-authoritative wording
- overview and endpoint payload exposure for these graph-summary structured fields

## Verified

`v1.21.0` includes:

- updated UI i18n catalog coverage for graph-summary contracts
- read-endpoint and overview tests for structured graph-summary fields
- UI smoke checks for graph-summary structured contracts
- full `ruff`, `pytest`, and `ui-smoke` verification before release

## Boundaries

`v1.21.0` does not add:

- hosted auth or broader mutation authority
- changed graph export semantics or index authority
- translated ids, paths, or persisted graph payloads
- new durable storage for presentation-only wording
