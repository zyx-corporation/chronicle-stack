# Chronicle Stack v1.48.0 Smoke Test

Related: `../readiness/release-readiness-v1.48.md`, `../status/release-status-v1.48.0.md`, `../notes/release-notes-v1.48.0.md`, `../../adr/0067-local-retrieval-handoff-command-detail-rendering.md`

This smoke profile validates the `v1.48.0` release track as a local retrieval-handoff command-detail rendering slice.

- `chronicle --version` reports `1.48.0`
- `chronicle ui-smoke` passes in read-only local mode
- `chronicle ui-smoke --json` reports `passed: true`
- `ruff check src tests` passes
- `pytest` passes
