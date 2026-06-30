# Release Readiness v1.126

- status: ready
- checks:
  - `./.venv/bin/ruff check src tests`
  - `./.venv/bin/pytest -q`
- notes:
  - repeated workspace table control clusters now compose through a shared helper
  - runtime records, review queue, and summary jobs keep the same control ordering and semantics
