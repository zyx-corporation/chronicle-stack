# Chronicle Stack v1.9.0 Release Readiness

Related: `docs/adr/0026-local-reviewer-session-proof-representation.md`, `docs/adr/0028-local-reviewer-session-enforcement-boundary.md`, `docs/release-status-v1.9.0.md`, `docs/smoke-test-v1.9.md`

## Decision

Chronicle Stack `v1.9.0` is ready for repository-side release preparation after the local reviewer/session enforcement-boundary slice, release notes, smoke profile, release status, version bump, and changelog update are merged with passing CI.

## Scope

`v1.9.0` is currently framed as a local reviewer/session enforcement-boundary and validation/gate-alignment release.

It includes:

- explicit `reviewer_enforcement_summary` exposure on UI boundary, readiness, detail, and apply surfaces
- explicit `reviewer_validation_gate_summary` exposure for validation, authorization, target-state, and durable-write failure families
- aligned reviewer/session wording across preview, apply, readiness, and release-facing docs
- `v1.9` release readiness
- `v1.9` smoke profile
- `v1.9` release notes
- version bump to `1.9.0`
- changelog update for `v1.9.0`

## Required verification

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
chronicle 1.9.0
```

Current repository-side verification for this track now reflects the finalized `1.9.0` package version and completed repo-side release-preparation state.

Repository-side verification now passes for this checkout, including editable reinstall, `chronicle --version = 1.9.0`, full `pytest`, and local `ui-smoke --json`.

## Boundary confirmation

`v1.9.0` does not imply:

- hosted authentication or authorization
- multi-user-safe authority
- default-on GUI mutation
- hidden background review execution
- non-local review operators
- GraphRAG runtime
- vector DB
- graph DB
- correctness proof
- security certification

## Release-operator reference

Use:

```text
docs/release-operator-guide.md
docs/release-tag-policy.md
docs/smoke-test-v1.9.md
```

## Warning classification

- Release warning: repository-side readiness is not external release publication.
- Auth warning: reviewer/session route alignment is not hosted identity proof.
- Mutation warning: aligned gate semantics do not imply default-on GUI mutation.
- Runtime warning: review-surface hardening does not imply hidden runtime/provider execution.
- Semantics warning: smoke and readiness remain diagnostic, not certification or proof.

## RDE review

Preserved: Chronicle JSONL primary-record authority, local-first UI boundary, CLI-visible recovery semantics, fail-closed route contracts.

Transformed: scattered `v1.9.0` reviewer/session boundary work becomes one release-readiness checkpoint.

Supplemented: explicit release framing for reviewer/session enforcement scope and shared validation/gate families.

Unresolved: any stronger enforcement beyond the current local single-operator boundary.
