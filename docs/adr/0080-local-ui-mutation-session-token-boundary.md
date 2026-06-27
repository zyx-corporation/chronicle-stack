# ADR-0080: Local UI Mutation Session Token Boundary

- Status: Accepted
- Date: 2026-06-27

## Context

Chronicle Stack already exposed an explicit loopback-local review write route guarded by reviewer metadata, session labels, auth/authz boundary metadata, and fail-closed audit/write semantics.
However, the browser-triggered mutation route still lacked a per-session token boundary, which left the local interactive UI hardening phase incomplete.

## Decision

- browser-triggered review write routes now require a per-session local mutation token
- the token is scoped to the foreground local UI server instance and transported via `X-Chronicle-UI-Mutation-Token`
- token requirements are exposed as route-contract metadata, while direct service-level mutation contracts remain unchanged

## Consequences

- the current interactive UI safety lane is stronger without changing Chronicle primary-record authority
- browser-side review apply routes now require both reviewer/session metadata and a local mutation token
- future interactive UI work can layer richer session hardening on top of this per-session route token
