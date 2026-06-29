# Smoke Test v1.110

Related: `../readiness/release-readiness-v1.110.md`, `../status/release-status-v1.110.0.md`, `../notes/release-notes-v1.110.0.md`, `../remaining/v1.110-release-remaining-issues.md`

## Commands

- `./.venv/bin/pytest -q tests/test_ui_server.py -k "federation_package_preview_query_surfaces or test_ui_data_service_read_endpoints"`
- `python -m chronicle.cli ui --json`

## Expected

- `/api/federation-package-preview` includes `package_route_summary`, `trust_reference_summary`, `consent_summary`, and `import_implication_summary`
- preview and import-preview payloads expose handoff context without implying shipment, import, or auto-apply
