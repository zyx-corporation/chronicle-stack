# Smoke Test v1.124

Related: `../readiness/release-readiness-v1.124.md`, `../status/release-status-v1.124.0.md`, `../notes/release-notes-v1.124.0.md`, `../remaining/v1.124-release-remaining-issues.md`

## Commands

- `./.venv/bin/pytest -q tests/test_ui_server.py -k "html or test_ui_data_service_detail_endpoints"`
- `python -m chronicle.cli ui --json`

## Expected

- action preview still renders `Detail`, `Recovery Contract`, `Review Action`, and `Current Result`
- those subsections now flow through the shared notice-section grouping helper
- detail payloads and mutation preview semantics remain unchanged
