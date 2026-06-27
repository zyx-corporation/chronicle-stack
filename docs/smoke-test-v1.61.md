# Chronicle Stack v1.61.0 Smoke Test

Related: `docs/release-readiness-v1.61.md`, `docs/release-status-v1.61.0.md`, `docs/release-notes-v1.61.0.md`, `docs/adr/0080-local-ui-mutation-session-token-boundary.md`

This smoke profile validates the `v1.61.0` release track as a local interactive-UI mutation-token hardening slice.

- `chronicle --version` reports `1.61.0`
- `chronicle ui-smoke` passes in read-only local mode
- `chronicle ui-smoke --json` reports `passed: true`
- `ruff check src tests` passes
- `pytest` passes
