# ADR 0092: Local Query-Engine Handoff Bundle Stays Descriptive

- Status: Accepted
- Date: 2026-06-27

## Context

After `v1.72.0`, Chronicle Stack could regenerate the adapter skeleton locally, but downstream consumers still needed a repeatable way to receive the current handoff, graph export, and skeleton together as one local bundle.

## Decision

Chronicle Stack will provide a local CLI command that writes a descriptive downstream handoff bundle directory. The bundle includes a handoff JSON file, adapter skeleton JSON file, derived graph export JSON file, and a small bundle manifest. It remains read-only and does not execute any downstream import or query runtime.

## Consequences

- downstream consumers can start from one reproducible handoff directory
- the bundle stays derived and non-authoritative over Chronicle primary records
- Chronicle Stack still does not become a hosted GraphRAG or query-engine runtime
