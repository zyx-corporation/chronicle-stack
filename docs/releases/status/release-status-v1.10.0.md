# Chronicle Stack v1.10.0 Release Status

Related: `../../adr/0029-local-reviewer-boundary-observability.md`, `release-status-v1.9.0.md`

`v1.10.0` is the published reviewer-boundary observability release after the published `v1.9.0` baseline.

- Latest published release: `v1.10.0`
- Release URL: `https://github.com/zyx-corporation/chronicle-stack/releases/tag/v1.10.0`
- Current repository-side release target: `TBD after v1.10.0 publication`
- Lane scope: local reviewer-boundary observability only

## Current repository-side progress

Published `v1.10.0` release progress includes:

- accepted ADR scope for reviewer-boundary observability
- overview aggregation for reviewer enforcement and validation-gate states
- read-only list-surface badges for existing reviewer boundary row statuses
- direct overview-to-list slice/filter navigation for reviewer-boundary statuses
- release-readiness, release-notes, and smoke-profile entry points for the lane
- i18n-ready presentation routing for reviewer-boundary labels and metrics
- version bump and changelog update for `1.10.0`
- editable install, `chronicle --version`, `ruff`, `pytest`, and `ui-smoke` verification
- external tag and GitHub Release publication

## Boundary notes

Published `v1.10.0` preserves:

- local-first single-operator scope
- explicit-enable mutation boundary
- fail-closed route semantics
- JSON/CLI contract authority over presentation summaries

Published `v1.10.0` still must not imply:

- hosted auth or multi-user safety
- new persistence for reviewer observability aggregates
- broader runtime execution guarantees
