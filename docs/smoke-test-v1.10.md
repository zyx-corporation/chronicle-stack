# Chronicle Stack v1.10.0 Reviewer Boundary Observability Smoke Profile

Related: `docs/release-readiness-v1.10.md`, `docs/release-status-v1.10.0.md`, `docs/release-notes-v1.10.0.md`, `docs/v1.10-release-remaining-issues.md`, `docs/adr/0029-local-reviewer-boundary-observability.md`

## Purpose

This smoke profile validates the current `v1.10.0` release track as a local reviewer-boundary observability and i18n-ready presentation slice.

It checks that:

- reviewer-boundary aggregates remain derived and read-only
- overview surfaces expose reviewer enforcement and validation-gate counts
- reviewer-boundary badges and fact labels resolve through translation keys
- machine-readable status values remain stable in payloads

## Verification

Run:

```bash
python -m pip install -e ".[dev]"
chronicle --version
ruff check src/ tests/
pytest
chronicle ui-smoke
chronicle ui-smoke --json
```

Expected version:

```text
chronicle 1.10.0
```

## Manual spot checks

When opening `chronicle ui` manually for local inspection, confirm:

- overview includes the reviewer-boundary panel
- runtime/review/summary rows display reviewer-boundary badges
- locale switching changes reviewer-boundary labels without changing status-code values
- no new write capability is implied by the added observability surface

## Boundary

`v1.10.0` smoke for this slice does not certify hosted auth, multi-user safety, default-on mutation, correctness proof, or security certification.
