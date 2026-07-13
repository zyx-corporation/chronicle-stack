# Release Readiness v2.1

- status: ready
- checks:
  - `./.venv/bin/ruff check src/ tests/`
  - `./.venv/bin/pytest -q`
  - `./.venv/bin/python -m chronicle.cli --version`
  - `./.venv/bin/python -m chronicle.cli ui-smoke --json`
  - temporary Chronicle `index rebuild` and `doctor --json`
- evidence:
  - source metadata and CLI output report `2.1.0`
  - Stage 2 M2.0 through M2.8 are complete with accepted ADRs and Exit RDE
  - runtime remains explicit, external network access remains default-off, and generated output remains review-required
  - external interaction receipt and command execution remain separated
  - `chronicle.jsonl` remains the primary record and derived indexes remain rebuildable
- publication:
  - cut the annotated `v2.1.0` tag from the merged release commit
  - verify tag dereference equals `origin/main`
  - publish the GitHub Release using `release-notes-v2.1.0.md`
