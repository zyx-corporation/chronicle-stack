# Smoke Test v1.95

## Commands

- `ruff check src tests`
- `pytest -q`
- `python -m chronicle.cli add-context --title "Federation Preflight Audit Smoke" --summary "Smoke context" --json`
- `python -m chronicle.cli federation consent record --target-node node:partner:beta --purpose "Smoke review" --scope project-review --granted-by reviewer --context <CONTEXT_ID> --json`
- `python -m chronicle.cli ui-smoke --json`
