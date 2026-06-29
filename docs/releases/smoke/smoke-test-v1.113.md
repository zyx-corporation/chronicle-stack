# Smoke Test v1.113

Related: `../readiness/release-readiness-v1.113.md`, `../status/release-status-v1.113.0.md`, `../notes/release-notes-v1.113.0.md`, `../remaining/v1.113-release-remaining-issues.md`

## Commands

- `./.venv/bin/pytest -q tests/test_ui_server.py -k "html or test_ui_data_service_read_endpoints or test_ui_data_service_detail_endpoints or trust_workspace_payloads_capture_withdrawal_history or query_engine_trial"`
- `python -m chronicle.cli ui --json`

## Expected

- runtime record detail renders a `Runtime Workspace` notice
- summary-job detail renders a `Summary Job Workspace` notice
- the new notices expose the workspace summaries without changing read-only boundaries
