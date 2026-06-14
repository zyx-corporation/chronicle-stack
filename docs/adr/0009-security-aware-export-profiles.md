# ADR-0009: Security-aware Export Profiles

Status: Accepted  
Date: 2026-06-14  
Scope: Chronicle Stack v0.5 and later  
Related: ADR-0001, ADR-0002, ADR-0005, ADR-0006, ADR-0008, `docs/security-aware-export-profiles.md`

## Context

Chronicle Stack exports are derived disclosure surfaces. v0.4 introduced explicit `--redact-sensitive` and `--exclude-sensitive` options. v0.5 adds classification, audit, lifecycle, integrity, and doctor security surfaces.

Users need stable named export profiles rather than re-specifying low-level redaction behavior every time.

## Decision

Chronicle Stack will introduce security-aware export profiles as named disclosure presets.

v0.5 defines:

```text
public-review
internal-review
local-analysis
restricted-summary
```

Profiles are disclosure controls for derived exports. They are not access control and do not mutate primary Chronicle records.

## Profile Semantics

```text
public-review:
  redact sensitive records in supported exports

internal-review:
  preserve sensitive records, intended for internal review

local-analysis:
  preserve sensitive records, intended for local-only analysis

restricted-summary:
  exclude sensitive records in supported exports
```

## CLI Surface

v0.5 exposes profile export through an auxiliary CLI:

```bash
chronicle-export profile --format yaml --profile public-review
chronicle-export profile --format html --profile restricted-summary
```

The primary `chronicle export` command remains unchanged in this issue to avoid destabilizing the main CLI surface.

## Non-goals

This ADR does not implement:

- access control
- publication workflow
- complete data-loss prevention
- all-format profile support
- automatic lifecycle filtering
- automatic audit insertion

## Consequences

### Positive

- Export intent becomes explicit and repeatable.
- Existing redaction options remain backward-compatible.
- Profile behavior is visible in export manifest options.

### Negative / Cost

- Profiles initially support YAML/HTML only.
- Primary CLI does not yet expose `--profile`.
- Profile names must be governed to avoid semantic drift.

## RDE Review

### Preserved

- Existing `chronicle export` redaction options remain compatible.
- JSONL remains primary.
- Export does not mutate original records.

### Transformed

- Export disclosure intent becomes a named profile.

### Added

- ExportProfile vocabulary.
- Profile-to-redaction mapping.
- `chronicle-export profile` auxiliary CLI.
- Profile tests.

### Unresolved

- Primary CLI `chronicle export --profile` shape.
- Graph/Markdown profile support.
- Lifecycle-aware export filtering.
- Audit event insertion for export operations.

### Deviation Risks

- Treating profiles as access control.
- Treating public-review as publication approval.
- Forgetting that profile exports are derived surfaces.
