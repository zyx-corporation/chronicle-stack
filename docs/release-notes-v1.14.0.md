# Chronicle Stack v1.14.0 Release Notes

Related: `docs/adr/0025-local-ui-i18n-presentation-boundary.md`, `docs/adr/0033-local-reviewer-boundary-derived-fallback-copy.md`, `docs/release-readiness-v1.14.md`, `docs/smoke-test-v1.14.md`

## Summary

Chronicle Stack `v1.14.0` is currently framed as a local reviewer-boundary derived-fallback-copy release over the published `v1.13.0` baseline.

## Highlights

### Derived reviewer-boundary fallback copy

`v1.14.0` is intended to include:

- deterministic fallback message and fact-line copy for reviewer-boundary drilldown payloads
- explicit drilldown variants for row-detail versus overview-dominant summaries
- preserved machine-readable reviewer-boundary values in API payloads
- read-only smoke/test coverage for explicit fallback-copy and variant fields

### i18n-ready presentation alignment

`v1.14.0` is intended to include:

- continued presentation-only separation between localized copy and authoritative contracts
- reduced payload-level wording drift across overview, list, and detail drilldown summaries
- smoke extensions only where new read-only derived fallback-copy fields become explicit

### Preserved local-first contract

`v1.14.0` preserves:

- local single-operator scope
- read-only derived surfaces
- CLI/JSON authority over presentation summaries
- no new reviewer-boundary persistence

## Boundary

`v1.14.0` does not add:

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
chronicle 1.14.0
```
