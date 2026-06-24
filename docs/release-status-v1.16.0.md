# Chronicle Stack v1.16.0 Release Status

Related: `docs/adr/0035-local-mutation-enablement-check-structured-i18n.md`, `docs/release-status-v1.15.0.md`

`v1.16.0` is the published local mutation-enablement-check structured-i18n release after the published `v1.15.0` baseline.

- Latest published release: `v1.16.0`
- Release URL: `https://github.com/zyx-corporation/chronicle-stack/releases/tag/v1.16.0`
- Current repository-side release target: `TBD after v1.16.0 publication`
- Lane scope: mutation enablement check structured i18n contracts only

## Current repository-side progress

Published `v1.16.0` release progress includes:

- accepted ADR scope for mutation enablement check structured i18n
- stable `label_key` and `detail_key` fields for mutation enablement checks
- stable `summary_key` plus params for unsatisfied mutation enablement checks
- HTML renderer support for preferring structured check keys while retaining fallback summaries
- smoke/test coverage for explicit mutation enablement check contracts
- version bump and release-readiness documents for `1.16.0`
- external tag and GitHub Release publication

## Boundary notes

Published `v1.16.0` preserves:

- local-first single-operator scope
- read-only derived-surface discipline
- i18n presentation-only boundary
- JSON/CLI authority over mutation gating meaning and write semantics

Published `v1.16.0` still must not imply:

- hosted auth or multi-user safety
- translated machine-readable check codes
- broader mutation capability
- correctness proof or security certification
