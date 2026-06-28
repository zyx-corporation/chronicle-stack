# Chronicle Stack v1.12.0 Release Notes

Related: `../../adr/0025-local-ui-i18n-presentation-boundary.md`, `../../adr/0031-local-reviewer-boundary-presentation-drilldown.md`, `../readiness/release-readiness-v1.12.md`, `../smoke/smoke-test-v1.12.md`

## Summary

Chronicle Stack `v1.12.0` is currently framed as a local reviewer-boundary presentation-drilldown release over the published `v1.11.0` baseline.

## Highlights

### Reviewer-boundary drilldown summaries

`v1.12.0` is intended to include:

- clearer read-only summaries that connect overview aggregates to list slices
- clearer read-only summaries that connect row-level statuses to detail facts
- preserved machine-readable reviewer-boundary values in API payloads
- read-only drilldown summary payloads for runtime records, review queue rows, and summary jobs
- HTML-shell rendering for those drilldown summaries in overview, list, and detail views
- dominant reviewer-boundary state badges that jump from overview into matching list slices
- structured drilldown message/template fields that keep localized dataset and status copy in the presentation layer

### i18n-ready presentation alignment

`v1.12.0` is intended to include:

- shared reviewer-boundary fact-line wording across overview, list, and detail surfaces
- continued presentation-only separation between localized copy and authoritative contracts
- smoke extensions only where new read-only presentation surfaces become explicit

### Preserved local-first contract

`v1.12.0` preserves:

- local single-operator scope
- read-only derived surfaces
- CLI/JSON authority over presentation summaries
- no new reviewer-boundary persistence

## Boundary

`v1.12.0` does not add:

- hosted auth or hosted review execution
- localized machine-readable payload values
- new durable storage for reviewer-boundary drilldown summaries
- default-on GUI mutation

## Verification

```bash
python -m pip install -e ".[dev]"
chronicle --version
ruff check src/ tests/
pytest
chronicle ui-smoke
chronicle ui-smoke --json
```

Expected current version baseline:

```text
chronicle 1.12.0
```
