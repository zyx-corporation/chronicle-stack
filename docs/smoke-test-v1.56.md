# Chronicle Stack v1.56.0 Smoke Test

Related: `docs/release-readiness-v1.56.md`, `docs/release-status-v1.56.0.md`, `docs/release-notes-v1.56.0.md`, `docs/adr/0075-local-preview-write-route-detail-status-localization.md`

This smoke profile validates the `v1.56.0` release track as a local write-route detail-status localization slice.

- `chronicle --version` reports `1.56.0`
- `chronicle ui-smoke` passes in read-only local mode
- `chronicle ui-smoke --json` reports `passed: true`
- `ruff check src tests` passes
- `pytest` passes
