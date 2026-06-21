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

## UI consequences

The local UI may surface:

- enabled controls only when server-side gating conditions are configured
- reviewer field requirements in read-only readiness surfaces
- accepted reviewer kinds and session requirements in read-only readiness surfaces
- exact rollback status, error code class, failure summary, and CLI recovery hints

The local UI must not imply:

- that enabled controls bypass server-side checks
- that reviewer form input alone grants authority
- that a blocked or partially failed route has durably applied a review decision

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
