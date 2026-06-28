# ADR-0033: Local Reviewer Boundary Derived Fallback Copy

- Status: Accepted
- Date: 2026-06-24

## Context

`v1.13.0` completed and published the local reviewer-boundary structured-presentation-contract lane.

That lane standardized drilldown message-template keys and params across overview, list, and detail payloads and extended smoke coverage for those explicit presentation fields.

After publication, the next narrow repository-side slice should keep the same reviewer-boundary meaning and read-only scope while reducing fallback-copy drift inside the payload itself.

The current local UI already exposes structured template keys, params, and machine-readable reviewer-boundary facts, but fallback `message` and `fact_line` strings can still drift if they are authored independently from the template contract.

Related records:

- `docs/adr/0025-local-ui-i18n-presentation-boundary.md`
- `docs/adr/0032-local-reviewer-boundary-structured-presentation-contracts.md`
- `docs/releases/status/release-status-v1.13.0.md`
- `docs/releases/remaining/v1.13-release-remaining-issues.md`

## Decision

`v1.14.0` begins as the local reviewer-boundary derived-fallback-copy lane after the published `v1.13.0` release.

This lane may:

1. derive reviewer-boundary fallback message and fact-line copy from shared structured contracts
2. distinguish row-detail versus overview-dominant drilldown variants explicitly in payloads
3. extend smoke and test coverage where those read-only fallback-copy contracts become explicit

This lane must not:

- change reviewer-boundary meaning or persistence
- widen browser mutation capability
- claim hosted identity or multi-user authority
- treat derived fallback copy as stronger proof than the underlying JSON/CLI contracts

## Consequences

Repository-side work in `v1.14.0` should keep reviewer-boundary drilldown payloads derived from existing local UI state while making fallback copy deterministic and variant-aware.

This keeps the slice narrow and useful: less wording drift across payload surfaces without changing Chronicle record authority or fail-closed semantics.

## Rationale

`v1.12.0` improved reviewer-boundary drilldown visibility, and `v1.13.0` standardized the presentation contract.

The next sensible step is to make fallback copy itself derived from that contract so payload-level wording stays aligned even outside the HTML renderer.
