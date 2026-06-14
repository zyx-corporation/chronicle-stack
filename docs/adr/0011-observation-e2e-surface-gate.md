# ADR-0011: Observation E2E as Separate Surface Gate

Status: Accepted  
Date: 2026-06-15  
Scope: Chronicle Stack v0.6-alpha and later  
Related: ADR-0002, `docs/observation-e2e-gate.md`, #87, #88

## Context

ADR-0002 established that Core CI is the primary phase gate and that Observation E2E is a separate surface gate.

However, ADR-0002 intentionally did not define the exact Observation E2E workflow.

Chronicle Stack v0.5 added several security-aware foundation surfaces:

```text
classification metadata
context-use dry-runs
prompt-injection boundary helpers
audit log surface
lifecycle log surface
integrity metadata helpers
doctor security checks
security-aware export profiles
controlled integration packages
```

These surfaces interact through user-facing workflows. Unit tests and contract tests can check known internal behavior, but they do not fully show whether a workflow still appears coherent from the outside.

Chronicle Stack therefore needs an observation layer for workflow drift while preserving the governance boundary that CI pass does not prove correctness or security.

## Decision

Chronicle Stack will define **Observation E2E** as a separate surface gate for workflow-oriented observation.

Observation E2E is not part of Core CI by default.

```text
Core CI          = primary phase gate
Observation E2E  = separate workflow observation surface
```

Observation E2E may be used for:

- release readiness checks
- workflow-sensitive PRs
- CLI surface changes
- export/profile changes
- package generation changes
- doctor behavior changes
- audit/lifecycle surface changes
- documentation-to-command consistency checks

Observation E2E must not be treated as:

- semantic correctness certification
- security certification
- privacy sufficiency certification
- proof of absence of prompt-injection risk
- GraphRAG runtime validation
- external model behavior validation

## Status vocabulary

Observation E2E uses the following vocabulary:

```text
pass
warning
fail
not-run
```

### pass

The observed workflow completed and no material drift was detected for the scenario.

A pass does not prove that the workflow is correct, safe, complete, or semantically valid.

### warning

The observed workflow completed, but a drift, ambiguity, incomplete security-readiness condition, or follow-up concern was identified.

Warnings must be classified as:

```text
blocking
tracked separately
informational
```

### fail

The workflow did not complete, or the observed behavior contradicts a documented contract, boundary, or expected workflow condition.

### not-run

The scenario was not executed.

Not-run must not be reported as pass.

## Initial scenario classes

Observation E2E should begin with scenarios that exercise v0.5 security-aware foundation surfaces.

Candidate scenario classes:

```text
fresh project init + doctor warning semantics
classification metadata examples
context-use dry-run examples
prompt-injection data-boundary example
security-aware export profile behavior
controlled package generation
audit/lifecycle parseability
```

The scenario inventory is defined in `docs/observation-e2e-gate.md`.

## Recording policy

When Observation E2E is relevant, the PR, release-readiness document, smoke-test document, or issue close comment should record:

```text
- scenario name
- status
- command/workflow summary
- observed warnings
- warning classification
- follow-up issue numbers, if any
```

This mirrors Chronicle Stack's provenance principle: the reason a workflow was considered ready should be reconstructable later.

## Consequences

### Positive

- Workflow drift becomes visible without overloading Core CI.
- v0.5 security-aware contracts become observable in real command sequences.
- Release readiness can distinguish implementation success from workflow coherence.
- Warnings can be preserved as part of project provenance.

### Negative / Cost

- PRs and releases may need additional observation notes.
- Observation scenarios may become brittle if they overfit exact output text.
- Maintaining scenario documentation requires discipline.
- Some drift may be ambiguous and require human judgment.

## Non-goals

This ADR does not:

- implement an Observation E2E runner
- promote Observation E2E to a required branch protection check
- replace Core CI
- define golden snapshot storage
- add external model calls
- introduce GraphRAG runtime behavior
- certify security, privacy, or semantic correctness

## RDE Review

### Preserved

- Core CI remains the primary phase gate.
- CI pass remains non-certifying.
- Observation E2E remains separate from Core CI.
- JSONL remains the primary record surface.
- Security-aware metadata and policies remain advisory unless later explicitly enforced.

### Transformed

- Observation E2E moves from an undefined term in ADR-0002 into a defined workflow observation gate.
- v0.5 security-aware surfaces gain a shared workflow observation vocabulary.

### Added

- Observation E2E status vocabulary.
- Initial scenario classes.
- Result recording policy.
- Explicit non-certification boundary.

### Unresolved

- Exact runner implementation.
- Whether any scenario class becomes required for final releases.
- Snapshot strategy.
- Environment isolation strategy.
- How Observation E2E results should be surfaced in GitHub labels or release templates.

### Deviation Risks

- Treating Observation E2E pass as correctness proof.
- Treating Observation E2E pass as security proof.
- Promoting Observation E2E into a slow mandatory gate without governance review.
- Hiding meaningful warnings through excessive output normalization.
- Creating brittle scenarios that fail on harmless formatting changes.
