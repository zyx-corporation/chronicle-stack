# Chronicle Stack v1.45.0 Smoke Test

Related: `docs/release-readiness-v1.45.md`, `docs/release-status-v1.45.0.md`, `docs/release-notes-v1.45.0.md`, `docs/adr/0064-local-review-command-detail-structured-rendering.md`

This smoke profile validates the `v1.45.0` release track as a local review-command-detail structured-rendering slice.

- `chronicle --version` reports `1.45.0`
- `chronicle ui-smoke` passes in read-only local mode
- `chronicle ui-smoke --json` reports `passed: true`
- `ruff check src tests` passes
- `pytest` passes
