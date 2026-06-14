# Audit Insertion Points

Status: Draft for v0.6-alpha  
Related: ADR-0005, ADR-0012, #87, #89

## Purpose

This document defines where Chronicle Stack should emit audit events for derived or high-risk operations.

v0.5 introduced the audit log model and `.chronicle/audit.jsonl` surface. v0.6-alpha defines the insertion policy before automatic audit writes are implemented.

The goal is to make operational provenance visible without confusing audit records with primary Chronicle records or proof of correctness.

## Surfaces

Chronicle Stack separates three important surfaces:

```text
.chronicle/chronicle.jsonl
  original record surface

.chronicle/audit.jsonl
  derived operation audit surface

.chronicle/lifecycle.jsonl
  lifecycle decision surface
```

Audit insertion must not mutate `.chronicle/chronicle.jsonl`.

## Insertion policy summary

| Operation family | Initial policy | Default failure mode | Notes |
|---|---|---|---|
| export | record by default once implemented | fail-open with warning | export remains a derived projection |
| context-use dry-run | record by explicit option first | fail-open with warning | avoids turning every check into persistent state too early |
| package generation | record by default once package persistence exists | fail-open with warning | package generation is not external submission |
| reinterpretation | record when workflow exists | fail-open with warning | must not overwrite original intent |
| lifecycle decision | record as lifecycle event first; audit linkage optional | fail-open with warning | lifecycle surface remains authoritative for lifecycle decisions |

This policy is intentionally conservative. The first implementation target should be narrow.

## Initial implementation target

The recommended first v0.6-beta target is:

```text
export operation audit insertion for security-aware export profiles
```

Reason:

- export is already a derived operation
- export profiles already express disclosure policy
- export is user-visible and easy to observe
- exported output should have provenance
- failure can be reported without claiming tamper-proofness

## Operation details

### Export operations

Potential audit event:

```text
operation: export
target_environment: file / local / unknown
purpose: export purpose if supplied, otherwise profile/format summary
referenced_records: exported record ids if available
result: info / warning / blocked
metadata:
  format
  profile
  redact_sensitive
  exclude_sensitive
  output_path_if_available
  lifecycle_policy_if_available
```

Export audit should not copy exported body content into audit metadata.

### Context-use dry-run

Potential audit event:

```text
operation: context_use
target_environment: local / external
purpose: user-supplied purpose
referenced_records: selected context ids
result: info / warning / blocked
metadata:
  decision
  unclassified_count
  layer4_count
  external_target
```

Initial policy:

- do not persist every dry-run automatically in v0.6-alpha
- design an explicit option such as `--record-audit`
- later versions may revisit default recording

Rationale:

Context-use checks may be run frequently during exploration. Automatically persisting every dry-run could create noise and accidental disclosure in metadata.

### Package generation

Potential audit event:

```text
operation: package_generate
target_environment: package / local / external
purpose: package purpose
referenced_records: packaged context/artifact ids
result: info / warning / blocked
metadata:
  package_id
  package_type
  target
  body_included_count
  reference_only_count
  excluded_count
  policy_snapshot_id_or_hash
```

Initial policy:

- define package persistence first
- record generation after package id and package surface are stable

Package audit must not imply permission grant or external submission.

### Reinterpretation flows

Potential audit event:

```text
operation: reinterpret
target_environment: local / external / unknown
purpose: reinterpretation purpose
referenced_records: source context/artifact/event ids
result: info / warning / blocked
metadata:
  derived_output_id
  human_review_status
  model_or_tool_if_explicit
```

Reinterpretation audit must preserve the distinction between:

```text
original record intent
later derived interpretation
```

### Lifecycle decisions

Lifecycle decisions are primarily represented in `.chronicle/lifecycle.jsonl`.

Potential audit event:

```text
operation: lifecycle_decision
target_environment: local
purpose: lifecycle reason
referenced_records: target ids
result: info / warning / blocked
metadata:
  lifecycle_action
  lifecycle_event_id
```

Initial policy:

- do not duplicate lifecycle semantics too early
- lifecycle event remains the decision surface
- audit linkage may be added once export/package behavior consumes lifecycle events

## Failure semantics

Audit insertion failures should be explicit.

Initial default:

```text
fail-open with warning
```

Meaning:

- the primary operation may complete
- the warning must be surfaced to the caller
- the warning must be classifiable as blocking / tracked separately / informational

Fail-closed behavior may be introduced later for selected high-risk operations, but only after a separate ADR or design update.

## Layering guidance

Preferred insertion layer:

```text
service layer first
CLI layer for user-facing options and warning display
```

Rationale:

- service layer can centralize operation semantics
- CLI layer can expose explicit flags and warning messages
- writing only in CLI risks missing non-CLI callers
- writing only in storage risks losing operation purpose and target context

## Timestamp and test stability

Implementation should avoid brittle timestamp expectations.

Recommended test patterns:

- assert required fields exist
- assert operation and referenced ids
- normalize or inject clock where practical
- avoid exact wall-clock equality
- keep snapshot tests focused on stable fields

## Security and privacy boundaries

Audit metadata should minimize sensitive content.

Do not store:

- full exported bodies
- secret payloads
- redacted content
- model-facing package bodies unless explicitly designed
- credentials or tokens

Audit events may store identifiers, counts, classifications, hashes, and policy summaries.

## Non-goals

Audit insertion does not provide:

- tamper-proof logging
- notarization
- cryptographic proof
- correctness certification
- security certification
- full retention enforcement
- legal compliance guarantees

## RDE review frame

### Preserved

- `.chronicle/chronicle.jsonl` remains the original record surface.
- `.chronicle/audit.jsonl` remains a derived operation audit surface.
- Audit events remain observational, not proof.
- Sensitive payload minimization remains a boundary.

### Transformed

- v0.5 audit model gains explicit insertion policy.
- Export/profile workflows become the first recommended implementation target.

### Added

- Operation-family insertion table.
- Failure semantics.
- Layering guidance.
- Privacy constraints for audit metadata.
- Initial v0.6-beta target.

### Unresolved

- Exact CLI option names.
- Whether context-use dry-run should become recorded by default later.
- Whether high-risk exports should become fail-closed.
- How audit insertion interacts with future package persistence.
- How audit records should be inspected from the CLI.

### Deviation risks

- Treating audit presence as correctness proof.
- Storing removed or secret payloads in audit metadata.
- Making audit writes mandatory before failure semantics are mature.
- Recording too much exploratory dry-run noise.
- Emitting audit at a layer that lacks purpose or target context.
