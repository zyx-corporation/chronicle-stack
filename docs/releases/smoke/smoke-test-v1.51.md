# Chronicle Stack v1.51.0 Smoke Test

Related: `../readiness/release-readiness-v1.51.md`, `../status/release-status-v1.51.0.md`, `../notes/release-notes-v1.51.0.md`, `../../adr/0070-local-package-handoff-command-detail-rendering.md`

This smoke profile validates the `v1.51.0` release track as a local package-handoff command-detail rendering slice.

- `chronicle --version` reports `1.51.0`
- `chronicle ui-smoke` passes in read-only local mode
- `chronicle ui-smoke --json` reports `passed: true`
- `ruff check src tests` passes
- `pytest` passes
