# ADR-0038: Local Navigation, Provider Response, and Runtime Preview Structured i18n

- Status: Accepted
- Date: 2026-06-24

## Context

`v1.18.0` completed the local package-parity-preview structured-i18n lane.

That lane reduced drift across package and preview surfaces, but several adjacent read-only UI seams still depended on ad hoc wording:

- related-link navigation labels still depended on fallback strings
- provider-response summaries still exposed only raw explanatory prose
- runtime-preview titles still depended on fallback titles

This left one more repeated i18n drift seam around navigation and runtime-observability surfaces.

Related records:

- `docs/adr/0025-local-ui-i18n-presentation-boundary.md`
- `docs/adr/0037-local-package-parity-and-preview-structured-i18n.md`
- `docs/releases/status/release-status-v1.18.0.md`
- `docs/releases/remaining/v1.18-release-remaining-issues.md`

## Decision

`v1.19.0` begins as the local navigation-provider-response-runtime-preview structured-i18n lane after the published `v1.18.0` release.

This lane may:

1. add stable `label_key` fields for related-link navigation labels
2. add stable `message_key` fields for provider-response summaries
3. add stable `title_key` and `title_params` fields for runtime-preview titles
4. let the embedded HTML renderer prefer these structured fields while retaining fallback strings
5. extend smoke/test coverage for these explicit navigation and runtime-observability presentation contracts

This lane must not:

- change navigation targets, provider-response semantics, or runtime-record meaning
- make UI wording authoritative over CLI/JSON contracts
- widen hosted-auth or multi-user claims
- translate machine-readable ids, paths, or persisted runtime payloads

## Consequences

Repository-side work in `v1.19.0` should keep navigation and runtime-observability surfaces descriptive, local-first, and presentation-only while making rendered wording more deterministic across locales.

This keeps the slice narrow and adjacent:

- package/parity/preview structured contracts stay intact
- navigation/provider-response/runtime-preview notices become more key-driven
- fallback strings remain available for CLI-compatible inspection and degraded renderers

## Rationale

After package and preview seams gained structured i18n contracts, the next repeated drift seam was the surrounding navigation labels and provider/runtime preview wording reused across the same read-only UI surfaces.

Closing that seam improves consistency without changing write authority or implying new runtime behavior.
