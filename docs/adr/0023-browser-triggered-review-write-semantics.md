# ADR-0023: Browser-Triggered Review Write Semantics and Audit Ordering

Status: Accepted  
Date: 2026-06-22  
Scope: Local UI browser-triggered approve/reject/request-changes route semantics  
Related: ADR-0012, ADR-0016, ADR-0019, ADR-0021, ADR-0022, `docs/v1.7-phase-h-gated-gui-mutation-preview.md`, `docs/v1.7-phase-h-auth-ui-design.md`, `docs/v1.7-phase-h-readiness-status.md`

## Context

Chronicle Stack now has a gated local browser-triggered review route family:

```text
POST /api/review-actions/<event_id>/approve
POST /api/review-actions/<event_id>/reject
POST /api/review-actions/<event_id>/request-changes
```

That route family is local-only and explicit-enable only, but it still needs one more architectural rule kept separate from the general mutation-path boundary:

```text
what exactly counts as success or failure when a browser-triggered write attempts
review decision persistence and audit insertion
```

Without this ADR, future work could drift in one of these directions:

- reporting browser-triggered success before both Chronicle append and audit insertion succeed
- treating self-declared reviewer metadata as sufficient write authority
- allowing route-local wording to hide differences between audit failure and decision persistence failure
- letting browser convenience erode CLI-equivalent recovery expectations

The repository already exposes fail-closed response contracts and separate error classes for:

- `audit_insertion_failed`
- `decision_persistence_failed`

This ADR fixes the semantic meaning of those cases.

## Decision

Chronicle Stack adopts the following rule for browser-triggered local review writes:

```text
A browser-triggered review write is successful only if
1. explicit local mutation gating passes,
2. reviewer-context checks pass,
3. review decision persistence succeeds, and
4. audit insertion succeeds.
```

Additionally:

1. Request reviewer metadata (`reviewer_label`, `reviewer_kind`, `session_label`, `ui_intent`) is required local context, but is not sufficient proof of authority on its own.
2. `reviewer_kind=user_declared` remains advisory-only and must not satisfy a write-capable reviewer requirement by itself.
3. Session-gated local mutation requires `session_label`.
4. Browser-triggered review mutation must remain server-side gated even if the UI renders enabled controls.
5. Browser-triggered write responses must preserve CLI-equivalent recovery and inspection commands.

## Write ordering rule

The accepted local browser-triggered write ordering is:

```text
validate route + reviewer context
-> perform review decision persistence attempt
-> perform audit insertion attempt
-> report success only if both durable side effects succeeded
```

If either durable side effect fails:

- the response is non-success
- `rollback_status` remains `fail_closed`
- the UI must not report the review as durably applied
- recovery must point back to explicit CLI or audit inspection commands

## Failure classification

Browser-triggered write failures are classified into two groups:

### Pre-mutation or gate failures

Examples:

- `mutation_disabled`
- `reviewer_label_required`
- `invalid_reviewer_kind`
- `ui_intent_mismatch`
- `authorization_failed`
- `review_target_not_found`
- `review_not_pending`
- `invalid_json`

Meaning:

- no durable mutation may be reported
- no downstream success state may be implied
- failure summary should be human-readable and operator-oriented

### Durable-write-path failures

Examples:

- `audit_insertion_failed`
- `decision_persistence_failed`

Meaning:

- route is still fail-closed
- browser UI must not collapse these into one generic blocked result
- response contracts must surface recovery commands and exact failure class

## Audit and Chronicle ordering semantics

The repository distinguishes:

1. review decision persistence failure
2. audit insertion failure

This ADR preserves that distinction in browser-triggered write semantics:

- audit failure must never be hidden behind a generic mutation-disabled response
- Chronicle append failure after audit insertion must remain visible as a separate failure class
- operators must be able to inspect which side effect failed using explicit recovery commands

This keeps browser-triggered writes aligned with Chronicle’s append-only and audit-visible design.

## Current failure-class mapping

For the current repository slice, the fail-closed browser-triggered write mapping is:

```text
mutation_disabled             = route/gate did not permit mutation attempt
audit_insertion_failed        = audit insertion failed before durable success could be reported
decision_persistence_failed   = audit insertion succeeded, but Chronicle primary-record append failed
```

Operational meaning:

- `mutation_disabled` stays in the pre-mutation / gate-failure family
- `audit_insertion_failed` and `decision_persistence_failed` stay separate durable-write-path failures
- CLI recovery and follow-up hints must continue reflecting that distinction
- future write-path expansion must preserve these classes unless a replacement ADR explicitly redefines them

## UI consequences

The local UI may surface:

- enabled controls only when server-side gating conditions are configured
- reviewer field requirements in read-only readiness surfaces
- accepted reviewer kinds and session requirements in read-only readiness surfaces
- exact rollback status, error code class, failure summary, and CLI recovery hints
- the same fail-closed contract vocabulary across blocked preview, apply response, list-level preview summaries, and detail drilldown surfaces
- thin list-level CLI fallback/follow-up hints before operators open full detail views

The local UI must not imply:

- that enabled controls bypass server-side checks
- that reviewer form input alone grants authority
- that a blocked or partially failed route has durably applied a review decision

## Current repository alignment

The current repository slice now demonstrates this ADR through:

- structured reviewer-context, write-route, and identity-proof contracts on `ui_boundary` and `mutation_readiness`
- structured authorization and target-state contracts on `ui_boundary` and `mutation_readiness`
- shared fail-closed response contracts on blocked preview responses, enabled apply responses, and review-action failure responses
- shared rollback / recovery / follow-up contract visibility in preview panels, result panels, and list-level preview summaries
- separate browser-visible failure classes for `mutation_disabled`, `audit_insertion_failed`, and `decision_persistence_failed`

Current local route-contract vocabulary now also makes explicit:

- server-side authorization checks required before mutation may proceed
- local single-operator authorization scope instead of hosted or multi-user authority claims
- target-state checks required before mutation may proceed
- current queue semantics where `approve` / `reject` resolve the pending target while `request-changes` leaves it pending

The current repository slice still does not claim:

- authenticated GUI mutation
- default-on mutation behavior
- multi-user-safe authority semantics
- multi-user-safe target-state isolation semantics
- stronger transactional guarantees than the local fail-closed contract already described here

## Follow-up boundary

Future mutation expansion should treat this ADR as the semantic floor, not merely historical context.

Before widening mutation capability, follow-up work should keep these invariants aligned:

- reviewer/session proof representation
- fail-closed error-class mapping
- CLI-equivalent recovery visibility
- shared wording across overview, list, preview, and detail surfaces

## Consequences

### Positive

- browser-triggered write semantics stay explicit instead of implicit in route code
- audit failure and Chronicle append failure remain operationally distinguishable
- read-only readiness surfaces can explain future mutation requirements without activating mutation
- CLI-equivalent recovery remains canonical

### Negative / Cost

- route implementation and tests must continue carrying richer failure contracts
- success/failure reporting is more verbose than a simple REST mutation surface
- future write-path changes must keep ADR-0021 and ADR-0023 aligned

## Non-goals

This ADR does not:

- define hosted multi-user auth
- define remote identity proof
- replace CLI review as the baseline mutation path
- claim transactional guarantees beyond the current local fail-closed boundary
- complete Phase F provider execution
