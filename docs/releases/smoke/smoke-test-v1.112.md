# Smoke Test v1.112

Related: `../readiness/release-readiness-v1.112.md`, `../status/release-status-v1.112.0.md`, `../notes/release-notes-v1.112.0.md`, `../remaining/v1.112-release-remaining-issues.md`

## Commands

- `./.venv/bin/pytest -q tests/test_ui_server.py -k "test_ui_data_service_read_endpoints or test_ui_data_service_detail_endpoints or trust_workspace_payloads_capture_withdrawal_history or query_engine_trial"`
- `python -m chronicle.cli ui --json`

## Expected

- `/api/runtime-records` rows include `posture_role`, `downstream_boundary_note`, `trial_sufficiency_summary`, and `handoff_summary`
- `/api/summary-jobs` rows include concise package, auth, and identity assurance summaries
- runtime and summary-job detail payloads reuse the same enriched workspace contract
