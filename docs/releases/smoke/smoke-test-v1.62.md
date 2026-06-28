# Chronicle Stack v1.62.0 Smoke Test

Related: `../readiness/release-readiness-v1.62.md`, `../status/release-status-v1.62.0.md`, `../notes/release-notes-v1.62.0.md`, `../../adr/0081-local-ui-mutation-session-continuity-and-duplicate-guard.md`

This smoke profile validates the `v1.62.0` release track as a local interactive-UI mutation-session continuity and duplicate-guard slice.

- `chronicle --version` reports `1.62.0`
- `chronicle ui-smoke` passes in read-only local mode
- `chronicle ui-smoke --json` reports `passed: true`
- `ruff check src tests` passes
- `pytest` passes
