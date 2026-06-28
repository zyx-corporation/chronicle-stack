# Chronicle Stack v1.14.0 Release Status

Related: `../../adr/0033-local-reviewer-boundary-derived-fallback-copy.md`, `release-status-v1.13.0.md`

`v1.14.0` is the published reviewer-boundary derived-fallback-copy release after the published `v1.13.0` baseline.

- Latest published release: `v1.14.0`
- Release URL: `https://github.com/zyx-corporation/chronicle-stack/releases/tag/v1.14.0`
- Current repository-side release target: `TBD after v1.14.0 publication`
- Lane scope: local reviewer-boundary derived fallback copy only

## Current repository-side progress

Published `v1.14.0` release progress includes:

- accepted ADR scope for reviewer-boundary derived fallback copy
- release-readiness, release-notes, and smoke-profile entry points for the lane
- explicit row-detail versus overview-dominant drilldown variants
- version bump and changelog update for `1.14.0`
- deterministic fallback message and fact-line copy derived from structured reviewer-boundary contracts
- smoke-contract coverage for explicit drilldown variant and fallback-copy fields
- editable install, `chronicle --version`, `ruff`, `pytest`, and `ui-smoke` verification
- external tag and GitHub Release publication

## Boundary notes

Published `v1.14.0` preserves:

- local-first single-operator scope
- read-only derived-surface discipline
- i18n presentation-only wording boundary
- JSON/CLI contract authority over reviewer-boundary meaning

Published `v1.14.0` still must not imply:

- hosted auth or multi-user safety
- new reviewer-boundary persistence
- broader mutation capability
- correctness proof or security certification
