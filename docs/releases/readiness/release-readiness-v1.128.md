# Release Readiness v1.128

- status: ready
- checks:
  - `./.venv/bin/ruff check src tests`
  - `./.venv/bin/pytest -q`
- notes:
  - workspace table list-query predicates now flow through shared helpers
  - runtime records, review queue, and summary jobs keep the same reviewer-boundary and metadata search behavior
