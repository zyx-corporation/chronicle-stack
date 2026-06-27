# Chronicle Stack v1.65 Release Readiness

## Included

- versioned `export_contract` on graph-json exports
- incremental expectation metadata for event-driven consumption
- graph CLI summary and local UI graph summary contract fields

## Validation target

- `ruff check src tests`
- `pytest`
- `python -m chronicle.cli ui-smoke --json`
