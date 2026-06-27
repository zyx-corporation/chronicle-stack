# Chronicle Stack v1.59.0 Smoke Test

Related: `docs/release-readiness-v1.59.md`, `docs/release-status-v1.59.0.md`, `docs/release-notes-v1.59.0.md`, `docs/adr/0078-local-invocation-auth-mutation-boolean-detail-localization.md`

This smoke profile validates the `v1.59.0` release track as a local invocation/auth/mutation boolean-detail localization slice.

- `chronicle --version` reports `1.59.0`
- `chronicle ui-smoke` passes in read-only local mode
- `chronicle ui-smoke --json` reports `passed: true`
- `ruff check src tests` passes
- `pytest` passes
