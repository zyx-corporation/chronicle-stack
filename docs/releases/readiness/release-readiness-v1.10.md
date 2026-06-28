# Chronicle Stack v1.10.0 Release Readiness

Related: `../../adr/0025-local-ui-i18n-presentation-boundary.md`, `../../adr/0029-local-reviewer-boundary-observability.md`, `../status/release-status-v1.10.0.md`, `../smoke/smoke-test-v1.10.md`

## Decision

Chronicle Stack `v1.10.0` is the active repository-side release lane for local reviewer-boundary observability and i18n-ready presentation alignment.

## Scope

`v1.10.0` is currently framed as:

- overview aggregation for reviewer enforcement and validation-gate states
- direct row-surface visibility for existing reviewer boundary statuses
- i18n-ready presentation routing for reviewer-boundary badges, panel labels, and metrics

## Required verification

```bash
python -m pip install -e ".[dev]"
chronicle --version
ruff check src/ tests/
pytest
chronicle ui-smoke
chronicle ui-smoke --json
```

Expected version:

```text
chronicle 1.10.0
```

## Boundary confirmation

`v1.10.0` does not imply:

- new persistence for reviewer-boundary aggregates
- hosted authentication or multi-user authority
- translation of machine-readable status values
- default-on GUI mutation

## RDE review

Preserved: Chronicle JSONL authority, local-first UI boundary, presentation-only i18n scope, fail-closed mutation contract.

Transformed: reviewer-boundary observability now includes explicit i18n-ready UI presentation routing.

Supplemented: release-lane framing for reviewer-boundary metrics, row badges, and translation-key coverage.

Unresolved: external publication timing and any follow-on lane after `v1.10.0`.
