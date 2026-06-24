# ADR-0054: Local Review Write-Route Failure Family Structured Contracts

- Status: Accepted
- Date: 2026-06-25

## Context

`v1.34.0` completed the local review-action-preview-summary structured-contract lane.

The adjacent review write-route contract still relied on ad hoc failure-family prose:

- `write_route_contract.failure_families[].summary` exposed raw fallback text without stable keys
- nested review-action `failure_contract.failure_families[]` exposed family/codes but no stable summary key
- contract rendering still depended on family/codes without localized failure-family summaries

## Decision

`v1.35.0` begins as the local review-write-route-failure-family structured-contract lane after the published `v1.34.0` release.

Repository-side work in this lane will:

1. add stable `summary_key` fields for review write-route failure families
2. add matching `summary_key` fields to nested review-action `failure_contract.failure_families`
3. make write-route and action-contract rendering prefer structured failure-family summaries
4. extend tests for boundary, preview, and failure payload contracts

## Consequences

- failure-family summaries stay local-first, fail-closed, and non-authoritative
- UI rendering can localize failure-family guidance without depending on exact fallback prose
- write-route semantics, status codes, and error families remain unchanged
