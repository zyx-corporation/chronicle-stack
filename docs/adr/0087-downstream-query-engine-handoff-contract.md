# ADR 0087: Downstream Query-Engine Handoff Stays Read-Only

- Status: Accepted
- Date: 2026-06-27

## Context

After local retrieval composition became visible in `v1.67.0`, the next safe question was how Chronicle Stack should prepare downstream query consumers without turning itself into a query engine. Downstream consumers need explicit export and scope cues, but Chronicle core must stay a record layer.

## Decision

Chronicle Stack will expose a `query_engine_handoff` contract as part of retrieval-plan outputs and runtime detail read models. The contract may summarize referenced records, eligible contexts, graph export compatibility, and prohibited assumptions, but it will remain derived, read-only, and non-authoritative over primary Chronicle records.

## Consequences

- Downstream consumers get a stable handoff contract before any import or runtime integration work begins.
- UI and CLI can show next-step export guidance without implying hosted query execution.
- Future consumer import validation remains separate from Chronicle Stack core runtime responsibilities.
