# Chronicle Stack v1.15.0 Blocker Structured i18n Smoke Profile

Related: `../readiness/release-readiness-v1.15.md`, `../status/release-status-v1.15.0.md`, `../notes/release-notes-v1.15.0.md`, `../remaining/v1.15-release-remaining-issues.md`, `../../adr/0034-local-blocker-structured-i18n-contracts.md`

## Purpose

This smoke profile validates the `v1.15.0` release track as a local blocker structured-i18n-contract slice.

It is expected to confirm that:

- auth-boundary and mutation-readiness payloads expose stable blocker keys plus fallback strings
- blocker summaries expose stable summary keys plus summary params
- HTML shell still renders blocker summaries as read-only explanatory surfaces
- blocker wording remains presentation-only and derived
- no new write capability is implied by the structured blocker fields

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

## Manual spot checks

Confirm that:

- blocker detail payloads include both stable keys and readable fallback messages
- blocker summaries include both stable keys and readable fallback summaries
- overview and detail notices keep read-only/local-first wording intact

## Boundary reminder

`v1.15.0` smoke for this slice must not certify hosted auth, multi-user safety, default-on mutation, correctness proof, or security certification.

