# Chronicle Stack v1.63 Release Readiness

## Included

- append-only artifact update proposal records
- append-only context update proposal records
- UI proposal summaries on `/api/contexts`, `/api/artifacts`, and detail payloads
- read-only `/api/proposals` list surface

## Validation target

- `ruff check src tests`
- `pytest`
- `python -m chronicle.cli ui-smoke --json`
