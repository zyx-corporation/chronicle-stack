# Release Readiness v2.2

- status: ready
- checks:
  - `./.venv/bin/ruff check src/ tests/`
  - `./.venv/bin/pytest -q`
  - `./.venv/bin/python -m chronicle.cli --version`
  - `./.venv/bin/python -m chronicle.cli ui-smoke --json`
- evidence:
  - source metadata and CLI output report `2.2.0`
  - Stage C closeout matrix maps every acceptance condition to product and test evidence
  - AI interpretation warnings have stable codes and remain separate from provider output
  - runtime/UI surfaces expose the same warning messages and next-safe actions
- publication:
  - cut annotated tag `v2.2.0` from merged main
  - verify tag dereference equals `origin/main`
  - publish GitHub Release from `release-notes-v2.2.0.md`
