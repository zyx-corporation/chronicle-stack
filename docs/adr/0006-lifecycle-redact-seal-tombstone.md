# ADR-0006: Lifecycle Model for Redact / Seal / Tombstone

Status: Accepted  
Date: 2026-06-14  
Scope: Chronicle Stack v0.5 and later  
Related: ADR-0001, ADR-0002, ADR-0005, `docs/lifecycle-model.md`

## Context

Chronicle Stack preserves provenance and meaning change over time. However, preserving everything forever creates privacy, legal, safety, and operational risks.

A local-first context system must design forgetting and sealing as first-class concepts.

The challenge is to preserve provenance where safe while avoiding silent rewriting, accidental disclosure, or storing removed secrets in secondary logs.

## Decision

Chronicle Stack will introduce a separate lifecycle event surface for redaction, sealing, expiration, tombstones, and hard-delete markers.

```text
Primary record:
  .chronicle/chronicle.jsonl

Audit record:
  .chronicle/audit.jsonl

Lifecycle record:
  .chronicle/lifecycle.jsonl
```

Lifecycle events do not mutate original records by themselves. They record lifecycle decisions and provide a contract for future doctor/export/context-use behavior.

## Lifecycle Actions

v0.5 defines:

```text
redact
seal
expire
tombstone
hard_delete
```

## Boundary Rules

Lifecycle events must not copy the sensitive content they are meant to remove or hide.

They should record:

```text
lifecycle_id
chronicle_id
created_at
action
target_id
target_kind
actor
reason_class
reason
replacement_ref
visible_detail_level
preserve_tombstone
metadata
```

## Non-goals

This ADR does not implement:

- legal compliance automation
- hard deletion from Git history
- automatic export filtering
- doctor enforcement
- secret manager integration
- irreversible deletion as default

## Consequences

### Positive

- Forgetting and sealing become explicit.
- Original records are not silently rewritten.
- Future export and doctor checks can inspect lifecycle state.
- Redaction/sealing can be audited without copying removed content.

### Negative / Cost

- There is a third JSONL surface to maintain.
- Future readers must understand lifecycle state.
- Hard deletion remains unresolved for Git-backed history.

## RDE Review

### Preserved

- JSONL remains primary.
- Original records are not silently rewritten.
- Provenance remains important.

### Transformed

- Chronicle Stack becomes a system that also designs forgetting and sealing.

### Added

- `LifecycleEvent` model.
- `.chronicle/lifecycle.jsonl` surface.
- `LifecycleStore`.
- `LifecycleService`.

### Unresolved

- CLI surface.
- Doctor checks.
- Export filtering behavior.
- Hard delete implementation.
- Git-backed history interaction.

### Deviation Risks

- Preserving everything despite safety risk.
- Deleting too much and destroying provenance.
- Recording removed secrets inside lifecycle or audit trails.
- Treating lifecycle events as actual deletion enforcement before enforcement exists.
