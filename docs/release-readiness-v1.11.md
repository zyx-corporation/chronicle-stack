# Chronicle Stack v1.11.0 Release Readiness

Related: `docs/adr/0030-local-reviewer-boundary-smoke-contract.md`, `docs/release-status-v1.11.0.md`, `docs/smoke-test-v1.11.md`

## Decision

Chronicle Stack `v1.11.0` is the active repository-side release lane for local reviewer-boundary smoke-contract hardening.

## Scope

`v1.11.0` is currently framed as:

- reviewer-boundary overview smoke coverage
- reviewer-boundary count-consistency smoke coverage
- reviewer-boundary list-row smoke coverage
- reviewer-boundary detail-summary smoke coverage
- reviewer-boundary HTML-shell continuity coverage

## Required verification

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

## Boundary confirmation

`v1.11.0` does not imply:

- new persistence for reviewer-boundary smoke data
- hosted authentication or multi-user authority
- default-on mutation
- correctness proof or security certification

## RDE review

Preserved: Chronicle JSONL authority, local-first UI boundary, read-only smoke discipline, derived-surface verification only.

Transformed: reviewer-boundary observability now has explicit smoke-contract coverage across overview, list, detail, and HTML shell surfaces.

Supplemented: release-lane framing for reviewer-boundary smoke checkpoints and HTML continuity markers.

Unresolved: eventual publication timing and any follow-on lane after `v1.11.0`.
