# Chronicle Stack v1.44.0 Smoke Test

Related: `../readiness/release-readiness-v1.44.md`, `../status/release-status-v1.44.0.md`, `../notes/release-notes-v1.44.0.md`, `../../adr/0063-local-review-route-summary-structured-details.md`

This smoke profile validates the `v1.44.0` release track as a local review-route-summary structured-detail slice.

- `chronicle --version` reports `1.44.0`
- `chronicle ui-smoke` passes in read-only local mode
- `chronicle ui-smoke --json` reports `passed: true`
- `ruff check src tests` passes
- `pytest` passes
