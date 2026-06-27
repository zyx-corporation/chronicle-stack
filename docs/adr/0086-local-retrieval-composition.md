# ADR 0086: Local Retrieval Composition Remains a Dry-Run Contract

- Status: Accepted
- Date: 2026-06-27

## Context

Chronicle Stack already exposes local vector hits, derived graph hits, and Chronicle search hits through `chronicle runtime retrieve-plan`. After adding the local graph retrieval adapter, the remaining design question was whether the next step should become a query engine or stay within the record-layer boundary.

## Decision

Chronicle Stack will compose retrieval hits only into a read-only dry-run overlap summary. The composition may highlight shared identifiers across vector, graph, and Chronicle search surfaces, but it will not execute ranking against an external runtime, persist any new derived authority, or imply a hosted GraphRAG engine.

## Consequences

- CLI and UI can show richer handoff context without changing mutation or provider boundaries.
- Operators can review overlap across local surfaces before downstream package or query-engine work.
- Future external GraphRAG/query-engine work remains downstream from Chronicle Stack core.
