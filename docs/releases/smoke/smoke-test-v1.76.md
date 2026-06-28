# Smoke Test v1.76

## Commands

- `./.venv/bin/ruff check src tests`
- `./.venv/bin/pytest -q`
- `./.venv/bin/python -m chronicle.cli --version`
- `./.venv/bin/python -m chronicle.cli package query-engine-bundle --query "graph context" --output-dir handoff-bundle`
- `./.venv/bin/python -m chronicle.cli package query-engine-trial-record --bundle-dir handoff-bundle --reviewer "operator" --consumer "downstream-demo" --sufficient --json`
