# ADR-0044: Local Embedded Package Review Structured Contracts

- Status: Accepted
- Date: 2026-06-24

## Context

`v1.24.0` completed the top-level package-review structured-i18n lane for `/api/package-review`.

Adjacent package surfaces still embedded raw package-review payloads inside read-only handoff and readiness views:

- runtime retrieval handoff preview embedded package-review status without structured presentation fields
- review-target package readiness embedded package-review status without structured presentation fields
- smoke/test coverage did not yet enforce package-review structured contracts once nested inside adjacent read-only package surfaces

Related records:

- `docs/adr/0037-local-package-parity-and-preview-structured-i18n.md`
- `docs/adr/0043-local-package-review-structured-i18n.md`
- `docs/releases/status/release-status-v1.24.0.md`
- `docs/releases/remaining/v1.24-release-remaining-issues.md`

## Decision

`v1.25.0` begins as the local embedded-package-review structured-contract lane after the published `v1.24.0` release.

This lane may:

1. reuse the same package-review structured presentation contract for nested read-only package surfaces
2. add common `message_key`, `counts_summary_key`, and `boundary_note_key` fields to embedded package-review payloads
3. extend smoke/test coverage for nested package-review presentation contracts

This lane must not:

- change package-review semantics or authority
- make embedded package-review wording authoritative over primary Chronicle records
- widen hosted-auth, multi-user, or mutation-authority claims
- translate ids, persisted payloads, or machine-readable status codes

## Consequences

Repository-side work in `v1.25.0` keeps adjacent package surfaces aligned with the same local-first, read-only, non-authoritative package-review contract already used by the top-level package-review endpoint.
