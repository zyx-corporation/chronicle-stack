# Release Readiness v1.127

- status: ready
- checks:
  - `./.venv/bin/ruff check src tests`
  - `./.venv/bin/pytest -q`
- notes:
  - mutation enablement detail notices now compose through grouped notice sections
  - status, operational, reviewer, write-route, and next-steps content keeps the same ordering and meaning
