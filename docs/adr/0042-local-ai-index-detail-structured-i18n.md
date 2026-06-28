# ADR-0042: Local AI Index Detail Structured i18n

- Status: Accepted
- Date: 2026-06-24

## Context

`v1.22.0` completed the local AI-index-status structured-i18n lane.

That still left adjacent AI-index detail surfaces relying on ad hoc wording:

- vector-entry detail still depended on raw metadata wording
- vector-entry size/metadata counts still lacked an explicit summary key
- graph-node detail still depended on raw neighbor wording
- graph-node label/property/neighbor counts still lacked an explicit summary key
- derived/read-only/non-authoritative notes for these detail surfaces still lacked stable keys

Related records:

- `docs/adr/0025-local-ui-i18n-presentation-boundary.md`
- `docs/adr/0041-local-ai-index-status-structured-i18n.md`
- `docs/releases/status/release-status-v1.22.0.md`
- `docs/releases/remaining/v1.22-release-remaining-issues.md`

## Decision

`v1.23.0` begins as the local AI-index-detail structured-i18n lane after the published `v1.22.0` release.

This lane may:

1. add stable `message_key` fields for vector-entry detail wording
2. add stable `counts_summary_key` fields for vector-entry text/metadata counts
3. add stable `message_key` fields for graph-node detail wording
4. add stable `counts_summary_key` fields for graph-node label/property/neighbor counts
5. add stable `boundary_note_key` fields for derived/read-only/non-authoritative detail wording
6. extend smoke/test coverage for explicit AI-index-detail presentation-contract fields

This lane must not:

- change vector/graph detail semantics or authority
- make AI-index detail wording authoritative over primary Chronicle records
- widen hosted-auth, multi-user, or mutation-authority claims
- translate ids, persisted index payloads, or machine-readable status codes

## Consequences

Repository-side work in `v1.23.0` keeps AI-index detail surfaces local-first, read-only, and descriptive while reducing locale drift around vector-entry and graph-node detail wording.
