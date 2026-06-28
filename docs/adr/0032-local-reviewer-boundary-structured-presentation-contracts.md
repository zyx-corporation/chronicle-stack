# ADR-0032: Local Reviewer Boundary Structured Presentation Contracts

- Status: Accepted
- Date: 2026-06-24

## Context

`v1.12.0` completed and published the local reviewer-boundary presentation-drilldown lane.

That lane made overview, list, and detail drilldown easier to reconstruct and aligned the HTML shell with the accepted i18n presentation boundary.

After publication, the next narrow repository-side slice should keep the same reviewer-boundary meaning and read-only scope while making the payload contract itself more presentation-ready.

The current local UI already exposes structured `message_key`, `fact_line_template_key`, and status/dataset fields for reviewer-boundary drilldown summaries, but some summary rows still carry per-surface English fallback sentences that are more specific than the contract needs to be.

That leaves two avoidable seams:

- smoke and test coverage cannot yet insist on a single structured message-template contract across overview, list, and detail drilldown payloads
- presentation fallback text is still more hand-written per dataset than necessary

Related records:

- `docs/adr/0025-local-ui-i18n-presentation-boundary.md`
- `docs/adr/0031-local-reviewer-boundary-presentation-drilldown.md`
- `docs/releases/status/release-status-v1.12.0.md`
- `docs/releases/remaining/v1.12-release-remaining-issues.md`

## Decision

`v1.13.0` begins as the local reviewer-boundary structured-presentation-contract lane after the published `v1.12.0` release.

This lane may:

1. standardize reviewer-boundary drilldown message templates across overview, list, and detail payloads
2. preserve dataset/status facts as machine-readable fields while moving more presentation wording behind i18n template keys
3. extend smoke and test coverage where those structured read-only presentation contracts become explicit

This lane must not:

- change reviewer-boundary meaning or persistence
- widen browser mutation capability
- claim hosted identity or multi-user authority
- treat presentation template fields as stronger proof than the underlying JSON/CLI contracts

## Consequences

Repository-side work in `v1.13.0` should keep reviewer-boundary drilldown summaries derived from existing local UI payloads while making the presentation contract more uniform and easier to localize.

This keeps the next slice narrow and useful: less per-surface wording drift without changing Chronicle record authority or fail-closed semantics.

## Rationale

`v1.12.0` made reviewer-boundary drilldown easier to follow.

The next sensible step is to make the presentation contract itself more uniform so later UI follow-ons can stay localized, derived, and smoke-verifiable without reintroducing copy drift.
