# ADR-0015: Python Code Splitting and Complexity Management Criteria

Status: Proposed  
Date: 2026-06-15  
Scope: Chronicle Stack Python implementation and future Python-adjacent tooling  
Related: ADR-0001, ADR-0002, ADR-0011, ADR-0012

## Context

Python is easy to start writing and is excellent for early development speed. As a codebase grows, however, multiple responsibilities can accumulate inside a single file, function, or class.

This risk is especially high when files with broad names become central dumping grounds.

Examples:

```text
main.py
app.py
service.py
manager.py
utils.py
```

The following conditions make change impact, testing, review, and refactoring difficult:

- CLI handling, configuration loading, database connection, external API calls, domain logic, logging, and exception handling coexist in the same module.
- Ambiguous `dict`-based data structures spread across multiple modules.
- Side-effecting operations and pure business decisions are not separated.
- Tests require excessive mocks or large fixtures.
- Code that changes for different reasons is locked into the same file, function, or class.
- A function or class becomes the only place where the whole system can be understood.

This is not merely a readability problem.

For Chronicle Stack, such growth can hide semantic change and make ΔM difficult to observe. If responsibilities are fused, a small edit can simultaneously change interface behavior, domain meaning, persistence behavior, audit semantics, and export behavior. That makes review and T-RDE interpretation unreliable.

Therefore this project needs explicit criteria for Python code splitting, dependency direction, complexity, and testability.

## Decision

Python code must be split and managed by responsibility, dependency direction, and testability rather than by line count alone.

Line count is a useful smell, but it is not the primary rule. The primary rule is whether the code still has one coherent reason to change.

## 1. Split by reason for change

Code that changes for the same reason may stay close.

Code that changes for different reasons should be separated.

The following are separate responsibilities by default:

- configuration loading
- CLI / Web API / external input interface
- domain logic
- use-case orchestration
- database / file / external API I/O
- logging setup
- exception definitions
- data structure definitions
- test helpers
- export / serialization formatting
- audit / lifecycle / integrity side surfaces

A module may coordinate multiple responsibilities only if it does not own their internal decisions.

For example, a CLI module may parse options and call a service, but it should not also contain domain policy, persistence details, and output serialization rules.

## 2. Separate I/O from domain logic

Domain logic must not directly mix with volatile side effects unless there is a small and explicit reason.

Avoid direct use of the following inside domain logic:

- `requests`
- `sqlite3`, SQLAlchemy sessions, or DB connections
- `boto3` or cloud SDK clients
- `os.environ`
- `pathlib` / file I/O
- `print`
- current-time acquisition
- random number generation
- process execution
- network calls

Side-effecting operations should live near the outer adapter / infrastructure layer.

The center should contain pure functions or low-side-effect domain services.

Preferred shape:

```text
outer adapters
  parse input, read files, call network, write output

usecases / services
  coordinate workflow and policy

domain
  make business decisions with explicit inputs
```

Current time, random values, and environment-derived configuration should be passed in or provided through small injectable boundaries when they affect test outcomes.

## 3. Fix import direction

The default dependency direction is:

```text
interfaces / cli / api
  ↓
usecases / services
  ↓
domain
  ↓
models / value objects
```

Infrastructure may be used through narrow boundaries:

```text
interfaces / cli / api
  ↓
usecases / services
  ↓
ports / protocols
  ↑
infrastructure adapters
```

The domain layer must not import CLI modules.

The domain layer must not import concrete infrastructure modules such as database clients, cloud SDKs, external API clients, or process-level CLI utilities.

A lower layer should not know which upper layer called it.

When this rule is inconvenient, define an explicit port / protocol or move the orchestration upward.

## 4. Avoid ambiguous `utils.py` growth

A generic `utils.py` file is allowed only for tiny, stable, project-wide helpers.

If a helper starts to represent a domain concept, it must move to a named module.

Prefer specific names:

```text
integrity.py
redaction.py
prompt_injection.py
export_manifest_service.py
audit_log_store.py
lifecycle_service.py
```

Avoid vague names:

```text
utils.py
helpers.py
common.py
manager.py
processor.py
misc.py
```

A utility module should be split when:

- it has more than one conceptual theme
- tests need unrelated fixtures
- it imports high-level project modules
- new helpers are added simply because the file already exists
- naming the helper requires explaining its hidden domain context

## 5. Prefer explicit data structures

Do not allow large `dict` payloads to become implicit domain models.

Use explicit structures when data crosses module boundaries or appears in more than one place:

- dataclasses
- Pydantic models
- typed dictionaries for simple transitional structures
- enums for bounded vocabularies
- value objects for identifiers, classifications, policies, and decisions where appropriate

A raw `dict` is acceptable for:

- direct serialization output
- short local transformations
- tests with intentionally minimal payloads
- metadata maps whose keys are genuinely open-ended

A raw `dict` is a smell when:

- the same keys are repeated across multiple modules
- tests rely on stringly typed keys
- validation is duplicated
- missing keys cause late failures
- reviewers must infer the schema from scattered usage

## 6. Complexity thresholds and refactoring triggers

These are not hard legal limits, but crossing them requires deliberate review.

### Function triggers

Consider splitting or refactoring a function when:

- it exceeds about 40-60 lines
- it has more than 3 levels of nesting
- it has more than 4 meaningful branches
- it mixes validation, business decision, I/O, and formatting
- its tests require several unrelated setup steps
- it cannot be named without using `and`

### Class triggers

Consider splitting or refactoring a class when:

- it has more than one reason to change
- it coordinates workflow and owns persistence details
- it has unrelated public methods
- it requires many optional constructor arguments
- tests need heavy mocking to isolate one method
- it becomes a hidden service locator

### Module triggers

Consider splitting or refactoring a module when:

- it exceeds about 300-500 lines and continues to grow
- it has multiple conceptual sections separated by comments
- it imports both high-level interface modules and low-level infrastructure modules
- it has unrelated tests in the same test file
- a small change frequently causes broad review uncertainty

### Test triggers

Consider refactoring production code when:

- testing a small decision requires constructing the whole application
- tests rely on many mocks for ordinary behavior
- fixtures become larger than the behavior under test
- test names describe setup more than behavior
- snapshot tests hide meaningful semantic change

## 7. Keep orchestration thin

Use-case or service code may orchestrate several collaborators, but it should avoid owning too much policy.

A use case may:

- validate inputs
- call domain policy
- call repositories or stores through explicit boundaries
- coordinate audit / lifecycle / export surfaces
- return a typed result

A use case should not also:

- parse CLI arguments
- format terminal output
- embed raw SQL or low-level file details
- construct large untyped payloads
- make hidden external calls

## 8. Keep CLI and API layers thin

CLI and API modules are interface adapters.

They may:

- parse user input
- call services
- translate service results into user-facing output
- map exceptions to exit codes or API responses

They should not:

- contain domain policy
- directly perform persistence logic
- construct complex package/export/audit semantics
- call external models or network services without service-level boundaries

When CLI code begins to require extensive tests for business meaning, that meaning should move into a service or domain function.

## 9. Make side effects visible

Functions or services that perform side effects should make them obvious in naming, return values, or boundaries.

Examples:

```text
record_export_audit(...)
write_package(...)
load_contexts(...)
build_export_manifest(...)
```

Avoid hiding side effects behind names such as:

```text
prepare(...)
process(...)
handle(...)
run(...)
```

unless the surrounding layer clearly defines the side-effect boundary.

## 10. Treat warnings and audit as first-class surfaces

For Chronicle Stack, audit, lifecycle, integrity, export, and Observation E2E surfaces are not incidental.

When code touches these surfaces, it should be structured so reviewers can see:

- what primary data is preserved
- what derived surface is written
- what warnings are surfaced
- what is advisory rather than enforced
- what is not proof, certification, or consent

This is especially important for code that writes:

```text
.chronicle/audit.jsonl
.chronicle/lifecycle.jsonl
.chronicle/packages/*
export manifests
```

## 11. Review checklist

When reviewing Python changes, ask:

```text
Does this code have one reason to change?
Are side effects separated from domain decisions?
Is the import direction preserved?
Are data structures explicit enough?
Can the core behavior be tested without heavy mocks?
Are warnings and boundary claims visible?
Could a future reader reconstruct the semantic change?
```

If the answer is no, split the code or record a follow-up issue with warning classification.

## Consequences

### Positive

- Changes become easier to review.
- Tests become smaller and more meaningful.
- Domain policy is less likely to be hidden inside interface code.
- ΔM becomes easier to observe because semantic changes are localized.
- Audit, lifecycle, export, and package behavior remain easier to reason about.

### Negative / Cost

- More modules may be created earlier than in small scripts.
- Some changes require naming boundaries before implementation feels strictly necessary.
- Over-splitting can create indirection if not guided by responsibility.
- Review may reject otherwise working code when responsibility boundaries are unclear.

## Non-goals

This ADR does not require:

- strict line-count enforcement
- microservice-style fragmentation
- over-engineered abstractions
- dependency injection frameworks
- complete domain-driven design formalism
- banning small scripts or simple local helpers

This ADR also does not replace tests, type checking, or CI.

## RDE Review

### Preserved

- Python remains the primary implementation language for Chronicle Stack.
- Fast iteration remains important.
- Simple functions and modules remain acceptable when their responsibility is clear.

### Transformed

- Code organization becomes part of Chronicle Stack governance rather than personal style.
- Large-code smells are interpreted as risks to semantic observability, not only readability.

### Added

- Responsibility-based splitting criteria.
- I/O and domain separation rule.
- Import direction guidance.
- Complexity and refactoring triggers.
- Review checklist connected to ΔM observability.

### Unresolved

- Whether CI should enforce specific complexity metrics later.
- Whether `ruff`, `radon`, or similar tools should become advisory checks.
- Exact package layout for future v0.6+ implementation surfaces.
- How strictly this ADR should apply to one-off migration scripts.

### Deviation Risks

- Treating line count as the only complexity signal.
- Over-splitting code into meaningless abstractions.
- Creating generic managers and utilities that hide domain meaning.
- Letting adapter code accumulate policy decisions.
- Hiding semantic changes behind mocks, fixtures, or broad snapshot tests.
