# Chronicle Stack v1.21.0 Release Readiness

Related: `../../adr/0025-local-ui-i18n-presentation-boundary.md`, `../../adr/0040-local-graph-summary-structured-i18n.md`, `../status/release-status-v1.21.0.md`, `../smoke/smoke-test-v1.21.md`

## Decision

Chronicle Stack `v1.21.0` is ready for repository-side release preparation after the local graph-summary structured-i18n slice, release notes, smoke profile, release status, version bump, and passing verification are merged.

## Scope

`v1.21.0` is currently framed as:

- structured `message_key` fields for graph-summary availability wording
- structured `counts_summary_key` fields for graph node/edge count wording
- structured `boundary_note_key` fields for derived/read-only/non-authoritative graph wording
- overview and endpoint exposure for structured graph-summary fields
- smoke/test coverage for explicit graph-summary presentation contracts

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
chronicle 1.21.0
```

## Boundary confirmation

`v1.21.0` does not imply:

- hosted authentication or multi-user authority
- translated machine-readable status codes or ids
- new durable storage for graph-summary presentation wording
- default-on GUI mutation
