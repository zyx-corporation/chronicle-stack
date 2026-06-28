# Release Readiness v1.101

- status: ready
- checks:
  - `./.venv/bin/ruff check src tests`
  - `./.venv/bin/pytest -q`
- notes:
  - overview Federation panel now surfaces manual `import-preview` guidance alongside the existing boundary-check and package-preview templates
  - the UI remains local-first, read-only, and preview-only; no package import execution path is added
