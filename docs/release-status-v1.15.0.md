# Chronicle Stack v1.15.0 Release Status

Related: `docs/adr/0034-local-blocker-structured-i18n-contracts.md`, `docs/release-status-v1.14.0.md`

`v1.15.0` is the repository-side local blocker structured-i18n-contract release after the published `v1.14.0` baseline.

- Latest published release: `v1.14.0`
- Current repository-side release target: `v1.15.0`
- Lane scope: auth-boundary and mutation-blocker structured i18n contracts only

## Current repository-side progress

Current `v1.15.0` release progress includes:

- accepted ADR scope for blocker structured i18n contracts
- stable blocker `message_key` fields for auth-boundary and mutation-readiness detail payloads
- stable blocker `summary_key` plus params for auth-boundary and mutation-readiness summaries
- HTML renderer support for preferring structured keys while retaining fallback strings
- smoke/test coverage for explicit blocker presentation-contract fields
- version bump and release-readiness documents for `1.15.0`

## Boundary notes

`v1.15.0` preserves:

- local-first single-operator scope
- read-only derived-surface discipline
- i18n presentation-only boundary
- JSON/CLI authority over blocker meaning and write semantics

`v1.15.0` still must not imply:

- hosted auth or multi-user safety
- translated machine-readable blocker codes
- broader mutation capability
- correctness proof or security certification

