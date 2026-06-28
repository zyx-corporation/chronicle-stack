# Chronicle Stack v1.18.0 Release Notes

Related: `../../adr/0025-local-ui-i18n-presentation-boundary.md`, `../../adr/0037-local-package-parity-and-preview-structured-i18n.md`, `../readiness/release-readiness-v1.18.md`, `../smoke/smoke-test-v1.18.md`

## Summary

Chronicle Stack `v1.18.0` is a local package-parity-preview structured-i18n release over the published `v1.17.0` baseline.

## Highlights

### Structured package-readiness and handoff preview summaries

`v1.18.0` includes:

- stable `message_key` fields for package-readiness summaries and detail payloads
- stable `message_key` fields for retrieval package-handoff preview payloads
- preserved fallback `message` strings for degraded consumers

### Structured preview and CLI parity summaries

`v1.18.0` includes:

- stable `message_key` fields for action-preview summaries
- stable `message_key` fields for CLI parity summaries
- preserved read-only/local-first preview guidance without changing write authority

### Renderer-side package/parity/preview i18n preference

`v1.18.0` includes:

- HTML renderer support that prefers structured package/parity/preview keys when present
- preserved fallback-string rendering for CLI-compatible and degraded paths
- no change to machine-readable status codes, action ids, persistence identifiers, or review semantics

## Boundary

`v1.18.0` does not add:

- hosted auth or hosted review execution
- localized machine-readable status codes
- new durable storage for presentation-only package/parity/preview wording
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
chronicle 1.18.0
```
