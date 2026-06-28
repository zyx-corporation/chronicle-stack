# Chronicle Stack v0.4 Smoke Test

Status: Release candidate smoke checklist  
Target: v0.4.0

## Purpose

This smoke test verifies the v0.4 Operational Readiness Layer without relying on external services.

The test must confirm:

- JSONL remains primary.
- Doctor is read-only.
- Exports are derived views.
- Export Manifest is present where expected.
- Redaction-aware export is explicit opt-in.
- Dashboard remains static/read-only.
- Graph inspection is read-only and does not imply GraphRAG.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
ruff check src/ tests/
pytest -v
```

Expected:

```text
ruff pass
pytest pass
```

## Create Smoke Chronicle

```bash
rm -rf /tmp/chronicle-v0.4-smoke
mkdir -p /tmp/chronicle-v0.4-smoke
cd /tmp/chronicle-v0.4-smoke

chronicle init --title "v0.4 Smoke"
chronicle add-context --title "Public Context" --summary "Public smoke context" --visibility public --scope project
chronicle add-context --title "Sensitive Context" --summary "Sensitive smoke context" --visibility sensitive --scope task

echo "Smoke artifact content" > artifact.md
chronicle artifact create --title "Smoke Artifact" --type document --file artifact.md --visibility private
chronicle decision record --type accepted --reason "Smoke decision accepted"
chronicle injection plan --task "Smoke task" --record
```

## Doctor

```bash
chronicle doctor
chronicle doctor --json
```

Expected:

- exit code 0
- status `ok` or `warning` depending on local derived index state
- no JSONL mutation

## Export Manifest

```bash
chronicle export --format yaml > smoke.yaml
chronicle export --format graph-json > graph.json
chronicle export --format html > dashboard.html
```

Expected:

- `smoke.yaml` includes top-level `export_manifest`
- `graph.json` includes top-level `export_manifest`
- `dashboard.html` includes `Export Manifest`
- JSONL remains unchanged

## Redaction-aware Export

```bash
chronicle export --format yaml --redact-sensitive > redacted.yaml
chronicle export --format yaml --exclude-sensitive > excluded.yaml
chronicle export --format html --redact-sensitive > redacted.html
chronicle export --format html --exclude-sensitive > excluded.html
```

Expected:

- `redacted.yaml` includes `[REDACTED:sensitive]`
- `excluded.yaml` excludes sensitive Context rows
- `redacted.html` includes `[REDACTED:sensitive]`
- `excluded.html` omits sensitive Context rows
- default export remains unredacted
- options are recorded in Export Manifest

Invalid option combination:

```bash
chronicle export --format yaml --redact-sensitive --exclude-sensitive
```

Expected:

- non-zero exit

Unsupported format:

```bash
chronicle export --format graph-json --redact-sensitive
```

Expected:

- non-zero exit

## Dashboard Navigation and Filtering

Open `dashboard.html` in a browser or inspect text:

```bash
grep -E "chronicle-filter|#contexts|#artifacts|#events|data-filter-row" dashboard.html
```

Expected:

- section navigation exists
- stable anchors exist
- local filter input exists
- rows include filter metadata
- no external assets required
- dashboard remains read-only

## Graph Inspection

```bash
chronicle-graph summary
chronicle-graph summary --json
chronicle-graph nodes
chronicle-graph nodes --type context
chronicle-graph nodes --json
chronicle-graph edges
chronicle-graph edges --type chronicle_has_event
chronicle-graph edges --json
```

Expected:

- commands exit 0
- JSON outputs parse correctly
- `nodes --type context` returns only context nodes
- `edges --type chronicle_has_event` returns only matching edges
- JSONL remains unchanged

## Non-goal Checks

Confirm that v0.4 does not introduce:

- GraphRAG query engine
- embeddings
- vector DB
- graph DB
- external LLM calls
- live dashboard server
- editing UI
- authentication
- cloud sync
- automatic LLM injection
- automatic repair
- cryptographic signing

## Release Pass Criteria

v0.4 smoke passes if:

- all tests pass
- doctor runs
- export manifest appears in supported outputs
- redaction-aware export is opt-in and works for YAML/HTML
- dashboard navigation and local filtering are present
- graph inspection commands run and do not mutate JSONL
- no non-goal has been introduced

## RDE Smoke Review

### Preserved

- JSONL primary record
- Derived-only exports
- Static read-only dashboard
- No GraphRAG engine

### Transformed

- Local operational visibility is improved

### Added

- Doctor verification
- Export provenance verification
- Redaction-aware export verification
- Dashboard inspection verification
- Graph inspection verification

### Deviation Risks

- Do not treat redaction-aware export as access control
- Do not treat Export Manifest as cryptographic proof
- Do not treat graph inspection as semantic retrieval
