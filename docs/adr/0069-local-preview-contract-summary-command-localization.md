# ADR-0069: Local Preview-Contract Summary Command Localization

- Status: Accepted
- Date: 2026-06-25

## Context

`v1.49.0` aligned package-readiness suggested commands with structured command details.
The adjacent compact preview-contract summary still rendered `recovery=` and `follow-up=` badges from raw command strings even when structured command summaries were already available.

## Decision

- compact preview-contract summaries now prefer structured recovery and follow-up command summaries
- copy buttons continue to target the original raw commands while the visible badge text becomes key-first

## Consequences

- compact preview badges become i18n-ready without changing any command semantics
- command copy behavior and fail-closed preview boundaries remain unchanged
