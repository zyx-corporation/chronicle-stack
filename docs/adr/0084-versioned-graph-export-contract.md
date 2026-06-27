# ADR 0084: Versioned graph export contract

## Status

Accepted

## Context

Graph export was already deterministic and derived, but downstream GraphRAG-adjacent consumers still relied on implicit assumptions about incremental consumption and rebuild semantics. We need an explicit contract before adding richer retrieval adapters.

## Decision

- graph export now carries a versioned `export_contract`
- the contract fixes the primary record, derived-only boundary, and non-runtime stance
- the contract also defines incremental expectations in terms of Chronicle events, `event_id`, and event ordering
- consumers may checkpoint incrementally, but full rebuild from `.chronicle/chronicle.jsonl` remains the compatibility baseline

## Consequences

- downstream consumers get a stable machine-readable graph export contract
- GraphRAG-adjacent adapters can state compatibility against a concrete contract version
- Chronicle Stack still avoids embedding a graph runtime, vector runtime, or hosted query engine
