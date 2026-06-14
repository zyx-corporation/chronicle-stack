# ADR-0013: Lifecycle-aware Export Filtering

Status: Accepted  
Date: 2026-06-15  
Scope: Chronicle Stack v0.6-alpha and later  
Related: ADR-0006, ADR-0009, ADR-0012, `docs/lifecycle-aware-export.md`, #87, #90

## Context

ADR-0006 introduced the lifecycle model for redact, seal, expire, tombstone, and hard-delete markers.

ADR-0009 introduced security-aware export profiles.

Both documents intentionally left lifecycle-aware export filtering unresolved.

Chronicle Stack needs a policy for how derived exports should respond to lifecycle decisions while preserving the boundary that lifecycle events do not mutate original records by themselves.

## Decision

Chronicle Stack will treat lifecycle-aware export filtering as derived projection behavior.

Lifecycle decisions may affect export outputs, warnings, manifests, and later audit events.

Lifecycle decisions must not rewrite `.chronicle/chronicle.jsonl`.

```text
lifecycle event != physical deletion
tombstone != automatic erasure
hard_delete marker != proof of deletion
export filter != access control
export filter != legal compliance automation
```

## Default projection policy

The default lifecycle-aware export design is conservative:

| Lifecycle action | Default export interpretation |
|---|---|
| `redact` | Prefer `replacement_ref` or redacted projection if available. |
| `seal` | Omit body for strict/public profiles; warn for internal/local profiles. |
| `expire` | Warn or exclude depending on profile and lifecycle policy. |
| `tombstone` | Exclude body; preserve tombstone marker only where configured. |
| `hard_delete` | Exclude body from derived exports if represented. |

## Profile interaction

Lifecycle filtering composes with export profiles.

Profiles with broader disclosure risk should be stricter.

```text
public-review       -> strict lifecycle interpretation
restricted-summary  -> strictest lifecycle interpretation
internal-review     -> warning-oriented lifecycle interpretation
local-analysis      -> warning-oriented, local-only lifecycle interpretation
```

## Lifecycle policy vocabulary

Future export implementations may expose:

```text
strict
warn
ignore
```

`ignore` must be explicit and should not be the default.

Lifecycle policy overrides may later trigger audit events under ADR-0012.

## Manifest requirement

Once implemented, lifecycle-aware exports should record lifecycle behavior in export manifests.

Candidate manifest content:

```text
lifecycle policy
records excluded by lifecycle
records warned by lifecycle
sealed bodies omitted
redacted replacements used
```

Manifest metadata must not copy hidden or removed content.

## Consequences

### Positive

- Lifecycle decisions become visible in derived outputs.
- Export profiles gain clearer safety behavior.
- Tombstone/seal/expire semantics become observable without mutating primary history.
- Future audit insertion has clear lifecycle override candidates.

### Negative / Cost

- Export behavior becomes more complex.
- Different profiles may produce different lifecycle projections.
- Users may need explicit override flags for exceptional internal review.
- Manifests need additional lifecycle summary fields.

## Non-goals

This ADR does not implement:

- physical hard deletion
- Git history rewriting
- legal compliance automation
- cryptographic deletion proof
- access control
- publication approval
- complete data-loss prevention

## RDE Review

### Preserved

- `.chronicle/chronicle.jsonl` remains primary.
- Lifecycle events remain a separate decision surface.
- Exports remain derived projections.
- Lifecycle-aware filtering does not claim deletion enforcement.

### Transformed

- Lifecycle events begin to influence derived export behavior.
- Security-aware export profiles gain lifecycle interpretation.

### Added

- Default lifecycle projection policy.
- Profile interaction policy.
- Lifecycle policy vocabulary.
- Manifest expectations.
- Audit interaction candidate.

### Unresolved

- Exact exporter implementation.
- Exact CLI option names.
- Replacement resolution across record types.
- Default blocking behavior for external targets.
- Interaction with package persistence.

### Deviation Risks

- Treating tombstone as physical deletion.
- Treating lifecycle-aware filtering as legal compliance automation.
- Leaking sealed content through permissive defaults.
- Hiding lifecycle warnings from manifests.
- Making profile behavior inconsistent across formats.
