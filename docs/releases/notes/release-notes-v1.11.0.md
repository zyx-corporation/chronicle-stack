# Chronicle Stack v1.11.0 Release Notes

Related: `../../adr/0030-local-reviewer-boundary-smoke-contract.md`, `../readiness/release-readiness-v1.11.md`, `../smoke/smoke-test-v1.11.md`

## Summary

Chronicle Stack `v1.11.0` is currently framed as a local reviewer-boundary smoke-contract release over the published `v1.10.0` baseline.

## Highlights

### Reviewer-boundary smoke checkpoints

`v1.11.0` currently includes:

- version bump and changelog update for `1.11.0`
- explicit smoke checks for reviewer-boundary overview summaries
- explicit smoke checks that reviewer-boundary overview counts match list-row statuses
- explicit smoke checks for reviewer-boundary list-row statuses
- explicit smoke checks for reviewer-boundary detail summaries

### HTML-shell continuity coverage

`v1.11.0` currently includes:

- smoke confirmation for reviewer-boundary panel markers
- smoke confirmation for reviewer-boundary slice/filter helper visibility
- preserved read-only UI-shell expectations

### Preserved local-first verification boundary

`v1.11.0` preserves:

- local single-operator scope
- derived-surface verification only
- read-only smoke discipline
- JSON/CLI contract authority over smoke wording

## Boundary

`v1.11.0` does not add:

- hosted auth or hosted review execution
- new reviewer-boundary persistence
- localized machine-readable payload changes
- correctness proof or security certification

## Verification

```bash
python -m pip install -e ".[dev]"
chronicle --version
ruff check src/ tests/
pytest
chronicle ui-smoke
chronicle ui-smoke --json
```

Expected current version baseline:

```text
chronicle 1.11.0
```
