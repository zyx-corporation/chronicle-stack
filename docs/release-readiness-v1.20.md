# Chronicle Stack v1.20.0 Release Readiness

Related: `docs/adr/0025-local-ui-i18n-presentation-boundary.md`, `docs/adr/0039-local-retrieval-handoff-and-invocation-plan-structured-i18n.md`, `docs/release-status-v1.20.0.md`, `docs/smoke-test-v1.20.md`

## Decision

Chronicle Stack `v1.20.0` is ready for repository-side release preparation after the local retrieval-handoff-and-invocation-plan structured-i18n slice, release notes, smoke profile, release status, version bump, and passing verification are merged.

## Scope

`v1.20.0` is currently framed as:

- structured `message_key` fields for retrieval-handoff notices
- structured `hit_counts_summary_key` fields for retrieval-handoff hit-count wording
- structured `message_key` fields for invocation-plan readiness summaries
- structured `provider_summary_key` fields for invocation-plan provider summaries
- renderer preference for structured retrieval/invocation fields with fallback string preservation
- smoke/test coverage for explicit retrieval/invocation presentation contracts

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
chronicle 1.20.0
```

## Boundary confirmation

`v1.20.0` does not imply:

- hosted authentication or multi-user authority
- translated machine-readable status codes or ids
- new durable storage for retrieval/invocation presentation wording
- default-on GUI mutation
