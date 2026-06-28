# Release Readiness v1.102

- status: ready
- checks:
  - `./.venv/bin/ruff check src tests`
  - `./.venv/bin/pytest -q`
- notes:
  - overview Federation panel now surfaces manual `inspect`, `preview`, and `import-preview` guidance together with the boundary-check template
  - the UI remains local-first, read-only, and preview-only; no package inspection execution path is added
