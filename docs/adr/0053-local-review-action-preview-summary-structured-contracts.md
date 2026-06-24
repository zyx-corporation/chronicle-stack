# ADR-0053: Local Review Action Preview Summary Structured Contracts

- Status: Accepted
- Date: 2026-06-25

## Context

`v1.33.0` completed the local review target-state-recovery structured-contract lane.

The adjacent review-action preview summary still relied on ad hoc summary strings:

- `action_preview_summary.recovery_summary` exposed a raw fallback string without a stable key
- `action_preview_summary.follow_up_summary` exposed a raw fallback string without a stable key
- preview-shell rendering still read those preview summary fields as plain text

## Decision

`v1.34.0` begins as the local review-action-preview-summary structured-contract lane after the published `v1.33.0` release.

Repository-side work in this lane will:

1. add stable `recovery_summary_key` fields for review-action preview recovery summaries
2. add stable `follow_up_summary_key` fields for review-action preview follow-up summaries
3. make preview-shell rendering prefer structured preview summary keys over raw fallback strings
4. extend tests for runtime, review, and summary preview payload contracts

## Consequences

- review-action preview summaries stay local-first, read-only, and non-authoritative
- UI rendering can localize preview command summaries without depending on exact fallback strings
- preview route semantics and CLI command generation remain unchanged
