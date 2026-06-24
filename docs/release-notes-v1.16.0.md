# Chronicle Stack v1.16.0 Release Notes

Related: `docs/adr/0025-local-ui-i18n-presentation-boundary.md`, `docs/adr/0035-local-mutation-enablement-check-structured-i18n.md`, `docs/release-readiness-v1.16.md`, `docs/smoke-test-v1.16.md`

## Summary

Chronicle Stack `v1.16.0` is a local mutation-enablement-check structured-i18n release over the published `v1.15.0` baseline.

## Highlights

### Structured mutation enablement checks

`v1.16.0` includes:

- stable `label_key` and `detail_key` fields for mutation enablement checks
- stable `summary_key` plus params for unsatisfied mutation enablement checks
- preserved fallback labels, details, and summaries for degraded consumers

### Renderer-side checklist i18n preference

`v1.16.0` includes:

- HTML renderer support that prefers structured check keys when present
- preserved read-only rendering when only fallback strings are available
- no change to machine-readable mutation enablement check codes

### Preserved local-first contract

`v1.16.0` preserves:

- local single-operator scope
- read-only derived surfaces
- fail-closed review-mutation semantics
- CLI/JSON authority over mutation gating meaning

## Boundary

`v1.16.0` does not add:

- hosted auth or hosted review execution
- localized machine-readable check codes
- new durable storage for mutation enablement presentation fields
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
chronicle 1.16.0
```

