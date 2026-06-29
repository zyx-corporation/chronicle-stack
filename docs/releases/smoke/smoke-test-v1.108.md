# Smoke Test v1.108

Related: `../readiness/release-readiness-v1.108.md`, `../status/release-status-v1.108.0.md`, `../notes/release-notes-v1.108.0.md`, `../remaining/v1.108-release-remaining-issues.md`

## Commands

- `./.venv/bin/pytest -q tests/test_ui_server.py -k "test_ui_overview_data or current_work_summary or html_shell"`
- `python -m chronicle.cli ui --json`

## Expected

- `/api/overview` includes `overview_evidence_summary`
- the local web overview shows an `Evidence Rail` panel with trust, boundary, audit, lifecycle, auth, and federation counts plus latest-record drilldowns
