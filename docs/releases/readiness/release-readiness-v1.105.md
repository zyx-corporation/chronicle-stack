# Release Readiness v1.105

- status: ready
- checks:
  - `./.venv/bin/ruff check src tests`
  - `./.venv/bin/pytest -q`
- notes:
  - artifact detail now exposes workbench-ready linked context, decision, RDE, source-event, boundary, and audit summaries
  - the UI boundary remains local-first and read-only; the richer detail payload does not add mutation-capable UI flows
