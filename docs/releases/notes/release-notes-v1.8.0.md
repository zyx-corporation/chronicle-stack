# Chronicle Stack v1.8.0 Release Notes

Related: `../../adr/0023-browser-triggered-review-write-semantics.md`, `../../adr/0026-local-reviewer-session-proof-representation.md`, `../../adr/0027-local-gui-review-route-contract.md`, `../readiness/release-readiness-v1.8.md`, `../smoke/smoke-test-v1.8.md`

## Summary

Chronicle Stack `v1.8.0` is currently framed as a local GUI review-route design-hardening and contract-hardening release over `v1.7.0`.

This release lane consolidates the next repository-side slice after the completed `v1.7.0` observability release: explicit action-route family visibility, explicit CLI-equivalent route visibility, and explicit HTTP status semantics for the current fail-closed local review route contract.

## Highlights

### Local GUI review route family visibility

`v1.8.0` currently includes:

- explicit read-only exposure of the local GUI review route family
- explicit per-action route templates for `approve`, `reject`, and `request-changes`
- explicit CLI-equivalent route semantics for each supported review action

This keeps the browser-side route contract inspectable without widening the product into hosted or default-on mutation behavior.

### Status-code contract visibility

`v1.8.0` currently includes:

- explicit read-only exposure of write-route status-code semantics
- route-family alignment for `200`, `400`, `403`, `404`, `409`, and `500`
- continued fail-closed separation between pre-mutation/gate failures and durable write-path failures

This keeps operator understanding aligned with the current local review-route boundary and recovery expectations.

### Preserved local-first mutation boundary

`v1.8.0` preserves:

- explicit-enable local mutation only
- single-operator local boundary assumptions
- CLI-visible recovery and follow-up guidance
- Chronicle JSONL as primary authority

The UI remains derived and read-only by default outside the explicit local mutation gate.

## Boundary

`v1.8.0` does not add:

- hosted runtime or hosted UI
- default-on GUI mutation
- multi-user authentication or authorization
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
chronicle 1.8.0
```

## Warning classification

- Release warning: repository-side preparation is not external release publication.
- Mutation warning: route-contract hardening does not imply default GUI mutation.
- Auth warning: reviewer/session proof remains local-first boundary metadata, not multi-user-safe authority.
- Runtime warning: review-route hardening does not imply hidden provider/runtime execution.
- Security warning: smoke evidence is not security certification.
- Semantics warning: contract visibility is not correctness proof.

## RDE review

Preserved: Chronicle JSONL authority, local-first UI boundary, fail-closed browser-triggered review semantics, CLI-visible recovery expectations.

Transformed: scattered `v1.8.0` contract-hardening progress becomes one release-framed release-note entry point.

Supplemented: explicit release framing for action-route family visibility and status-code contract visibility.

Unresolved: any stronger enforcement beyond the current local route contract surface.
