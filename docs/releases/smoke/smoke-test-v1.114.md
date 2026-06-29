# Smoke Test v1.114

Related: `../readiness/release-readiness-v1.114.md`, `../status/release-status-v1.114.0.md`, `../notes/release-notes-v1.114.0.md`, `../remaining/v1.114-release-remaining-issues.md`

## Commands

- `./.venv/bin/pytest -q tests/test_ui_server.py -k "html or test_ui_data_service_read_endpoints or test_ui_data_service_detail_endpoints"`
- `python -m chronicle.cli ui --json`

## Expected

- `/api/audit` renders an `Audit Governance` summary rail
- audit detail renders an `Audit Governance` notice
- both surfaces stay read-only while exposing governance interpretation context
