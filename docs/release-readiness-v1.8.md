# Chronicle Stack v1.8.0 Release Readiness

Related: `docs/adr/0023-browser-triggered-review-write-semantics.md`, `docs/adr/0026-local-reviewer-session-proof-representation.md`, `docs/adr/0027-local-gui-review-route-contract.md`, `docs/release-status-v1.8.0.md`, `docs/smoke-test-v1.8.md`

## Decision

Chronicle Stack `v1.8.0` becomes ready for repository-side release preparation when the local GUI review-route contract-hardening slice, release notes, smoke profile, release status, version bump, and changelog update are merged with passing CI.

## Scope

`v1.8.0` is currently framed as a local GUI review-route design-hardening and contract-hardening release.

It includes:

- explicit local GUI review route family visibility
- read-only exposure of action-route and CLI-equivalent route semantics
- read-only exposure of write-route status-code semantics
- preserved fail-closed browser-triggered review mutation contract
- `v1.8` release readiness
- `v1.8` smoke profile
- future `v1.8` release notes
- future version bump to `1.8.0`
- future changelog update for `v1.8.0`

## Required verification

```bash
python -m pip install -e ".[dev]"
chronicle --version
ruff check src/ tests/
pytest
chronicle ui-smoke
chronicle ui-smoke --json
```

Expected current version before final release cut:

```text
chronicle 1.7.0
```

Expected release version at the actual `v1.8.0` cut:

```text
chronicle 1.8.0
```

Current repository-side verification for this track is still pre-release framing and contract hardening, not final release execution.

## Boundary confirmation

`v1.8.0` does not imply:

- hosted UI
- default-on GUI mutation
- multi-user authentication or authorization
- hidden background review execution
- non-local mutation operators
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
docs/smoke-test-v1.8.md
```

## Warning classification

- Release warning: repository-side readiness is not external release publication.
- Mutation warning: contract hardening does not imply default-on GUI mutation.
- Auth warning: current reviewer/session proof shape remains local-first and boundary-scoped.
- Runtime warning: review-route hardening does not imply hidden runtime/provider execution.
- Semantics warning: smoke and readiness remain diagnostic, not certification or proof.

## RDE review

Preserved: Chronicle JSONL primary-record authority, local-first UI boundary, CLI-visible recovery semantics, fail-closed route contracts.

Transformed: scattered `v1.8.0` design-hardening progress becomes one release-readiness checkpoint.

Supplemented: explicit release framing for route-family semantics, status-code semantics, and local reviewer/session contract boundaries.

Unresolved: actual `v1.8.0` release notes, version bump, changelog entry, publication evidence, and any future stronger enforcement beyond the current local contract surface.
