# Release Readiness v1.118

- status: ready
- checks:
  - `./.venv/bin/ruff check src tests`
  - `./.venv/bin/pytest -q`
- notes:
  - boundary detail now surfaces a governance notice with links back to `/api/boundary` and the latest related audit when derived
  - lifecycle detail now surfaces a governance notice with links back to `/api/lifecycle` and the latest related audit when derived
