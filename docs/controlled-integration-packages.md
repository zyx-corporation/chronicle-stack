# Chronicle Stack Controlled Integration Packages

Status: v0.5 contract  
Related: #70, [ADR-0010](adr/0010-controlled-integration-packages.md)

## Purpose

Controlled integration packages define how Chronicle Stack records may be prepared for future CSG-RAG, Sayane, review, and retrieval workflows.

The package is a transport contract. It does not execute models or retrieval engines.

## Boundary

Important:

```text
integration package != permission grant
integration package != model execution
integration package != GraphRAG engine
integration package != publication approval
integration package does not mutate primary records
```

## CLI

v0.5 exposes context packages through an auxiliary command:

```bash
chronicle-package context --purpose "Sayane review" --target local
chronicle-package context --purpose "External review" --target external --context ctx_...
```

## Package Manifest

Every package includes a manifest:

| Field | Meaning |
|---|---|
| `package_id` | Package identifier. |
| `chronicle_id` | Chronicle ID. |
| `created_at` | Package creation timestamp. |
| `package_kind` | context_package / review_package. |
| `purpose` | Human supplied package purpose. |
| `target_environment` | local / external / unknown. |
| `referenced_records` | Record IDs included or referenced. |
| `output_classification` | Highest derived classification label. |
| `warnings` | Package-level warnings. |
| `metadata` | String metadata map. |

## Record Boundary

Records use one of two content boundaries.

```text
chronicle_data:
  Record body is included, wrapped as stored data, not instructions.

reference_only:
  Record body is not included. Used for Layer 4 / Restricted Secret contexts by default.
```

## Warnings

Warnings can include:

```text
unclassified_context
layer4_reference_only
external_sensitive_context_not_allowed
prompt_marker:<pattern_id>
```

Warnings are advisory and must be interpreted by downstream workflows.

## Non-goals

The v0.5 package contract does not provide:

- GraphRAG engine
- vector DB
- graph DB
- external model runtime
- automatic review judgment
- automatic audit insertion
- package persistence

## RDE Review

### Preserved

- JSONL remains primary.
- Original records are not mutated.
- Model-context dry-run remains separate.
- Export profiles remain separate derived surfaces.

### Transformed

- Future integrations receive controlled packages rather than raw records.

### Added

- IntegrationPackage models.
- IntegrationPackageService.
- `chronicle-package context` auxiliary CLI.
- Context package tests.

### Unresolved

- Review package semantics.
- Artifact package semantics.
- Audit insertion.
- Package persistence.
- Actual CSG-RAG / Sayane runtime integration.

### Deviation Risks

- Treating packages as permission grants.
- Treating reference-only records as proof of safety.
- Passing raw records outside the package boundary.
