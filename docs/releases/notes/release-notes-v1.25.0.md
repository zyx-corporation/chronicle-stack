# Chronicle Stack v1.25.0 Release Notes

Chronicle Stack `v1.25.0` is a local embedded-package-review structured-contract release over the published `v1.24.0` baseline.

## Added

`v1.25.0` includes:

- shared structured package-review contract decoration for nested handoff and readiness surfaces
- embedded package-review `message_key` contracts on adjacent read-only package surfaces
- embedded package-review `counts_summary_key` and `boundary_note_key` contracts

## Verified

`v1.25.0` includes:

- UI data-service tests for embedded package-review structured fields
- UI smoke checks for nested package-review structured contracts
- full `ruff`, `pytest`, and `ui-smoke` verification before release

## Boundaries

`v1.25.0` does not add:

- hosted auth or broader mutation authority
- changed package-review semantics or authority
- translated ids, paths, or persisted payloads
- new durable storage for presentation-only wording
