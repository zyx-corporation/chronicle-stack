# Smoke Test v1.126

Related: `../readiness/release-readiness-v1.126.md`, `../status/release-status-v1.126.0.md`, `../notes/release-notes-v1.126.0.md`, `../remaining/v1.126-release-remaining-issues.md`

## Commands

- `./.venv/bin/pytest -q tests/test_ui_server.py -k "html or test_ui_data_service_detail_endpoints"`
- `python -m chronicle.cli ui --json`

## Expected

- runtime records, review queue, and summary jobs still render the same filter, sort, button rows, mutation form, and preview status blocks
- the repeated route-level workspace table control cluster now flows through the shared helper
- list payloads, table row rendering, and mutation preview semantics remain unchanged
