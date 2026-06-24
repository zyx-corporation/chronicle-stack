# ADR-0050: Local Review Warning Structured Contracts

- Status: Accepted
- Date: 2026-06-25

## Context

`v1.30.0` completed the mutation-summary structured-contract lane.

The adjacent review warning surfaces still relied on ad hoc prose:

- `review_capability.warning_details` exposed raw messages without stable keys
- overview `warning_summaries` exposed fallback labels/messages without structured label/message contracts
- overview badge rendering still depended on raw warning labels instead of locale-stable keys

## Decision

`v1.31.0` begins as the local review-warning structured-contract lane after the published `v1.30.0` release.

Repository-side work in this lane will:

1. add stable `message_key` fields for `review_capability.warning_details`
2. add stable `label_key` and `message_key` fields for overview `warning_summaries`
3. add stable `summary_key` plus params for warning-summary count wording
4. extend smoke/test coverage for overview, list, detail, and review-action warning payloads

## Consequences

- warning payloads stay descriptive, local-first, and non-authoritative
- UI rendering can prefer key-driven warning wording over raw fallback prose
- warning codes, priorities, and review semantics remain unchanged
