# Smoke Test v1.118

Related: `../readiness/release-readiness-v1.118.md`, `../status/release-status-v1.118.0.md`, `../notes/release-notes-v1.118.0.md`, `../remaining/v1.118-release-remaining-issues.md`

## Commands

- `./.venv/bin/pytest -q tests/test_ui_server.py -k "html or test_ui_data_service_read_endpoints or test_ui_data_service_detail_endpoints"`
- `python -m chronicle.cli ui --json`

## Expected

- `/api/boundary/<rule_id>` renders a governance notice with navigation back to `/api/boundary`
- `/api/lifecycle/<lifecycle_id>` renders a governance notice with navigation back to `/api/lifecycle`
- when related audit evidence is derived, both notices also expose a link to the latest audit detail
