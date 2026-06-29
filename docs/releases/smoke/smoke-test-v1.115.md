# Smoke Test v1.115

Related: `../readiness/release-readiness-v1.115.md`, `../status/release-status-v1.115.0.md`, `../notes/release-notes-v1.115.0.md`, `../remaining/v1.115-release-remaining-issues.md`

## Commands

- `./.venv/bin/pytest -q tests/test_ui_server.py -k "html or federation_package_preview_query_surfaces or http_server_endpoints_and_detail_routes"`
- `python -m chronicle.cli ui --json`

## Expected

- `/api/federation-package-preview` renders a `Federation Package Preview` summary rail
- the route surfaces package route, trust reference, consent, and import implication summary panels before the raw JSON payload
- the route remains read-only and navigational, with links out to trust reference and latest audit details
