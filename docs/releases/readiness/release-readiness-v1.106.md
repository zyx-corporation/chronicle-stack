# Release Readiness v1.106

- status: ready
- checks:
  - `./.venv/bin/ruff check src tests`
  - `./.venv/bin/pytest -q`
- notes:
  - artifact detail now renders the workbench summaries in the local web UI
  - the notice preserves the local-first, read-only boundary and does not add artifact mutation flows
