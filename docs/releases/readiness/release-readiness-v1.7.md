# Chronicle Stack v1.7.0 Release Readiness

Related: `../../adr/0018-local-ui-read-only-navigation-boundary.md`, `../../adr/0019-local-ui-review-semantics-parity-boundary.md`, `../../adr/0021-gated-local-ui-mutation-write-path.md`, `../../adr/0023-browser-triggered-review-write-semantics.md`, `../../adr/0024-explicit-configured-provider-execution-boundary.md`, `../../adr/0026-local-reviewer-session-proof-representation.md`

## Decision

Chronicle Stack v1.7.0 is ready for repository-side release preparation when this document, release notes, smoke profile, release status, version bump, and changelog update are merged with passing CI.

## Scope

v1.7.0 is a local AI/runtime/review/package observability and gated-local-mutation-preparation release.

It includes:

- local placeholder AI index CLI surface
- read-only local UI visibility for AI index / runtime / review / package surfaces
- explicit local runtime summarize / invoke / execute-plan surfaces
- retrieval-plan and invocation-plan dry-run / reviewable record surfaces
- Phase H auth-readiness / identity / mutation-readiness overview-list-detail visibility
- explicit gated local review write-path preview and fail-closed route contracts
- v1.7 release notes
- v1.7 smoke profile
- v1.7 release readiness
- v1.7 release status
- version bump to `1.7.0`
- changelog update for `v1.7.0`

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
chronicle 1.7.0
```

Repository-side verification now passes for this checkout after editable reinstall refreshed the CLI package metadata to `1.7.0`.

External release execution has also been completed for `v1.7.0`, including GitHub Release publication, tag/main equivalence confirmation, clean installer smoke, and tag-based `ui-smoke` evidence.

## Boundary confirmation

v1.7.0 does not introduce:

- daemon or background service installation
- hosted UI
- default-on GUI mutation
- authenticated GUI mutation
- authorization enforcement beyond local descriptive metadata
- browser-triggered audit semantics beyond the current local fail-closed contract
- hidden provider execution
- automatic model invocation on record creation
- GraphRAG runtime
- vector DB
- graph DB
- correctness proof
- security certification
- legal/governance finalization

## Release-operator reference

Use:

```text
../operations/release-operator-guide.md
../operations/release-tag-policy.md
../smoke/smoke-test-v1.7.md
```

External release execution has been completed for `v1.7.0`; keep these documents as the reference for any follow-up evidence review or corrective release work.

## Warning classification

- Release warning: repository-side readiness is not external release publication.
- Mutation warning: gated local write-path visibility does not imply default-on GUI mutation.
- Auth warning: placeholder auth/authz metadata remains descriptive, not enforcement.
- Runtime warning: explicit local runtime and configured-provider contracts do not imply hidden/background execution.
- Security warning: smoke is not security certification.
- Semantics warning: smoke and readiness signals are not correctness proof.
- Legal warning: commercial/contributor drafts remain draft completed / counsel review pending.

## RDE review

Preserved: Chronicle JSONL primary-record authority, local-first UI boundary, CLI-first mutation semantics, inspectable release evidence workflow.

Transformed: scattered v1.7 phase completion notes become one repo-side release readiness checkpoint.

Supplemented: explicit release framing for AI index, runtime, retrieval-plan, and Phase H readiness surfaces.

Unresolved: stronger authenticated GUI mutation, richer authorization enforcement, and deeper provider/runtime expansion beyond the current local observability slice.

Deviation risks: treating gated-local-write preparation as default GUI mutation, overstating provider/runtime maturity, or treating smoke as certification.
