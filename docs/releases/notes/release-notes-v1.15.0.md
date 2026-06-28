# Chronicle Stack v1.15.0 Release Notes

Related: `../../adr/0025-local-ui-i18n-presentation-boundary.md`, `../../adr/0034-local-blocker-structured-i18n-contracts.md`, `../readiness/release-readiness-v1.15.md`, `../smoke/smoke-test-v1.15.md`

## Summary

Chronicle Stack `v1.15.0` is a local blocker structured-i18n-contract release over the published `v1.14.0` baseline.

## Highlights

### Structured blocker payload copy

`v1.15.0` includes:

- stable `message_key` fields for auth-boundary and mutation blocker details
- stable `summary_key` plus params for blocker summaries
- preserved fallback `message` and `summary` strings for degraded or non-HTML consumers

### Renderer-side i18n preference

`v1.15.0` includes:

- HTML renderer support that prefers blocker keys and params when present
- preserved read-only rendering when only fallback strings are available
- no change to machine-readable blocker codes

### Preserved local-first contract

`v1.15.0` preserves:

- local single-operator scope
- read-only derived surfaces
- fail-closed review-mutation semantics
- CLI/JSON authority over blocker meaning

## Boundary

`v1.15.0` does not add:

- hosted auth or hosted review execution
- localized machine-readable blocker codes
- new durable storage for blocker presentation fields
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
chronicle 1.15.0
```

