# Smoke Test v1.105

Related: `../readiness/release-readiness-v1.105.md`, `../status/release-status-v1.105.0.md`, `../notes/release-notes-v1.105.0.md`, `../remaining/v1.105-release-remaining-issues.md`

## Commands

- `./.venv/bin/pytest -q tests/test_ui_server.py -k artifact_detail_exposes_workbench_summaries`
- `python -m chronicle.cli ui --json`

## Expected

- `/api/artifacts/<id>` includes linked workbench summaries for contexts, decisions, RDE records, source events, boundary posture, and related audits
- the new artifact detail summaries stay descriptive and do not imply direct UI mutation authority
