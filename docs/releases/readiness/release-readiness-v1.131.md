# Release Readiness v1.131

- status: ready
- checks:
  - `./.venv/bin/ruff check src tests`
  - `./.venv/bin/pytest -q`
- notes:
  - repeated workspace panel framing now flows through a shared helper
  - runtime records, review queue, and summary jobs keep the same panel content and latest-response navigation targets
