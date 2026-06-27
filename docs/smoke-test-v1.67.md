# Smoke Test v1.67

## Commands

- `./.venv/bin/ruff check src tests`
- `./.venv/bin/pytest -q`
- `./.venv/bin/python -m chronicle.cli --version`
- `./.venv/bin/python -m chronicle.cli runtime retrieve-plan --query "graph context" --json`
- `./.venv/bin/python -m chronicle.cli ui-smoke --json`
