# Chronicle Stack v1.13.0 Structured Presentation Contract Smoke Profile

Related: `docs/release-readiness-v1.13.md`, `docs/release-status-v1.13.0.md`, `docs/release-notes-v1.13.0.md`, `docs/v1.13-release-remaining-issues.md`, `docs/adr/0032-local-reviewer-boundary-structured-presentation-contracts.md`

## Purpose

This smoke profile will validate the `v1.13.0` release track as a local reviewer-boundary structured-presentation-contract slice.

It is expected to confirm that:

- overview, list, and detail drilldown summaries still expose reviewer-boundary machine-readable facts
- drilldown summaries now expose explicit message-template keys and template params where implemented
- HTML shell still renders reviewer-boundary drilldown summaries as read-only navigation aids
- any added structured presentation fields remain derived from existing reviewer-boundary state
- no new write capability is implied by the structured-presentation additions

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
chronicle 1.13.0
```

## Manual spot checks

Once `v1.13.0` implementation exists, confirm that:

- drilldown template keys do not replace reviewer-boundary machine-readable values
- dataset-specific wording remains localized through templates rather than per-surface payload drift
- detail summaries still distinguish descriptive read models from authoritative record contracts

## Boundary reminder

`v1.13.0` smoke for this slice must not certify hosted auth, multi-user safety, default-on mutation, correctness proof, or security certification.
