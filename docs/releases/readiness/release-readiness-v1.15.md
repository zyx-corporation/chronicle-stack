# Chronicle Stack v1.15.0 Release Readiness

Related: `../../adr/0025-local-ui-i18n-presentation-boundary.md`, `../../adr/0034-local-blocker-structured-i18n-contracts.md`, `../status/release-status-v1.15.0.md`, `../smoke/smoke-test-v1.15.md`

## Decision

Chronicle Stack `v1.15.0` is ready for repository-side release preparation after the local blocker structured-i18n-contract slice, release notes, smoke profile, release status, version bump, and passing verification are merged.

## Scope

`v1.15.0` is currently framed as:

- structured blocker `message_key` fields for auth-boundary and mutation-readiness details
- structured blocker `summary_key` plus params for auth-boundary and mutation-readiness summaries
- renderer preference for structured blocker keys with fallback string preservation
- smoke/test coverage for explicit blocker presentation contracts

Current repository-side progress already includes the structured payload fields plus HTML-renderer handling for those fields.

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
chronicle 1.15.0
```

## Boundary confirmation

`v1.15.0` does not imply:

- hosted authentication or multi-user authority
- translated machine-readable blocker codes
- new blocker persistence
- default-on GUI mutation

## Release-operator reference

Use:

```text
../operations/release-operator-guide.md
../operations/release-tag-policy.md
../smoke/smoke-test-v1.15.md
```

## Warning classification

- Release warning: repository-side readiness is not external release publication.
- Mutation warning: structured blocker copy does not widen mutation capability.
- Auth warning: blocker presentation remains descriptive and local-first.
- Semantics warning: localized blocker rendering does not supersede authoritative codes or CLI/JSON contracts.

