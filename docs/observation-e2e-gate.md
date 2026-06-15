# Observation E2E Gate

Status: Draft for v0.6-beta  
Related: ADR-0002, ADR-0011, #87, #127

## Purpose

Observation E2E is a separate workflow observation surface for Chronicle Stack.

It exists to make user-facing and integration-facing behavior visible across realistic command sequences, especially when multiple security-aware surfaces interact.

Observation E2E is not a replacement for Core CI. It is not a proof of semantic correctness, safety, security, privacy sufficiency, lifecycle enforcement, or policy sufficiency.

## Relationship to Core CI

Core CI remains the primary phase gate.

Core CI checks the repository-wide implementation surface, including linting, tests, serialization contracts, and known behavior. Observation E2E checks whether important workflows still look coherent from the outside.

```text
Core CI          = primary merge phase gate
Observation E2E  = separate workflow observation surface
```

Observation E2E may be run during release preparation, workflow-sensitive PRs, CLI changes, documentation updates, or security-aware feature work. It should not be silently promoted into a required merge gate without a new architecture decision.

A Core CI pass does not imply Observation E2E pass. An Observation E2E pass does not imply semantic correctness or security certification.

## What Observation E2E observes

Observation E2E should focus on externally visible workflow drift.

Examples:

- command sequence drift
- output shape drift
- warning classification drift
- documentation / command mismatch
- doctor status drift
- export profile behavior drift
- lifecycle-aware export behavior drift
- package persistence and package inspection drift
- package boundary drift
- lifecycle / audit surface parseability drift

Observation E2E should not try to prove that a generated output is semantically correct.

## Initial scenario inventory

The v0.6-beta scenario inventory starts with the following candidates.

### Fresh project and doctor warning semantics

Scenario:

```bash
chronicle init --title "Observation E2E"
chronicle doctor
chronicle doctor --json
```

Expected observation:

- project initializes
- doctor remains read-only
- new security-readiness warnings are visible where expected
- warning status is interpreted as incomplete security readiness, not structural corruption

### Classification metadata example

Scenario:

```bash
chronicle add-context --title "Internal Context" --summary "Internal review context" --scope task --visibility private
```

Expected observation:

- context record remains valid whether classification metadata is present or absent
- unclassified context may produce advisory warnings in security-aware checks

### Context-use dry-run example

Scenario:

```bash
chronicle-context check --target local --purpose "internal review"
chronicle-context check --target external --purpose "draft public summary" --json
```

Expected observation:

- commands do not call external model APIs
- dry-run result distinguishes allow, warn, and block cases where applicable
- external target use is stricter than local target use

### Prompt-injection data-boundary example

Scenario:

- store content containing instruction-like text
- package or prepare the content for model-facing use

Expected observation:

- stored Chronicle content remains faithful
- model-facing representation wraps stored content as data, not instructions
- prompt-injection scan results are advisory, not complete safety guarantees

### Security-aware export profile example

Scenario:

```bash
chronicle-export profile --format yaml --profile public-review
chronicle-export profile --format yaml --profile restricted-summary
```

Expected observation:

- public and restricted profiles are stricter than internal/local profiles
- profile behavior remains documented and explicit
- export remains a derived projection, not publication approval

### Lifecycle-aware export example

Scenario:

```bash
chronicle export --format markdown
chronicle export --format yaml
chronicle export --format html
chronicle export --format graph-json
```

Expected observation:

- derived exports omit records marked by tombstone or hard-delete lifecycle markers where lifecycle data is available
- sealed records remain visible but are marked or warned as `lifecycle_sealed_record`
- directly referencing event rows or nodes are hidden when they would leak lifecycle-omitted record titles or summaries
- lifecycle-aware export remains advisory derived-output filtering, not deletion or access-control enforcement

### Controlled package generation example

Scenario:

```bash
chronicle-package context --purpose "Sayane review" --target local
chronicle-package context --purpose "External review" --target external
```

Expected observation:

- package generation does not submit content to external services
- Layer 4 or restricted content defaults to reference-only where applicable
- package records are transport contracts, not permission grants

### Package persistence and inspection example

Scenario:

```bash
chronicle-package context --purpose "Persistence observation" --persist
chronicle-package list
chronicle-package show --package <package_id>
chronicle-package records --package <package_id>
```

Expected observation:

- persisted package manifests and record summaries are inspectable
- record inspection does not print full record body content by default
- package persistence remains a derived transport artifact, not permission grant or external submission
- package audit metadata records package facts but does not copy record body content

### Audit and lifecycle parseability example

Scenario:

- create or provide `.chronicle/audit.jsonl`
- create or provide `.chronicle/lifecycle.jsonl`
- run doctor or parseability checks

Expected observation:

- parseable logs are recognized
- malformed logs are reported as workflow-relevant warnings or failures
- audit and lifecycle surfaces remain separate from the original record surface

## Gate status vocabulary

Observation E2E should use a status vocabulary that is distinct from Core CI.

```text
pass
warning
fail
not-run
```

### pass

The observed workflow completed and no material drift was detected for the scenario.

`pass` does not mean semantic correctness or security certification.

### warning

The workflow completed, but drift, ambiguity, incomplete security readiness, environmental limitation, or follow-up work was observed.

Warnings must be classified as:

```text
blocking
tracked separately
informational
```

### fail

The workflow could not complete, or the observed behavior contradicts a documented contract or boundary.

A failure may block a release or PR when the affected workflow is in scope.

### not-run

The scenario was not executed.

`not-run` must not be presented as success.

## What counts as drift

Observation E2E drift includes:

- documented command no longer exists
- command output shape changes without documentation update
- expected warning disappears unexpectedly
- warning becomes an unclassified failure
- a dry-run performs real external submission
- package generation changes body/reference-only semantics
- package persistence or inspection exposes body content where only summaries were expected
- export profile behavior diverges from documentation
- lifecycle-aware export silently leaks omitted record content through another derived surface
- lifecycle or audit surfaces are silently ignored where observability was expected

## What does not count as certification

Observation E2E does not certify:

- semantic correctness
- security correctness
- privacy sufficiency
- absence of prompt-injection risk
- correctness of future model interpretation
- cryptographic integrity
- compliance with deletion laws
- physical deletion
- access-control enforcement
- correctness of GraphRAG or Sayane runtime behavior

## Recording results

When Observation E2E is relevant to a PR or release, record:

```text
- scenario name
- status: pass / warning / fail / not-run
- command or workflow summary
- observed warnings
- warning classification
- follow-up issue numbers, if any
```

This can be recorded in the PR body, release-readiness document, smoke-test document, or issue close comment.

## RDE review frame

### Preserved

- Core CI remains the primary phase gate.
- Observation E2E remains separate from Core CI.
- JSONL primary record semantics remain unchanged.
- Security-aware metadata remains advisory unless later explicitly enforced.
- Lifecycle markers remain advisory derived-output signals unless later explicitly enforced.

### Transformed

- v0.5 and v0.6 contracts become observable workflow expectations.
- Warnings become part of release and workflow provenance rather than incidental console output.
- Lifecycle-aware derived export behavior becomes part of the observation inventory.

### Added

- Gate status vocabulary.
- Scenario inventory.
- Drift definition.
- Result recording guidance.
- Lifecycle-aware export and package persistence observation scenarios.

### Unresolved

- Exact runner implementation.
- Whether Observation E2E should become required for specific release types.
- Where golden snapshots should live if introduced.
- How to keep workflow snapshots stable without hiding meaningful drift.

### Deviation risks

- Treating Observation E2E pass as semantic correctness proof.
- Treating Observation E2E pass as security certification.
- Treating lifecycle-aware export observation as deletion or access-control proof.
- Making examples too brittle to serve as practical observations.
- Over-normalizing outputs until meaningful warnings disappear.
