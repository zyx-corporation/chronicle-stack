# Chronicle Stack v1.17.0 Readiness and Expectation Structured i18n Smoke Profile

Related: `../readiness/release-readiness-v1.17.md`, `../status/release-status-v1.17.0.md`, `../notes/release-notes-v1.17.0.md`, `../remaining/v1.17-release-remaining-issues.md`, `../../adr/0036-local-readiness-and-expectation-structured-i18n.md`

## Purpose

This smoke profile validates the `v1.17.0` release track as a local readiness-and-expectation structured-i18n slice.

It is expected to confirm that:

- readiness and identity payloads expose stable keys plus readable fallback strings
- reviewer-context expectation and note payloads expose stable keys plus readable fallback strings
- reviewer-enforcement and reviewer-validation summaries expose stable keys plus readable fallback strings
- HTML shell still renders readiness and mutation-readiness as read-only explanatory surfaces
- no new write capability is implied by the structured readiness/expectation fields

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

## Manual spot checks

Confirm that:

- auth/readiness and identity summaries include both stable keys and readable fallback messages
- reviewer-context expectation and note fields include both stable keys and readable fallback text
- overview and detail readiness notices keep read-only/local-first wording intact

## Boundary reminder

`v1.17.0` smoke for this slice must not certify hosted auth, multi-user safety, default-on mutation, correctness proof, or security certification.
