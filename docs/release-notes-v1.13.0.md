# Chronicle Stack v1.13.0 Release Notes

Related: `docs/adr/0025-local-ui-i18n-presentation-boundary.md`, `docs/adr/0032-local-reviewer-boundary-structured-presentation-contracts.md`, `docs/release-readiness-v1.13.md`, `docs/smoke-test-v1.13.md`

## Summary

Chronicle Stack `v1.13.0` is currently framed as a local reviewer-boundary structured-presentation-contract release over the published `v1.12.0` baseline.

## Highlights

### Structured reviewer-boundary drilldown copy contracts

`v1.13.0` is intended to include:

- shared message-template keys for reviewer-boundary drilldown summaries
- shared message params that keep dataset identity explicit without hard-coding per-surface wording
- preserved machine-readable reviewer-boundary values in API payloads
- read-only smoke/test coverage for explicit drilldown message-template fields

### i18n-ready presentation alignment

`v1.13.0` is intended to include:

- continued presentation-only separation between localized copy and authoritative contracts
- reduced per-surface fallback wording drift across overview, list, and detail drilldown summaries
- smoke extensions only where new read-only structured presentation fields become explicit

### Preserved local-first contract

`v1.13.0` preserves:

- local single-operator scope
- read-only derived surfaces
- CLI/JSON authority over presentation summaries
- no new reviewer-boundary persistence

## Boundary

`v1.13.0` does not add:

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
chronicle 1.13.0
```
