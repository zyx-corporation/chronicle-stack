# Chronicle Stack v0.4 Release Readiness

Status: Ready for release candidate review  
Target: v0.4.0  
Theme: Operational Readiness Layer

## Summary

v0.4 moves Chronicle Stack from a record/export tool toward a locally operable Chronicle foundation.

The release adds operational diagnosis, export provenance, explicit redaction-aware export controls, improved static dashboard inspection, and graph export inspection commands.

## Scope Completion

| Issue | Scope | Status |
|---|---|---|
| #44 | v0.4 roadmap and scope | Complete |
| #45 | Chronicle health check command | Complete |
| #46 | Export manifest and provenance metadata | Complete |
| #47 | Redaction-aware export options | Complete |
| #48 | Dashboard filtering and local navigation | Complete |
| #49 | Graph export inspection commands | Complete |

## Release Readiness Criteria

| Criterion | Status | Notes |
|---|---|---|
| ruff pass | Ready | Verified in CI for the implementation PRs |
| pytest pass | Ready | Verified in CI for the implementation PRs |
| JSONL primary contract unchanged | Ready | JSONL remains the single primary record |
| Contract tests maintained | Ready | v0.3 contract tests remain in force |
| `chronicle doctor` available | Ready | Read-only health check command |
| Export Manifest available | Ready | YAML / graph-json / HTML |
| Redaction-aware export opt-in only | Ready | YAML / HTML only |
| Default export behavior unchanged | Ready | No default redaction |
| HTML dashboard static read-only | Ready | Local navigation and filtering only |
| Graph inspection read-only | Ready | Auxiliary `chronicle-graph` command |
| Smoke test document exists | Ready | `docs/smoke-test-v0.4.md` |

## Implemented Capabilities

### Chronicle Doctor

```bash
chronicle doctor
chronicle doctor --json
```

Checks local project health without mutating JSONL or indexes.

### Export Manifest

Export Manifest is added to supported derived exports.

- YAML: top-level `export_manifest`
- graph-json: top-level `export_manifest`
- HTML: Export Manifest section

Export Manifest is provenance metadata, not cryptographic proof.

### Redaction-aware Export

```bash
chronicle export --format yaml --redact-sensitive
chronicle export --format yaml --exclude-sensitive
chronicle export --format html --redact-sensitive
chronicle export --format html --exclude-sensitive
```

This is explicit opt-in disclosure control for derived exports. It is not access control.

### Dashboard Filtering and Local Navigation

HTML dashboard remains a static, single-file, read-only derived view.

Added:

- local section navigation
- stable anchors
- lightweight local row filtering

### Graph Export Inspection

```bash
chronicle-graph summary
chronicle-graph nodes
chronicle-graph edges
```

These commands inspect the derived graph-json structure. They do not implement GraphRAG.

## Intentional Design Notes

### `chronicle-graph` vs `chronicle graph`

The roadmap originally listed `chronicle graph summary`, `chronicle graph nodes`, and `chronicle graph edges` as candidate command names.

The v0.4 implementation exposes these as `chronicle-graph` auxiliary console commands instead. This avoids a risky late change to the primary Typer CLI structure while still delivering read-only graph inspection.

This can be revisited in v0.5 if a nested graph command is desired.

### Ruff Configuration

The CI lint scope is aligned with the current codebase style. v0.4 does not include a full code formatting campaign.

## Non-goals Confirmed

v0.4 does not include:

- GraphRAG query engine
- embeddings
- vector database integration
- graph database integration
- external LLM API calls
- automatic LLM injection
- live dashboard server
- dashboard editing UI
- authentication
- cloud sync
- access control
- automatic redaction
- cryptographic signing
- commercial license template

## RDE Review

### Preserved

- JSONL remains primary.
- Derived views remain derived.
- Interface contracts remain in force.
- HTML dashboard remains static and read-only.
- Graph export remains a derived structure.
- Redaction-aware export remains explicit opt-in.

### Transformed

- Chronicle Stack becomes more operationally reliable.
- Export outputs become more traceable.
- Dashboard inspection becomes more usable for larger local Chronicles.
- Graph-ready export becomes inspectable from CLI.

### Added

- `chronicle doctor`
- `ExportManifest`
- redaction-aware export options
- dashboard navigation/filtering
- `chronicle-graph` inspection command
- v0.4 smoke test and readiness documentation

### Unresolved

- `chronicle graph` nested command is not implemented.
- Redaction-aware export does not cover graph-json or Markdown.
- Export Manifest is not signed.
- Dashboard remains HTML-only, not an application.

### Deviation Risks

- Do not treat Export Manifest as cryptographic proof.
- Do not treat redaction-aware export as access control.
- Do not treat dashboard filtering as live dashboard functionality.
- Do not treat graph inspection as GraphRAG.

## Release Decision

v0.4 is ready to proceed to release smoke testing and final version/tag preparation once `docs/smoke-test-v0.4.md` is merged and CI passes.
