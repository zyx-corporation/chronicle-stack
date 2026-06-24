# Chronicle Stack v1.12.0 Release Readiness

Related: `docs/adr/0025-local-ui-i18n-presentation-boundary.md`, `docs/adr/0031-local-reviewer-boundary-presentation-drilldown.md`, `docs/release-status-v1.12.0.md`, `docs/smoke-test-v1.12.md`

## Decision

Chronicle Stack `v1.12.0` is the active repository-side release lane for local reviewer-boundary presentation/read-model drilldown.

## Scope

`v1.12.0` is currently framed as:

- reviewer-boundary drilldown summaries across overview, list, and detail surfaces
- clearer reconstruction links between overview counts, filtered list slices, and detail facts
- i18n-ready alignment for reviewer-boundary fact-line wording and read-only summary labels

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

## Boundary confirmation

`v1.12.0` does not imply:

- new reviewer-boundary persistence
- hosted authentication or multi-user authority
- localized machine-readable payload values
- default-on GUI mutation

## RDE review

Preserved: Chronicle JSONL authority, local-first UI boundary, presentation-only i18n scope, read-only derived-surface discipline.

Transformed: reviewer-boundary observability and smoke-preservation work now gains a dedicated presentation-drilldown release lane.

Supplemented: explicit release-lane framing for reviewer-boundary reconstruction across overview, list, and detail surfaces.

Unresolved: concrete `v1.12.0` implementation slices, eventual version bump, and publication timing.
