# Chronicle Stack v1.11.0 Reviewer Boundary Smoke Contract Profile

Related: `docs/release-readiness-v1.11.md`, `docs/release-status-v1.11.0.md`, `docs/release-notes-v1.11.0.md`, `docs/v1.11-release-remaining-issues.md`, `docs/adr/0030-local-reviewer-boundary-smoke-contract.md`

## Purpose

This smoke profile validates the current `v1.11.0` release track as a local reviewer-boundary smoke-contract slice.

It checks that:

- overview payloads expose reviewer-boundary summary aggregates
- overview aggregates stay consistent with runtime/review/summary list-row statuses
- runtime/review/summary list payloads expose reviewer-boundary statuses
- derived detail payloads expose reviewer-boundary summaries
- HTML shell still exposes reviewer-boundary panel and navigation helpers

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

Expected current version baseline:

```text
chronicle 1.10.0
```

## Manual spot checks

When opening `chronicle ui` manually for local inspection, confirm:

- overview still shows the reviewer-boundary panel
- reviewer-boundary slice/filter navigation still reaches runtime, review, and summary lists
- reviewer-boundary labels remain present across locale changes
- no new write capability is implied by the smoke-contract additions

## Boundary

`v1.11.0` smoke for this slice does not certify hosted auth, multi-user safety, default-on mutation, correctness proof, or security certification.
