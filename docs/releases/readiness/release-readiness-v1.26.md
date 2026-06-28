# Chronicle Stack v1.26.0 Release Readiness

Related: `../../adr/0045-local-package-readiness-summary-structured-contracts.md`, `../status/release-status-v1.26.0.md`, `../smoke/smoke-test-v1.26.md`

## Decision

Chronicle Stack `v1.26.0` is ready for repository-side release preparation after the local package-readiness-summary structured-contract slice, release notes, smoke profile, release status, version bump, and passing verification are merged.

## Scope

`v1.26.0` is currently framed as:

- structured `label_key` fields for package readiness summary badges
- structured `message_template_key` fields for package readiness summary copy
- smoke/test coverage for explicit package readiness summary presentation contracts

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
chronicle 1.26.0
```
