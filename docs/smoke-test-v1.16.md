# Chronicle Stack v1.16.0 Mutation Enablement Check Structured i18n Smoke Profile

Related: `docs/release-readiness-v1.16.md`, `docs/release-status-v1.16.0.md`, `docs/release-notes-v1.16.0.md`, `docs/v1.16-release-remaining-issues.md`, `docs/adr/0035-local-mutation-enablement-check-structured-i18n.md`

## Purpose

This smoke profile validates the `v1.16.0` release track as a local mutation-enablement-check structured-i18n slice.

It is expected to confirm that:

- mutation enablement checks expose stable label/detail keys plus fallback strings
- unsatisfied mutation enablement checks expose stable summary keys plus params
- HTML shell still renders mutation readiness as a read-only explanatory surface
- checklist wording remains presentation-only and derived
- no new write capability is implied by the structured check fields

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
chronicle 1.16.0
```

## Manual spot checks

Confirm that:

- enablement check payloads include both stable keys and readable fallback labels/details
- unsatisfied-check summaries include both stable keys and readable fallback summaries
- overview and detail mutation-readiness notices keep read-only/local-first wording intact

## Boundary reminder

`v1.16.0` smoke for this slice must not certify hosted auth, multi-user safety, default-on mutation, correctness proof, or security certification.

