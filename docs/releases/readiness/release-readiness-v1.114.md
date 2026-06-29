# Release Readiness v1.114

- status: ready
- checks:
  - `./.venv/bin/ruff check src tests`
  - `./.venv/bin/pytest -q`
- notes:
  - `/api/audit` now renders an audit governance summary rail above the event stream
  - audit detail now renders an `Audit Governance` notice with implication and impacted-target context
