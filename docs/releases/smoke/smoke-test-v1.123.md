# Smoke Test v1.123

Related: `../readiness/release-readiness-v1.123.md`, `../status/release-status-v1.123.0.md`, `../notes/release-notes-v1.123.0.md`, `../remaining/v1.123-release-remaining-issues.md`

## Commands

- `./.venv/bin/pytest -q tests/test_ui_server.py -k "html or test_ui_data_service_detail_endpoints"`
- `python -m chronicle.cli ui --json`

## Expected

- detail views still render navigation, notices, and record JSON in the same order
- navigation and notice panels now flow through the shared multi-panel detail helper
- detail payloads and notice semantics remain unchanged
