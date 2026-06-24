# ADR-0040: Local Graph Summary Structured i18n

- Status: Accepted
- Date: 2026-06-24

## Context

`v1.20.0` completed the local retrieval-handoff-and-invocation-plan structured-i18n lane.

That still left `graph_summary` as an adjacent read-only UI seam exposing ad hoc wording:

- graph-summary availability still depended on raw prose
- graph node/edge counts still lacked an explicit summary key
- derived/read-only/non-authoritative graph wording still lacked a stable boundary key

This seam sits next to already-structured runtime, provider-response, retrieval, and invocation read-model surfaces.

Related records:

- `docs/adr/0025-local-ui-i18n-presentation-boundary.md`
- `docs/adr/0039-local-retrieval-handoff-and-invocation-plan-structured-i18n.md`
- `docs/release-status-v1.20.0.md`
- `docs/v1.20-release-remaining-issues.md`

## Decision

`v1.21.0` begins as the local graph-summary structured-i18n lane after the published `v1.20.0` release.

This lane may:

1. add stable `message_key` fields for graph-summary availability wording
2. add stable `counts_summary_key` fields for graph node/edge count wording
3. add stable `boundary_note_key` fields for derived/read-only/non-authoritative graph wording
4. expose these structured graph-summary contracts in read-only endpoint and overview payloads
5. extend smoke/test coverage for explicit graph-summary presentation-contract fields

This lane must not:

- change graph export semantics or index authority
- make graph-summary wording authoritative over primary Chronicle records
- widen hosted-auth, multi-user, or mutation-authority claims
- translate ids, persisted graph data, or machine-readable status codes

## Consequences

Repository-side work in `v1.21.0` keeps graph-summary surfaces local-first, read-only, and descriptive while reducing locale drift around graph availability and derived-boundary wording.

This keeps the slice narrow and adjacent:

- prior structured i18n contracts stay intact
- graph-summary wording becomes more key-driven
- fallback strings remain available for CLI-compatible inspection and degraded renderers

## Rationale

After runtime-detail seams gained structured contracts, the next repeated drift seam was graph-summary presentation wording reused in overview and endpoint payloads.

Closing that seam improves determinism across locales without changing runtime behavior, graph semantics, or authority boundaries.
