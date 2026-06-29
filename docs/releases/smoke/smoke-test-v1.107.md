# Smoke Test v1.107

Related: `../readiness/release-readiness-v1.107.md`, `../status/release-status-v1.107.0.md`, `../notes/release-notes-v1.107.0.md`, `../remaining/v1.107-release-remaining-issues.md`

## Commands

- `./.venv/bin/pytest -q tests/test_ui_server.py -k "test_ui_overview_data or current_work_summary or html_shell"`
- `python -m chronicle.cli ui --json`

## Expected

- `/api/overview` includes `current_work_summary`
- the local web overview shows a `Current Work` panel with links into question, proposal, objection, and artifact detail flows
