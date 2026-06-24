# ADR-0039: Local Retrieval Handoff and Invocation Plan Structured i18n

- Status: Accepted
- Date: 2026-06-24

## Context

`v1.19.0` completed the local navigation-provider-response-runtime-preview structured-i18n lane.

That left adjacent runtime-detail seams still relying on ad hoc wording inside read-only payload rendering:

- retrieval-handoff notices still embedded raw hit-count wording
- invocation-plan notices still embedded raw readiness wording
- invocation-plan provider summaries still depended on inline fallback strings

These seams sit next to the already-structured runtime preview and provider-response contracts and drift for the same reason: presentation-only detail notices still exposed ad hoc prose instead of explicit keys.

Related records:

- `docs/adr/0025-local-ui-i18n-presentation-boundary.md`
- `docs/adr/0038-local-navigation-provider-response-and-runtime-preview-structured-i18n.md`
- `docs/release-status-v1.19.0.md`
- `docs/v1.19-release-remaining-issues.md`

## Decision

`v1.20.0` begins as the local retrieval-handoff-and-invocation-plan structured-i18n lane after the published `v1.19.0` release.

This lane may:

1. add stable `message_key` fields for retrieval-handoff notices
2. add stable `hit_counts_summary_key` fields for retrieval-handoff hit-count summaries
3. add stable `message_key` fields for invocation-plan readiness summaries
4. add stable `provider_summary_key` fields for invocation-plan provider summaries
5. let the embedded HTML renderer prefer these structured fields while retaining fallback strings
6. extend smoke/test coverage for these explicit runtime-detail presentation contracts

This lane must not:

- change retrieval semantics, invocation readiness semantics, or downstream CLI contracts
- make UI wording authoritative over CLI/JSON runtime payloads
- widen hosted-auth, multi-user, or mutation-authority claims
- translate ids, paths, persisted runtime payloads, or execution-request content

## Consequences

Repository-side work in `v1.20.0` keeps runtime-detail surfaces local-first, descriptive, and read-only while reducing locale drift around retrieval handoff and invocation planning.

This keeps the slice narrow and adjacent:

- runtime-preview/provider-response structured contracts stay intact
- retrieval-handoff/invocation-plan notices become more key-driven
- fallback strings remain available for CLI-compatible inspection and degraded renderers

## Rationale

After the runtime preview and provider-response seams gained structured i18n contracts, the next repeated drift seam was the surrounding retrieval handoff and invocation-plan prose reused in runtime-record detail payloads.

Closing that seam improves determinism across locales without changing authority, runtime behavior, or write scope.
