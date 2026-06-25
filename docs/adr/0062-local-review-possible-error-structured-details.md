# ADR-0062: Local Review Possible-Error Structured Details

- Status: Accepted
- Date: 2026-06-25

## Context

`v1.42.0` aligned the review status-code contract with stable structured summaries.
The adjacent failure-contract `possible_error_codes` list still rendered as raw error-code strings in read-only detail panels.

## Decision

- failure contracts now carry `possible_error_details` with stable `message_key` values
- review action detail renderers prefer localized possible-error details and fall back to raw codes only when needed

## Consequences

- failure-contract detail surfaces become more readable without changing the underlying error taxonomy
- local fail-closed review behavior and boundary semantics remain unchanged
