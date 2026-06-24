# ADR-0043: Local Package Review Structured i18n

- Status: Accepted
- Date: 2026-06-24

## Context

`v1.23.0` completed the local AI-index-detail structured-i18n lane.

That still left the adjacent package-review read model with partially ad hoc wording:

- package-review status text still depended on raw per-status copy
- package-review record/warning/finding counts still lacked a stable summary key
- derived/read-only/non-authoritative boundary wording still lacked a stable key
- smoke/test coverage did not yet enforce a structured package-review presentation contract

Related records:

- `docs/adr/0025-local-ui-i18n-presentation-boundary.md`
- `docs/adr/0037-local-package-parity-and-preview-structured-i18n.md`
- `docs/adr/0042-local-ai-index-detail-structured-i18n.md`
- `docs/release-status-v1.23.0.md`
- `docs/v1.23-release-remaining-issues.md`

## Decision

`v1.24.0` begins as the local package-review structured-i18n lane after the published `v1.23.0` release.

This lane may:

1. add stable `message_key` fields for package-review status wording
2. add stable `counts_summary_key` fields for record/warning/finding summaries
3. add stable `boundary_note_key` fields for derived/read-only/non-authoritative wording
4. extend smoke/test coverage for explicit package-review presentation-contract fields
5. keep package-review wording aligned across supported UI locales without translating machine-readable status codes

This lane must not:

- change package-review semantics or authority
- make package-review wording authoritative over primary Chronicle records
- widen hosted-auth, multi-user, or mutation-authority claims
- translate ids, persisted payloads, or machine-readable status codes

## Consequences

Repository-side work in `v1.24.0` keeps the package-review surface local-first, read-only, and descriptive while reducing locale drift around package-review summaries and boundary notes.
