# Smoke Test v1.85

## Commands

- `ruff check src tests`
- `pytest -q`
- `python -m chronicle.cli federation message create --type request_context --source-node node:local:alpha --target-node node:local:beta --purpose "Smoke review" --json`
- `python -m chronicle.cli federation message create --type decay_notice --source-node node:local:alpha --target-node node:local:beta --purpose "Smoke revoke/decay audit" --box inbox --json`
- `python -m chronicle.cli federation inbox inspect --json`
- `python -m chronicle.cli ui-smoke --json`
