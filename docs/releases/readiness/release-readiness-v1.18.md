# Chronicle Stack v1.18.0 Release Readiness

Related: `../../adr/0025-local-ui-i18n-presentation-boundary.md`, `../../adr/0037-local-package-parity-and-preview-structured-i18n.md`, `../status/release-status-v1.18.0.md`, `../smoke/smoke-test-v1.18.md`

## Decision

Chronicle Stack `v1.18.0` is ready for repository-side release preparation after the local package-parity-preview structured-i18n slice, release notes, smoke profile, release status, version bump, and passing verification are merged.

## Scope

`v1.18.0` is currently framed as:

- structured `message_key` fields for package-readiness summaries and detail payloads
- structured `message_key` fields for retrieval package-handoff preview payloads
- structured `message_key` fields for action-preview summaries
- structured `message_key` fields for CLI parity summaries
- renderer preference for structured package/parity/preview keys with fallback string preservation
- smoke/test coverage for explicit package/parity/preview presentation contracts

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
chronicle 1.18.0
```

## Boundary confirmation

`v1.18.0` does not imply:

- hosted authentication or multi-user authority
- translated machine-readable status codes
- new durable storage for presentation-only package/parity/preview wording
- default-on GUI mutation
