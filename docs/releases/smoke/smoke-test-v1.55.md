# Chronicle Stack v1.55.0 Smoke Test

Related: `../readiness/release-readiness-v1.55.md`, `../status/release-status-v1.55.0.md`, `../notes/release-notes-v1.55.0.md`, `../../adr/0074-local-preview-transaction-rollback-localization.md`

This smoke profile validates the `v1.55.0` release track as a local transaction-and-rollback compact-badge localization slice.

- `chronicle --version` reports `1.55.0`
- `chronicle ui-smoke` passes in read-only local mode
- `chronicle ui-smoke --json` reports `passed: true`
- `ruff check src tests` passes
- `pytest` passes
