# Smoke Test v1.117

Related: `../readiness/release-readiness-v1.117.md`, `../status/release-status-v1.117.0.md`, `../notes/release-notes-v1.117.0.md`, `../remaining/v1.117-release-remaining-issues.md`

## Commands

- `./.venv/bin/pytest -q tests/test_ui_server.py -k "html or test_ui_data_service_read_endpoints or test_ui_data_service_detail_endpoints"`
- `python -m chronicle.cli ui --json`

## Expected

- `/api/boundary` renders a `Boundary Governance` summary rail above the rule table
- `/api/lifecycle` renders a `Lifecycle Governance` summary rail above the marker table
- both routes remain read-only and keep their existing detail navigation
