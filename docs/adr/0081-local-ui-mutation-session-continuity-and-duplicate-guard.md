# ADR-0081: Local UI Mutation Session Continuity and Duplicate Guard

- Status: Accepted
- Date: 2026-06-27

## Context

`v1.61.0` introduced a per-session local mutation token for browser-triggered review write routes.
The next interactive UI hardening gap was continuity rather than mere possession: browser-triggered apply routes still needed explicit local mutation session continuity and duplicate-submit protection.

## Decision

- browser-triggered review write routes now require both `mutation_session_id` and `mutation_request_id`
- the local UI server rejects missing or misaligned mutation sessions before the review write route runs
- each `mutation_request_id` may be used only once per local UI server session

## Consequences

- preview/apply flows now carry explicit local session continuity metadata
- duplicate browser-triggered submissions are fail-closed before durable review work begins
- Chronicle primary-record authority and CLI parity remain unchanged
