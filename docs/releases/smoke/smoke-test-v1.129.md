# Smoke Test v1.129

Related: `../readiness/release-readiness-v1.129.md`, `../status/release-status-v1.129.0.md`, `../notes/release-notes-v1.129.0.md`, `../remaining/v1.129-release-remaining-issues.md`

## Commands

- `./.venv/bin/pytest -q tests/test_ui_server.py -k "html or test_ui_data_service_detail_endpoints"`
- `python -m chronicle.cli ui --json`

## Expected

- review queue and summary jobs still sort attention/review views with the same drift, advisory, ready, package, and resolved ordering
- repeated review attention ranking now flows through the shared helper
- route-specific sort tie-break rules and mutation/list behavior remain unchanged
