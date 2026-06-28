# Chronicle Stack v0.6 Release Readiness

Status: Final readiness candidate  
Target: v0.6.0  
Theme: Observation Gates and Controlled Runtime Integration Boundaries

## Summary

v0.6 moves Chronicle Stack from v0.5 security-aware foundation contracts toward observable workflows and controlled runtime integration boundaries.

The release strengthens derived-output behavior, package persistence, Observation E2E documentation, primary CLI discoverability, and future bridge guidance without claiming enforcement or runtime execution guarantees.

v0.6 does not claim semantic correctness, complete security, access control, physical deletion, lifecycle enforcement, GraphRAG execution, vector database integration, graph database integration, external model execution, or complete encrypted storage.

## Scope Completion

| Issue | Scope | Status |
|---|---|---|
| #87 | v0.6 roadmap | In progress until release closure |
| #88 | Observation E2E surface gate ADR | Complete |
| #89 | Audit insertion point ADR | Complete |
| #90 | Package persistence ADR / model | Complete |
| #91 | Package persistence implementation | Complete |
| #92 | Package inspection commands | Complete |
| #114 | Lifecycle-aware Markdown export slice | Complete |
| #117 | Lifecycle-aware YAML export slice | Complete |
| #119 | Lifecycle-aware HTML export slice | Complete |
| #121 | Lifecycle-aware graph-json export slice | Complete |
| #123 | Lifecycle export helper consolidation | Complete |
| #125 | HTML lifecycle helper consolidation | Complete |
| #127 | Observation E2E boundary refresh | Complete |
| #130 | Auxiliary CLI integration boundary ADR | Complete |
| #132 | Primary package CLI alias | Complete |
| #134 | Primary context CLI alias | Complete |
| #136 | Primary graph CLI alias | Complete |
| #138 | Primary export profile CLI alias | Complete |
| #140 | Primary CLI alias documentation | Complete |
| #142 | v0.6 release-readiness document | This document |

## Release Readiness Criteria

| Criterion | Status | Notes |
|---|---|---|
| Core CI pass | Pending final PR | All implementation slices were merged after CI success; final release PR still requires CI confirmation |
| Warning classification recorded | Ready | PR descriptions and #87 progress updates recorded warning classification |
| Observation E2E boundary defined | Ready | ADR-0011 and `../../observation-e2e-gate.md` define separate non-certifying surface gate |
| Observation E2E not promoted to Core CI | Ready | Core CI remains primary phase gate |
| Package persistence available | Ready | Persisted manifests and record summaries are available under `.chronicle/packages` |
| Package inspection avoids body dumping | Ready | `records` inspection reports summaries and `has_content`, not full body content |
| Lifecycle-aware exports available | Ready | Markdown, YAML, HTML, and graph-json derived exports interpret lifecycle markers |
| Lifecycle markers remain advisory | Ready | Tombstone / hard-delete markers filter derived outputs but do not physically delete primary records |
| Primary CLI aliases available | Ready | package, context, graph, and export profile surfaces are reachable through `chronicle ...` |
| Auxiliary CLI compatibility preserved | Ready | `chronicle-package`, `chronicle-context`, `chronicle-graph`, and `chronicle-export` remain available |
| Future HTTP bridge auth boundary documented | Ready | ADR-0016 records future guidance without adding HTTP runtime code |
| No external model/runtime calls introduced | Ready | context checks, packages, exports, and graph inspection remain local operations |

## Implemented Capabilities

### Observation E2E Boundary

v0.6 defines Observation E2E as a separate workflow observation surface.

```text
Core CI          = primary merge phase gate
Observation E2E  = separate workflow observation surface
```

Observation E2E can expose workflow drift. It does not certify semantic correctness, security, privacy sufficiency, lifecycle enforcement, access-control enforcement, or GraphRAG/Sayane runtime behavior.

### Package Persistence and Inspection

Controlled integration packages can be persisted and inspected.

```bash
chronicle package context --purpose "Sayane review" --target local --persist
chronicle package list
chronicle package show --package pkg_xxx
chronicle package records --package pkg_xxx --json
```

Package persistence remains a derived transport artifact. It is not a permission grant, external submission, access-control decision, or proof of safety.

Record inspection intentionally exposes summaries and metadata rather than dumping full package body content.

### Lifecycle-aware Exports

Derived exports now interpret lifecycle markers.

Supported derived export surfaces:

```text
markdown
yaml
html
graph-json
```

Candidate behavior now implemented:

- tombstone / hard-delete markers omit matching records from derived outputs
- directly referencing event rows or graph event nodes are hidden when they would leak omitted record titles or summaries
- sealed records remain visible but are marked or warned as `lifecycle_sealed_record`
- primary JSONL remains unchanged

Boundary:

```text
lifecycle-aware export != physical deletion
lifecycle-aware export != access-control enforcement
hard_delete marker != actual erasure
```

### Primary CLI Aliases

v0.6 adds compatibility-preserving primary CLI aliases for previously auxiliary surfaces.

```bash
chronicle package ...
chronicle context ...
chronicle graph ...
chronicle export profile ...
```

Auxiliary scripts remain supported:

```bash
chronicle-package ...
chronicle-context ...
chronicle-graph ...
chronicle-export profile ...
```

The aliases share the same Typer apps or command implementations where practical. They are not semantic rewrites.

### Future HTTP Bridge Auth Boundary

ADR-0016 records a future-facing rule for HTTP bridge / Sayane integration surfaces:

```text
auth-only HTTP dependencies should be route metadata, not endpoint dummy parameters
```

This does not add FastAPI, a Chronicle HTTP bridge, authentication, or access-control enforcement to Chronicle Stack v0.6.

## ADR Coverage

| ADR | Decision |
|---|---|
| ADR-0001 | Treat Chronicle Records as Context Assets |
| ADR-0002 | CI as T-RDE Execution and Phase Gate |
| ADR-0003 | Encrypted Store Abstraction Boundary |
| ADR-0004 | Prompt Injection Sanitizer Boundary |
| ADR-0005 | Audit Log for Derived Operations |
| ADR-0006 | Lifecycle Model for Redact / Seal / Tombstone |
| ADR-0007 | Integrity Metadata Preparation |
| ADR-0008 | Doctor Security Checks |
| ADR-0009 | Security-aware Export Profiles |
| ADR-0010 | Controlled CSG-RAG / Sayane Integration Packages |
| ADR-0011 | Observation E2E as Separate Surface Gate |
| ADR-0012 | Audit Insertion Points for Derived Operations |
| ADR-0013 | Lifecycle-aware Export Filtering |
| ADR-0014 | Package Persistence Model |
| ADR-0015 | Python Code Splitting and Complexity Management Criteria |
| ADR-0016 | HTTP Bridge Auth Dependency Boundary |
| ADR-0017 | Auxiliary CLI Integration Boundary |

## Non-goals Confirmed

v0.6 does not include:

- Observation E2E runner implementation
- golden snapshot system
- mandatory Observation E2E branch protection
- semantic correctness certification
- security certification
- complete access control
- authentication / authorization implementation for Chronicle Stack
- physical deletion or lifecycle enforcement
- complete encrypted backend
- key management
- external model API calls
- GraphRAG engine
- vector database integration
- graph database integration
- Sayane runtime execution
- HTTP bridge implementation
- automatic publication

## Intentional Design Notes

### Core CI and Observation E2E

Core CI remains the primary phase gate. Observation E2E remains a separate observation surface.

A passing CI run does not prove correctness. A passing Observation E2E run, when such a runner exists, must also not be treated as correctness or security certification.

### Package Persistence

Persisted packages improve inspectability and transport provenance. They do not grant permission to use or submit data.

### Lifecycle-aware Export

Lifecycle-aware export reduces accidental re-exposure in derived outputs. It does not alter the primary record and does not satisfy deletion-law compliance by itself.

### Primary CLI Aliases

Primary aliases improve discoverability. Auxiliary scripts remain compatibility surfaces during transition.

## RDE Review

### Preserved

- local-first context asset model
- JSONL primary record surface
- derived-view separation
- advisory security boundary
- Core CI as primary phase gate
- auxiliary CLI compatibility during transition
- no false claim of complete security

### Transformed

- v0.5 contracts become more observable through documented Observation E2E scenarios
- package contracts become persisted inspectable package surfaces
- lifecycle events influence derived export behavior
- auxiliary CLI surfaces become reachable through primary CLI aliases
- future HTTP bridge auth lessons are captured before implementation

### Complemented

- release-readiness now records the non-certification boundaries explicitly
- documentation connects primary aliases with auxiliary compatibility
- lifecycle-aware export behavior is covered across major derived export formats

### Unresolved

- exact Observation E2E runner implementation
- golden snapshot strategy
- whether Observation E2E becomes required for specific release types
- canonical deprecation policy for auxiliary scripts after a future transition
- encrypted backend / key management implementation
- Sayane / CSG-RAG runtime consumption implementation

### Deviation Risks

- treating advisory metadata as enforcement
- treating lifecycle markers as deletion
- treating package persistence as permission grant or external submission
- treating primary CLI aliases as auxiliary CLI deprecation
- treating Observation E2E pass as semantic correctness or security certification
- treating HTTP bridge auth guidance as a current Chronicle Stack auth implementation
