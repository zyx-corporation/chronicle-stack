# ADR-0059: Local Review Authorization Action-Matrix Structured Contracts

- Status: Accepted
- Date: 2026-06-25

## Context

`v1.39.0` aligned adjacent target-state action-matrix rendering across write-route detail and overview mutation-readiness panels.
The neighboring `authorization_contract.action_authorization_matrix` still relied on presentation-only concatenation at render time.

## Decision

- each authorization action-matrix row carries a stable `summary_key`
- write-route detail and overview mutation-readiness panels render authorization rows from the key first
- local fallback `summary` text remains present for fail-closed read-only rendering

## Consequences

- adjacent review-write authorization wording stays aligned across both render surfaces
- the local-first single-operator boundary remains explicit without adding hosted or multi-user claims
