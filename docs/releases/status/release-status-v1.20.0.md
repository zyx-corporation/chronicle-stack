# Chronicle Stack v1.20.0 Release Status

Related: `../../adr/0039-local-retrieval-handoff-and-invocation-plan-structured-i18n.md`, `release-status-v1.19.0.md`

`v1.20.0` is the repository-side local retrieval-handoff-and-invocation-plan structured-i18n release after the published `v1.19.0` baseline.

- Latest published release: `v1.19.0`
- Release URL: `https://github.com/zyx-corporation/chronicle-stack/releases/tag/v1.19.0`
- Current repository-side release target: `v1.20.0`
- Lane scope: retrieval-handoff and invocation-plan structured i18n contracts only

## Current repository-side progress

Planned `v1.20.0` release progress includes:

- accepted ADR scope for retrieval-handoff and invocation-plan structured i18n
- stable `message_key` fields for retrieval-handoff summaries
- stable `hit_counts_summary_key` fields for retrieval-handoff hit-count wording
- stable `message_key` fields for invocation-plan readiness summaries
- stable `provider_summary_key` fields for invocation-plan provider summaries
- HTML renderer support for preferring structured retrieval/invocation fields while retaining fallback strings
- smoke/test coverage for explicit retrieval/invocation presentation-contract fields
- version bump and release-readiness documents for `1.20.0`

## Boundary notes

Planned `v1.20.0` preserves:

- local-first single-operator scope
- read-only derived-surface discipline
- i18n presentation-only boundary
- JSON/CLI authority over retrieval hits, invocation readiness, and downstream commands

`v1.20.0` still must not imply:

- hosted auth or multi-user authority
- translated machine-readable status codes or ids
- broader GUI mutation authority
- correctness proof or security certification
