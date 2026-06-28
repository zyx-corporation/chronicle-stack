# Chronicle Stack v1.33.0 Release Notes

Chronicle Stack `v1.33.0` is a local review-target-state-recovery structured-contract release over the published `v1.32.0` baseline.

## Added

- structured `summary_key` fields for review-action `target_state_recovery`
- structured `resolved_queue_reason_key` fields for resolved-queue recovery guidance
- key-first rendering for review-action target-state recovery details

## Kept stable

- local-first fail-closed review-action semantics
- append-only Chronicle record authority
- read-only UI boundaries outside explicit local mutation
