# Chronicle Stack v1.23.0 Release Notes

Chronicle Stack `v1.23.0` is a local AI-index-detail structured-i18n release over the published `v1.22.0` baseline.

## Added

`v1.23.0` includes:

- structured vector-entry detail `message_key` contracts
- structured vector-entry detail `counts_summary_key` contracts
- structured graph-node detail `message_key` contracts
- structured graph-node detail `counts_summary_key` contracts
- structured derived/read-only `boundary_note_key` contracts for both detail surfaces

## Verified

`v1.23.0` includes:

- updated UI i18n catalog coverage for AI-index-detail contracts
- read-detail tests for vector-entry and graph-node structured fields
- UI smoke checks for AI-index-detail structured contracts
- full `ruff`, `pytest`, and `ui-smoke` verification before release

## Boundaries

`v1.23.0` does not add:

- hosted auth or broader mutation authority
- changed vector/graph detail semantics or authority
- translated ids, paths, or persisted index payloads
- new durable storage for presentation-only wording
