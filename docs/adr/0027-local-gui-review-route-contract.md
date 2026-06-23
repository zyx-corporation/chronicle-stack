# ADR-0027: Local GUI Review Route Contract and Expansion Boundary

- Status: Accepted
- Date: 2026-06-23

## Context

`v1.7.0` completed the local UI observability and review-surface preparation lane while keeping browser mutation explicit-enable, local-only, and fail-closed.

The next release slice needs a narrow boundary for any follow-on local GUI review-route work so that repository planning does not drift into hosted auth, default-on mutation, or hidden runtime claims.

Related records:

- `docs/adr/0018-local-ui-read-only-navigation-boundary.md`
- `docs/adr/0019-local-ui-review-semantics-parity-boundary.md`
- `docs/adr/0021-gated-local-ui-mutation-write-path.md`
- `docs/adr/0023-browser-triggered-review-write-semantics.md`
- `docs/adr/0026-local-reviewer-session-proof-representation.md`
- `docs/v1.7-phase-h-gated-gui-mutation-preview.md`
- `docs/v1.7-phase-f-g-h-remaining-issues.md`

## Decision

`v1.8.0` begins as the local GUI review-route design-hardening and contract-hardening lane after the completed `v1.7.0` release.

Any repository-side work in this lane must preserve the existing route family:

```text
POST /api/review-actions/<event_id>/approve
POST /api/review-actions/<event_id>/reject
POST /api/review-actions/<event_id>/request-changes
```

The route family remains bounded by all of the following invariants:

1. single-operator local use only
2. explicit-enable mutation only
3. fail-closed default behavior
4. CLI-parity-visible recovery and action semantics
5. JSONL-authority-preserving persistence semantics
6. no durable success reported unless decision persistence and audit persistence both succeed

## Consequences

`v1.8.0` repository planning may include:

- route-contract clarification
- mutation-boundary metadata hardening
- reviewer/session proof alignment for local operator flows
- UI/CLI parity refinements for local review mutation previews and results

`v1.8.0` repository planning must not claim:

- hosted or multi-user authentication/authorization
- default-on browser mutation
- hidden background runtime or daemonized review execution
- non-local review operators
- GraphRAG/runtime-provider execution coupling as part of review-route enablement
- durable proof or compliance guarantees beyond current local session metadata boundaries

## Rationale

This boundary keeps the next release coherent: it advances the local GUI review contract without widening Chronicle Stack into a networked or silently stateful mutation product.

It also preserves the already-established rule that the browser surface must remain an explicit local presentation and action shell around Chronicle’s primary JSONL record and CLI-compatible review semantics.
