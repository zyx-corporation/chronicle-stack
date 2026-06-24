# Chronicle Stack v1.20.0 Release Notes

Chronicle Stack `v1.20.0` is a local retrieval-handoff-and-invocation-plan structured-i18n release over the published `v1.19.0` baseline.

## Added

`v1.20.0` includes:

- structured retrieval-handoff `message_key` contracts for runtime-record detail payloads
- structured retrieval-handoff `hit_counts_summary_key` contracts for hit-count wording
- structured invocation-plan `message_key` contracts for readiness wording
- structured invocation-plan `provider_summary_key` contracts for provider-summary wording
- HTML renderer preference for structured retrieval/invocation fields with fallback string preservation

## Verified

`v1.20.0` includes:

- updated UI i18n catalog coverage for retrieval-handoff and invocation-plan contracts
- detail-payload tests for retrieval-handoff and invocation-plan structured fields
- UI smoke checks for retrieval-handoff and invocation-plan structured contracts
- full `ruff`, `pytest`, and `ui-smoke` verification before release

## Boundaries

`v1.20.0` does not add:

- hosted auth or broader mutation authority
- changed retrieval semantics or invocation semantics
- translated ids, paths, or persisted runtime payloads
- new durable storage for presentation-only wording
