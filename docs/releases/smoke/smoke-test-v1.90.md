# Smoke Test v1.90

## Commands

- `ruff check src tests`
- `pytest -q`
- `python -m chronicle.cli add-context --title "Federation Signed Package Smoke" --summary "Smoke context" --json`
- `python -m chronicle.cli federation package create --purpose "Smoke review" --target-node node:partner:beta --signature-mode local_dev --output-dir /tmp/chronicle-federation-package-signed`
- `python -m chronicle.cli federation package inspect --package-dir /tmp/chronicle-federation-package-signed --json`
- `python -m chronicle.cli federation package verify --package-dir /tmp/chronicle-federation-package-signed --json`
