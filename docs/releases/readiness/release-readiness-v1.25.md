# Chronicle Stack v1.25.0 Release Readiness

Related: `../../adr/0044-local-embedded-package-review-structured-contracts.md`, `../status/release-status-v1.25.0.md`, `../smoke/smoke-test-v1.25.md`

## Decision

Chronicle Stack `v1.25.0` is ready for repository-side release preparation after the local embedded-package-review structured-contract slice, release notes, smoke profile, release status, version bump, and passing verification are merged.

## Scope

`v1.25.0` is currently framed as:

- shared structured `message_key` fields for embedded package-review status wording
- shared structured `counts_summary_key` fields for embedded package-review record/warning/finding counts
- shared structured `boundary_note_key` fields for embedded package-review derived/read-only wording
- smoke/test coverage for explicit embedded package-review presentation contracts

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
chronicle 1.25.0
```
