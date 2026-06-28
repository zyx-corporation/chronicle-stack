# Chronicle Stack v1.17.0 Release Notes

Related: `../../adr/0025-local-ui-i18n-presentation-boundary.md`, `../../adr/0036-local-readiness-and-expectation-structured-i18n.md`, `../readiness/release-readiness-v1.17.md`, `../smoke/smoke-test-v1.17.md`

## Summary

Chronicle Stack `v1.17.0` is a local readiness-and-expectation structured-i18n release over the published `v1.16.0` baseline.

## Highlights

### Structured readiness and identity summaries

`v1.17.0` includes:

- stable `message_key` fields for auth-readiness, auth-boundary, identity-boundary, identity-assurance, and review-capability summaries
- stable `scope_note_key` fields for boundary/readiness explanatory notes
- preserved fallback `message` and `scope_note` strings for degraded consumers

### Structured reviewer expectation contracts

`v1.17.0` includes:

- stable reviewer-context expectation and note keys
- stable reviewer-enforcement and reviewer-validation summary keys
- preserved read-only/local-first reviewer guidance without changing write authority

### Renderer-side readiness and expectation i18n preference

`v1.17.0` includes:

- HTML renderer support that prefers structured readiness and expectation keys when present
- preserved fallback-string rendering for CLI-compatible and degraded paths
- no change to machine-readable status codes, persistence identifiers, or review semantics

## Boundary

`v1.17.0` does not add:

- hosted auth or hosted review execution
- localized machine-readable status codes
- new durable storage for presentation-only readiness wording
- default-on GUI mutation

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
chronicle 1.17.0
```
