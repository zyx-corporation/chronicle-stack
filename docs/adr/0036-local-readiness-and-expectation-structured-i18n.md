# ADR-0036: Local Readiness and Expectation Structured i18n

- Status: Accepted
- Date: 2026-06-24

## Context

`v1.16.0` completed and published the local mutation-enablement-check structured-i18n lane.

That lane made mutation enablement checks more explicit, but several adjacent read-only UI payloads still relied on ad hoc presentation strings:

- auth-readiness notices still depended on raw `message` and `scope_note` text
- identity-boundary and identity-assurance summaries still depended on raw descriptive strings
- review-capability notices still exposed only fallback wording
- reviewer-context expectation and note fields still depended on presentation-only prose
- reviewer-enforcement and reviewer-validation summaries still carried unkeyed explanatory text

This left the local UI with a narrower but still repeated i18n drift seam around readiness, expectation, and advisory wording.

Related records:

- `docs/adr/0025-local-ui-i18n-presentation-boundary.md`
- `docs/adr/0035-local-mutation-enablement-check-structured-i18n.md`
- `docs/release-status-v1.16.0.md`
- `docs/v1.16-release-remaining-issues.md`

## Decision

`v1.17.0` begins as the local readiness-and-expectation structured-i18n lane after the published `v1.16.0` release.

This lane may:

1. add stable `message_key` fields for auth-readiness, auth-boundary, identity-boundary, identity-assurance, and review-capability summaries
2. add stable `scope_note_key` fields where readiness notices expose explanatory boundary scope
3. add stable reviewer-context expectation and note keys while preserving readable fallback strings
4. add stable reviewer-enforcement and reviewer-validation summary keys for read-only mutation-readiness surfaces
5. let the embedded HTML renderer prefer these structured keys while retaining fallback strings for degraded consumers
6. extend smoke/test coverage for these explicit readiness and expectation presentation contracts

This lane must not:

- change review mutation gating or write semantics
- make UI wording authoritative over CLI/JSON contracts
- widen hosted-auth claims or multi-user guarantees
- translate machine-readable status codes or persistence identifiers

## Consequences

Repository-side work in `v1.17.0` should keep readiness and expectation surfaces descriptive, local-first, and presentation-only while making rendered wording more deterministic across locales.

This keeps the slice narrow and adjacent:

- structured blocker and enablement-check contracts stay intact
- readiness and expectation notices become more key-driven
- fallback strings remain available for CLI-compatible inspection and degraded renderers

## Rationale

After blockers and enablement checks gained structured i18n contracts, the next repeated drift seam was the surrounding readiness and expectation prose that explains local auth, reviewer identity, and review-route constraints.

Closing that seam improves consistency without changing authority boundaries or implying new mutation capability.
