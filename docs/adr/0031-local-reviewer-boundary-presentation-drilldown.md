# ADR-0031: Local Reviewer Boundary Presentation Drilldown

- Status: Accepted
- Date: 2026-06-24

## Context

`v1.11.0` completed the local reviewer-boundary smoke-contract lane and published the resulting release.

That lane preserved reviewer-boundary observability with explicit read-only smoke coverage across overview, list, detail, and HTML shell surfaces.

After that preservation step, the next narrow repository-side slice should return to presentation/read-model improvements without changing reviewer-boundary meaning, write authority, or persistence.

The current local UI already exposes reviewer-boundary status values, summaries, counts, and drill-through filters, but local operators still need to move between overview, filtered list, and detail surfaces to reconstruct:

- which reviewer-boundary state matters most right now
- which list slice explains an overview count
- which detail facts explain a row-level badge
- whether the current surface is summary-only, row-level, or detail-level evidence

Related records:

- `docs/adr/0025-local-ui-i18n-presentation-boundary.md`
- `docs/adr/0029-local-reviewer-boundary-observability.md`
- `docs/adr/0030-local-reviewer-boundary-smoke-contract.md`
- `docs/releases/status/release-status-v1.11.0.md`

## Decision

`v1.12.0` begins as the local reviewer-boundary presentation-drilldown lane after the published `v1.11.0` release.

This lane may:

1. improve read-only reviewer-boundary drilldown summaries across overview, list, and detail surfaces
2. make the relationship between overview counts, list slices, and detail facts easier to reconstruct in the UI shell
3. align reviewer-boundary fact-line wording and summary labels with the accepted i18n presentation boundary
4. extend smoke checks only where those read-only presentation/read-model surfaces become explicit

This lane must not:

- widen browser mutation capability
- add hosted identity or multi-user authority claims
- introduce new reviewer-boundary persistence
- treat presentation drilldown summaries as stronger proof than the underlying JSON/CLI contracts

## Consequences

Repository-side work in `v1.12.0` should keep reviewer-boundary drilldown improvements derived from existing local UI payloads, with presentation-only wording layered on top of stable machine-readable state.

This keeps the next slice narrow and useful: easier reconstruction for local operators without changing Chronicle record authority or fail-closed semantics.

## Rationale

`v1.10.0` made reviewer-boundary state easier to see, and `v1.11.0` made it easier to preserve.

The next sensible step is to make that same state easier to follow across overview, list, and detail surfaces before considering broader scope.
