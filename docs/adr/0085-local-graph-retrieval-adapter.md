# ADR 0085: Local graph retrieval adapter

## Status

Accepted

## Context

After `v1.65.0`, Chronicle Stack had a versioned graph export contract but still lacked a concrete local adapter that consumed it for retrieval dry-runs. The next safe step is to use the derived graph export locally without widening runtime claims into a GraphRAG engine.

## Decision

- add a local graph retrieval adapter that reads the derived graph export
- rank matches with deterministic token overlap plus small adjacency bonuses
- surface adapter metadata through `runtime retrieve-plan` and `chronicle graph retrieve`
- keep the adapter local-first, read-only, and rebuild-compatible with Chronicle events

## Consequences

- retrieval dry-runs gain a concrete graph-backed local adapter without introducing a graph runtime
- downstream adapter behavior becomes inspectable through explicit contract and hit metadata
- Chronicle Stack still stops short of hosted query engines, embeddings, or external retrieval services
