# Chronicle Stack v1.19.0 Release Notes

Related: `../../adr/0025-local-ui-i18n-presentation-boundary.md`, `../../adr/0038-local-navigation-provider-response-and-runtime-preview-structured-i18n.md`, `../readiness/release-readiness-v1.19.md`, `../smoke/smoke-test-v1.19.md`

## Summary

Chronicle Stack `v1.19.0` is a local navigation-provider-response-runtime-preview structured-i18n release over the published `v1.18.0` baseline.

## Highlights

### Structured navigation labels

`v1.19.0` includes:

- stable `label_key` fields for related-link navigation labels
- stable label params for dynamic record ids
- preserved fallback labels for degraded consumers

### Structured runtime-observability summaries

`v1.19.0` includes:

- stable `message_key` fields for provider-response summaries
- stable `title_key` and `title_params` fields for runtime-preview titles
- preserved read-only/local-first runtime-observability wording without changing runtime semantics

### Renderer-side navigation/provider/runtime i18n preference

`v1.19.0` includes:

- HTML renderer support that prefers structured navigation/provider/runtime fields when present
- preserved fallback-string rendering for CLI-compatible and degraded paths
- no change to machine-readable ids, paths, persisted runtime payloads, or review semantics

## Boundary

`v1.19.0` does not add:

- hosted auth or hosted review execution
- localized machine-readable ids or status codes
- new durable storage for presentation-only navigation/provider/runtime wording
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
chronicle 1.19.0
```
