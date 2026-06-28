# Smoke Test v1.86

## Commands

- `ruff check src tests`
- `pytest -q`
- `python -m chronicle.cli trust node add --node-id node:partner:beta --subject-id subject:beta --json`
- `python -m chronicle.cli trust assert --target-node node:partner:beta --domain technical_review --purpose "Smoke review" --level trusted --capability review --json`
- `python -m chronicle.cli federation message create --type trust_assertion --source-node node:local:alpha --target-node node:partner:beta --purpose "Smoke trust assertion" --json`
- `python -m chronicle.cli package context --purpose "Smoke package trust" --trust-target-node node:partner:beta`
- `python -m chronicle.cli ui-smoke --json`
