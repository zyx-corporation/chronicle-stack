# Chronicle Stack v1.47.0 Smoke Test

Related: `docs/release-readiness-v1.47.md`, `docs/release-status-v1.47.0.md`, `docs/release-notes-v1.47.0.md`, `docs/adr/0066-local-review-cli-equivalent-structured-rendering.md`

This smoke profile validates the `v1.47.0` release track as a local review CLI-equivalent structured-rendering slice.

- `chronicle --version` reports `1.47.0`
- `chronicle ui-smoke` passes in read-only local mode
- `chronicle ui-smoke --json` reports `passed: true`
- `ruff check src tests` passes
- `pytest` passes
