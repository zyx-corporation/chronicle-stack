# Chronicle Stack v1.42.0 Smoke Test

Related: `docs/release-readiness-v1.42.md`, `docs/release-status-v1.42.0.md`, `docs/release-notes-v1.42.0.md`, `docs/adr/0061-local-review-status-code-contract-structured-summaries.md`

This smoke profile validates the `v1.42.0` release track as a local review-status-code-contract structured-summary slice.

- `chronicle --version` reports `1.42.0`
- `chronicle ui-smoke` passes in read-only local mode
- `chronicle ui-smoke --json` reports `passed: true`
- `ruff check src tests` passes
- `pytest` passes
