# ADR-0063: Local Review Route Summary Structured Details

- Status: Accepted
- Date: 2026-06-25

## Context

`v1.43.0` aligned possible-error detail rendering for review failure contracts.
The adjacent write-route action-route and CLI-equivalent lines still used renderer-side concatenation even though they were stable read-only route descriptors.

## Decision

- each review write-route entry now carries stable path and CLI summary keys
- the write-route detail renderer formats route and CLI lines from those keys first

## Consequences

- route-descriptor wording becomes i18n-ready without changing any route shape
- local fail-closed review semantics and CLI parity remain unchanged
