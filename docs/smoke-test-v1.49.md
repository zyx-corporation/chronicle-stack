# Chronicle Stack v1.49.0 Smoke Test

Related: `docs/release-readiness-v1.49.md`, `docs/release-status-v1.49.0.md`, `docs/release-notes-v1.49.0.md`, `docs/adr/0068-local-package-readiness-command-detail-rendering.md`

This smoke profile validates the `v1.49.0` release track as a local package-readiness command-detail rendering slice.

- `chronicle --version` reports `1.49.0`
- `chronicle ui-smoke` passes in read-only local mode
- `chronicle ui-smoke --json` reports `passed: true`
- `ruff check src tests` passes
- `pytest` passes
