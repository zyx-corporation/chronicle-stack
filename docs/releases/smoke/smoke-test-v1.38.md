# Chronicle Stack v1.38.0 Smoke Test

Related: `../readiness/release-readiness-v1.38.md`, `../status/release-status-v1.38.0.md`, `../notes/release-notes-v1.38.0.md`, `../../adr/0057-local-review-target-state-action-matrix-structured-contracts.md`

This smoke profile validates the `v1.38.0` release track as a local review-target-state-action-matrix structured-contract slice.

- `chronicle --version` reports `1.38.0`
- `chronicle ui-smoke` passes in read-only local mode
- `chronicle ui-smoke --json` reports `passed: true`
- `ruff check src tests` passes
- `pytest` passes
