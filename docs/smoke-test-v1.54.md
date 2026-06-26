# Chronicle Stack v1.54.0 Smoke Test

Related: `docs/release-readiness-v1.54.md`, `docs/release-status-v1.54.0.md`, `docs/release-notes-v1.54.0.md`, `docs/adr/0073-local-preview-write-route-compact-localization.md`

This smoke profile validates the `v1.54.0` release track as a local write-route compact-badge localization slice.

- `chronicle --version` reports `1.54.0`
- `chronicle ui-smoke` passes in read-only local mode
- `chronicle ui-smoke --json` reports `passed: true`
- `ruff check src tests` passes
- `pytest` passes
