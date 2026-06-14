# Chronicle Stack Security-aware Export Profiles

Status: v0.5 profile contract  
Related: #69, [ADR-0009](adr/0009-security-aware-export-profiles.md)

## Purpose

Security-aware export profiles provide named disclosure presets for derived exports.

They are intended to make export intent explicit and repeatable.

## Boundary

Important:

```text
export profile != access control
export profile != publication approval
export profile != complete data-loss prevention
export profile does not mutate primary records
```

## Profiles

| Profile | Behavior |
|---|---|
| `public-review` | Redact sensitive records in supported exports. |
| `internal-review` | Preserve sensitive records for internal review. |
| `local-analysis` | Preserve sensitive records for local-only analysis. |
| `restricted-summary` | Exclude sensitive records in supported exports. |

## CLI

v0.5 exposes profiles through an auxiliary command:

```bash
chronicle-export profile --format yaml --profile public-review
chronicle-export profile --format html --profile restricted-summary
```

Supported formats in v0.5:

```text
yaml
html
```

The existing primary command remains available:

```bash
chronicle export --format yaml --redact-sensitive
chronicle export --format yaml --exclude-sensitive
```

## Manifest

Profile exports include profile information in export manifest options:

```yaml
export_options:
  redact_sensitive: true
  exclude_sensitive: false
  profile: public-review
```

## Non-goals

The v0.5 profile layer does not provide:

- access control
- automatic publication workflow
- complete data-loss prevention
- lifecycle-aware filtering
- automatic audit insertion
- Graph/Markdown profile support

## RDE Review

### Preserved

- Existing redaction options remain compatible.
- JSONL remains primary.
- Export does not mutate original records.

### Transformed

- Export disclosure intent becomes explicit through named profiles.

### Added

- ExportProfile vocabulary.
- Profile-to-redaction mapping.
- `chronicle-export profile` auxiliary CLI.
- Profile tests.

### Unresolved

- Primary CLI `chronicle export --profile` shape.
- Graph/Markdown support.
- Lifecycle-aware export filtering.
- Audit event insertion for export operations.

### Deviation Risks

- Treating profiles as access control.
- Treating public-review as publication approval.
- Forgetting that profile exports are derived surfaces.
