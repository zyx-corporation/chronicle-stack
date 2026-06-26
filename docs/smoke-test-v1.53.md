# Chronicle Stack v1.53.0 Smoke Test

Related: `docs/release-readiness-v1.53.md`, `docs/release-status-v1.53.0.md`, `docs/release-notes-v1.53.0.md`, `docs/adr/0072-local-preview-identity-proof-localization.md`

This smoke profile validates the `v1.53.0` release track as a local identity-proof compact-badge localization slice.

- `chronicle --version` reports `1.53.0`
- `chronicle ui-smoke` passes in read-only local mode
- `chronicle ui-smoke --json` reports `passed: true`
- `ruff check src tests` passes
- `pytest` passes
