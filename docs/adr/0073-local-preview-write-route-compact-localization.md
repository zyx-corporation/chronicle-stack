# ADR-0073: Local Preview Write-Route Compact Localization

- Status: Accepted
- Date: 2026-06-26

## Context

`v1.53.0` localized compact identity-proof badges on preview and mutation summaries.
Adjacent compact write-route badges still rendered raw request fields, transaction steps, checks, and status codes even though the structured write-route contract already provided enough semantics to expose localized summaries.

## Decision

- write-route contracts now expose structured details for request fields, transaction order, authorization checks, and target-state checks
- compact `success-status=` and `blocked-status=` badges now reuse structured status-code summaries
- mutation enablement summaries mirror the localized blocked-status contract

## Consequences

- adjacent compact write-route badges become i18n-ready without changing route behavior
- raw fallback values remain available if structured localized detail is absent
- local-first, read-only, presentation-only boundaries remain unchanged
