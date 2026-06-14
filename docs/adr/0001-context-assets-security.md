# ADR-0001: Treat Chronicle Records as Context Assets

Status: Accepted  
Date: 2026-06-14  
Scope: Chronicle Stack v0.5 and later  
Related: `docs/roadmap-v0.5.md`, `docs/security-policy-v0.1.md` (future)

## Context

Chronicle Stack does not merely store finished documents.

It stores the provenance of thought and work:

- originating questions
- decision history
- rejected alternatives
- objections
- uncertainty
- meaning changes
- RDE records
- reinterpretation history
- organizational learning traces

Therefore, Chronicle Stack records can reveal more than ordinary knowledge-base documents. They can reveal judgment patterns, weak points, internal strategy, personal context, and the time axis of reasoning.

The security policy draft frames this as a shift from protecting information assets to protecting context assets.

## Decision

Chronicle Stack will treat Chronicle records as **context assets**, not merely information assets.

This means security requirements must cover not only confidentiality, integrity, and availability, but also:

- provenance preservation
- chronology preservation
- reinterpretation boundaries
- context sovereignty
- layer-aware disclosure
- LLM injection control
- auditability of export / inject / reinterpret operations

## Consequences

### Security model

Chronicle Stack must distinguish at least the following dimensions:

- visibility
- classification layer
- allowed operations
- LLM policy
- retention policy
- integrity metadata

Existing `VisibilityHint` is not enough for v0.5 security work.

### Operation boundaries

The following operations must not be conflated:

- view
- summarize
- reinterpret
- export
- inject
- publish

In particular, "readable by a person or tool" does not mean "safe to inject into an external LLM".

### LLM boundary

LLM-facing workflows must treat Chronicle records as data, not instructions.

Stored records may contain prompt injection attempts, classification downgrade attempts, or malicious instructions aimed at downstream agents.

### Release planning

v0.5 must prioritize security-aware composition before deeper external integration.

This changes the v0.5 theme from:

```text
Composition and Integration Layer
```

to:

```text
Security-aware Composition and Integration Layer
```

## Non-goals

This ADR does not implement:

- full access control
- authentication
- encryption
- tenant isolation
- cryptographic signing
- secret management
- GraphRAG runtime
- external LLM gateway

It establishes the architectural direction for those future decisions.

## Required follow-up ADRs

The following ADRs should be created before or during v0.5 implementation:

- classification metadata schema
- operation permission model
- LLM injection policy
- prompt-injection sanitizer boundary
- audit log model
- redaction / seal / tombstone lifecycle
- integrity metadata and hash-chain strategy

## RDE Review

### Preserved

- JSONL remains primary.
- Derived views remain derived.
- Visibility hints remain advisory.
- Redaction-aware export is not access control.
- Graph inspection is not GraphRAG.

### Transformed

- Chronicle Stack security framing changes from document security to context-asset protection.
- v0.5 planning becomes security-first rather than integration-first.

### Added

- Context asset concept.
- Security-aware composition requirement.
- Explicit separation between read/export/inject/reinterpret/publish.

### Unresolved

- Exact metadata schema is not defined here.
- Exact permission enforcement model is not defined here.
- Existing records migration strategy is not defined here.

### Deviation Risks

- Treating classification metadata as sufficient enforcement.
- Treating redaction as access control.
- Allowing external integration before LLM injection policy exists.
- Preserving all context without supporting redact / seal / delete workflows.
