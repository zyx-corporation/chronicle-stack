# Chronicle Stack v1.17.0 Release Status

Related: `docs/adr/0036-local-readiness-and-expectation-structured-i18n.md`, `docs/release-status-v1.16.0.md`

`v1.17.0` is the repository-side local readiness-and-expectation structured-i18n release after the published `v1.16.0` baseline.

- Latest published release: `v1.16.0`
- Release URL: `https://github.com/zyx-corporation/chronicle-stack/releases/tag/v1.16.0`
- Current repository-side release target: `v1.17.0`
- Lane scope: readiness, expectation, and advisory structured i18n contracts only

## Current repository-side progress

Planned `v1.17.0` release progress includes:

- accepted ADR scope for readiness and expectation structured i18n
- stable `message_key` fields for auth-readiness, auth-boundary, identity-boundary, identity-assurance, and review-capability summaries
- stable `scope_note_key` fields for auth/readiness boundary notes
- stable reviewer-context expectation and note keys
- stable reviewer-enforcement and reviewer-validation summary keys
- HTML renderer support for preferring structured readiness and expectation keys while retaining fallback strings
- smoke/test coverage for explicit readiness and expectation presentation-contract fields
- version bump and release-readiness documents for `1.17.0`

## Boundary notes

Planned `v1.17.0` preserves:

- local-first single-operator scope
- read-only derived-surface discipline
- i18n presentation-only boundary
- JSON/CLI authority over readiness meaning and mutation semantics

`v1.17.0` still must not imply:

- hosted auth or multi-user safety
- translated machine-readable status codes
- broader GUI mutation authority
- correctness proof or security certification
