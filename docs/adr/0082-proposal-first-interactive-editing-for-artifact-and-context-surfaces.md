# ADR 0082: Proposal-first interactive editing for artifact and context surfaces

## Status

Accepted

## Context

The interactive UI roadmap requires editable artifact/context surfaces without introducing direct in-place browser writes. Chronicle Stack still treats `.chronicle/chronicle.jsonl` as the primary record, keeps browser affordances local-first, and avoids turning a preview surface into an implicit durable editor.

## Decision

- artifact/context edit intent is recorded first as an append-only Chronicle event
- proposal events carry `review_status=needs_review` so the existing review queue can gate them
- approval remains separate from apply; review acceptance does not mutate the target record automatically
- UI surfaces expose proposal summaries and proposal history as read-only derived views
- CLI remains the explicit apply path for target mutation after review

## Consequences

- edit intent becomes reconstructable without adding in-place mutable browser state
- existing review/audit surfaces can inspect proposal traffic with minimal new infrastructure
- users see a clear boundary between "proposal accepted" and "artifact/context updated"
- a later apply workflow can consume approved proposal events without changing the primary record model
