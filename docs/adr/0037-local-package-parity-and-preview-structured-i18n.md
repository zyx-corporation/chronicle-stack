# ADR-0037: Local Package, Parity, and Preview Structured i18n

- Status: Accepted
- Date: 2026-06-24

## Context

`v1.17.0` completed the local readiness-and-expectation structured-i18n lane.

That lane made auth/readiness and reviewer-context wording more explicit, but several adjacent read-only UI payloads still depended on ad hoc presentation strings:

- package-readiness summaries still exposed only fallback `message` strings
- retrieval-package handoff previews still exposed only fallback `message` strings
- action-preview summaries still exposed only fallback status prose
- CLI parity summaries still exposed only fallback alignment prose

This left the local UI with one more repeated i18n drift seam around package, parity, and preview explanation surfaces.

Related records:

- `docs/adr/0025-local-ui-i18n-presentation-boundary.md`
- `docs/adr/0036-local-readiness-and-expectation-structured-i18n.md`
- `docs/releases/status/release-status-v1.17.0.md`
- `docs/releases/remaining/v1.17-release-remaining-issues.md`

## Decision

`v1.18.0` begins as the local package-parity-preview structured-i18n lane after the published `v1.17.0` release.

This lane may:

1. add stable `message_key` fields for package-readiness summaries and detail payloads
2. add stable `message_key` fields for retrieval package-handoff preview payloads
3. add stable `message_key` fields for action-preview summaries
4. add stable `message_key` fields for CLI parity summaries
5. let the embedded HTML renderer prefer these structured keys while retaining fallback strings
6. extend smoke/test coverage for these explicit package, parity, and preview presentation contracts

This lane must not:

- change package-review or review-mutation semantics
- make UI wording authoritative over CLI/JSON contracts
- widen hosted-auth or multi-user claims
- translate machine-readable status codes, action ids, or persistence identifiers

## Consequences

Repository-side work in `v1.18.0` should keep package, parity, and preview surfaces descriptive, local-first, and presentation-only while making rendered wording more deterministic across locales.

This keeps the slice narrow and adjacent:

- readiness and expectation structured contracts stay intact
- package/parity/preview notices become more key-driven
- fallback strings remain available for CLI-compatible inspection and degraded renderers

## Rationale

After readiness and reviewer-context seams gained structured i18n contracts, the next repeated drift seam was the surrounding package-preview, CLI-parity, and action-preview prose used across the same read-only review surfaces.

Closing that seam improves consistency without changing write authority or implying new mutation capability.
