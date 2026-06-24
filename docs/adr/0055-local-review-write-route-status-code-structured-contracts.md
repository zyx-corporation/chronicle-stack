# ADR-0055: Local Review Write-Route Status-Code Structured Contracts

- Status: Accepted
- Date: 2026-06-25

## Context

`v1.35.0` completed the local review-write-route-failure-family structured-contract lane.

The adjacent review write-route status-code contract still relied on ad hoc `when` prose:

- `write_route_contract.status_code_contract[].when` exposed raw fallback text without stable keys
- UI rendering still depended on plain `when` strings in the status-code contract summary
- tests validated literal prose instead of stable localization keys for those contract reasons

## Decision

`v1.36.0` begins as the local review-write-route-status-code structured-contract lane after the published `v1.35.0` release.

Repository-side work in this lane will:

1. add stable `when_key` fields for review write-route status-code contract entries
2. keep fallback `when` prose while making UI rendering prefer structured keys
3. extend tests for boundary and HTML status-code contract rendering
4. preserve current status-code families and fail-closed route semantics

## Consequences

- status-code contract reasons stay local-first, fail-closed, and non-authoritative
- UI rendering can localize status-code reasons without depending on exact fallback prose
- review-route status codes, families, and boundary rules remain unchanged
