# Smoke Test v1.128

Related: `../readiness/release-readiness-v1.128.md`, `../status/release-status-v1.128.0.md`, `../notes/release-notes-v1.128.0.md`, `../remaining/v1.128-release-remaining-issues.md`

## Commands

- `./.venv/bin/pytest -q tests/test_ui_server.py -k "html or test_ui_data_service_detail_endpoints"`
- `python -m chronicle.cli ui --json`

## Expected

- runtime records, review queue, and summary jobs still honor the same free-text and reviewer-boundary filters
- repeated query token extraction now flows through shared workspace query helpers
- list payloads, row rendering, and mutation preview semantics remain unchanged
