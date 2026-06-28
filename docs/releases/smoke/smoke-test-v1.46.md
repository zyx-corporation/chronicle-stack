# Chronicle Stack v1.46.0 Smoke Test

Related: `../readiness/release-readiness-v1.46.md`, `../status/release-status-v1.46.0.md`, `../notes/release-notes-v1.46.0.md`, `../../adr/0065-local-invocation-plan-command-detail-rendering.md`

This smoke profile validates the `v1.46.0` release track as a local invocation-plan command-detail rendering slice.

- `chronicle --version` reports `1.46.0`
- `chronicle ui-smoke` passes in read-only local mode
- `chronicle ui-smoke --json` reports `passed: true`
- `ruff check src tests` passes
- `pytest` passes
