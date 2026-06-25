# ADR-0060: Local Overview Failure-Family Structured Rendering

- Status: Accepted
- Date: 2026-06-25

## Context

`v1.40.0` aligned review authorization action-matrix rows across the write-route detail and overview mutation-readiness panels.
The adjacent overview mutation-readiness failure-family list still rendered with presentation-only concatenation, even though the underlying rows already carried stable summary keys.

## Decision

- the overview mutation-readiness panel renders failure-family rows from `summary_key` first
- fallback local summary text remains available for fail-closed read-only rendering

## Consequences

- adjacent write-route and overview failure-family wording stay aligned
- no mutation behavior, authority boundary, or hosted-runtime claim changes
