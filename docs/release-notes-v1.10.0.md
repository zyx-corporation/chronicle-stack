# Chronicle Stack v1.10.0 Release Notes

Related: `docs/adr/0025-local-ui-i18n-presentation-boundary.md`, `docs/adr/0029-local-reviewer-boundary-observability.md`, `docs/release-readiness-v1.10.md`, `docs/smoke-test-v1.10.md`

## Summary

Chronicle Stack `v1.10.0` is currently framed as a local reviewer-boundary observability and i18n-ready presentation release over the published `v1.9.0` baseline.

## Highlights

### Reviewer-boundary overview aggregation

`v1.10.0` currently includes:

- aggregated reviewer enforcement and validation-gate counts across runtime records, review queue rows, and summary jobs
- a dedicated read-only overview panel for reviewer-boundary visibility
- preserved machine-readable status values in API payloads

### i18n-ready reviewer presentation

`v1.10.0` currently includes:

- translation-key routing for reviewer-boundary badges
- translation-key routing for reviewer-boundary metrics and fact labels
- continued presentation-only separation between localized copy and authoritative contracts

### Preserved local-first contract

`v1.10.0` preserves:

- local single-operator scope
- explicit-enable mutation boundary
- CLI/JSON authority over presentation summaries
- read-only derivation for overview aggregates

## Boundary

`v1.10.0` does not add:

- hosted auth or hosted review execution
- localized machine-readable payload values
- new durable storage for reviewer-boundary metrics
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
chronicle 1.9.0
```
