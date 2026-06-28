# ADR-0028: Local Reviewer and Session Enforcement Boundary

- Status: Accepted
- Date: 2026-06-23

## Context

`v1.8.0` completed the local GUI review-route contract-hardening lane and fixed:

- explicit action-route family visibility
- explicit CLI-equivalent route semantics
- explicit status-code contract visibility

That release intentionally preserved the current reviewer/session model as a descriptive, local-first proof shape rather than a stronger enforcement model.

The next release lane needs a narrow boundary for how future work may strengthen reviewer/session enforcement without drifting into hosted identity claims, multi-user authority, or default-on browser mutation.

Related records:

- `docs/adr/0021-gated-local-ui-mutation-write-path.md`
- `docs/adr/0023-browser-triggered-review-write-semantics.md`
- `docs/adr/0026-local-reviewer-session-proof-representation.md`
- `docs/adr/0027-local-gui-review-route-contract.md`
- `docs/releases/status/release-status-v1.8.0.md`
- `docs/releases/remaining/v1.8-release-remaining-issues.md`

## Decision

`v1.9.0` begins as the local reviewer/session enforcement-boundary lane after the completed `v1.8.0` release.

Any repository-side work in this lane must preserve all of the following:

1. local single-operator boundary only
2. explicit-enable mutation only
3. fail-closed route behavior
4. CLI-visible recovery and parity semantics
5. Chronicle JSONL authority
6. separation between descriptive proof shape and stronger enforcement claims

The `v1.9.0` lane may strengthen:

- reviewer/session validation consistency
- enforcement wording across UI contract surfaces
- explicit distinction between required local mutation fields and advisory-only reviewer metadata
- boundary-aligned server-side checks for the existing local mutation gate

The `v1.9.0` lane must not claim:

- hosted authentication or authorization
- multi-user-safe authority semantics
- non-local review operators
- default-on browser mutation
- hidden daemonized review execution
- distributed trust or compliance guarantees from local reviewer/session fields alone

## Consequences

`v1.9.0` repository planning may include:

- clarifying enforcement vocabulary in release docs and ADRs
- tightening local reviewer/session boundary wording in UI/readiness surfaces
- aligning future validation or gate checks with the accepted proof representation from ADR-0026

`v1.9.0` repository planning should avoid:

- silently replacing the local proof model with one-off route-local assumptions
- treating `user_declared` metadata as equivalent to a write-capable reviewer kind
- weakening the explicit distinction between descriptive proof visibility and stronger enforcement

## Rationale

This boundary gives Chronicle Stack a narrow, coherent next step after `v1.8.0`: strengthen local reviewer/session enforcement boundaries without widening the product into hosted auth or broader runtime claims.
