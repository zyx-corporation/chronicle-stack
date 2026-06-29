# Smoke Test v1.119

Related: `../readiness/release-readiness-v1.119.md`, `../status/release-status-v1.119.0.md`, `../notes/release-notes-v1.119.0.md`, `../remaining/v1.119-release-remaining-issues.md`

## Commands

- `./.venv/bin/pytest -q tests/test_ui_server.py -k "html or federation_package_preview_query_surfaces or test_ui_data_service_read_endpoints or test_ui_data_service_detail_endpoints"`
- `python -m chronicle.cli ui --json`

## Expected

- `/api/audit`, `/api/boundary`, `/api/lifecycle`, and `/api/federation-package-preview` still render their existing panels
- those multi-panel routes now share the same route composition helper
- response JSON visibility and detail navigation remain unchanged
