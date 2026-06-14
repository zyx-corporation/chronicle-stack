# ADR-0010: Controlled CSG-RAG / Sayane Integration Packages

Status: Accepted  
Date: 2026-06-14  
Scope: Chronicle Stack v0.5 and later  
Related: ADR-0001, ADR-0002, ADR-0004, ADR-0005, ADR-0008, ADR-0009, `docs/controlled-integration-packages.md`

## Context

Chronicle Stack records may be used by future CSG-RAG, Sayane, review, and retrieval workflows.

However, raw records must not be handed directly to model-facing or retrieval-facing systems without explicit boundaries. v0.5 already introduced classification metadata, operation permissions, model-context dry-runs, prompt-injection boundaries, audit logs, lifecycle logs, integrity metadata, and export profiles.

A controlled integration package provides a transport contract that preserves these boundaries.

## Decision

Chronicle Stack will introduce controlled integration package contracts.

The initial v0.5 implementation provides context packages for selected Context records.

```text
chronicle-package context --purpose "Sayane review" --target local
```

This is a packaging contract only.

It is not:

- a GraphRAG engine
- a vector database
- a graph database
- a model runtime
- an automatic review judgment
- an external submission mechanism

## Package Boundary

Package records must represent content as either:

```text
chronicle_data
reference_only
```

`chronicle_data` records are wrapped with an explicit data boundary.

`reference_only` records do not include body text, and are used for Layer 4 / Restricted Secret contexts by default.

## Manifest

Every package has a manifest containing:

```text
package_id
chronicle_id
created_at
package_kind
purpose
target_environment
referenced_records
output_classification
warnings
metadata
```

## Consequences

### Positive

- Future CSG-RAG / Sayane integrations get a stable, testable package contract.
- Stored content is marked as data, not instructions.
- Layer 4 content is reference-only by default.
- Warnings travel with the package.

### Negative / Cost

- Package semantics must be governed.
- Current packages are context-only.
- No persistence or audit insertion is automatic yet.

## Non-goals

This ADR does not implement:

- GraphRAG engine
- vector DB
- graph DB
- external model runtime
- automatic review judgment
- automatic publication
- automatic audit insertion

## RDE Review

### Preserved

- JSONL remains primary.
- Original records are not mutated.
- Prompt-injection boundary remains advisory.
- Export profiles remain separate derived surfaces.

### Transformed

- Future integrations now receive a controlled package contract rather than raw records.

### Added

- IntegrationPackage models.
- IntegrationPackageService.
- `chronicle-package context` auxiliary CLI.
- Context package tests.

### Unresolved

- Review package semantics.
- Artifact package semantics.
- Audit insertion for package creation.
- Persistence of generated packages.
- Integration with actual CSG-RAG / Sayane runtimes.

### Deviation Risks

- Treating packages as permission grants.
- Treating reference-only records as safe proof of disclosure.
- Passing raw records outside the package boundary.
