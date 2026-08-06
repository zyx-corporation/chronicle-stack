# Release Notes v2.3.0

## Added

- `chronicle ui --workspace` for guarded local capture and Chronicle questions
- OpenAI Embeddings and Responses API integration
- rebuildable `.chronicle/runtime/vector.sqlite3` and `graph.sqlite3` projections
- GraphRAG status, rebuild, and ask CLI commands
- source-linked, review-required answer metadata

## Changed

- project and CLI version report `2.3.0`
- default read-only UI, review-mutation UI, and GraphRAG workspace are separately gated
- product and architecture docs distinguish the optional local runtime from hosted query services

## Verification

- Ruff passed for `src/` and `tests/`
- 519 tests passed locally
- `ui-smoke --json` passed in read-only mode without starting an external runtime
- in-app browser verification confirmed both default read-only and workspace presentation with no console errors

## Boundary

- Chronicle JSONL remains authoritative
- SQLite projections are derived and rebuildable
- model calls happen only on explicit rebuild or query actions
- workspace writes require loopback-local mutation, session-token, session-id, and request-id gates
- hosted runtime, daemon execution, managed databases, and multi-user authorization remain outside this release
