# Smoke Test v1.84

## Commands

- `ruff check src tests`
- `pytest -q`
- `python -m chronicle.cli object record --type question --summary "Smoke question" --created-by smoke --json`
- `python -m chronicle.cli object list --json`
- `python -m chronicle.cli ui-smoke --json`
