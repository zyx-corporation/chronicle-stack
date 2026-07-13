# ADR-0034: Stage 2 Proposal Surface

- Status: Accepted
- Date: 2026-07-13

## Context

The local UI needs a review-oriented representation without accepting executable UI plugins or gaining mutation powers unavailable to the CLI.

## Decision

Proposal surfaces are declarative, versioned JSON read models with enumerated allowed actions. The local UI renders these models and delegates mutation to the same proposal, review, and apply services used by CLI commands. Mutation requires loopback scope, explicit enablement, configured authentication and authorization, session continuity, request identity, and stale/duplicate checks.

No surface payload contains executable script, and the UI never writes Chronicle stores directly.

## Consequences

- CLI and UI share mutation semantics
- UI rendering can change without changing the persisted proposal contract
- read-only fallback remains available
- new surface actions require command-layer and security review
