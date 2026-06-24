# Chronicle Stack v1.13.0 Release Status

Related: `docs/adr/0032-local-reviewer-boundary-structured-presentation-contracts.md`, `docs/release-status-v1.12.0.md`

`v1.13.0` is the published reviewer-boundary structured-presentation-contract release after the published `v1.12.0` baseline.

- Latest published release: `v1.13.0`
- Release URL: `https://github.com/zyx-corporation/chronicle-stack/releases/tag/v1.13.0`
- Current repository-side release target: `TBD after v1.13.0 publication`
- Lane scope: local reviewer-boundary structured presentation contracts only

## Current repository-side progress

Published `v1.13.0` release progress includes:

- accepted ADR scope for reviewer-boundary structured presentation contracts
- release-readiness, release-notes, and smoke-profile entry points for the lane
- version bump and changelog update for `1.13.0`
- standardized drilldown message-template keys and template params across overview, list, and detail payloads
- smoke-contract coverage for explicit drilldown message-template fields
- editable install, `chronicle --version`, `ruff`, `pytest`, and `ui-smoke` verification
- external tag and GitHub Release publication

## Boundary notes

Published `v1.13.0` preserves:

- local-first single-operator scope
- read-only derived-surface discipline
- i18n presentation-only wording boundary
- JSON/CLI contract authority over reviewer-boundary meaning

Published `v1.13.0` still must not imply:

- hosted auth or multi-user safety
- new reviewer-boundary persistence
- broader mutation capability
- correctness proof or security certification
