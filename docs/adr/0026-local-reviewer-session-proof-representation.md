# ADR-0026: Local Reviewer and Session Proof Representation

Status: Accepted  
Date: 2026-06-23  
Scope: Representation of reviewer/session proof for gated local UI review mutation  
Related: ADR-0016, ADR-0019, ADR-0021, ADR-0023, `docs/v1.7-phase-h-auth-ui-design.md`, `docs/v1.7-phase-h-readiness-status.md`, `docs/v1.7-phase-f-g-h-remaining-issues.md`

## Context

Phase H now exposes reviewer-context and identity-proof data across:

```text
ui_boundary
mutation_readiness
blocked/apply review responses
review/runtime/summary list rows
detail drilldown surfaces
```

That visibility made one design gap explicit:

```text
what exact reviewer/session proof shape should the local UI and route contracts use
before stronger auth/authz semantics exist
```

Without a dedicated ADR, future work could drift in these ways:

- treating arbitrary reviewer form fields as implicit authority
- changing field requirements between overview/list/detail/apply surfaces
- allowing `user_declared` metadata to look equivalent to a write-capable reviewer kind
- making session labels optional in one surface but required in another

## Decision

Chronicle Stack adopts the following reviewer/session proof representation for the current local UI mutation slice:

```text
reviewer_label   = required local operator attribution field
reviewer_kind    = required reviewer classification field
ui_intent        = required fail-closed route/action match field
session_label    = required only when the local mutation boundary is session-gated
```

Additionally:

1. `reviewer_kind=local_operator` is the only reviewer kind represented as eligible for explicit local GUI mutation in the current slice.
2. `reviewer_kind=user_declared` remains advisory-only metadata and must never satisfy a write-capable reviewer requirement by itself.
3. `session_boundary_status` must be represented explicitly as `required` or `optional`.
4. `expectation_summary`, field notes, and authority notes may explain the current slice, but they must not imply authenticated authority.
5. `identity_proof_contract` must expose the same required identity fields as the reviewer-context contract so overview/list/detail/apply surfaces stay aligned.

## Accepted representation

The accepted descriptive proof shape is:

```text
required_fields
effective_required_fields
accepted_reviewer_kinds
required_reviewer_kinds_for_mutation
advisory_only_reviewer_kinds
session_boundary_status
session_label_required
reviewer_label_pattern
session_label_pattern
ui_intent_required
```

Supporting descriptive fields may include:

```text
expectation_summary
authority_note
reviewer_label_note
reviewer_kind_note
session_note
ui_intent_note
proof_note
```

## Boundary

This representation means:

- reviewer/session proof is currently a local contract shape, not a hosted identity guarantee
- field presence and validation are necessary for the current gated write path, but not sufficient proof of broader authority
- the same proof shape should appear in read-only readiness surfaces and write-response contracts
- stronger auth/authz layers may refine enforcement later, but should not silently replace this shape with route-local one-offs

This representation does not mean:

- local reviewer metadata is equivalent to authenticated multi-user identity
- session labels imply cross-process or distributed trust
- the UI may infer authority from descriptive proof fields alone

## UI consequences

The local UI may surface:

- reviewer field requirements before mutation is enabled
- session-label requirements when session-gated local mutation is configured
- accepted vs advisory-only reviewer kinds
- expectation summaries and proof notes in overview/list/detail/apply surfaces

The local UI must not surface:

- conflicting reviewer/session requirements between preview and apply paths
- wording that suggests `user_declared` is enough for write authority
- proof fields without explicit indication that they remain local/descriptive in the current slice

## Current repository alignment

The current repository slice now demonstrates this ADR through:

- `reviewer_context_requirements` and `identity_proof_contract` on `ui_boundary` and `mutation_readiness`
- shared reviewer/session expectation wording on blocked/apply responses and detail drilldown surfaces
- list/detail/readiness surfaces that expose the same accepted reviewer kinds, session boundary status, and field requirements
- route contracts that keep reviewer/session proof aligned with explicit authorization checks and explicit target-state checks

The current repository slice still does not claim:

- hosted reviewer identity
- multi-user-safe authority semantics
- stronger server-side authorization than the current local single-operator boundary
- that reviewer/session proof fields alone define pending/resolved target-state semantics without the separate target-state contract

## Consequences

### Positive

- reviewer/session requirements stay stable across overview, list, detail, and apply surfaces
- future auth/authz expansion has a known descriptive proof shape to extend rather than replace implicitly
- tests and smoke coverage can validate one shared reviewer/session contract instead of many route-local variants

### Negative / Cost

- some wording remains verbose because the current slice favors explicitness over convenience
- future stronger identity models must preserve or intentionally migrate this proof shape

## Non-goals

This ADR does not:

- define hosted authentication
- define remote identity proof
- make `user_declared` write-capable
- complete browser-triggered authorization semantics beyond the current local boundary
