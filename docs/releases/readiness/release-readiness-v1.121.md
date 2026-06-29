# Release Readiness v1.121

- status: ready
- checks:
  - `./.venv/bin/ruff check src tests`
  - `./.venv/bin/pytest -q`
- notes:
  - `/api/review-queue` now renders a `Review Queue Workspace` panel above the table
  - the route also returns `review_queue_summary` alongside the existing review queue rows
