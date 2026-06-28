# Smoke Test v1.74

## Commands

- `./.venv/bin/ruff check src tests`
- `./.venv/bin/pytest -q`
- `./.venv/bin/python -m chronicle.cli --version`
- `./.venv/bin/python -m chronicle.cli package query-engine-bundle --query "graph context" --output-dir handoff-bundle`
- `cat handoff-bundle/ACCEPTANCE_CHECKLIST.md`
