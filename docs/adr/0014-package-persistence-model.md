# ADR-0014: Package Persistence Model

Status: Accepted  
Date: 2026-06-15  
Scope: Chronicle Stack v0.6-alpha and later  
Related: ADR-0010, ADR-0012, ADR-0013, `docs/package-persistence-model.md`, #87, #91

## Context

ADR-0010 introduced controlled integration packages as transport contracts for future CSG-RAG, Sayane, review, and retrieval workflows.

The v0.5 package contract intentionally excluded package persistence.

Chronicle Stack now needs a policy for whether generated packages should become persisted derived surfaces, and if so, what surface and metadata should be used.

This decision must preserve the boundary that packages are not permission grants, external submissions, model execution, or GraphRAG runtime behavior.

## Decision

Chronicle Stack will define package persistence as an optional derived package surface.

The preferred persisted surface is:

```text
.chronicle/packages/<package_id>.json
.chronicle/packages/index.jsonl
```

Package files contain generated package payloads and manifests.

The package index contains lightweight discovery metadata.

Both surfaces are derived from primary records and package-generation policy.

Package persistence must not mutate `.chronicle/chronicle.jsonl`.

## Boundary

```text
package persistence != permission grant
package persistence != external submission
package persistence != publication approval
package persistence != model execution
package persistence != GraphRAG runtime
package persistence != confidentiality guarantee
```

Persisting a package records that a package was generated and stored locally. It does not mean the package was sent anywhere or approved for use.

## Package metadata

Persisted packages should include enough information to reconstruct why a package contained, omitted, or referenced records.

Candidate metadata:

```text
package_id
chronicle_id
package_type
schema_version
created_at
actor
purpose
target_environment
source_context_ids
source_artifact_ids
source_event_ids
policy_snapshot
classification_summary
lifecycle_summary
body_boundary_summary
integrity
warnings
entries
metadata
```

## Package types

Initial type:

```text
context_package
```

Future types may include:

```text
review_package
artifact_package
release_package
```

The persistence model should not be context-only in principle.

## Interactions

### Classification

Layer 4 / Restricted Secret records should default to `reference_only`.

Persisted package metadata should include classification summaries without copying hidden content unnecessarily.

### Lifecycle

Package persistence should respect lifecycle-aware export design where applicable.

Tombstoned, hard-delete-marked, sealed, expired, or redacted records should be handled conservatively and summarized in metadata.

### Audit

Package generation and package persistence are audit candidates under ADR-0012.

External submission, if ever introduced, must be a separate explicit audited operation.

### Integrity

Persisted packages should include integrity metadata for drift detection.

Integrity metadata is not signing, notarization, or proof.

## Failure semantics

Initial persistence failure mode:

```text
fail-open with warning
```

Meaning:

- package generation may complete even if persistence fails
- the warning must be surfaced
- warning classification must be recorded when relevant

Fail-closed behavior may be defined later for workflows that require persisted provenance.

## Consequences

### Positive

- Generated packages become reconstructable.
- Future Sayane / CSG-RAG workflows can refer to package ids.
- Package discovery can be supported without scanning all raw records.
- Classification, lifecycle, audit, and integrity summaries can travel with packages.

### Negative / Cost

- Persisted packages create another derived surface to maintain.
- Package content may duplicate sensitive material if policies are wrong.
- Index rebuild and pruning semantics must be designed later.
- Persistence failure handling must be visible.

## Non-goals

This ADR does not implement:

- package persistence code
- package listing CLI
- external model calls
- GraphRAG runtime
- publication workflow
- cryptographic signing
- encrypted package storage
- legal compliance automation

## RDE Review

### Preserved

- Source records remain primary.
- Packages remain derived transport contracts.
- Package persistence does not imply permission or consent.
- Package persistence does not imply external submission.
- Restricted content defaults to reference-only.

### Transformed

- Ephemeral package generation becomes a reconstructable package surface.
- Package ids can become stable references for future integrations.

### Added

- Package file surface.
- Package index surface.
- Metadata expectations.
- Classification/lifecycle/audit/integrity interaction policy.
- Fail-open-with-warning default.

### Unresolved

- Exact schema implementation.
- CLI option names.
- Whether persistence becomes default.
- Index rebuild semantics.
- Package pruning and lifecycle management.
- Encrypted package storage.

### Deviation Risks

- Treating package persistence as consent.
- Treating package persistence as external submission.
- Leaking body content through persisted package files.
- Storing Layer 4 content when reference-only was intended.
- Letting package semantics drift from export, lifecycle, and classification policy.
