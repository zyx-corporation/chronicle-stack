# Release Readiness v1.130

- status: ready
- checks:
  - `./.venv/bin/ruff check src tests`
  - `./.venv/bin/pytest -q`
- notes:
  - runtime mutation-sort and auth-sort now flow through a shared readiness comparator
  - primary sort priority still flips correctly between mutation-first and auth-first modes
