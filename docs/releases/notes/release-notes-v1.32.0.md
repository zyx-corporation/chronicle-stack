# Chronicle Stack v1.32.0 Release Notes

Chronicle Stack `v1.32.0` is a local review-action-failure structured-contract release over the published `v1.31.0` baseline.

## Added

- structured `message_key` fields for blocked/error review-action payloads
- structured `failure_summary_key` fields for review-action failure summaries
- key-first rendering for review-action result panels

## Kept stable

- local-first fail-closed review-action semantics
- append-only Chronicle record authority
- read-only UI boundaries outside explicit local mutation
