# Smoke Test v1.120

Related: `../readiness/release-readiness-v1.120.md`, `../status/release-status-v1.120.0.md`, `../notes/release-notes-v1.120.0.md`, `../remaining/v1.120-release-remaining-issues.md`

## Commands

- `./.venv/bin/pytest -q tests/test_ui_server.py -k "html or test_ui_data_service_read_endpoints or test_ui_data_service_detail_endpoints"`
- `python -m chronicle.cli ui --json`

## Expected

- `/api/runtime-records` renders a `Runtime Records Workspace` panel above the table
- `/api/summary-jobs` renders a `Summary Jobs Workspace` panel above the table
- both routes still expose their existing row tables and detail navigation
