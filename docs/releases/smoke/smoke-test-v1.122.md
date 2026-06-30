# Smoke Test v1.122

Related: `../readiness/release-readiness-v1.122.md`, `../status/release-status-v1.122.0.md`, `../notes/release-notes-v1.122.0.md`, `../remaining/v1.122-release-remaining-issues.md`

## Commands

- `./.venv/bin/pytest -q tests/test_ui_server.py -k "html or test_ui_data_service_read_endpoints or test_ui_data_service_detail_endpoints"`
- `python -m chronicle.cli ui --json`

## Expected

- runtime records, review queue, and summary jobs workspace panels still expose the same counts and latest-response navigation
- those panels now share common helper lines for counts, summary blocks, and latest-response placement
- route payloads and detail navigation remain unchanged
