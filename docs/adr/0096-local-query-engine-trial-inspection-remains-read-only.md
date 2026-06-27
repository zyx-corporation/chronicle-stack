# ADR 0096: Local Query-Engine Trial Inspection Remains Read-Only

- Status: Accepted
- Date: 2026-06-28

## Context

After `v1.76.0`, Chronicle Stack could record real downstream trial outcomes as `assistant_output` events. However, recorded trials still lacked a dedicated repository-side inspection surface for list/detail review.

## Decision

Chronicle Stack will provide read-only CLI inspection commands for recorded query-engine trial outcomes. These commands only surface previously recorded metadata and do not trigger downstream execution.

## Consequences

- recorded downstream trials become easier to inspect and compare
- escalation decisions can reference an explicit local history
- Chronicle Stack still remains non-executing for downstream query runtimes
