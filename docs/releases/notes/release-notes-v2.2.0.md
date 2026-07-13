# Release Notes v2.2.0

## Added

- stable AI interpretation warning categories:
  - `not_primary_fact`
  - `review_required`
  - `decay_candidate`
  - `external_context_disclosure`
  - `derived_content_persisted`
- structured warning severity, message, and next-safe-action contracts
- CLI and runtime/UI read-model visibility for interpretation warnings
- Stage C Security and Boundary Baseline completion evidence

## Changed

- project and CLI version report `2.2.0`
- overall roadmap now identifies Stage C as complete
- the next roadmap slice is the final reading flow for major local UI workspaces

## Verification

- Ruff passed for `src/` and `tests/`
- 511 tests passed locally
- GitHub CI passed on PR #385
- structured warning CLI JSON and runtime preview surfaces are covered by tests

## Boundary

- warning classification is advisory, not RBAC/ABAC or model-correctness proof
- AI preview does not send context externally
- generated interpretation remains separate from primary facts and requires review
- identity enforcement, tenant isolation, perfect prompt-injection prevention, cryptographic attestation, and OS-level sandboxing remain outside this release
