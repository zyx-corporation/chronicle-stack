# Release Readiness v1.108

- status: ready
- checks:
  - `./.venv/bin/ruff check src tests`
  - `./.venv/bin/pytest -q`
- notes:
  - overview now exposes and renders an evidence-rail aggregate for trust, boundary, audit, lifecycle, auth, and federation inspection
  - the panel stays local-first and read-only, linking to detail surfaces without introducing automation or mutation behavior
