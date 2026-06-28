# Smoke Test v1.97

## Commands

- `ruff check src tests`
- `pytest -q`
- `python -m chronicle.cli add-context --title "Overview Overlap Smoke" --summary "Smoke context" --json`
- `python -m chronicle.cli federation consent record --target-node node:partner:beta --purpose "Smoke review" --scope project-review --context <CONTEXT_ID> --granted-by reviewer --json`
- `python -m chronicle.cli ui-smoke --json`
