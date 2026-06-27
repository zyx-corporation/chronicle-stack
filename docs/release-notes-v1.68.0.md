# Release Notes v1.68.0

## Added

- `runtime retrieve-plan --json` now includes a read-only `query_engine_handoff` contract for downstream derived consumers
- runtime detail UI now shows a query-engine handoff preview with export, scope, and prohibited-assumption cues

## Changed

- CLI text output now summarizes query-engine handoff coverage alongside retrieval composition

## Boundary

- Chronicle Stack still does not execute a GraphRAG or hosted query engine
- the new handoff remains derived, read-only, and non-authoritative over `.chronicle/chronicle.jsonl`
