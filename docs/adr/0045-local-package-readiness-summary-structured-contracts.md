# ADR-0045: Local Package Readiness Summary Structured Contracts

- Status: Accepted
- Date: 2026-06-24

## Context

`v1.25.0` completed the embedded-package-review structured-contract lane.

Adjacent package readiness summary surfaces still depended on partially ad hoc presentation fields:

- `package_readiness_summary.label` remained a raw badge string
- `package_readiness_summary.message` remained derived from ad hoc summary copy
- list-row smoke coverage did not yet enforce a stable structured contract for package readiness summaries

Related records:

- `docs/adr/0043-local-package-review-structured-i18n.md`
- `docs/adr/0044-local-embedded-package-review-structured-contracts.md`
- `docs/release-status-v1.25.0.md`
- `docs/v1.25-release-remaining-issues.md`

## Decision

`v1.26.0` begins as the local package-readiness-summary structured-contract lane after the published `v1.25.0` release.

This lane may:

1. add stable `label_key` fields for package readiness summary badges
2. add stable `message_template_key` fields for package readiness summary copy
3. reuse existing readiness status and parameter fields without changing semantics
4. extend smoke/test coverage for package readiness summary structured fields

This lane must not:

- change package readiness semantics or authority
- make package readiness summaries authoritative over primary Chronicle records
- widen hosted-auth, multi-user, or mutation-authority claims
- translate ids, persisted payloads, or machine-readable status codes

## Consequences

Repository-side work in `v1.26.0` keeps package readiness summaries local-first, read-only, and descriptive while reducing locale drift around badge and summary presentation contracts.
