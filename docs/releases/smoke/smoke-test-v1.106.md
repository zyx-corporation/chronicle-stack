# Smoke Test v1.106

Related: `../readiness/release-readiness-v1.106.md`, `../status/release-status-v1.106.0.md`, `../notes/release-notes-v1.106.0.md`, `../remaining/v1.106-release-remaining-issues.md`

## Commands

- `./.venv/bin/pytest -q tests/test_ui_server.py -k "artifact_detail_exposes_workbench_summaries or html_shell"`
- `python -m chronicle.cli ui --json`

## Expected

- artifact detail exposes an `Artifact Workbench` notice in the local UI shell
- the notice shows linked context / decision / RDE / source-event / audit inspection hints without enabling mutation
