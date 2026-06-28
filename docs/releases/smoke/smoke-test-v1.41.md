# Chronicle Stack v1.41.0 Smoke Test

Related: `../readiness/release-readiness-v1.41.md`, `../status/release-status-v1.41.0.md`, `../notes/release-notes-v1.41.0.md`, `../../adr/0060-local-overview-failure-family-structured-rendering.md`

This smoke profile validates the `v1.41.0` release track as a local overview-failure-family structured-rendering slice.

- `chronicle --version` reports `1.41.0`
- `chronicle ui-smoke` passes in read-only local mode
- `chronicle ui-smoke --json` reports `passed: true`
- `ruff check src tests` passes
- `pytest` passes
