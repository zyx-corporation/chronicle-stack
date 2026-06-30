# Release Readiness v1.129

- status: ready
- checks:
  - `./.venv/bin/ruff check src tests`
  - `./.venv/bin/pytest -q`
- notes:
  - shared review attention ranking now covers both review queue and summary jobs paths
  - review queue still preserves its `review_requested` fast-path while summary jobs keeps the same route-specific tie-break behavior
