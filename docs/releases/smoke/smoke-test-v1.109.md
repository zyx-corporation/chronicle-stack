# Smoke Test v1.109

Related: `../readiness/release-readiness-v1.109.md`, `../status/release-status-v1.109.0.md`, `../notes/release-notes-v1.109.0.md`, `../remaining/v1.109-release-remaining-issues.md`

## Commands

- `./.venv/bin/pytest -q tests/test_ui_server.py -k "test_ui_data_service_read_endpoints or trust_workspace_payloads_capture_withdrawal_history"`
- `python -m chronicle.cli ui --json`

## Expected

- `/api/trust-nodes` includes `latest_activity_summary` and `domain_coverage_summary`
- `/api/trust-relations` includes `subject_summary`, `active_state`, `history_summary`, and `federation_implication`
- withdrawn relations remain visible as read-only trust history instead of disappearing from detail flows
