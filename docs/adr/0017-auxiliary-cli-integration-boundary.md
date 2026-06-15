# ADR-0017: Auxiliary CLI Integration Boundary

Status: Accepted  
Date: 2026-06-15  
Scope: Chronicle Stack v0.6-final and later  
Related: ADR-0011, ADR-0012, ADR-0014, ADR-0016, #87, #130

## Context

Chronicle Stack currently exposes a primary CLI and several auxiliary command entry points.

Current package scripts include:

```text
chronicle          = primary CLI
chronicle-graph    = graph inspection / graph export related auxiliary CLI
chronicle-context  = model-context dry-run auxiliary CLI
chronicle-export   = security-aware export profile auxiliary CLI
chronicle-package  = controlled integration package auxiliary CLI
```

The primary `chronicle` CLI already hosts core commands and several command groups:

```text
chronicle init
chronicle add-context
chronicle export
chronicle doctor
chronicle artifact ...
chronicle decision ...
chronicle rde ...
chronicle index ...
chronicle boundary ...
chronicle injection ...
```

v0.6 added more durable derived surfaces:

```text
package persistence
package inspection
lifecycle-aware exports
Observation E2E boundary documentation
future HTTP bridge guidance
```

As these surfaces mature, it becomes desirable to expose them through a more coherent primary CLI shape such as:

```text
chronicle context ...
chronicle package ...
chronicle export profile ...
chronicle graph ...
```

However, existing auxiliary scripts may already be used in local workflows, documentation, tests, and Observation E2E scenarios. Removing or renaming them would create avoidable workflow drift.

## Decision

Chronicle Stack will treat auxiliary CLI integration as a compatibility-preserving transition.

Current auxiliary entry points remain supported during v0.6:

```text
chronicle-context
chronicle-export
chronicle-package
chronicle-graph
```

Future work may add equivalent primary CLI subcommands, but it must not remove the auxiliary scripts in the same step.

Preferred migration shape:

```text
existing auxiliary command remains available
new primary CLI route is added as an alias or shared registration path
Observation E2E records both old and new surfaces during transition
later deprecation, if any, requires a separate ADR or release policy
```

The first v0.6 decision is therefore:

```text
Document the boundary first. Do not rewrite or remove CLI behavior in this slice.
```

## Rationale

Auxiliary CLIs were introduced to keep new surfaces isolated while they were still stabilizing.

That separation had value:

- it reduced risk to the primary `chronicle` command
- it allowed package/export/context-use work to evolve independently
- it made security-aware surfaces explicit
- it avoided overloading the primary CLI during early design

But long-term usability favors a coherent primary CLI namespace.

The challenge is to improve discoverability without creating compatibility drift. A transition policy is needed before implementation begins.

The policy mirrors other Chronicle Stack boundaries:

```text
primary JSONL remains source of truth
exports remain derived projections
packages remain transport contracts
Observation E2E remains non-certifying
auxiliary scripts remain compatibility surfaces during migration
```

## Consequences

### Positive

- Existing scripts remain stable for users, tests, docs, and local workflows.
- Future primary CLI integration can proceed incrementally.
- Observation E2E can detect drift between auxiliary and primary aliases.
- The project avoids treating CLI cleanup as permission to break established command names.
- Command grouping can improve without forcing a single large CLI rewrite.

### Negative / Cost

- Duplicate command surfaces may exist during transition.
- Documentation must clearly distinguish canonical, auxiliary, and transitional command paths.
- Tests may need to cover both entry points when behavior parity matters.
- The project must avoid letting compatibility aliases become undocumented clutter.

## Required Future Pattern

When integrating an auxiliary command into the primary CLI, prefer shared registration or a shared service boundary rather than duplicating business logic.

Accepted direction:

```text
service / command implementation is shared
auxiliary CLI keeps existing script name
primary CLI adds equivalent subcommand
behavioral parity is tested for the shared path
```

Example target shape:

```text
chronicle-context check ...
chronicle context check ...
```

```text
chronicle-package context --persist ...
chronicle package context --persist ...
```

```text
chronicle-export profile --profile public-review ...
chronicle export profile --profile public-review ...
```

```text
chronicle-graph summary ...
chronicle graph summary ...
```

Any implementation PR should clearly state whether it adds aliases, changes canonical documentation, or begins a deprecation path.

## Rejected Patterns

### Immediate removal of auxiliary scripts

Rejected because it would break existing local workflows and Observation E2E scenarios.

### Silent behavior divergence

Rejected because an auxiliary command and its primary alias must not produce materially different behavior unless documented as separate surfaces.

### One-shot CLI rewrite

Rejected because it risks destabilizing multiple mature surfaces at once.

### Treating primary CLI integration as semantic improvement

Rejected because moving a command path does not by itself improve package, export, lifecycle, or context-use semantics.

## Observation E2E Guidance

Observation E2E should treat auxiliary CLI integration as workflow drift-sensitive.

Candidate future scenarios:

```text
chronicle-context check ...
chronicle context check ...
```

```text
chronicle-package list
chronicle package list
```

```text
chronicle-export profile --format yaml --profile public-review
chronicle export profile --format yaml --profile public-review
```

Expected observation:

- both command surfaces remain available during transition
- output shape remains compatible where behavior is intended to be equivalent
- warnings remain classified the same way
- no command performs external model or runtime calls unless explicitly documented
- alias pass does not imply semantic correctness or security certification

## Non-goals

This ADR does not:

- add primary CLI aliases
- remove auxiliary scripts
- deprecate auxiliary scripts
- change package, export, graph, context-use, lifecycle, or audit semantics
- add an Observation E2E runner
- introduce external model, vector DB, graph DB, embedding, or runtime calls
- certify CLI behavior as semantically correct

## RDE Review

### Preserved

- Existing auxiliary CLI scripts remain supported.
- Primary CLI behavior remains unchanged in this decision.
- Service-layer semantics remain the source of behavior, not command naming.
- Observation E2E remains a non-certifying workflow observation surface.

### Transformed

- Auxiliary CLI integration moves from an implicit future cleanup idea into an explicit compatibility-preserving migration boundary.
- Command names are treated as user-facing workflow contracts rather than disposable implementation details.

### Added

- A migration policy for future primary CLI aliases.
- A warning against removing auxiliary scripts during the first integration step.
- Observation E2E guidance for auxiliary/primary parity checks.

### Unresolved

- Which auxiliary command should be integrated first.
- Whether any command path becomes canonical in v0.6-final documentation.
- Whether deprecation policy is needed after parity aliases exist.
- Exact test strategy for command parity.

### Deviation Risks

- Treating a new primary CLI alias as permission to remove auxiliary scripts.
- Allowing alias behavior to drift from auxiliary command behavior.
- Treating command-path cleanup as a semantic improvement to package/export/lifecycle behavior.
- Expanding primary CLI integration into a broad rewrite without a separate implementation issue.
