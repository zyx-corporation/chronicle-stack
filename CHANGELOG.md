# Changelog

## v0.2.0 - Unreleased

### Added
- Formal Context Scope Model (`ContextScope`) for Context records.
- Backward-compatible loading from v0.1 `scope_hint`.
- `VisibilityHint` for Context and Artifact records.
- CLI support for setting Context / Artifact visibility (`--visibility`).

## v0.1.0 - 2026-06-13

### Added
- Chronicle Event JSONL primary store (`chronicle.jsonl`)
- Artifact create / update / history with version snapshots
- Decision records (accepted, rejected, deferred, etc.)
- RDE Diff Records with six fixed audit fields
- RDE Markdown reports (`.chronicle/reports/rde/`)
- RDE-to-ArtifactVersion derived linkage (via `index rebuild`)
- YAML and Markdown export (`chronicle export`)
- CLI integration tests (`test_cli.py`)
- GitHub Actions CI (ruff + pytest)

### Fixed
- Persist `ArtifactVersion.source_event_id` in `chronicle.jsonl`
- Persist `Decision.event_id` in `chronicle.jsonl`
- Prevent accidental empty artifact updates (`ARTIFACT_CONTENT_MISSING` error)

### Notes
- GraphRAG is out of scope for v0.1
- Dashboard is out of scope for v0.1
- RDE is a structured diff record, not a full semantic validation engine
- `chronicle.jsonl` is the primary record; `indexes/` are derived and rebuildable
- Multiple RDE records targeting the same version: the last RDE in JSONL order wins in the derived index
