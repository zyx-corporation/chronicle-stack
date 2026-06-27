# Chronicle Stack v1.60.0 Smoke Test

Related: `docs/release-readiness-v1.60.md`, `docs/release-status-v1.60.0.md`, `docs/release-notes-v1.60.0.md`, `docs/adr/0079-local-target-state-recovery-and-review-capability-status-localization.md`

This smoke profile validates the `v1.60.0` release track as a local target-state-recovery and review-capability status localization slice.

- `chronicle --version` reports `1.60.0`
- `chronicle ui-smoke` passes in read-only local mode
- `chronicle ui-smoke --json` reports `passed: true`
- `ruff check src tests` passes
- `pytest` passes
