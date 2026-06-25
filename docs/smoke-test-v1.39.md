# Chronicle Stack v1.39.0 Smoke Test

Related: `docs/release-readiness-v1.39.md`, `docs/release-status-v1.39.0.md`, `docs/release-notes-v1.39.0.md`, `docs/adr/0058-local-overview-mutation-readiness-action-matrix-rendering.md`

This smoke profile validates the `v1.39.0` release track as a local overview-mutation-readiness action-matrix rendering slice.

- `chronicle --version` reports `1.39.0`
- `chronicle ui-smoke` passes in read-only local mode
- `chronicle ui-smoke --json` reports `passed: true`
- `ruff check src tests` passes
- `pytest` passes
