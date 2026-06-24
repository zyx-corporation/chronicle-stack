# Chronicle Stack v1.18.0 Release Status

Related: `docs/adr/0037-local-package-parity-and-preview-structured-i18n.md`, `docs/release-status-v1.17.0.md`

`v1.18.0` is the repository-side local package-parity-preview structured-i18n release after the published `v1.17.0` baseline.

- Latest published release: `v1.17.0`
- Release URL: `https://github.com/zyx-corporation/chronicle-stack/releases/tag/v1.17.0`
- Current repository-side release target: `v1.18.0`
- Lane scope: package, parity, and preview structured i18n contracts only

## Current repository-side progress

Planned `v1.18.0` release progress includes:

- accepted ADR scope for package, parity, and preview structured i18n
- stable `message_key` fields for package-readiness summaries and detail payloads
- stable `message_key` fields for retrieval package-handoff preview payloads
- stable `message_key` fields for action-preview summaries
- stable `message_key` fields for CLI parity summaries
- HTML renderer support for preferring structured package/parity/preview keys while retaining fallback strings
- smoke/test coverage for explicit package/parity/preview presentation-contract fields
- version bump and release-readiness documents for `1.18.0`

## Boundary notes

Planned `v1.18.0` preserves:

- local-first single-operator scope
- read-only derived-surface discipline
- i18n presentation-only boundary
- JSON/CLI authority over package, preview, and mutation semantics

`v1.18.0` still must not imply:

- hosted auth or multi-user safety
- translated machine-readable status codes
- broader GUI mutation authority
- correctness proof or security certification
