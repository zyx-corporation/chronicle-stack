# Smoke Test v1.72

## Commands

- `./.venv/bin/ruff check src tests`
- `./.venv/bin/pytest -q`
- `./.venv/bin/python -m chronicle.cli --version`
- `./.venv/bin/python -m chronicle.cli package query-engine-adapter --query "graph context"`
- `./.venv/bin/python -m chronicle.cli runtime retrieve-plan --query "graph context" --json`
