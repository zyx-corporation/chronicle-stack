# Release Readiness v1.110

- status: ready
- checks:
  - `./.venv/bin/ruff check src tests`
  - `./.venv/bin/pytest -q`
- notes:
  - federation package preview now exposes route, trust, consent, and import implication summaries
  - preview and import-preview remain advisory inspection surfaces over an explicitly supplied local bundle directory
