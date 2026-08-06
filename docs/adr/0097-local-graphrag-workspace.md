# ADR-0097: Local GraphRAG workspace with rebuildable databases

## Status

Accepted — 2026-07-13

## Context

The previous UI exposed implementation-oriented read models and placeholder AI indexes. Users could inspect many contracts, but everyday capture, model-backed questions, vector persistence, and graph persistence were not connected as one workflow.

## Decision

- Keep `.chronicle/chronicle.jsonl` as the sole authoritative record.
- Add `.chronicle/runtime/vector.sqlite3` and `.chronicle/runtime/graph.sqlite3` as derived, rebuildable databases.
- Use OpenAI Embeddings for semantic vectors and the Responses API for grounded answers.
- Expand retrieved vector hits by one graph hop before synthesis.
- Mark every generated answer as review-required and return source record IDs.
- Expose writes and model calls only inside the existing loopback/auth/authz/session-token boundary.
- Provide `chronicle ui --workspace` as the user-oriented local entry point; retain read-only `chronicle ui` as the default.

## Consequences

Deleting either SQLite file does not lose Chronicle history; `chronicle runtime graphrag-rebuild` recreates both from JSONL. External calls happen only on explicit rebuild/query actions. This runtime is single-user and foreground-local; it is not a hosted service or multi-user authorization system.
