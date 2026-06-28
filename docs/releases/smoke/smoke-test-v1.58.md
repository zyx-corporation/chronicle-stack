# Chronicle Stack v1.58.0 Smoke Test

Related: `../readiness/release-readiness-v1.58.md`, `../status/release-status-v1.58.0.md`, `../notes/release-notes-v1.58.0.md`, `../../adr/0077-local-response-metadata-and-runtime-config-detail-localization.md`

This smoke profile validates the `v1.58.0` release track as a local response-metadata and runtime-config detail localization slice.

- `chronicle --version` reports `1.58.0`
- `chronicle ui-smoke` passes in read-only local mode
- `chronicle ui-smoke --json` reports `passed: true`
- `ruff check src tests` passes
- `pytest` passes
