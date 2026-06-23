# ADR-0029: Local Reviewer Boundary Observability

- Status: Accepted
- Date: 2026-06-23

## Context

`v1.9.0` completed the local reviewer/session enforcement-boundary lane and published the resulting release.

That lane made reviewer enforcement and validation-gate contracts explicit in JSON payloads and mutation-readiness summaries, but the overview surface still requires drilling into detail payloads to understand how those boundary states are distributed across runtime records, review queue rows, and summary jobs.

The next repository-side slice should stay local-first, read-only by default, and presentation-oriented while improving observability of the already-accepted reviewer boundary contract.

Related records:

- `docs/adr/0025-local-ui-i18n-presentation-boundary.md`
- `docs/adr/0026-local-reviewer-session-proof-representation.md`
- `docs/adr/0028-local-reviewer-session-enforcement-boundary.md`
- `docs/release-status-v1.9.0.md`

## Decision

`v1.10.0` begins as the local reviewer-boundary observability lane after the published `v1.9.0` release.

This lane may:

1. aggregate reviewer enforcement and reviewer validation-gate statuses across overview-visible UI datasets
2. surface those aggregates in read-only overview panels
3. expose existing row-level reviewer boundary statuses directly in list surfaces
4. keep presentation strings compatible with the current i18n-ready UI label boundary

This lane must not:

- widen browser mutation capability
- introduce hosted identity or multi-user authority claims
- treat row-level badges as stronger proof than the underlying local boundary contracts
- replace CLI or JSON detail surfaces as the authoritative contract record

## Consequences

Repository-side work in `v1.10.0` should prefer derived summaries over new persistence, and should keep all reviewer-boundary aggregates rebuildable from existing Chronicle and UI payload state.

The overview surface becomes faster to audit for local operators while preserving the current fail-closed, local-only mutation boundary.

## Rationale

This keeps the next slice narrow and useful: make accepted reviewer-boundary contracts easier to see without changing what those contracts mean.
