# Chronicle Stack v1.26.0 Release Notes

Chronicle Stack `v1.26.0` is a local package-readiness-summary structured-contract release over the published `v1.25.0` baseline.

## Added

`v1.26.0` includes:

- structured `label_key` contracts for package readiness summary badges
- structured `message_template_key` contracts for package readiness summary copy
- review-queue smoke checks for package readiness summary structured fields

## Verified

`v1.26.0` includes:

- UI data-service tests for package readiness summary structured fields
- UI smoke checks for review-queue package readiness summary structured contracts
- full `ruff`, `pytest`, and `ui-smoke` verification before release

## Boundaries

`v1.26.0` does not add:

- hosted auth or broader mutation authority
- changed package readiness semantics or authority
- translated ids, paths, or persisted payloads
- new durable storage for presentation-only wording
