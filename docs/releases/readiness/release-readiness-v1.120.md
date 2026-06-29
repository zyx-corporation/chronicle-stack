# Release Readiness v1.120

- status: ready
- checks:
  - `./.venv/bin/ruff check src tests`
  - `./.venv/bin/pytest -q`
- notes:
  - `/api/runtime-records` now renders a `Runtime Records Workspace` panel above the table
  - `/api/summary-jobs` now renders a `Summary Jobs Workspace` panel above the table
