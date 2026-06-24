# ADR-0056: Local Review Target-State Note Structured Contracts

- Status: Accepted
- Date: 2026-06-25

## Context

`v1.36.0` completed the local review-write-route-status-code structured-contract lane.

The adjacent review target-state contract still relied on ad hoc note prose:

- `target_state_contract.scope_note` exposed raw fallback text without a stable key
- `target_state_contract.resolved_behavior_note` exposed raw fallback text without a stable key
- write-route rendering did not localize those target-state notes explicitly

## Decision

`v1.37.0` begins as the local review-target-state-note structured-contract lane after the published `v1.36.0` release.

Repository-side work in this lane will:

1. add stable keys for `target_state_contract.scope_note`
2. add stable keys for `target_state_contract.resolved_behavior_note`
3. make write-route rendering prefer structured target-state note keys
4. extend tests for boundary payloads and HTML rendering

## Consequences

- target-state notes stay local-first, read-only, and non-authoritative
- UI rendering can localize target-state guidance without depending on exact fallback prose
- target-state checks, status codes, and route semantics remain unchanged
