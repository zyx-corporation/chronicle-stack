# Release Readiness v2.0

- status: ready
- checks:
  - `./.venv/bin/ruff check src tests`
  - `./.venv/bin/pytest -q`
  - `./.venv/bin/python -m chronicle.cli --version`
  - `./.venv/bin/python -m chronicle.cli ui-smoke --json`
- notes:
  - versioned source metadata and CLI version output now report `2.0.0`
  - roadmap current-position docs and release current pointers now match one coherent `v2.0.0` release lane
  - validation confirms the repository remains local-first, read-only by default, and diagnostic rather than hosted or networked
