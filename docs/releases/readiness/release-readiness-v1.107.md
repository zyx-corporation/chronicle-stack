# Release Readiness v1.107

- status: ready
- checks:
  - `./.venv/bin/ruff check src tests`
  - `./.venv/bin/pytest -q`
- notes:
  - overview now exposes and renders a current-work aggregate for question-centric landing
  - the panel stays local-first and read-only, linking to detail surfaces without adding mutation behavior
