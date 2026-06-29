# Release Readiness v1.115

- status: ready
- checks:
  - `./.venv/bin/ruff check src tests`
  - `./.venv/bin/pytest -q`
- notes:
  - `/api/federation-package-preview` now renders a `Federation Package Preview` summary rail above the raw payload
  - package route, trust reference, consent, and import implication summaries now render as dedicated read-only panels in the local UI
