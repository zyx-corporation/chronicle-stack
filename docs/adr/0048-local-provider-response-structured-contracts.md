# ADR-0048: Local Provider Response Structured Contracts

- Status: Accepted
- Date: 2026-06-24

## Context

`v1.28.0` completed the package-readiness-detail structured-contract lane.

The adjacent provider response metadata summary still lacked a complete structured contract:

- provider response summary exposed `message_key` but no stable counts summary key
- provider response summary lacked a stable derived/read-only boundary note key
- smoke/test coverage did not yet enforce a structured contract for response metadata list-row summaries

## Decision

`v1.29.0` begins as the local provider-response structured-contract lane after the published `v1.28.0` release.
