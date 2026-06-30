# Smoke Test v1.131

Related: `../readiness/release-readiness-v1.131.md`, `../status/release-status-v1.131.0.md`, `../notes/release-notes-v1.131.0.md`, `../remaining/v1.131-release-remaining-issues.md`

## Commands

- `./.venv/bin/pytest -q tests/test_ui_server.py -k "html or test_ui_data_service_detail_endpoints"`
- `python -m chronicle.cli ui --json`

## Expected

- runtime records, review queue, and summary jobs workspace panels still render the same counts, summary rails, and latest response links
- repeated workspace panel framing now flows through the shared summary panel helper
- overview, detail notices, and list interactions remain unchanged
