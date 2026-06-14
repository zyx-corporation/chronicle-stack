# ADR-0002: CI as T-RDE Execution and Phase Gate

Status: Accepted  
Date: 2026-06-14  
Scope: Chronicle Stack v0.5 and later  
Related: ADR-0001, `docs/roadmap-v0.5.md`, `.github/workflows/*`

## Context

Chronicle Stack uses CI to run project checks before code and documentation changes are merged.

As Chronicle Stack moves into security-aware composition, CI must be treated as part of architecture governance rather than merely an automation convenience.

Chronicle Stack also uses RDE / T-RDE thinking: changes should be observed for preserved elements, transformed elements, added elements, unresolved issues, and deviation risks.

CI is one execution surface for that discipline.

However, CI pass must not be mistaken for correctness certification. CI can show that known checks passed. It cannot prove that the system is correct, secure, complete, or semantically valid.

## Decision

Chronicle Stack will treat CI as a **project-wide T-RDE execution surface** and as a phase gate for development work.

The following governance rules apply:

```text
- CI is applied project-wide.
- Core CI is the primary phase gate.
- Observation E2E is a separate surface gate.
- CI results must be recorded before closing implementation issues.
- Warnings must be classified as blocking, tracked separately, or informational.
- CI workflow changes are architecture governance changes.
- CI is an execution surface for T-RDE.
- CI pass is not correctness certification.
```

## CI Surfaces

### Core CI

Core CI is the primary phase gate for ordinary PR merge and issue closure.

Core CI includes the repository-wide checks that confirm the project remains executable and internally consistent, such as:

```text
ruff check src/ tests/
pytest -v
```

Core CI is project-wide. Even when a change looks local, it can affect serialization, CLI behavior, export behavior, doctor behavior, or interface contracts.

### Observation E2E

Observation E2E is a separate surface gate.

It covers observation-oriented, integration-oriented, UI-oriented, or workflow-oriented behavior that is broader than the core library and unit/contract test surface.

Observation E2E should not be silently folded into Core CI without explicit governance review, because it has a different purpose and failure interpretation.

## Warning Classification

Warnings must be classified before an issue is closed.

```text
blocking:
  The PR, release, or issue close must stop until resolved.

tracked separately:
  The current issue may close, but a follow-up issue must track the warning.

informational:
  The warning is recorded for context, but does not require immediate action.
```

Warnings must not be treated as either all-blocking or all-ignorable.

## Issue Closure Policy

Before closing an implementation issue, the closing PR or issue comment should record:

```text
- Core CI result
- Observation E2E result, if applicable
- remaining warnings
- warning classification
- unresolved follow-up items
```

This is consistent with Chronicle Stack's own provenance principle: the reason an issue was considered done should be reconstructable later.

## CI Workflow Governance

Changes to CI workflow files are architecture governance changes.

Changing CI means changing what the project treats as a gate. Therefore CI workflow changes should be reviewed as architectural changes, not as incidental maintenance.

Examples:

```text
- adding or removing required checks
- changing warning handling
- changing test scope
- splitting or merging Core CI and Observation E2E
- changing allowed failure behavior
- changing required Python versions or execution environments
```

## T-RDE Interpretation

CI is one execution surface for T-RDE.

CI can help detect:

```text
- regressions
- interface drift
- serialization drift
- contract breakage
- style or lint deviation
- test coverage for known expected behavior
```

CI does not prove:

```text
- semantic correctness
- security correctness
- policy sufficiency
- absence of prompt-injection risk
- correctness of future interpretation
- completeness of threat modeling
```

## Consequences

### Positive

- CI becomes aligned with Chronicle Stack's provenance and RDE principles.
- Issue closure becomes auditable.
- Warning handling becomes explicit.
- Core CI and Observation E2E remain distinct surfaces.
- CI workflow changes receive appropriate governance attention.

### Negative / Cost

- PRs and issues need slightly more explicit verification notes.
- Some warnings require follow-up issue creation.
- CI workflow changes become slower, because they require architectural review.

## Non-goals

This ADR does not define:

- exact Observation E2E implementation
- branch protection settings
- required GitHub status checks
- full release governance
- security certification
- correctness certification

## RDE Review

### Preserved

- CI remains automated project verification.
- Core CI remains the ordinary merge gate.
- RDE remains a structured way to observe change, not a proof system.

### Transformed

- CI is reframed as a T-RDE execution surface.
- CI workflow changes are treated as architecture governance.
- Issue closure requires CI result recording.

### Added

- Core CI vs Observation E2E distinction.
- Warning classification policy.
- Explicit statement that CI pass is not correctness certification.

### Unresolved

- Exact Observation E2E workflow definition.
- Whether branch protection should enforce Core CI.
- Where CI results should be recorded for issue closure.
- How warning classification labels should be represented in GitHub.

### Deviation Risks

- Treating CI pass as proof of correctness.
- Treating all warnings as non-blocking.
- Expanding Core CI until it becomes too slow to serve as a practical phase gate.
- Allowing CI workflow changes without governance review.
