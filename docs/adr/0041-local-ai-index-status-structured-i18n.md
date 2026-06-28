# ADR-0041: Local AI Index Status Structured i18n

- Status: Accepted
- Date: 2026-06-24

## Context

`v1.21.0` completed the local graph-summary structured-i18n lane.

That left an adjacent overview/index surface still relying on ad hoc wording:

- AI index status availability still depended on raw prose
- vector entry counts still lacked an explicit summary key
- graph node/edge counts inside AI index status still lacked an explicit summary key
- derived/read-only/non-authoritative AI index wording still lacked a stable boundary key

This seam sits next to already-structured graph-summary and other read-only UI contracts.

Related records:

- `docs/adr/0025-local-ui-i18n-presentation-boundary.md`
- `docs/adr/0040-local-graph-summary-structured-i18n.md`
- `docs/releases/status/release-status-v1.21.0.md`
- `docs/releases/remaining/v1.21-release-remaining-issues.md`

## Decision

`v1.22.0` begins as the local AI-index-status structured-i18n lane after the published `v1.21.0` release.

This lane may:

1. add stable `message_key` fields for AI-index-status availability wording
2. add stable `counts_summary_key` fields for vector entry counts
3. add stable `counts_summary_key` fields for graph node/edge counts inside AI-index-status
4. add stable `boundary_note_key` fields for derived/read-only/non-authoritative AI index wording
5. expose these structured AI-index-status contracts in read-only endpoint and overview-adjacent payloads
6. extend smoke/test coverage for explicit AI-index-status presentation-contract fields

This lane must not:

- change vector/graph index semantics or authority
- make AI-index-status wording authoritative over primary Chronicle records
- widen hosted-auth, multi-user, or mutation-authority claims
- translate ids, persisted index payloads, or machine-readable status codes

## Consequences

Repository-side work in `v1.22.0` keeps AI-index-status surfaces local-first, read-only, and descriptive while reducing locale drift around derived index availability and count wording.

## Rationale

After graph-summary gained structured contracts, the next repeated drift seam was the adjacent AI-index-status wording reused in overview-facing payloads.

Closing that seam improves determinism across locales without changing index behavior or authority boundaries.
