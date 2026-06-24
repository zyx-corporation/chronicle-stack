# Chronicle Stack v1.12.0 Release Status

Related: `docs/adr/0031-local-reviewer-boundary-presentation-drilldown.md`, `docs/release-status-v1.11.0.md`

`v1.12.0` is the active repository-side reviewer-boundary presentation-drilldown release lane after the published `v1.11.0` baseline.

- Latest published release: `v1.11.0`
- Current repository-side release target: `v1.12.0`
- Lane scope: local reviewer-boundary presentation/read-model drilldown only

## Current repository-side progress

Current `v1.12.0` repository progress includes:

- accepted ADR scope for reviewer-boundary presentation drilldown
- release-readiness, release-notes, and smoke-profile entry points for the lane
- explicit framing that the next slice returns to presentation/read-model improvements after smoke-contract preservation
- read-only reviewer-boundary drilldown summaries across overview, runtime, review, and summary payloads
- HTML-shell visibility for reviewer-boundary drilldown summaries across overview, list, and detail surfaces
- smoke coverage for reviewer-boundary drilldown summaries across overview, list, and detail surfaces

## Boundary notes

Current `v1.12.0` planning must preserve:

- local-first single-operator scope
- read-only derived-surface discipline
- i18n presentation-only wording boundary
- JSON/CLI contract authority over reviewer-boundary meaning

Current `v1.12.0` planning must not claim:

- hosted auth or multi-user safety
- new reviewer-boundary persistence
- broader mutation capability
- correctness proof or security certification
