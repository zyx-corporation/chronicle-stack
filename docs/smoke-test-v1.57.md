# Chronicle Stack v1.57.0 Smoke Test

Related: `docs/release-readiness-v1.57.md`, `docs/release-status-v1.57.0.md`, `docs/release-notes-v1.57.0.md`, `docs/adr/0076-local-reviewer-context-detail-localization.md`

This smoke profile validates the `v1.57.0` release track as a local reviewer-context detail localization slice.

- `chronicle --version` reports `1.57.0`
- `chronicle ui-smoke` passes in read-only local mode
- `chronicle ui-smoke --json` reports `passed: true`
- `ruff check src tests` passes
- `pytest` passes
