# Chronicle Stack v1.66 Release Readiness

## Included

- local graph retrieval adapter service over graph export
- `chronicle graph retrieve --query ...`
- `runtime retrieve-plan` graph adapter metadata

## Validation target

- `ruff check src tests`
- `pytest`
- `python -m chronicle.cli ui-smoke --json`
