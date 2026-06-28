# Chronicle Stack v1.17.0 Release Readiness

Related: `../../adr/0025-local-ui-i18n-presentation-boundary.md`, `../../adr/0036-local-readiness-and-expectation-structured-i18n.md`, `../status/release-status-v1.17.0.md`, `../smoke/smoke-test-v1.17.md`

## Decision

Chronicle Stack `v1.17.0` is ready for repository-side release preparation after the local readiness-and-expectation structured-i18n slice, release notes, smoke profile, release status, version bump, and passing verification are merged.

## Scope

`v1.17.0` is currently framed as:

- structured `message_key` fields for auth/readiness, identity, and review-capability summaries
- structured `scope_note_key` fields for readiness/auth-boundary explanatory notes
- structured reviewer-context expectation and note keys
- structured reviewer-enforcement and reviewer-validation summary keys
- renderer preference for structured readiness/expectation keys with fallback string preservation
- smoke/test coverage for explicit readiness-and-expectation presentation contracts

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
chronicle 1.17.0
```

## Boundary confirmation

`v1.17.0` does not imply:

- hosted authentication or multi-user authority
- translated machine-readable status codes
- new durable storage for presentation-only readiness wording
- default-on GUI mutation
