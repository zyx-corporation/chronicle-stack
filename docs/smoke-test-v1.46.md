# Chronicle Stack v1.46.0 Smoke Test

Related: `docs/release-readiness-v1.46.md`, `docs/release-status-v1.46.0.md`, `docs/release-notes-v1.46.0.md`, `docs/adr/0065-local-invocation-plan-command-detail-rendering.md`

This smoke profile validates the `v1.46.0` release track as a local invocation-plan command-detail rendering slice.

- `chronicle --version` reports `1.46.0`
- `chronicle ui-smoke` passes in read-only local mode
- `chronicle ui-smoke --json` reports `passed: true`
- `ruff check src tests` passes
- `pytest` passes
