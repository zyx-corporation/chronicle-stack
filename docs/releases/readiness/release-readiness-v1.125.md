# Release Readiness v1.125

- status: ready
- checks:
  - `./.venv/bin/ruff check src tests`
  - `./.venv/bin/pytest -q`
- notes:
  - grouped route-control button rows now compose through a shared helper
  - runtime, review queue, summary jobs, and overview workspace controls keep the same actions and ordering
