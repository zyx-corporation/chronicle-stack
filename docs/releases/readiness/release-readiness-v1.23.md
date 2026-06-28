# Chronicle Stack v1.23.0 Release Readiness

Related: `../../adr/0025-local-ui-i18n-presentation-boundary.md`, `../../adr/0042-local-ai-index-detail-structured-i18n.md`, `../status/release-status-v1.23.0.md`, `../smoke/smoke-test-v1.23.md`

## Decision

Chronicle Stack `v1.23.0` is ready for repository-side release preparation after the local AI-index-detail structured-i18n slice, release notes, smoke profile, release status, version bump, and passing verification are merged.

## Scope

`v1.23.0` is currently framed as:

- structured `message_key` fields for vector-entry detail wording
- structured `counts_summary_key` fields for vector-entry text/metadata counts
- structured `message_key` fields for graph-node detail wording
- structured `counts_summary_key` fields for graph-node label/property/neighbor counts
- structured `boundary_note_key` fields for derived/read-only/non-authoritative detail wording
- smoke/test coverage for explicit AI-index-detail presentation contracts

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
chronicle 1.23.0
```

## Boundary confirmation

`v1.23.0` does not imply:

- hosted authentication or multi-user authority
- translated machine-readable status codes or ids
- new durable storage for AI-index detail presentation wording
- default-on GUI mutation
