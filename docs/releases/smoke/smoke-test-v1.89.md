# Smoke Test v1.89

## Commands

- `ruff check src tests`
- `pytest -q`
- `python -m chronicle.cli add-context --title "Federation Package Smoke" --summary "Smoke context" --json`
- `python -m chronicle.cli federation package create --purpose "Smoke review" --target-node node:partner:beta --output-dir /tmp/chronicle-federation-package`
- `python -m chronicle.cli federation package inspect --package-dir /tmp/chronicle-federation-package --json`
- `python -m chronicle.cli federation package verify --package-dir /tmp/chronicle-federation-package --json`
