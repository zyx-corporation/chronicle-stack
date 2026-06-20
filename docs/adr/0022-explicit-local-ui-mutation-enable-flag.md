# ADR-0022: Explicit Local UI Mutation Enable Flag

Status: Accepted  
Date: 2026-06-20  
Related: ADR-0018, ADR-0019, ADR-0021, `docs/v1.7-phase-h-gated-gui-mutation-preview.md`

## Context

Chronicle Stack now has a concrete local UI review mutation route shape and server-side gating rules.

However, one design question remains critical:

```text
how does an operator cross from read-only preview mode into write-capable local UI mode
without overloading an existing descriptive flag
```

The repository already used:

- `--mutation-capability-flag` as preview intent only
- auth/authz placeholder metadata for readiness visibility
- read-only parity and blocked-route preview surfaces

Reusing `--mutation-capability-flag` as actual write enablement would blur:

```text
preview intent vs actual mutation authority
descriptive readiness vs explicit operator enablement
```

## Decision

Chronicle Stack requires a second, explicit operator opt-in for local UI mutation:

```text
--enable-ui-mutation
```

The local UI may report `mutation_enabled=true` only when all of these hold:

1. `--enable-ui-mutation` is set
2. `--mutation-capability-flag` is set
3. `--auth-mode loopback_local`
4. `--authorization-mode reviewer_declared`

If any condition is missing, the UI remains in preview-only mode and review action routes must fail closed.

## Consequences

### Positive

- Preview intent remains descriptive-only.
- Write enablement becomes an explicit operator decision.
- Tests and docs can distinguish read-only default mode from gated local mutation mode.

### Cost

- Local UI startup becomes slightly more verbose for mutation-capable sessions.
- Two flags must stay synchronized in docs and tests.

## Non-goals

This ADR does not:

- define remote or hosted identity systems
- remove CLI review as the baseline mutation path
- claim multi-user safety beyond current loopback-local assumptions
