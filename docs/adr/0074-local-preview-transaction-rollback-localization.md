# ADR-0074: Local Preview Transaction and Rollback Localization

- Status: Accepted
- Date: 2026-06-26

## Context

`v1.54.0` localized compact write-route field, check, and status badges.
The remaining compact `rollback=`, `transaction=`, and `durable-on-failure=` badges still rendered raw internal values even though success and failure contracts were already the canonical structured source for these states.

## Decision

- success contracts now expose key-first localized transaction and rollback summaries
- failure contracts now expose key-first localized rollback and durable-on-failure summaries
- preview and detail surfaces reuse the same structured success/failure summary fields

## Consequences

- the remaining compact success/failure state badges become i18n-ready
- detail panels stay aligned with compact badge wording
- local-first, read-only, presentation-only boundaries remain unchanged
