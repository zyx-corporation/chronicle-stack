# Smoke Test v1.130

Related: `../readiness/release-readiness-v1.130.md`, `../status/release-status-v1.130.0.md`, `../notes/release-notes-v1.130.0.md`, `../remaining/v1.130-release-remaining-issues.md`

## Commands

- `./.venv/bin/pytest -q tests/test_ui_server.py -k "html or test_ui_data_service_detail_endpoints"`
- `python -m chronicle.cli ui --json`

## Expected

- runtime records still sort correctly for both mutation-first and auth-first modes
- repeated runtime readiness ordering now flows through the shared comparator
- review queue, summary jobs, and all non-runtime list behavior remain unchanged
