# Smoke Test v1.127

Related: `../readiness/release-readiness-v1.127.md`, `../status/release-status-v1.127.0.md`, `../notes/release-notes-v1.127.0.md`, `../remaining/v1.127-release-remaining-issues.md`

## Commands

- `./.venv/bin/pytest -q tests/test_ui_server.py -k "html or test_ui_data_service_detail_endpoints"`
- `python -m chronicle.cli ui --json`

## Expected

- mutation enablement notices still render the same readiness, operational, reviewer, write-route, and next-step content
- those grouped mutation details now flow through shared `noticeSection(...)` subsections composed by `noticeSectionGroup(...)`
- detail payloads and mutation preview semantics remain unchanged
