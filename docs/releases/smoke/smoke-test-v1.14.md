# Chronicle Stack v1.14.0 Derived Fallback Copy Smoke Profile

Related: `../readiness/release-readiness-v1.14.md`, `../status/release-status-v1.14.0.md`, `../notes/release-notes-v1.14.0.md`, `../remaining/v1.14-release-remaining-issues.md`, `../../adr/0033-local-reviewer-boundary-derived-fallback-copy.md`

## Purpose

This smoke profile will validate the `v1.14.0` release track as a local reviewer-boundary derived-fallback-copy slice.

It is expected to confirm that:

- overview, list, and detail drilldown summaries still expose reviewer-boundary machine-readable facts
- drilldown summaries now expose explicit variant fields plus deterministic fallback message and fact-line copy
- HTML shell still renders reviewer-boundary drilldown summaries as read-only navigation aids
- any added fallback-copy fields remain derived from existing reviewer-boundary state
- no new write capability is implied by the derived-fallback-copy additions

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
chronicle 1.14.0
```

## Manual spot checks

Once `v1.14.0` implementation exists, confirm that:

- fallback copy stays aligned with template params and status fields
- overview-dominant summaries stay distinct from row-detail summaries without changing reviewer-boundary meaning
- detail summaries still distinguish descriptive read models from authoritative record contracts

## Boundary reminder

`v1.14.0` smoke for this slice must not certify hosted auth, multi-user safety, default-on mutation, correctness proof, or security certification.
