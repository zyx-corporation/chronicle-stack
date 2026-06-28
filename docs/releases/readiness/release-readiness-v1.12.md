# Chronicle Stack v1.12.0 Release Readiness

Related: `../../adr/0025-local-ui-i18n-presentation-boundary.md`, `../../adr/0031-local-reviewer-boundary-presentation-drilldown.md`, `../status/release-status-v1.12.0.md`, `../smoke/smoke-test-v1.12.md`

## Decision

Chronicle Stack `v1.12.0` is ready for repository-side release preparation after the local reviewer-boundary presentation/read-model drilldown slice, release notes, smoke profile, release status, version bump, and changelog update are merged with passing verification.

## Scope

`v1.12.0` is currently framed as:

- reviewer-boundary drilldown summaries across overview, list, and detail surfaces
- clearer reconstruction links between overview counts, filtered list slices, and detail facts
- i18n-ready alignment for reviewer-boundary fact-line wording and read-only summary labels

Current repository-side progress already includes reviewer-boundary drilldown summaries in read-only overview/list/detail payloads plus matching `ui-smoke` coverage for those summaries.

- `v1.12` release readiness
- `v1.12` smoke profile
- `v1.12` release notes
- version bump to `1.12.0`
- changelog update for `v1.12.0`

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
chronicle 1.12.0
```

Current repository-side verification for this track now reflects the finalized `1.12.0` package version and completed repo-side release-preparation state.

Repository-side verification now passes for this checkout, including editable reinstall, `chronicle --version = 1.12.0`, full `pytest`, and local `ui-smoke --json`.

## Boundary confirmation

`v1.12.0` does not imply:

- new reviewer-boundary persistence
- hosted authentication or multi-user authority
- localized machine-readable payload values
- default-on GUI mutation

## Release-operator reference

Use:

```text
../operations/release-operator-guide.md
../operations/release-tag-policy.md
../smoke/smoke-test-v1.12.md
```

## Warning classification

- Release warning: repository-side readiness is not external release publication.
- Mutation warning: presentation-drilldown completion does not imply default-on GUI mutation.
- Auth warning: reviewer-boundary summaries remain local-first and preview-scoped, not hosted identity proof.
- Runtime warning: presentation and smoke coverage do not imply hidden runtime/provider execution.
- Semantics warning: drilldown and readiness remain descriptive and reconstructive, not certification or proof.

## RDE review

Preserved: Chronicle JSONL authority, local-first UI boundary, presentation-only i18n scope, read-only derived-surface discipline.

Transformed: reviewer-boundary observability and smoke-preservation work now becomes one release-readiness checkpoint with explicit presentation-drilldown and i18n-ready read-model coverage across overview, list, detail, and HTML shell surfaces.

Supplemented: release-lane framing for reviewer-boundary reconstruction plus structured presentation-field contracts for localized drilldown wording.

Unresolved: external publication timing and any follow-on lane after `v1.12.0`.
