# Changelog

## v0.3.0 - Unreleased

### Added
- Interface stability and serialization contracts (`docs/interface-contracts.md`).
- Contract tests for JSONL primary records, EventType payload shapes, model compatibility, CLI JSON output, rebuild, and export behavior.
- Explicit Injection Plan persistence via `chronicle injection plan --record`.
- `injection_plan_recorded` Chronicle Event type.
- Graph-ready export boundary and deterministic `graph-json` export.
- Graph candidate models for nodes, edges, and graph export snapshots.
- Static read-only HTML dashboard export via `chronicle export --format html`.
- `chronicle --version` CLI option.
- CLI UX tests for version, help, and invalid-input behavior.

### Changed
- Project metadata updated for v0.3 development (`0.3.0.dev0`).
- CLI help text updated for the Chronicle Stack v0.3 feature set.
- Documentation expanded for GraphRAG boundary, interface contracts, commercial support scope, and contributor license policy.
- Injection Plans remain non-persistent by default; persistence is now available only by explicit `--record`.
- Export surface now includes `yaml`, `markdown`, `graph-json`, and `html`.

### Notes
- `chronicle.jsonl` remains the primary record.
- `graph-json` and HTML dashboard exports are derived views.
- GraphRAG query engine, embeddings, vector database integration, graph database integration, live dashboard, authentication, editing UI, and redaction are out of scope for v0.3.
- Visibility hints are not access control or redaction.
- Boundary Rules are advisory.
- Injection Plans do not inject anything into LLMs.

## v0.2.0 - 2026-06-13

### Added
- Formal Context Scope Model (`ContextScope`) for Context records.
- Backward-compatible loading from v0.1 `scope_hint`.
- `VisibilityHint` for Context and Artifact records.
- CLI support for setting Context / Artifact visibility (`--visibility`).
- Structured SourceProvenance metadata for Events, Contexts, and Artifacts.
- CLI support for source metadata on record, add-context, and artifact create.
- Context Boundary Rule model and CLI (boundary add/list/check).
- Boundary rule index rebuild support.
- Rule-based Context Injection Plan generation.
- `chronicle injection plan` CLI command.

### Changed
- License changed to AGPL-3.0-or-later for v0.2.0 and later, with commercial licensing available separately from ZYX Corp株式会社.
- Earlier releases that were published under different license terms are not retroactively changed by this transition.

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
