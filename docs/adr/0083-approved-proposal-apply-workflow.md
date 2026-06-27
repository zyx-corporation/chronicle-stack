# ADR 0083: Approved proposal apply workflow

## Status

Accepted

## Context

`v1.63.0` introduced append-only proposal events for artifact and context edits, but operators still needed a manual, implicit translation from "approved proposal" to "mutated target". That left the proposal/review/apply lane incomplete and made repeatable operator behavior harder to reconstruct.

## Decision

- approved proposals are applied only through explicit CLI commands
- artifact proposals use the normal artifact versioning path when applied
- context proposals use a new append-only Context snapshot with the same `context_id`
- apply commands require an approved review disposition for the proposal target
- apply commands record proposal provenance on the resulting durable event payload so duplicate apply attempts can be rejected

## Consequences

- the proposal/review/apply lane becomes explicit without introducing browser-side in-place editing
- artifact/context durable state still changes through existing append-only Chronicle events
- approved proposals remain inspectable after application, including whether they are `apply_ready` or already `applied`
