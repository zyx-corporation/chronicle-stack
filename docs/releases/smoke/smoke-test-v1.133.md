# Smoke Test v1.133

Related: `../readiness/release-readiness-v1.133.md`, `../status/release-status-v1.133.0.md`, `../notes/release-notes-v1.133.0.md`, `../remaining/v1.133-release-remaining-issues.md`

## Commands

- `./.venv/bin/pytest -q tests/test_ui_server.py -k "html or test_ui_data_service_detail_endpoints"`
- `python -m chronicle.cli ui --json`

## Expected

- no behavior change from v1.132
- release trail now explicitly records that helper convergence should pause until a fresh repeated pattern appears
- current UI remains stable and test coverage stays green
