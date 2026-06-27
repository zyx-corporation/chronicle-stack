# Smoke Test v1.78

## Commands

- `./.venv/bin/ruff check src tests`
- `./.venv/bin/pytest -q`
- `./.venv/bin/python -m chronicle.cli --version`
- `./.venv/bin/python -m chronicle.cli package query-engine-bundle --query "Smoke Query" --output-dir /tmp/chronicle-query-engine-bundle`
- `./.venv/bin/python -m chronicle.cli package query-engine-trial-record --bundle-dir /tmp/chronicle-query-engine-bundle --consumer smoke-consumer --reviewer smoke-reviewer --query "Smoke Query" --answer "Recorded downstream outcome" --summary "Recorded read-only trial" --sufficient yes --json`
- `./.venv/bin/python -m chronicle.cli ui-export --json`
