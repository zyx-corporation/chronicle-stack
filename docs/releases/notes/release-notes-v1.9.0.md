# Chronicle Stack v1.9.0 Release Notes

Related: `../../adr/0026-local-reviewer-session-proof-representation.md`, `../../adr/0028-local-reviewer-session-enforcement-boundary.md`, `../readiness/release-readiness-v1.9.md`, `../smoke/smoke-test-v1.9.md`

## Summary

Chronicle Stack `v1.9.0` is currently framed as a local reviewer/session enforcement-boundary and validation/gate-alignment release over `v1.8.0`.

This release lane consolidates the next repository-side slice after the completed `v1.8.0` route-contract release: explicit distinction between route-enforced reviewer/session conditions and descriptive read-only metadata, plus shared validation/gate wording across readiness, detail, and apply surfaces.

## Highlights

### Reviewer enforcement boundary visibility

`v1.9.0` currently includes:

- explicit `reviewer_enforcement_summary` visibility on UI boundary, mutation readiness, detail, and review-action responses
- explicit separation between route-enforced reviewer/session fields and descriptive-only metadata
- preserved local single-operator scope for all browser-triggered mutation semantics

This keeps the reviewer/session boundary inspectable without widening Chronicle Stack into hosted auth or multi-user authority claims.

### Validation and gate-family alignment

`v1.9.0` currently includes:

- explicit `reviewer_validation_gate_summary` visibility for validation, authorization, target-state, and durable-write-path failure families
- aligned gate wording across preview, apply, readiness, and recovery-facing surfaces
- continued fail-closed separation between pre-mutation/gate failures and durable write-path failures

This keeps operator understanding aligned with the current local review-route boundary and follow-up expectations.

### Preserved local-first mutation boundary

`v1.9.0` preserves:

- explicit-enable local mutation only
- session-gated local operator expectations
- CLI-visible recovery and follow-up guidance
- Chronicle JSONL as primary authority

The UI remains derived and read-only by default outside the explicit local mutation gate.

## Boundary

`v1.9.0` does not add:

- hosted runtime or hosted UI
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

## Verification

Repository-side verification expected before release:

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

## Warning classification

- Release warning: repository-side preparation is not external release publication.
- Auth warning: reviewer/session boundary alignment is not hosted identity proof.
- Mutation warning: gate-family hardening does not imply default GUI mutation.
- Runtime warning: review-surface hardening does not imply hidden provider/runtime execution.
- Security warning: smoke evidence is not security certification.
- Semantics warning: boundary visibility is not correctness proof.

## RDE review

Preserved: Chronicle JSONL authority, local-first UI boundary, fail-closed browser-triggered review semantics, CLI-visible recovery expectations.

Transformed: scattered `v1.9.0` reviewer/session boundary work becomes one release-framed release-note entry point.

Supplemented: explicit release framing for enforcement scope and shared validation/gate-family visibility.

Unresolved: any stronger enforcement beyond the current local route contract surface.
