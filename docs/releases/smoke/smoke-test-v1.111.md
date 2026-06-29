# Smoke Test v1.111

Related: `../readiness/release-readiness-v1.111.md`, `../status/release-status-v1.111.0.md`, `../notes/release-notes-v1.111.0.md`, `../remaining/v1.111-release-remaining-issues.md`

## Commands

- `./.venv/bin/pytest -q tests/test_ui_server.py -k "test_ui_data_service_read_endpoints or test_ui_data_service_detail_endpoints"`
- `python -m chronicle.cli ui --json`

## Expected

- `/api/audit` includes `governance_summary`
- each audit row includes `related_boundary_rule_ids`, `related_lifecycle_ids`, `impacted_target_summary`, and `operational_implication`
- `/api/audit/<audit_id>` reuses the same enriched read-model contract
