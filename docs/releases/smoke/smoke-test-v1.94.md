# Smoke Test v1.94

## Commands

- `ruff check src tests`
- `pytest -q`
- `python -m chronicle.cli add-context --title "Federation Preview UI Smoke" --summary "Smoke context" --json`
- `python -m chronicle.cli federation package create --purpose "Smoke review" --target-node node:partner:beta --output-dir /tmp/chronicle-federation-package-ui-preview`
- `python -m chronicle.cli federation package preview --package-dir /tmp/chronicle-federation-package-ui-preview --json`
- `python -m chronicle.cli federation package import-preview --package-dir /tmp/chronicle-federation-package-ui-preview --json`
