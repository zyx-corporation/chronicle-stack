# ADR 0088: Downstream Import Validation Remains Preview-Only

- Status: Accepted
- Date: 2026-06-27

## Context

After `v1.68.0`, Chronicle Stack could describe a downstream query-engine handoff, but it still lacked a local way to verify that the handoff aligned with the current derived graph export. The next safe step is structural validation only, without actually importing data into any downstream consumer.

## Decision

Chronicle Stack will attach an `import_validation` preview to the query-engine handoff contract. The preview may compare graph export format, contract version, incremental mode, primary-record path, and runtime-boundary flags, but it will not execute any downstream import, query runtime, or persistence.

## Consequences

- Operators can spot contract drift before attempting downstream integration work.
- CLI and UI remain local-first and descriptive.
- Downstream fixtures or import adapters remain future work outside Chronicle Stack core.
