# Repository Guidelines

Chronicle Stack v2.3 — a local-first record layer for AI-assisted thinking, writing, design, and development.
Its core value is **reconstructability**: why an artifact exists, what changed, which decision accepted or rejected it, and how meaning shifted across versions.

## AI Operation Canon

Chronicle Stack treats AI operation as four co-equal elements:

1. Instructions
2. Shared memory
3. Feedback
4. Chronicle

Do not make one element silently override the others. Durable guidance belongs in this file,
stable definitions and procedures belong in `docs/`, important decisions belong in `docs/adr/`,
task-specific history belongs in `docs/chronicles/`, and workspace-wide policy history belongs
in `chronicle.md`.

## Reading Order

Before making non-trivial changes:

1. Read `AGENTS.md`.
2. Use `README.md` as the repository map.
3. Check `roadmap.md` for the next-order map and canonical roadmap pointers.
4. Check `docs/adr/` for decisions that affect architecture, security boundaries, data
   contracts, governance, and interoperability.
5. Check `docs/` for specifications, definitions, criteria, procedures, and contracts.
6. Make the change.
7. If the work fails in a way future maintainers should learn from, add a Failure Note in the
   relevant task history.
8. If the work makes or depends on an important decision, add or update an ADR.
9. If the work changes project-wide operating policy, append `chronicle.md`.
10. Promote stable knowledge into `docs/`, `docs/adr/`, or another canonical document rather
    than leaving it only in a transient work note.

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
  adr/                   # Architecture Decision Records and governance decisions
  chronicles/            # Task-specific decision history and maintenance entries
roadmap.md               # Root roadmap map that points to canonical roadmap documents
chronicle.md             # Workspace-wide policy and maintenance chronicle
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
pytest                    # Run the full test suite
ruff check src/ tests/    # Lint and format check (line-length 100)
```

The CLI entry point is `chronicle` (registered via `pyproject.toml` `[project.scripts]`).

CI uses `.github/workflows/ci.yml`: Python 3.11, ruff, then pytest. Per ADR-0098,
local `act` is the primary Core CI execution surface; GitHub Actions remains the hosted mirror.

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

## Documentation Rules

- `AGENTS.md` is the working canon for agent behavior, prohibitions, and repository-specific
  operating rules.
- `README.md` is a map for first readers. Do not turn it into a rationale document.
- `roadmap.md` is the root pointer to next-order planning documents.
- `docs/adr/` records important decisions and their reasons.
- `docs/chronicles/` records task-specific maintenance history.
- `chronicle.md` records workspace-wide policy and documentation stewardship history.
- Do not store transient work notes in `docs/`; keep them in the task surface or another
  temporary area unless they are promoted into stable documentation.
- For substantial development work, follow the MDES standard procedure stored at
  `docs/development/mdes-standard-coding-procedure-manifest.md` within the adoption boundary
  defined by ADR-0100.

## Key Design Rules

- `.chronicle/chronicle.jsonl` is the primary record. Indexes are derived and must be rebuildable.
- `ArtifactVersion.source_event_id` and `Decision.event_id` are persisted in JSONL payloads.
- Artifact update rejects missing content (no `--file` or `--content` → error).
- RDE Diff Records have six sections (`preserved`, `transformed`, `supplemented`, `unresolved`, `deviation_risks`, `next_update_policy`). Empty sections render as `(none)`.
- RDE-to-version links are derived during `chronicle index rebuild` and stored in `ArtifactVersion.rde_record_id`.
- Local runtime, GraphRAG workspace, federation package/message surfaces, and trust model remain
  explicitly bounded surfaces. They must not silently replace the JSONL primary record or become
  hidden background execution paths.

## Prohibitions

- Do not overwrite chronicles; append instead.
- Do not mix rationale or decision records into `README.md`.
- Do not turn future plans into current specifications.
- Do not silently strengthen, weaken, or replace canonical source-of-truth definitions.
- Do not fabricate sources, citations, DOIs, experiment results, datasets, or benchmark scores.
- Do not remove constraints, objections, or limitations merely to make an artifact more persuasive.
- Do not perform destructive, irreversible, or source-of-truth-changing operations without explicit
  human confirmation.
