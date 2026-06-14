# Chronicle Stack Audit Log Model

Status: v0.5 model contract  
Related: #65, [ADR-0005](adr/0005-audit-log-for-derived-operations.md)

## Purpose

The audit log records high-risk derived operations:

```text
export
context_use
reinterpret
```

It exists to preserve the operational provenance around records without confusing later operations with original Chronicle records.

## Storage Surface

Chronicle Stack now distinguishes:

```text
.chronicle/chronicle.jsonl
  primary record surface

.chronicle/audit.jsonl
  operational audit surface
```

The audit log is append-only JSONL, but it is not the primary Chronicle record.

## AuditEvent

Fields:

| Field | Meaning |
|---|---|
| `audit_id` | Audit event identifier. |
| `chronicle_id` | Chronicle ID. |
| `created_at` | Audit event timestamp. |
| `operation` | export / context_use / reinterpret. |
| `actor` | Human, tool, or process name. |
| `purpose` | Purpose supplied by the caller. |
| `target_environment` | local / external / file / package / unknown. |
| `target_layer` | Optional classification layer. |
| `output_classification` | Classification of produced output. |
| `referenced_records` | Referenced event/context/artifact IDs. |
| `source_event_id` | Optional source ChronicleEvent. |
| `result` | info / warning / blocked. |
| `summary` | Human-readable audit summary. |
| `metadata` | String metadata map. |

## Boundary

Audit events should not store sensitive removed content by default.

```text
audit event should record that an operation occurred
audit event should not copy secret payloads unnecessarily
```

## Non-goals

The v0.5 audit log model does not provide:

- cryptographic proof
- external immutable log service
- full identity system
- SIEM integration
- automatic insertion into all existing commands
- retention enforcement

## RDE Review

### Preserved

- JSONL primary record remains unchanged.
- Original records remain distinct from later operations.
- No proof or notarization is claimed.

### Transformed

- Export / context-use / reinterpretation become representable as audit events.

### Added

- AuditEvent model.
- AuditLogStore.
- AuditService.
- `.chronicle/audit.jsonl` surface.

### Unresolved

- Automatic insertion points.
- CLI inspection surface.
- Doctor audit checks.
- Retention/seal integration.

### Deviation Risks

- Storing removed secrets in audit metadata.
- Treating audit logs as tamper-proof.
- Confusing reinterpretation audit with original intent.
