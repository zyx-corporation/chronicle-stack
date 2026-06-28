# Chronicle Stack v1.24.0 Release Notes

Chronicle Stack `v1.24.0` is a local package-review structured-i18n release over the published `v1.23.0` baseline.

## Added

`v1.24.0` includes:

- structured package-review `message_key` contracts
- structured package-review `counts_summary_key` contracts
- structured derived/read-only package-review `boundary_note_key` contracts

## Verified

`v1.24.0` includes:

- updated UI i18n catalog coverage for package-review contracts
- UI data-service tests for package-review structured fields
- UI smoke checks for package-review structured contracts
- full `ruff`, `pytest`, and `ui-smoke` verification before release

## Boundaries

`v1.24.0` does not add:

- hosted auth or broader mutation authority
- changed package-review semantics or authority
- translated ids, paths, or persisted payloads
- new durable storage for presentation-only wording
