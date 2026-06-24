# Chronicle Stack v1.13.0 Release Status

Related: `docs/adr/0032-local-reviewer-boundary-structured-presentation-contracts.md`, `docs/release-status-v1.12.0.md`

`v1.13.0` is the active repository-side reviewer-boundary structured-presentation-contract release lane after the published `v1.12.0` baseline.

- Latest published release: `v1.12.0`
- Current repository-side release target: `v1.13.0`
- Lane scope: local reviewer-boundary structured presentation contracts only

## Current repository-side progress

Current `v1.13.0` repository progress includes:

- accepted ADR scope for reviewer-boundary structured presentation contracts
- release-readiness, release-notes, and smoke-profile entry points for the lane
- standardized drilldown message-template keys and template params across overview, list, and detail payloads
- smoke-contract coverage for explicit drilldown message-template fields

## Boundary notes

Current `v1.13.0` planning must preserve:

- local-first single-operator scope
- read-only derived-surface discipline
- i18n presentation-only wording boundary
- JSON/CLI contract authority over reviewer-boundary meaning

Current `v1.13.0` planning must not claim:

- hosted auth or multi-user safety
- new reviewer-boundary persistence
- broader mutation capability
- correctness proof or security certification
