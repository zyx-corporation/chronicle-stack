# Smoke Test v1.92

## Commands

- `ruff check src tests`
- `pytest -q`
- `python -m chronicle.cli add-context --title "Federation Preview Smoke" --summary "Smoke context" --json`
- `python -m chronicle.cli federation package create --purpose "Smoke review" --target-node node:partner:beta --output-dir /tmp/chronicle-federation-package-preview`
- `python -m chronicle.cli federation package preview --package-dir /tmp/chronicle-federation-package-preview --json`
- `python -m chronicle.cli federation package import-preview --package-dir /tmp/chronicle-federation-package-preview --json`
