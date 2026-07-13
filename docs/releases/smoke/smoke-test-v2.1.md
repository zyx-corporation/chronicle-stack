# Smoke Test v2.1

Related: `../readiness/release-readiness-v2.1.md`, `../status/release-status-v2.1.0.md`, `../notes/release-notes-v2.1.0.md`, `../remaining/v2.1-release-remaining-issues.md`

## Commands

- `./.venv/bin/ruff check src/ tests/`
- `./.venv/bin/pytest -q`
- `./.venv/bin/python -m chronicle.cli --version`
- `./.venv/bin/python -m chronicle.cli ui-smoke --json`
- initialize a temporary Chronicle, run `chronicle index rebuild`, then `chronicle doctor --json`

## Expected

- lint and tests complete successfully
- `chronicle --version` reports `2.1.0`
- UI smoke reports `passed: true`, `read_only: true`, `server_started: false`, and `external_runtime: false`
- index rebuild succeeds and doctor reports zero errors
- runtime status remains explicit/manual and no external provider call occurs
- release pointers agree on the `v2.1.0` release lane
