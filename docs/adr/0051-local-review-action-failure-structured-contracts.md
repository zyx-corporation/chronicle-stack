# ADR-0051: Local Review Action Failure Structured Contracts

- Status: Accepted
- Date: 2026-06-25

## Context

`v1.31.0` completed the review-warning structured-contract lane.

The adjacent review-action failure payloads still relied on ad hoc prose:

- blocked/error responses exposed raw `message` strings without stable keys
- failure summaries for authorization and durable-write errors exposed raw prose without stable summary keys
- review-action result rendering still read those failure fields as plain text

## Decision

`v1.32.0` begins as the local review-action-failure structured-contract lane after the published `v1.31.0` release.

Repository-side work in this lane will:

1. add stable `message_key` fields for blocked/error review-action payloads
2. add stable `failure_summary_key` plus params where failure summaries are exposed
3. make review-action result rendering prefer structured keys over raw fallback prose
4. extend tests for parser-stage, gate-stage, and durable-write failure payload contracts

## Consequences

- review-action failure payloads stay local-first, fail-closed, and non-authoritative
- UI rendering can localize blocked/error responses without depending on exact fallback prose
- route semantics, status codes, and durable-write rules remain unchanged
