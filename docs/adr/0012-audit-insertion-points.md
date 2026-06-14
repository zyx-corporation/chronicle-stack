# ADR-0012: Audit Insertion Points for Derived Operations

Status: Accepted  
Date: 2026-06-15  
Scope: Chronicle Stack v0.6-alpha and later  
Related: ADR-0005, `docs/audit-insertion-points.md`, #87, #89

## Context

ADR-0005 introduced the audit log for derived operations.

The v0.5 audit model defined:

```text
.chronicle/audit.jsonl
```

as a separate operational audit surface for high-risk derived operations such as:

```text
export
context_use
reinterpret
```

However, v0.5 intentionally did not wire automatic audit insertion into all workflows.

Chronicle Stack now needs a policy for where audit events should be emitted, which layer should emit them, and how failures should be handled.

This must be done without turning audit logs into a false proof system.

## Decision

Chronicle Stack will define audit insertion points before implementing broad automatic audit writes.

Audit insertion will follow these principles:

```text
- audit events are derived operation records
- audit events do not mutate primary Chronicle records
- audit events should minimize sensitive payload copying
- audit logs are not tamper-proof
- audit presence is not correctness proof
- audit presence is not security certification
```

The recommended first implementation target is:

```text
export operation audit insertion for security-aware export profiles
```

## Insertion policy

| Operation family | Initial policy | Default failure mode |
|---|---|---|
| export | record by default once implemented | fail-open with warning |
| context-use dry-run | record by explicit option first | fail-open with warning |
| package generation | record by default once package persistence exists | fail-open with warning |
| reinterpretation | record when workflow exists | fail-open with warning |
| lifecycle decision | lifecycle event first; audit linkage optional | fail-open with warning |

## Layering decision

Audit insertion should be implemented primarily at the service layer.

CLI handlers may expose options, purpose text, warning display, and user-facing policy choices.

Storage-only insertion is not preferred because storage layers often lack operation purpose and target context.

CLI-only insertion is not preferred because non-CLI callers could bypass audit behavior.

## Failure semantics

The initial default audit insertion failure mode is:

```text
fail-open with warning
```

Meaning:

- the primary operation may complete
- the audit failure must be surfaced
- the warning must be classifiable as blocking, tracked separately, or informational

Fail-closed behavior may be introduced later only for explicitly selected high-risk operations and should require a separate ADR or design update.

## Sensitive data minimization

Audit metadata should not copy full sensitive payloads.

Audit events may include:

- identifiers
- counts
- classifications
- policy names
- profile names
- hashes
- result summaries

Audit events should avoid:

- full exported content
- secret payloads
- redacted content
- tokens or credentials
- model-facing package bodies unless separately designed

## Consequences

### Positive

- The audit model gains a clear path toward implementation.
- Export/profile behavior can become observable and reconstructable.
- Failure handling is explicit before broad writes are added.
- Sensitive payload minimization is preserved.

### Negative / Cost

- Implementation must pass operation context into audit insertion.
- Some operations may initially emit warnings rather than fail closed.
- Dry-run audit behavior remains conservative to avoid noisy persistent state.
- Future implementation must keep service and CLI responsibilities aligned.

## Non-goals

This ADR does not provide:

- tamper-proof logging
- notarization
- cryptographic signing
- correctness certification
- security certification
- legal compliance guarantees
- full retention enforcement
- complete audit insertion implementation

## RDE Review

### Preserved

- `.chronicle/chronicle.jsonl` remains the original record surface.
- `.chronicle/audit.jsonl` remains a derived operation surface.
- Audit is observational, not proof.
- Audit does not replace lifecycle records.

### Transformed

- Audit moves from v0.5 model availability to explicit insertion policy.
- Export/profile workflows become the first implementation target.

### Added

- Operation-family insertion policy.
- Service-layer preference.
- Fail-open-with-warning default.
- Sensitive data minimization guidance.

### Unresolved

- Exact implementation shape.
- CLI option names such as `--record-audit`.
- Whether selected high-risk exports should later become fail-closed.
- How audit inspection should appear in CLI.
- Interaction with package persistence once defined.

### Deviation Risks

- Treating audit logs as proof.
- Copying sensitive payloads into audit metadata.
- Making audit mandatory before failure semantics are mature.
- Recording exploratory dry-runs too aggressively.
- Emitting audit events without sufficient purpose or target context.
