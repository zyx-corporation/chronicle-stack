# Chronicle Stack v1.12.0 Release Status

Related: `docs/adr/0031-local-reviewer-boundary-presentation-drilldown.md`, `docs/release-status-v1.11.0.md`

`v1.12.0` is the published reviewer-boundary presentation-drilldown release after the published `v1.11.0` baseline.

- Latest published release: `v1.12.0`
- Release URL: `https://github.com/zyx-corporation/chronicle-stack/releases/tag/v1.12.0`
- Current repository-side release target: `TBD after v1.12.0 publication`
- Lane scope: local reviewer-boundary presentation/read-model drilldown only

## Current repository-side progress

Published `v1.12.0` release progress includes:

- accepted ADR scope for reviewer-boundary presentation drilldown
- version bump and changelog update for `1.12.0`
- release-readiness, release-notes, and smoke-profile entry points for the lane
- explicit framing that the next slice returns to presentation/read-model improvements after smoke-contract preservation
- read-only reviewer-boundary drilldown summaries across overview, runtime, review, and summary payloads
- HTML-shell visibility for reviewer-boundary drilldown summaries across overview, list, and detail surfaces
- dominant reviewer-boundary state visibility across overview drilldown navigation
- i18n-ready drilldown rendering that formats localized dataset and status labels from structured summary fields
- smoke coverage for reviewer-boundary drilldown summaries across overview, list, and detail surfaces
- editable install, `chronicle --version`, `ruff`, `pytest`, and `ui-smoke` verification
- external tag and GitHub Release publication

## Boundary notes

Published `v1.12.0` preserves:

- local-first single-operator scope
- read-only derived-surface discipline
- i18n presentation-only wording boundary
- JSON/CLI contract authority over reviewer-boundary meaning

Published `v1.12.0` still must not imply:

- hosted auth or multi-user safety
- new reviewer-boundary persistence
- broader mutation capability
- correctness proof or security certification
