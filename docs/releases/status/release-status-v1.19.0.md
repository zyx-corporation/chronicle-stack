# Chronicle Stack v1.19.0 Release Status

Related: `../../adr/0038-local-navigation-provider-response-and-runtime-preview-structured-i18n.md`, `release-status-v1.18.0.md`

`v1.19.0` is the repository-side local navigation-provider-response-runtime-preview structured-i18n release after the published `v1.18.0` baseline.

- Latest published release: `v1.18.0`
- Release URL: `https://github.com/zyx-corporation/chronicle-stack/releases/tag/v1.18.0`
- Current repository-side release target: `v1.19.0`
- Lane scope: navigation, provider-response, and runtime-preview structured i18n contracts only

## Current repository-side progress

Planned `v1.19.0` release progress includes:

- accepted ADR scope for navigation, provider-response, and runtime-preview structured i18n
- stable `label_key` fields for related-link navigation labels
- stable `message_key` fields for provider-response summaries
- stable `title_key` and `title_params` fields for runtime-preview titles
- HTML renderer support for preferring structured navigation/provider/runtime fields while retaining fallback strings
- smoke/test coverage for explicit navigation/provider/runtime presentation-contract fields
- version bump and release-readiness documents for `1.19.0`

## Boundary notes

Planned `v1.19.0` preserves:

- local-first single-operator scope
- read-only derived-surface discipline
- i18n presentation-only boundary
- JSON/CLI authority over navigation targets and runtime semantics

`v1.19.0` still must not imply:

- hosted auth or multi-user safety
- translated machine-readable status codes or ids
- broader GUI mutation authority
- correctness proof or security certification
