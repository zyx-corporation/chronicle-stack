# Smoke Test v2.0

Related: `../readiness/release-readiness-v2.0.md`, `../status/release-status-v2.0.0.md`, `../notes/release-notes-v2.0.0.md`, `../remaining/v2.0-release-remaining-issues.md`

## Commands

- `./.venv/bin/ruff check src tests`
- `./.venv/bin/pytest -q`
- `./.venv/bin/python -m chronicle.cli --version`
- `./.venv/bin/python -m chronicle.cli ui-smoke --json`

## Expected

- full lint and test validation complete successfully
- `chronicle --version` reports `2.0.0`
- `ui-smoke --json` reports `passed: true`, `read_only: true`, `server_started: false`, `browser_required: false`, and `external_runtime: false`
- roadmap and release pointers agree on the `v2.0.0` release lane
