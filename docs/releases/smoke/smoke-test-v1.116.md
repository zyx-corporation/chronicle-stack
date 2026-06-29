# Smoke Test v1.116

Related: `../readiness/release-readiness-v1.116.md`, `../status/release-status-v1.116.0.md`, `../notes/release-notes-v1.116.0.md`, `../remaining/v1.116-release-remaining-issues.md`

## Commands

- `./.venv/bin/pytest -q tests/test_ui_server.py -k "html or test_ui_data_service_read_endpoints or test_ui_data_service_detail_endpoints"`
- `python -m chronicle.cli ui --json`

## Expected

- `/api/audit` renders an `Audit Governance` summary rail followed by `Audit Timeline` and `Audit Interpretation` panels
- the timeline panel emphasizes event chronology while the interpretation panel emphasizes implication and impacted target context
- the route remains read-only and keeps existing detail navigation intact
