# Lifecycle-aware Export Filtering

Status: Draft for v0.6-alpha  
Related: ADR-0006, ADR-0009, ADR-0013, #87, #90

## Purpose

This document defines how Chronicle Stack export surfaces should interpret lifecycle decisions.

v0.5 introduced the lifecycle model and `.chronicle/lifecycle.jsonl`. v0.6-alpha defines how derived exports should project, warn, or exclude records affected by lifecycle events.

The key boundary remains:

```text
lifecycle events record lifecycle decisions
lifecycle events do not mutate original records by themselves
export is a derived projection
```

## Surfaces

Chronicle Stack separates the following surfaces:

```text
.chronicle/chronicle.jsonl
  primary record surface

.chronicle/lifecycle.jsonl
  lifecycle decision surface

export outputs
  derived projection surfaces
```

Lifecycle-aware export filtering only affects derived export outputs.

It must not rewrite `.chronicle/chronicle.jsonl`.

## Lifecycle projection policy

| Lifecycle action | Strict/public projection | Internal/local projection | Notes |
|---|---|---|---|
| `redact` | prefer replacement or redacted projection | prefer replacement or warn if original included | do not copy removed secrets |
| `seal` | metadata only or omit body | include metadata and warning; body requires explicit override | seal means ordinary use should stop |
| `expire` | exclude or warn depending on profile | warn by default | expiration is retention signal, not physical deletion |
| `tombstone` | exclude body; preserve tombstone if configured | preserve tombstone marker, not body | tombstone is not physical deletion by itself |
| `hard_delete` | exclude from derived export if represented | exclude from derived export if represented | does not guarantee Git/history erasure |

## Default behavior

The default v0.6 design should be conservative:

```text
tombstone   -> exclude body from derived exports by default
hard_delete -> exclude body from derived exports by default
seal        -> omit body in strict/public profiles; warn in internal/local profiles
expire      -> warn or exclude based on profile
redact      -> prefer replacement_ref if available
```

This default is not legal deletion enforcement. It is derived export behavior.

## Profile interaction

Existing v0.5 profiles:

```text
public-review
internal-review
local-analysis
restricted-summary
```

Lifecycle-aware export should compose with profiles rather than replace them.

### public-review

Strict external-facing review profile.

Candidate behavior:

- redacted replacement preferred
- sealed body omitted
- expired content excluded or warning-only if summary is safe
- tombstoned content body excluded
- hard-delete-marked content excluded

### restricted-summary

Strictest summary profile.

Candidate behavior:

- sensitive records excluded
- sealed body excluded
- expired content excluded
- tombstone marker may be preserved only as summary metadata
- hard-delete-marked content excluded

### internal-review

Internal review profile.

Candidate behavior:

- redacted replacement preferred, but original may be included with warning if explicitly allowed
- sealed records included as metadata by default
- sealed body requires explicit override
- expired content warning is visible
- tombstone marker preserved, body excluded

### local-analysis

Local-only analysis profile.

Candidate behavior:

- similar to internal-review
- may permit more inclusion with explicit overrides
- warnings must remain visible

## Lifecycle policy vocabulary

Exports may later expose a lifecycle policy option:

```text
strict
warn
ignore
```

### strict

Lifecycle decisions actively restrict derived output.

Candidate behavior:

- omit tombstoned and hard-delete-marked bodies
- omit sealed bodies unless explicit override exists
- prefer redacted replacements
- exclude expired records where profile says strict

### warn

Lifecycle decisions remain visible as warnings while still allowing some internal/local output.

Candidate behavior:

- include warning metadata
- avoid sealed bodies unless explicit override exists
- preserve tombstone markers, not bodies

### ignore

Lifecycle decisions are not applied to export filtering.

This should be discouraged, explicit, and audit-worthy once audit insertion exists.

`ignore` must not be the default.

## Candidate CLI options

Potential future options:

```text
--lifecycle-policy strict|warn|ignore
--include-tombstoned
--include-expired
--include-sealed-body
```

These are design candidates, not implemented behavior in this document.

High-risk overrides should produce visible warnings and may later produce audit events.

## Manifest interaction

Export manifests should record lifecycle-aware behavior once implemented.

Candidate manifest fields:

```yaml
export_options:
  profile: public-review
  lifecycle_policy: strict
  include_tombstoned: false
  include_expired: false
  include_sealed_body: false

lifecycle_summary:
  lifecycle_events_seen: 5
  records_excluded_by_lifecycle: 2
  records_warned_by_lifecycle: 1
  sealed_records_omitted: 1
  redacted_replacements_used: 1
```

Manifest metadata should avoid copying hidden content.

## Audit interaction

Lifecycle overrides should be candidates for audit insertion.

Examples:

- exporting with `--lifecycle-policy ignore`
- including sealed bodies
- including expired content for external target
- exporting tombstone markers

This should connect to the audit insertion policy defined in `docs/audit-insertion-points.md`.

## Failure and warning semantics

Lifecycle-aware export may produce:

```text
pass
warning
blocked
```

### pass

No lifecycle decision affects the export, or all lifecycle decisions were applied cleanly.

### warning

Lifecycle decisions affected output or required visible caveats.

Examples:

- sealed records omitted
- expired records included with warning
- redacted replacement missing

### blocked

The requested export contradicts lifecycle policy and cannot proceed without explicit override.

`blocked` should be reserved for strict policy cases.

## Non-goals

Lifecycle-aware export filtering does not provide:

- physical deletion
- Git history rewriting
- legal compliance automation
- cryptographic proof of deletion
- access control
- publication approval
- complete data-loss prevention

## RDE review frame

### Preserved

- `.chronicle/chronicle.jsonl` remains primary.
- Lifecycle events remain a separate decision surface.
- Export remains a derived projection.
- No deletion enforcement is claimed.

### Transformed

- Lifecycle decisions become visible in derived export behavior.
- Export profiles gain lifecycle-aware interpretation.

### Added

- Lifecycle projection policy.
- Profile interaction policy.
- Candidate lifecycle policy vocabulary.
- Manifest and audit interaction design.

### Unresolved

- Exact implementation in exporters.
- Exact CLI option names.
- Whether strict policy should block by default for external targets.
- How replacement references are resolved across record types.
- How lifecycle-aware filtering interacts with package persistence.

### Deviation risks

- Treating tombstone as physical deletion.
- Leaking sealed or expired content through permissive defaults.
- Hiding lifecycle warnings in manifests.
- Making profile behavior inconsistent across export formats.
- Treating lifecycle-aware export as legal compliance automation.
