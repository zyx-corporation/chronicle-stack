# Chronicle Stack v1.13.0 Release Readiness

Related: `docs/adr/0025-local-ui-i18n-presentation-boundary.md`, `docs/adr/0032-local-reviewer-boundary-structured-presentation-contracts.md`, `docs/release-status-v1.13.0.md`, `docs/smoke-test-v1.13.md`

## Decision

Chronicle Stack `v1.13.0` is ready for repository-side release preparation after the local reviewer-boundary structured-presentation-contract slice, release notes, smoke profile, release status, version bump, and changelog update are merged with passing verification.

## Scope

`v1.13.0` is currently framed as:

- standardized reviewer-boundary drilldown message-template contracts across overview, list, and detail surfaces
- clearer separation between machine-readable reviewer-boundary facts and localized presentation wording
- smoke/test coverage for explicit message-template fields in read-only drilldown payloads

Current repository-side progress already includes structured message-template keys and params for reviewer-boundary drilldown summaries plus matching smoke/test coverage for those contracts.

- `v1.13` release readiness
- `v1.13` smoke profile
- `v1.13` release notes
- version bump to `1.13.0`
- changelog update for `v1.13.0`

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

Current repository-side verification for this track now reflects the finalized `1.13.0` package version and completed repo-side release-preparation state.

Repository-side verification now passes for this checkout, including editable reinstall, `chronicle --version = 1.13.0`, full `pytest`, and local `ui-smoke --json`.

## Release-operator reference

Use:

```text
docs/release-operator-guide.md
docs/release-tag-policy.md
docs/smoke-test-v1.13.md
```

## Warning classification

- Release warning: repository-side readiness is not external release publication.
- Mutation warning: structured presentation contracts do not imply default-on GUI mutation.
- Auth warning: reviewer-boundary summaries remain local-first and preview-scoped, not hosted identity proof.
- Runtime warning: presentation and smoke coverage do not imply hidden runtime/provider execution.
- Semantics warning: drilldown templates and readiness remain descriptive and reconstructive, not certification or proof.

## Boundary confirmation

`v1.13.0` does not imply:

- new reviewer-boundary persistence
- hosted authentication or multi-user authority
- localized machine-readable payload values
- default-on GUI mutation

## RDE review

Preserved: Chronicle JSONL authority, local-first UI boundary, presentation-only i18n scope, read-only derived-surface discipline.

Transformed: reviewer-boundary drilldown payloads now move more presentation wording behind shared message-template contracts instead of per-surface fallback sentences.

Supplemented: explicit release-lane framing for structured reviewer-boundary message-template verification across overview, list, detail, and smoke surfaces.

Unresolved: external publication timing and any follow-on lane after `v1.13.0`.
