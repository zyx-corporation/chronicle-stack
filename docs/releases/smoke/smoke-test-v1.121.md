# Smoke Test v1.121

Related: `../readiness/release-readiness-v1.121.md`, `../status/release-status-v1.121.0.md`, `../notes/release-notes-v1.121.0.md`, `../remaining/v1.121-release-remaining-issues.md`

## Commands

- `./.venv/bin/pytest -q tests/test_ui_server.py -k "html or test_ui_data_service_read_endpoints or test_ui_data_service_detail_endpoints"`
- `python -m chronicle.cli ui --json`

## Expected

- `/api/review-queue` renders a `Review Queue Workspace` panel above the table
- the endpoint payload includes `review_queue_summary`
- existing review actions remain preview-only unless the broader mutation boundary is enabled
