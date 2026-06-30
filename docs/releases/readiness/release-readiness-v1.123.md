# Release Readiness v1.123

- status: ready
- checks:
  - `./.venv/bin/ruff check src tests`
  - `./.venv/bin/pytest -q`
- notes:
  - detail rendering now composes navigation and notice panels through a shared multi-panel helper
  - record JSON placement remains unchanged while future detail panel expansion becomes more consistent
