# Smoke Test v2.3

Related: `../readiness/release-readiness-v2.3.md`, `../status/release-status-v2.3.0.md`, `../notes/release-notes-v2.3.0.md`, `../remaining/v2.3-release-remaining-issues.md`

## Commands

- `./.venv/bin/ruff check src/ tests/`
- `./.venv/bin/pytest -q`
- `./.venv/bin/python -m chronicle.cli --version`
- `./.venv/bin/python -m chronicle.cli ui-smoke --json`
- `act pull_request -j test --matrix python-version:3.11 -P ubuntu-latest=catthehacker/ubuntu:act-latest`
- `./.venv/bin/chronicle ui --workspace`

## Expected

- lint and 519 tests complete successfully
- the full CI workflow succeeds locally under `act`
- `chronicle --version` reports `2.3.0`
- UI smoke remains read-only and reports no external runtime
- default UI hides workspace controls and does not expose workspace POST routes
- `--workspace` displays capture and Chronicle-question forms inside the guarded local session
- release pointers agree on `v2.3.0`
