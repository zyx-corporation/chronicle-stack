# Release Readiness v1.109

- status: ready
- checks:
  - `./.venv/bin/ruff check src tests`
  - `./.venv/bin/pytest -q`
- notes:
  - trust nodes now expose latest activity and domain coverage summaries
  - trust relations now expose subject, active-state, audit-history, and federation-implication summaries while staying local-first and read-only
