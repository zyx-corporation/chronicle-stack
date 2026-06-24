# Chronicle Stack v1.11.0 Release Status

Related: `docs/adr/0030-local-reviewer-boundary-smoke-contract.md`, `docs/release-status-v1.10.0.md`

`v1.11.0` is the repository-side reviewer-boundary smoke-contract release candidate after the published `v1.10.0` baseline.

- Latest published release: `v1.10.0`
- Release URL: `TBD after v1.11.0 publication`
- Current repository-side release target: `v1.11.0`
- Lane scope: local reviewer-boundary smoke contract only

## Current repository-side progress

Current `v1.11.0` repository progress includes:

- accepted ADR scope for reviewer-boundary smoke coverage
- version bump and changelog update for `1.11.0`
- read-only smoke checks for reviewer-boundary overview summaries
- read-only smoke checks for reviewer-boundary list-row statuses
- read-only smoke checks for reviewer-boundary detail summaries
- HTML-shell continuity checks for reviewer-boundary panel/navigation helpers
- release-readiness, release-notes, and smoke-profile entry points for the lane
- reviewer-boundary count-consistency checks between overview aggregates and list-row statuses
- repository-side verification target for editable reinstall, `chronicle --version`, `ruff`, `pytest`, and `ui-smoke`

Repository-side verification now passes for `v1.11.0`, while external tag and GitHub Release publication remain explicit follow-on operator steps.

## Boundary notes

Current `v1.11.0` preserves:

- local-first single-operator scope
- read-only smoke discipline
- derived-surface verification only
- JSON/CLI contract authority over smoke wording

Current `v1.11.0` still must not imply:

- hosted auth or multi-user safety
- new reviewer-boundary persistence
- correctness proof or security certification
