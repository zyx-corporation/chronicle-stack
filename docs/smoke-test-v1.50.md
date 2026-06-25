# Chronicle Stack v1.50.0 Smoke Test

Related: `docs/release-readiness-v1.50.md`, `docs/release-status-v1.50.0.md`, `docs/release-notes-v1.50.0.md`, `docs/adr/0069-local-preview-contract-summary-command-localization.md`

This smoke profile validates the `v1.50.0` release track as a local preview-contract summary command-localization slice.

- `chronicle --version` reports `1.50.0`
- `chronicle ui-smoke` passes in read-only local mode
- `chronicle ui-smoke --json` reports `passed: true`
- `ruff check src tests` passes
- `pytest` passes
