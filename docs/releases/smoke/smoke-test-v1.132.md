# Smoke Test v1.132

Related: `../readiness/release-readiness-v1.132.md`, `../status/release-status-v1.132.0.md`, `../notes/release-notes-v1.132.0.md`, `../remaining/v1.132-release-remaining-issues.md`

## Commands

- `./.venv/bin/pytest -q tests/test_ui_server.py -k "html or test_ui_data_service_detail_endpoints"`
- `python -m chronicle.cli ui --json`

## Expected

- auth boundary overview still renders the same latest response navigation target
- that latest-response line now flows through the shared workspace helper
- other overview panels, detail notices, and list interactions remain unchanged
