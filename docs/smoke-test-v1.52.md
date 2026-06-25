# Chronicle Stack v1.52.0 Smoke Test

Related: `docs/release-readiness-v1.52.md`, `docs/release-status-v1.52.0.md`, `docs/release-notes-v1.52.0.md`, `docs/adr/0071-local-preview-contract-error-summary-localization.md`

This smoke profile validates the `v1.52.0` release track as a local preview-contract error-summary localization slice.

- `chronicle --version` reports `1.52.0`
- `chronicle ui-smoke` passes in read-only local mode
- `chronicle ui-smoke --json` reports `passed: true`
- `ruff check src tests` passes
- `pytest` passes
