# Smoke Test v2.2

Related: `../readiness/release-readiness-v2.2.md`, `../status/release-status-v2.2.0.md`, `../notes/release-notes-v2.2.0.md`, `../remaining/v2.2-release-remaining-issues.md`

## Commands

- `./.venv/bin/ruff check src/ tests/`
- `./.venv/bin/pytest -q`
- `./.venv/bin/python -m chronicle.cli --version`
- `./.venv/bin/python -m chronicle.cli ui-smoke --json`

## Expected

- lint and tests complete successfully
- `chronicle --version` reports `2.2.0`
- UI smoke remains read-only and reports no external runtime
- AI boundary JSON contains structured interpretation warnings
- release pointers agree on `v2.2.0`
