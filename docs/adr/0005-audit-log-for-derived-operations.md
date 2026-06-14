# ADR-0005: Audit Log for Derived Operations

Status: Accepted  
Date: 2026-06-14  
Scope: Chronicle Stack v0.5 and later  
Related: ADR-0001, ADR-0002, `docs/audit-log-model.md`

## Context

Chronicle Stack preserves original records and their provenance. However, later operations such as export, model-context use, and reinterpretation also change the operational context around a record.

These operations should be visible, but they must not be confused with original Chronicle records.

## Decision

Chronicle Stack will introduce a separate append-only audit log surface for high-risk derived operations.

```text
Primary record:
  .chronicle/chronicle.jsonl

Audit record:
  .chronicle/audit.jsonl
```

The audit log records facts about operations. It does not become the original record itself.

## Audited Operations

v0.5 defines the following audit operation categories:

```text
export
context_use
reinterpret
```

## Boundary Rules

Audit events must not store redacted or deleted secret content by default.

Audit events should record:

```text
audit_id
chronicle_id
created_at
operation
actor
purpose
target_environment
target_layer
output_classification
referenced_records
source_event_id
result
summary
metadata
```

## Non-goals

This ADR does not implement:

- external immutable audit service
- cryptographic notarization
- SIEM integration
- full identity system
- automatic audit insertion for every operation
- storage of sensitive removed content

## Consequences

### Positive

- Original records remain distinct from later operations.
- Export / context-use / reinterpretation become traceable.
- Issue closure and RDE practice can reference concrete audit surfaces.

### Negative / Cost

- There is a second JSONL surface to maintain.
- Integrations must decide when to record audit events.
- Future doctor checks will need to inspect both primary and audit logs.

## RDE Review

### Preserved

- JSONL remains primary.
- Original records are not mutated by audit logging.
- Audit logging does not claim proof or notarization.

### Transformed

- Derived operations gain a separate provenance surface.

### Added

- `AuditEvent` model.
- `.chronicle/audit.jsonl` path.
- `AuditLogStore`.
- `AuditService`.

### Unresolved

- Automatic insertion points.
- CLI surface.
- Doctor checks for audit log health.
- Audit event retention policy.

### Deviation Risks

- Confusing audit events with original intent.
- Storing sensitive removed content in audit logs.
- Treating audit logs as tamper-proof.
