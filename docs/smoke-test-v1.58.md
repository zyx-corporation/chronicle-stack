# Chronicle Stack v1.58.0 Smoke Test

Related: `docs/release-readiness-v1.58.md`, `docs/release-status-v1.58.0.md`, `docs/release-notes-v1.58.0.md`, `docs/adr/0077-local-response-metadata-and-runtime-config-detail-localization.md`

This smoke profile validates the `v1.58.0` release track as a local response-metadata and runtime-config detail localization slice.

- `chronicle --version` reports `1.58.0`
- `chronicle ui-smoke` passes in read-only local mode
- `chronicle ui-smoke --json` reports `passed: true`
- `ruff check src tests` passes
- `pytest` passes
