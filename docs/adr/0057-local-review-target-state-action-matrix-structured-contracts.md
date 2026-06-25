# ADR-0057: Local Review Target-State Action Matrix Structured Contracts

- Status: Accepted
- Date: 2026-06-25

## Context

`v1.37.0` aligned the review target-state scope and resolved-behavior notes with stable i18n-ready keys.
However, the `target_state_contract.action_target_matrix` rows still rendered as presentation-only concatenated strings in the local UI.

That left one adjacent part of the same read-only review contract without stable key-based wording.

## Decision

- each `target_state_contract.action_target_matrix` row carries a stable `summary_key`
- each row keeps a fallback `summary` for fail-closed local rendering
- the browser shell formats matrix rows from `summary_key` first, then falls back to `summary`

## Consequences

- review target-state action outcomes remain local-first and read-only
- the UI no longer depends on ad hoc concatenation for action-matrix explanations
- adjacent target-state contract wording can evolve without changing the route or mutation boundary
