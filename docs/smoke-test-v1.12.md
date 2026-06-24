# Chronicle Stack v1.12.0 Reviewer Boundary Presentation Drilldown Smoke Profile

Related: `docs/release-readiness-v1.12.md`, `docs/release-status-v1.12.0.md`, `docs/release-notes-v1.12.0.md`, `docs/v1.12-release-remaining-issues.md`, `docs/adr/0031-local-reviewer-boundary-presentation-drilldown.md`

## Purpose

This smoke profile will validate the `v1.12.0` release track as a local reviewer-boundary presentation/read-model drilldown slice.

It is expected to confirm that:

- overview surfaces still expose reviewer-boundary summary aggregates
- list surfaces still expose reviewer-boundary row statuses
- detail surfaces still expose reviewer-boundary summaries
- overview, list, and detail surfaces expose reviewer-boundary drilldown summaries where implemented
- HTML shell still renders reviewer-boundary drilldown summaries as read-only navigation aids
- any added read-only drilldown summaries remain derived from existing reviewer-boundary state
- no new write capability is implied by the presentation-drilldown additions

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
chronicle 1.11.0
```

## Manual spot checks

Once `v1.12.0` implementation exists, confirm that:

- overview drilldown wording does not overstate reviewer-boundary certainty
- list summaries clearly distinguish row-level status from detail-level explanation
- detail summaries clearly distinguish descriptive read models from authoritative record contracts

## Boundary reminder

`v1.12.0` smoke for this slice must not certify hosted auth, multi-user safety, default-on mutation, correctness proof, or security certification.
