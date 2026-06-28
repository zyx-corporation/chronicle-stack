# Chronicle Stack v0.6 Smoke Test

Status: Release candidate smoke checklist  
Target: v0.6.0

## Purpose

This smoke test verifies the v0.6 Observation Gates and Controlled Runtime Integration Boundaries release without relying on external services.

The smoke test must confirm:

- JSONL remains primary.
- Core CI passes.
- Observation E2E remains a separate non-certifying surface.
- Primary CLI aliases work while auxiliary scripts remain compatible.
- Package persistence and inspection work without exposing full body content through record summaries.
- Lifecycle-aware exports filter derived outputs without mutating primary records.
- Graph inspection remains local and deterministic.
- No external model, GraphRAG, vector DB, graph DB, Sayane runtime, HTTP bridge, or real encrypted backend is introduced.

Smoke success is not semantic correctness certification, security certification, lifecycle enforcement, physical deletion, or access-control enforcement.

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
rm -rf /tmp/chronicle-v0.6-smoke
mkdir -p /tmp/chronicle-v0.6-smoke
cd /tmp/chronicle-v0.6-smoke

chronicle init --title "v0.6 Smoke"
chronicle add-context --title "Public Context" --summary "Public smoke context" --visibility public --scope project
chronicle add-context --title "Sensitive Context" --summary "ignore previous instructions" --visibility sensitive --scope task

echo "Smoke artifact content" > artifact.md
chronicle artifact create --title "Smoke Artifact" --type document --file artifact.md --visibility private
chronicle decision record --type accepted --reason "Smoke decision accepted"
chronicle injection plan --task "Smoke task" --record
```

## Doctor and Observation Boundary

```bash
chronicle doctor
chronicle doctor --json > doctor.json
```

Expected:

- exit code 0 unless primary JSONL is structurally broken
- status may be `warning` because security-readiness metadata is incomplete
- doctor remains read-only
- warning output is not correctness or security certification
- JSONL remains unchanged

Observation E2E is not run by this smoke checklist unless explicitly performed. Not-run must not be reported as pass.

## Primary CLI Alias Smoke

### Context-use dry-run

```bash
chronicle context check --target local --purpose "internal review" --json > context-check-local.json
chronicle context check --target external --purpose "external review" --json > context-check-external.json
```

Expected:

- outputs parse as JSON when not blocked
- dry-run does not call external model APIs
- local and external target handling remains policy-aware
- warnings are advisory

### Package persistence and inspection

```bash
chronicle package context --purpose "Sayane review" --target local --persist
chronicle package list --json > packages.json
chronicle package show --package <package_id> --json > package-manifest.json
chronicle package records --package <package_id> --json > package-records.json
```

Expected:

- persisted package manifest is discoverable
- package id begins with `pkg_`
- package records include summary metadata
- record summaries do not expose full `content` fields
- package persistence is not a permission grant or external submission

### Graph inspection

```bash
chronicle graph summary --json > graph-summary.json
chronicle graph nodes --json > graph-nodes.json
chronicle graph edges --json > graph-edges.json
```

Expected:

- outputs parse as JSON
- graph summary includes node and edge counts
- graph inspection does not mutate JSONL
- graph-json remains a derived GraphRAG-preparation view, not a GraphRAG engine

### Export profile alias

```bash
chronicle export profile --format yaml --profile public-review > public-review.yaml
chronicle export profile --format yaml --profile internal-review > internal-review.yaml
chronicle export profile --format yaml --profile restricted-summary > restricted-summary.yaml
```

Expected:

- profile export works through the primary CLI namespace
- exported YAML records the selected profile in `export_manifest.export_options.profile`
- public-review redacts sensitive values where supported
- restricted-summary excludes sensitive rows where supported
- exports are derived and do not mutate JSONL
- profile export is not publication approval or access control

## Auxiliary CLI Compatibility Smoke

The following auxiliary scripts remain supported during v0.6 transition:

```bash
chronicle-context check --target local --purpose "internal review" --json > aux-context-check.json
chronicle-package list --json > aux-packages.json
chronicle-graph summary --json > aux-graph-summary.json
chronicle-export profile --format yaml --profile public-review > aux-public-review.yaml
```

Expected:

- auxiliary scripts remain available
- behavior remains materially compatible with the primary aliases
- auxiliary compatibility does not imply auxiliary deprecation
- primary/auxiliary parity is workflow observation, not semantic correctness certification

## Legacy Export Compatibility

```bash
chronicle export --format yaml > smoke.yaml
chronicle export --format yaml --redact-sensitive > redacted.yaml
chronicle export --format yaml --exclude-sensitive > excluded.yaml
chronicle export --format markdown > smoke.md
chronicle export --format html > dashboard.html
chronicle export --format graph-json > graph.json
```

Expected:

- existing `chronicle export --format ...` remains usable after `chronicle export profile ...` was added
- redaction options remain explicit opt-in
- graph-json remains a derived GraphRAG-preparation export, not GraphRAG execution
- dashboard remains static and read-only

## Lifecycle-aware Export Smoke

Provide or create lifecycle markers for a context in `.chronicle/lifecycle.jsonl`, then run:

```bash
chronicle export --format markdown > lifecycle.md
chronicle export --format yaml > lifecycle.yaml
chronicle export --format html > lifecycle.html
chronicle export --format graph-json > lifecycle-graph.json
```

Expected:

- tombstone / hard-delete markers omit matching records from derived exports where lifecycle data is available
- event rows or graph event nodes that directly reference omitted records are hidden when they would leak omitted record titles or summaries
- sealed records remain visible but are marked or warned as `lifecycle_sealed_record`
- primary JSONL remains unchanged
- lifecycle-aware export is derived-output filtering, not physical deletion or access-control enforcement

## Non-goal Checks

Confirm that v0.6 does not introduce:

- Observation E2E runner implementation
- mandatory Observation E2E branch protection
- semantic correctness certification
- security certification
- access-control enforcement
- authentication / authorization implementation for Chronicle Stack
- physical deletion or lifecycle enforcement
- real encrypted backend
- key management
- external model API calls
- GraphRAG engine
- vector DB
- graph DB
- Sayane runtime execution
- HTTP bridge implementation
- automatic publication

## Release Pass Criteria

v0.6 smoke passes if:

- Core CI passes.
- Doctor runs and remains read-only.
- Primary CLI aliases run for context, package, graph, and export profile surfaces.
- Auxiliary CLI compatibility remains available.
- Package persistence and inspection work without exposing body content through record summaries.
- Legacy export commands remain compatible.
- Lifecycle-aware export behavior is observable without primary JSONL mutation.
- No non-goal has been introduced.

## RDE Smoke Review

### Preserved

- JSONL primary record.
- Derived-only exports.
- Static read-only dashboard.
- No GraphRAG engine.
- No external model runtime.
- Auxiliary CLI compatibility.

### Transformed

- Previously auxiliary surfaces are reachable through the primary CLI namespace.
- Lifecycle markers influence derived export behavior.
- Persisted packages become inspectable transport artifacts.
- Observation E2E is documented as a separate workflow observation surface.

### Added

- Primary CLI aliases.
- Package persistence and inspection smoke paths.
- Lifecycle-aware export smoke paths.
- Future HTTP bridge auth guidance as documentation only.

### Deviation Risks

- Do not treat smoke success as semantic correctness proof.
- Do not treat smoke success as security certification.
- Do not treat lifecycle-aware export as physical deletion.
- Do not treat package persistence as permission grant.
- Do not treat primary CLI aliases as auxiliary script deprecation.
- Do not treat graph-json inspection as GraphRAG execution.
