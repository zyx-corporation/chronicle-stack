# Chronicle Stack v0.3 Release Readiness

この文書は、Chronicle Stack v0.3 のリリース判定メモです。

## Release target

- Target version: `v0.3.0`
- Current development version: `0.3.0.dev0`
- Primary branch: `main`
- Primary record: `.chronicle/chronicle.jsonl`

## Completed phases

| Phase | Issue | PR | Status |
|---|---|---|---|
| Interface Contracts | #32 | #33 | merged |
| Contract Tests | #34 | #35 | merged |
| Persist Injection Plans | #22 | #36 | merged |
| GraphRAG Integration Boundary | #23 | #37 | merged |
| Static HTML Dashboard Export | #24 | #38 | merged |
| CLI UX and Project Metadata | #25 | #39 | merged |

## Feature summary

### Interface Contracts

`docs/interface-contracts.md` defines stability levels for JSONL, model serialization, CLI JSON output, export formats, and Python modules.

### Contract Tests

Contract tests protect machine-facing interfaces:

- JSONL primary records
- EventType payload shapes
- model serialization compatibility
- CLI JSON shape
- rebuild/export behavior

### Persisted Injection Plans

`chronicle injection plan` remains non-persistent by default.

`chronicle injection plan --record` explicitly records an `injection_plan_recorded` Event in JSONL.

### Graph-ready Export

`chronicle export --format graph-json` produces deterministic node/edge JSON derived from Chronicle records.

It is graph-ready export, not a GraphRAG engine.

### Static HTML Dashboard Export

`chronicle export --format html` produces a static read-only dashboard.

It is a human-facing derived view, not a live dashboard or editing UI.

### CLI UX and Metadata

- `chronicle --version`
- project version set to `0.3.0.dev0`
- CLI help updated for v0.3 commands
- CLI UX tests added

## Verification

Expected verification at release candidate point:

```bash
ruff check src/ tests/
pytest -v
```

Expected result:

```text
ruff: pass
pytest: 155 passed or higher
```

## Smoke test

Manual smoke test procedure:

- [v0.3 Smoke Test](smoke-test-v0.3.md)

Required checks:

- init/show works
- Context scope and visibility are preserved
- Artifact / Decision / RDE flows work
- Boundary Rules can be added and evaluated
- Injection Plan default non-persistence is preserved
- `--record` records `injection_plan_recorded`
- search and index rebuild work
- yaml / markdown / graph-json / html exports work
- graph-json is deterministic derived view
- HTML dashboard is static read-only derived view

## Compatibility

### v0.1 compatibility

- `scope_hint`-only Contexts remain readable.
- `scope` is populated from `scope_hint` when missing.

### v0.2 compatibility

- Context Scope, VisibilityHint, SourceProvenance, Boundary Rules, and non-persistent Injection Plans remain compatible.
- Injection Plans remain non-persistent by default.

### v0.3 additions

- `injection_plan_recorded` EventType is additive.
- `graph-json` export is additive.
- `html` export is additive.
- `chronicle --version` is additive.

## Non-goals for v0.3

v0.3 does not include:

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
- redaction
- final commercial license template

## Interface contract status

| Interface | Status |
|---|---|
| JSONL primary records | Primary Stable |
| Pydantic model serialization | Public Stable-ish |
| CLI `--json` output | Public Stable-ish |
| Human-readable CLI output | Human-facing |
| YAML export | Semi-public |
| Markdown export | Human-facing |
| graph-json export | Semi-public / derived |
| HTML dashboard export | Human-facing / derived |
| `.chronicle/indexes/*` | Derived/Internal |

## Risk review

### Preserved

- JSONL remains primary.
- indexes remain rebuildable.
- Boundary Rules remain advisory.
- VisibilityHint remains a hint, not access control.
- Injection Plans do not inject anything into LLMs.
- graph-json and HTML dashboard are derived views.

### Transformed

- Injection Plans can now be explicitly recorded.
- Chronicle records can now be exported as graph-ready node/edge JSON.
- Chronicle state can now be inspected through static HTML dashboard.

### Added

- Contract tests.
- Interface contract documentation.
- graph-json export.
- HTML dashboard export.
- CLI version command.

### Unresolved

- final v0.3.0 release tag not yet created.
- `CHANGELOG.md` still uses `v0.3.0 - Unreleased` until release.
- commercial license template (#26) remains on hold.
- GraphRAG engine remains future work.
- live dashboard remains future work.
- redaction option remains future work.

## Release decision

Current status: **v0.3.0 release candidate preparation is possible after smoke test and CI success.**

Required before tag:

1. Confirm main CI success.
2. Confirm `ruff check src/ tests/` pass.
3. Confirm `pytest -v` pass.
4. Complete `docs/smoke-test-v0.3.md`.
5. Change `CHANGELOG.md` from `## v0.3.0 - Unreleased` to a dated release entry.
6. Change project version from `0.3.0.dev0` to `0.3.0` if publishing a final package/release.
7. Create `v0.3.0` tag.
8. Create GitHub Release.
