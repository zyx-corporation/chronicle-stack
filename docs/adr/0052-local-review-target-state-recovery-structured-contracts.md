# ADR-0052: Local Review Target-State Recovery Structured Contracts

- Status: Accepted
- Date: 2026-06-25

## Context

`v1.32.0` completed the local review-action-failure structured-contract lane.

The adjacent `target_state_recovery` payload still relied on ad hoc prose:

- recovery summaries exposed raw `summary` strings without stable keys
- resolved-queue explanations exposed raw `resolved_queue_reason` strings without stable keys
- review-action result rendering still read those recovery fields as plain text

## Decision

`v1.33.0` begins as the local review-target-state-recovery structured-contract lane after the published `v1.32.0` release.

Repository-side work in this lane will:

1. add stable `summary_key` fields for `target_state_recovery` payloads
2. add stable `resolved_queue_reason_key` fields where resolved-queue explanations are exposed
3. make review-action result rendering prefer structured recovery keys over raw fallback prose
4. extend tests for resolved and missing review-target recovery payload contracts

## Consequences

- target-state recovery payloads stay local-first, fail-closed, and non-authoritative
- UI rendering can localize recovery guidance without depending on exact fallback prose
- route semantics, status codes, and CLI recovery commands remain unchanged
