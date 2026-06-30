# Release Readiness v1.124

- status: ready
- checks:
  - `./.venv/bin/ruff check src tests`
  - `./.venv/bin/pytest -q`
- notes:
  - grouped detail notice subsections can now be composed through a shared helper
  - action preview keeps the same sections and order while using the shared grouping path
