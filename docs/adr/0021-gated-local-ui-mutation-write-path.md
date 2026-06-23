# ADR-0021: Gated Local UI Mutation Write-Path Boundary

Status: Accepted  
Date: 2026-06-20  
Scope: Chronicle Stack future local UI approve/reject/request-changes mutation path  
Related: ADR-0016, ADR-0018, ADR-0019, `docs/v1.7-phase-h-auth-ui-design.md`, `docs/v1.7-phase-h-ui-mutation-threat-model.md`, `docs/v1.7-phase-h-readiness-status.md`

## Context

Phase H preparation work now provides broad read-only visibility for:

```text
auth/authz placeholder state
review capability and warning summaries
identity assurance summaries
CLI parity summaries
runtime/review/summary auth-readiness surfaces
```

That visibility is intentionally non-mutating, but it reveals a remaining gap:

```text
what exact boundary must hold before the local UI may execute review mutations
```

Chronicle already established that:

- Chronicle JSONL remains authoritative
- CLI review is the current mutation contract
- local UI wording is descriptive only
- auth/authz readiness visibility is not enforcement
- GUI mutation must not appear through convenience drift

Without a dedicated ADR, future implementation could blur:

```text
preview readiness        vs actual write enablement
reviewer identity hints  vs authenticated reviewer authority
UI action controls       vs audit-worthy mutation execution
parity summaries         vs mutation safety guarantees
```

## Decision

Chronicle Stack adopts the following rule for any future local UI review mutation path:

```text
GUI review mutation may exist only as an explicitly gated command-layer equivalent
that preserves authentication, authorization, audit insertion, and rollback semantics
as first-class write-path requirements.
```

This means:

1. `mutation_enabled` must remain false until a write-capable route design explicitly satisfies this ADR.
2. Any GUI approve/reject/request-changes route must require an authenticated local reviewer context rather than self-declared identity metadata alone.
3. Authorization rules for who may approve / reject / request changes must be explicit and evaluated server-side before mutation logic runs.
4. Every GUI mutation must insert the same audit-worthy review decision semantics expected from the CLI mutation path.
5. GUI mutation must preserve a CLI-equivalent action model so parity remains inspectable rather than hidden behind UI-only behavior.
6. Partial failure behavior must fail closed: no durable review mutation may appear successful unless audit insertion and decision persistence both complete.
7. Read-only readiness/preview surfaces may continue to exist before mutation enablement, but they must not themselves toggle write capability.
8. The current repository slice may describe local single-operator authorization and target-state semantics explicitly, but that description must remain local-only and must not imply multi-user-safe enforcement.

## Boundary

The accepted write-path boundary is:

```text
CLI review command                = current authoritative mutation path
future GUI mutation route         = gated alternate execution surface
authenticated reviewer context    = required precondition
server-side authorization check   = required precondition
audit insertion                   = required mutation side effect
decision persistence              = required mutation side effect
rollback/fail-closed behavior     = required failure semantics
read-only readiness visibility    = descriptive preparation only
```

The future GUI mutation path may describe or expose:

```text
disabled action previews
auth-readiness blockers
CLI-equivalent commands
mutation gating status
read-only parity summaries
```

It may also describe the current local mutation contract as:

```text
authorized reviewer kind      = local_operator only
authorization scope           = local single-operator boundary only
target review status          = needs_review
approve/reject queue result   = resolved and hidden from default pending queue
request-changes queue result  = remains pending until a later resolving decision
```

It must not imply:

```text
that preview readiness enables writes
that self-declared reviewer metadata is sufficient for mutation
that UI-only success without audit insertion is acceptable
that parity summaries replace explicit mutation checks
that write routing may bypass Chronicle JSONL authority
```

## Rationale

This rule keeps the next step honest:

1. Phase H readiness work can culminate in a real write-path design without reusing descriptive metadata as implicit permission.
2. The command layer remains the baseline for what “correct mutation” means.
3. Future GUI mutation can be added incrementally while preserving auditability and fail-closed behavior.
4. The distinction between read-only visibility and mutation authority stays explicit even as the UI becomes more capable.

## Consequences

### Positive

- Future GUI mutation work has a concrete acceptance boundary before routes are implemented.
- Auth/authz design becomes a write-path prerequisite rather than a later polish step.
- Audit insertion remains central rather than optional implementation detail.
- Read-only readiness signals keep their descriptive value without being overloaded as activation controls.

### Negative / Cost

- Future mutation work must coordinate UI, server-side gating, audit logic, and failure semantics together.
- Implementation will be slower than adding simple write endpoints.
- Some existing preview surfaces may need refinement once real mutation routes exist.

## Required Future Pattern

Future Phase H write-path work should follow this rule:

```text
If a change only expands readiness visibility, keep it read-only and inside ADR-0019.
If a change can mutate review state from the UI, satisfy ADR-0021 preconditions before enabling it.
```

Examples that remain outside GUI mutation enablement:

```text
new auth-readiness summaries
additional warning drill-downs
read-only mutation gating status
smoke coverage for descriptive auth surfaces
```

Examples that require explicit ADR-0021 conformance in implementation:

```text
POST approve/reject/request-changes routes
browser-triggered audit insertion
session-backed local reviewer identity enforcement
server-side authorization middleware for GUI review actions
fail-closed rollback for partial GUI review mutation
```

## Non-goals

This ADR does not:

- implement GUI mutation
- define a hosted multi-user review service
- choose a remote identity provider
- replace CLI review as the default mutation path
- treat current placeholder auth metadata as enforcement
- claim shared-machine-safe or multi-user-safe target-state isolation semantics
