# Chronicle Stack v1.43.0 Smoke Test

Related: `docs/release-readiness-v1.43.md`, `docs/release-status-v1.43.0.md`, `docs/release-notes-v1.43.0.md`, `docs/adr/0062-local-review-possible-error-structured-details.md`

This smoke profile validates the `v1.43.0` release track as a local review-possible-error structured-detail slice.

- `chronicle --version` reports `1.43.0`
- `chronicle ui-smoke` passes in read-only local mode
- `chronicle ui-smoke --json` reports `passed: true`
- `ruff check src tests` passes
- `pytest` passes
