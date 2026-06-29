# Release Readiness v1.117

- status: ready
- checks:
  - `./.venv/bin/ruff check src tests`
  - `./.venv/bin/pytest -q`
- notes:
  - `/api/boundary` now renders a `Boundary Governance` summary rail above the rule table
  - `/api/lifecycle` now renders a `Lifecycle Governance` summary rail above the marker table
