# ADR-0030: Local Reviewer Boundary Smoke Contract

- Status: Accepted
- Date: 2026-06-24

## Context

`v1.10.0` completed the local reviewer-boundary observability lane and published the resulting release.

That release made reviewer-boundary summaries, badges, counts, and slice/filter navigation easier to inspect in the local UI, but the read-only smoke surface still focuses mostly on broader auth, mutation, detail, and HTML continuity checks.

The next narrow repository-side slice should keep Chronicle local-first and read-only while tightening smoke coverage around the already-accepted reviewer-boundary contract.

Related records:

- `docs/adr/0025-local-ui-i18n-presentation-boundary.md`
- `docs/adr/0028-local-reviewer-session-enforcement-boundary.md`
- `docs/adr/0029-local-reviewer-boundary-observability.md`
- `docs/release-status-v1.10.0.md`

## Decision

`v1.11.0` begins as the local reviewer-boundary smoke-contract lane after the published `v1.10.0` release.

This lane may:

1. extend read-only `chronicle ui-smoke` checks to confirm reviewer-boundary overview summaries
2. confirm reviewer-boundary list-row statuses across runtime, review, and summary surfaces
3. confirm reviewer-boundary detail summaries remain present in derived detail payloads
4. confirm HTML-shell continuity for reviewer-boundary navigation helpers and panel markers

This lane must not:

- widen browser mutation capability
- add new persistence for reviewer-boundary smoke data
- treat smoke checks as correctness proof, security certification, or hosted identity evidence
- replace JSON payload contracts as the authoritative source of reviewer-boundary meaning

## Consequences

Repository-side work in `v1.11.0` should keep all reviewer-boundary smoke checks derived from existing local UI payloads and HTML shell output.

This raises confidence that reviewer-boundary observability remains intact as adjacent UI work evolves, without widening the product beyond its accepted local-only scope.

## Rationale

This is the narrowest useful follow-on to `v1.10.0`: preserve the new reviewer-boundary surface with explicit smoke coverage before growing the UI contract further.
