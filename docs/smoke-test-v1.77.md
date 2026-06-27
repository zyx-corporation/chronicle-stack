# Smoke Test v1.77

## Commands

- `./.venv/bin/ruff check src tests`
- `./.venv/bin/pytest -q`
- `./.venv/bin/python -m chronicle.cli --version`
- `./.venv/bin/python -m chronicle.cli package query-engine-trial-list --json`
- `./.venv/bin/python -m chronicle.cli package query-engine-trial-show --event <evt_id> --json`
