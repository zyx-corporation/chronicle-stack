# ADR-0077: Local Response-Metadata and Runtime-Config Detail Localization

- Status: Accepted
- Date: 2026-06-27

## Context

`v1.57.0` localized reviewer-context detail lines.
The adjacent provider-response metadata and runtime-config / runtime-boundary detail panels still exposed raw finish-reason, provider-status, source, provider-kind, and boolean values, leaving the current detail-line i18n cleanup phase incomplete.

## Decision

- provider-response metadata contracts now expose key-first finish-reason and provider-status summaries
- runtime-config contracts now expose key-first source, provider-kind, and boolean summaries for detail rendering
- runtime-boundary detail panels now prefer explicit boolean summary strings instead of raw booleans

## Consequences

- the current response-metadata / runtime-config detail localization phase is complete for the read-only local UI slice
- raw fallback values remain available if a summary key is absent or a future status is unknown
- local-first, read-only, presentation-only boundaries remain unchanged
