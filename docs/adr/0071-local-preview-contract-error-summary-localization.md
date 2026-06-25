# ADR-0071: Local Preview-Contract Error-Summary Localization

- Status: Accepted
- Date: 2026-06-25

## Context

`v1.51.0` aligned package-handoff preview command hints with structured command details.
The adjacent compact preview-contract summary still rendered `errors=` from raw error codes even though structured possible-error details were already available.

## Decision

- compact preview-contract summaries now prefer structured possible-error details
- fallback to raw error codes remains in place when structured detail is unavailable

## Consequences

- compact `errors=` badges become i18n-ready without changing any preview semantics
- existing fail-closed behavior and error payload contracts remain unchanged
