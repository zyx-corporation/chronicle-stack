# Smoke Test v1.93

## Commands

- `ruff check src tests`
- `pytest -q`
- `python -m chronicle.cli add-context --title "Federation Boundary Smoke" --summary "Smoke context" --json`
- `python -m chronicle.cli federation boundary check --purpose "Smoke review" --target-node node:partner:beta --visibility public --json`
- `python -m chronicle.cli federation consent record --target-node node:partner:beta --purpose "Smoke review" --scope project-review --granted-by reviewer --json`
