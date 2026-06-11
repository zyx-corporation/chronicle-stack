# Repository Guidelines

Chronicle Stack v0.1 — a local-first record layer for AI-assisted thinking, writing, design, and development.
Its core value is **reconstructability**: why an artifact exists, what changed, which decision accepted or rejected it, and how meaning shifted across versions.

## Project Structure

```
src/chronicle/           # Application source
  cli.py                 # Typer CLI entry point
  errors.py              # ChronicleError subclasses
  ids.py                 # Prefixed ID generation (art_, ver_, rde_, evt_, dec_, …)
  models/                # Pydantic v2 models (event, artifact, decision, rde, context, metadata)
  services/              # Service classes (ChronicleService, ArtifactService, DecisionService, RdeService, SearchService, ContextService)
  store/                 # Storage backends (JsonlStore, IndexStore, ArtifactStore, paths)
  exporters/             # YAML and Markdown exporters, RDE report formatter
tests/                   # pytest tests (one file per concern)
docs/                    # Specifications, ADRs, CLI reference, data model, testing strategy
.github/workflows/       # CI (pytest + ruff)
```

Storage layout under `.chronicle/`:

```
.chronicle/
  chronicle.jsonl        # Primary record — source of truth
  metadata.yaml
  artifacts/<id>/current.md, versions/<ver>.md
  indexes/               # Derived, rebuildable from JSONL
  reports/rde/<rde_id>.md
```

## Build, Test, and Development Commands

```bash
pip install -e ".[dev]"   # Install with test/lint deps (pytest, pytest-cov, ruff)
pytest                    # Run all 39 tests
ruff check src/ tests/    # Lint and format check (line-length 100)
```

The CLI entry point is `chronicle` (registered via `pyproject.toml` `[project.scripts]`).

CI runs on push/PR to `main` (`.github/workflows/ci.yml`): Python 3.11, ruff, then pytest.

## Coding Style & Naming Conventions

- Python 3.11+, 4-space indentation.
- Ruff with `line-length = 100` and `target-version = "py311"`.
- All IDs are prefixed: `chr_` (Chronicle), `evt_` (Event), `ctx_` (Context), `art_` (Artifact), `ver_` (Version), `dec_` (Decision), `rde_` (RDE record), `src_` (Source).
- Prefer small service classes with explicit responsibilities. Avoid hidden global state.
- Errors use `ChronicleError` subclasses — raw exceptions must not escape CLI commands.

## Testing Guidelines

- Framework: pytest with Typer `CliRunner` for CLI tests.
- Test isolation: each test runs in a `tmp_path`; `os.chdir(tmp_path)` to simulate a project directory.
- Test files map to concerns: `test_init.py`, `test_event_recording.py`, `test_artifact.py`, `test_decision.py`, `test_rde.py`, `test_search.py`, `test_cli.py`.
- Required coverage: service tests, CLI integration tests, index rebuild, JSONL corruption tolerance, artifact version history, decision persistence, RDE reports, exports.
- Run `pytest` before completing any change.

## Commit & Pull Request Guidelines

- Commit messages follow concise prefix conventions: `fix:`, `feat:`, `test:`, `ci:`, `docs:`.
- Pull requests must pass CI (ruff + pytest) before merging.

## Key Design Rules

- `.chronicle/chronicle.jsonl` is the primary record. Indexes are derived and must be rebuildable.
- `ArtifactVersion.source_event_id` and `Decision.event_id` are persisted in JSONL payloads.
- Artifact update rejects missing content (no `--file` or `--content` → error).
- RDE Diff Records have six sections (`preserved`, `transformed`, `supplemented`, `unresolved`, `deviation_risks`, `next_update_policy`). Empty sections render as `(none)`.
- RDE-to-version links are derived during `chronicle index rebuild` and stored in `ArtifactVersion.rde_record_id`.
- Keep v0.1 simple: no database, queue, plugin system, agent runtime, or graph backend.
