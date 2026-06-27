# Chronicle Stack v1.64 Release Readiness

## Included

- `chronicle artifact apply-proposal --event <proposal_event_id>`
- `chronicle context apply-proposal --event <proposal_event_id>`
- approved-only apply gate with duplicate-apply protection
- `/api/proposals` apply-ready and applied state

## Validation target

- `ruff check src tests`
- `pytest`
- `python -m chronicle.cli ui-smoke --json`
