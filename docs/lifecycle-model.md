# Chronicle Stack Lifecycle Model

Status: v0.5 model contract  
Related: #79, [ADR-0006](adr/0006-lifecycle-redact-seal-tombstone.md)

## Purpose

The lifecycle model records decisions to redact, seal, expire, tombstone, or hard-delete markers for Chronicle records and derived artifacts.

It exists because Chronicle Stack must preserve provenance, but must also support forgetting and sealing where privacy, legal, safety, or user-requested reasons require it.

## Storage Surface

Chronicle Stack distinguishes three JSONL surfaces:

```text
.chronicle/chronicle.jsonl
  primary record surface

.chronicle/audit.jsonl
  derived operation audit surface

.chronicle/lifecycle.jsonl
  redact / seal / tombstone lifecycle surface
```

Lifecycle events are not original records. They are lifecycle decisions about records.

## Lifecycle Actions

| Action | Meaning |
|---|---|
| `redact` | Remove or mask sensitive portions while preserving a safer derived record. |
| `seal` | Remove from ordinary use while preserving a governed trace. |
| `expire` | Mark as expired under retention policy. |
| `tombstone` | Preserve only a deletion/sealing marker. |
| `hard_delete` | Mark intent or fact of irreversible deletion. |

## LifecycleEvent

Fields:

| Field | Meaning |
|---|---|
| `lifecycle_id` | Lifecycle event identifier. |
| `chronicle_id` | Chronicle ID. |
| `created_at` | Lifecycle event timestamp. |
| `action` | redact / seal / expire / tombstone / hard_delete. |
| `target_id` | Target record or artifact ID. |
| `target_kind` | event / context / artifact / decision / audit / other. |
| `actor` | Human, tool, or process name. |
| `reason_class` | privacy / legal / safety / secret / user_request / retention / error_correction / other. |
| `reason` | Human-readable reason. Do not store removed secrets here. |
| `replacement_ref` | Optional reference to redacted replacement. |
| `visible_detail_level` | full / summary_only / tombstone_only / hidden. |
| `preserve_tombstone` | Whether a tombstone should remain visible. |
| `metadata` | String metadata map. |

## Boundary

Lifecycle events must not copy the content they are meant to hide, seal, or remove.

```text
lifecycle event records the decision
lifecycle event does not by itself rewrite original history
lifecycle event must not store removed secrets
```

## Non-goals

The v0.5 lifecycle model does not provide:

- legal compliance automation
- hard deletion from Git history
- automatic export filtering
- doctor enforcement
- secret manager integration
- irreversible deletion as default

## Relationship to Other v0.5 Work

Lifecycle events prepare later work:

- Doctor checks for sealed or unredacted records.
- Security-aware export profiles.
- Audit log retention rules.
- Encrypted store migration policy.
- Context-use dry-run filtering.

## RDE Review

### Preserved

- JSONL primary record remains unchanged.
- Original records are not silently rewritten.
- Provenance remains important.

### Transformed

- Chronicle Stack gains a first-class forgetting and sealing surface.

### Added

- LifecycleEvent model.
- LifecycleStore.
- LifecycleService.
- `.chronicle/lifecycle.jsonl` surface.

### Unresolved

- CLI surface.
- Doctor checks.
- Export filtering behavior.
- Hard delete implementation.
- Git-backed history interaction.

### Deviation Risks

- Preserving everything despite safety risk.
- Deleting too much and destroying provenance.
- Recording removed secrets in lifecycle metadata.
- Treating lifecycle events as deletion enforcement before enforcement exists.
