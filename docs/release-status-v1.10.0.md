# Chronicle Stack v1.10.0 Release Status

Related: `docs/adr/0029-local-reviewer-boundary-observability.md`, `docs/release-status-v1.9.0.md`

`v1.10.0` is the active repository-side release lane after the published `v1.9.0` baseline.

- Latest published release: `v1.9.0`
- Current repository-side release target: `v1.10.0`
- Lane scope: local reviewer-boundary observability only

## Current repository-side progress

Current `v1.10.0` repository progress includes:

- accepted ADR scope for reviewer-boundary observability
- overview aggregation for reviewer enforcement and validation-gate states
- read-only list-surface badges for existing reviewer boundary row statuses
- direct overview-to-list slice/filter navigation for reviewer-boundary statuses
- release-readiness, release-notes, and smoke-profile entry points for the lane
- i18n-ready presentation routing for reviewer-boundary labels and metrics
- version bump and changelog update for `1.10.0`

## Boundary notes

Current `v1.10.0` planning must preserve:

- local-first single-operator scope
- explicit-enable mutation boundary
- fail-closed route semantics
- JSON/CLI contract authority over presentation summaries

Current `v1.10.0` planning must not claim:

- hosted auth or multi-user safety
- new persistence for reviewer observability aggregates
- broader runtime execution guarantees
