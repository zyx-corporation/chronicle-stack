# Smoke Test v1.125

Related: `../readiness/release-readiness-v1.125.md`, `../status/release-status-v1.125.0.md`, `../notes/release-notes-v1.125.0.md`, `../remaining/v1.125-release-remaining-issues.md`

## Commands

- `./.venv/bin/pytest -q tests/test_ui_server.py -k "html or test_ui_data_service_detail_endpoints"`
- `python -m chronicle.cli ui --json`

## Expected

- runtime records, review queue, and summary jobs still render the same route-level control rows
- grouped workspace button rows now flow through the shared helper in route and overview panels
- filters, sort order, and mutation preview behavior remain unchanged
