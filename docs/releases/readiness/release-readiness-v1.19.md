# Chronicle Stack v1.19.0 Release Readiness

Related: `../../adr/0025-local-ui-i18n-presentation-boundary.md`, `../../adr/0038-local-navigation-provider-response-and-runtime-preview-structured-i18n.md`, `../status/release-status-v1.19.0.md`, `../smoke/smoke-test-v1.19.md`

## Decision

Chronicle Stack `v1.19.0` is ready for repository-side release preparation after the local navigation-provider-response-runtime-preview structured-i18n slice, release notes, smoke profile, release status, version bump, and passing verification are merged.

## Scope

`v1.19.0` is currently framed as:

- structured `label_key` fields for related-link navigation labels
- structured `message_key` fields for provider-response summaries
- structured `title_key` and `title_params` fields for runtime-preview titles
- renderer preference for structured navigation/provider/runtime fields with fallback string preservation
- smoke/test coverage for explicit navigation/provider/runtime presentation contracts

## Required verification

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

## Boundary confirmation

`v1.19.0` does not imply:

- hosted authentication or multi-user authority
- translated machine-readable status codes or ids
- new durable storage for presentation-only navigation/provider/runtime wording
- default-on GUI mutation
