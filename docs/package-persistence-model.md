# Package Persistence Model

Status: Draft for v0.6-alpha  
Related: ADR-0010, ADR-0012, ADR-0013, ADR-0014, #87, #91

## Purpose

This document defines how Chronicle Stack may persist controlled integration packages after generation.

v0.5 introduced controlled integration packages as transport contracts for future CSG-RAG, Sayane, review, and retrieval workflows. v0.6-alpha defines whether generated packages should become reconstructable derived surfaces.

The central boundary remains:

```text
package persistence != permission grant
package persistence != external submission
package persistence != publication approval
package persistence != model execution
package persistence != GraphRAG runtime
```

## Surface decision

The recommended persisted surface is:

```text
.chronicle/packages/<package_id>.json
.chronicle/packages/index.jsonl
```

Rationale:

- individual package files keep generated package payloads inspectable
- an index keeps package discovery cheap
- packages remain separate from the primary record surface
- package payloads can later be pruned, sealed, or regenerated without mutating source records
- different package types can share one package directory

Alternative considered:

```text
.chronicle/package.jsonl
```

This is simpler, but it risks creating very large JSONL records and makes individual package inspection, replacement, or pruning harder.

## Surface roles

### Package file

```text
.chronicle/packages/<package_id>.json
```

Contains the generated package manifest and package entries.

It is a derived package artifact, not a primary Chronicle record.

### Package index

```text
.chronicle/packages/index.jsonl
```

Contains lightweight package index entries.

Candidate fields:

```text
package_id
package_type
created_at
purpose
target_environment
package_path
referenced_records
output_classification
warnings
integrity_digest
metadata
```

The index should be rebuildable from package files if possible.

## Package metadata

A persisted package should include:

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

## Package entries

Each package entry should preserve the v0.5 record boundary vocabulary:

```text
chronicle_data
reference_only
```

### chronicle_data

The record body is included, wrapped as stored data rather than instructions.

This is a data boundary, not prompt-injection immunity.

### reference_only

The record body is omitted.

This is the default for Layer 4 / Restricted Secret contexts and other records where body inclusion is not appropriate.

Reference-only does not prove safety; it only describes the package boundary.

## Package types

Initial type:

```text
context_package
```

Future types:

```text
review_package
artifact_package
release_package
```

The persistence model should not overfit to context-only packages.

## Policy snapshot

Persisted packages should include enough policy information to reconstruct why records were included, excluded, or reference-only.

Candidate fields:

```text
target_environment
purpose
export_profile_if_any
lifecycle_policy_if_any
classification_policy
llm_policy_summary
prompt_injection_scan_summary
```

Policy snapshots are explanatory metadata, not proof of correct policy application.

## Classification interaction

Persisted packages should preserve classification summaries.

Candidate metadata:

```text
highest_layer
highest_sensitivity
unclassified_count
restricted_count
layer4_count
reference_only_count
body_included_count
```

Layer 4 / Restricted Secret records should default to `reference_only`.

## Lifecycle interaction

Package persistence should respect lifecycle-aware export design where applicable.

Candidate behavior:

- tombstoned and hard-delete-marked bodies are omitted by default
- sealed bodies require explicit override
- expired records produce warnings or exclusion depending on target and policy
- redacted replacements are preferred when available

Lifecycle decisions should be summarized in package metadata without copying hidden content.

## Audit interaction

Package generation and package persistence are audit candidates under ADR-0012.

Candidate audit events:

```text
package_generate
package_persist
package_read
package_export_external
```

Initial recommendation:

- package generation should become auditable once package persistence is implemented
- package external submission, if ever introduced, must be a separate explicit audited operation

Package persistence itself does not imply user consent or external transmission.

## Integrity interaction

Persisted package files should include integrity metadata.

Candidate integrity data:

```text
canonical package digest
source record digests where available
policy snapshot digest
package schema version
```

Integrity metadata is drift detection, not proof or signing.

## Failure semantics

Initial persistence failure mode:

```text
fail-open with warning
```

Meaning:

- package generation may succeed even if persistence fails
- caller must receive a visible warning
- warning must be classifiable as blocking, tracked separately, or informational

Fail-closed behavior may later be defined for operations that require persisted provenance.

## CLI implications

Future CLI candidates:

```bash
chronicle-package context --purpose "Sayane review" --target local --persist
chronicle-package list
chronicle-package show <package_id>
chronicle-package verify <package_id>
```

These are design candidates, not implemented behavior in this document.

Existing non-persistent package generation should remain available during transition.

## Non-goals

Package persistence does not provide:

- permission grant
- external submission
- model execution
- GraphRAG runtime
- publication approval
- complete prompt-injection safety
- cryptographic signing
- confidentiality guarantee
- legal compliance automation

## RDE review frame

### Preserved

- Source records remain primary.
- Packages remain derived transport contracts.
- Package persistence does not imply permission grant.
- Package persistence does not imply external submission.
- Layer 4 / Restricted Secret records default to reference-only.

### Transformed

- Ephemeral package generation becomes reconstructable derived evidence.
- Future Sayane / CSG-RAG workflows can reference package ids rather than raw records.

### Added

- Package persistence surface.
- Package index concept.
- Package metadata expectations.
- Classification, lifecycle, audit, and integrity interaction design.

### Unresolved

- Exact schema classes.
- Exact CLI option names.
- Whether persistence should be default or explicit.
- Rebuild semantics for package index.
- Package pruning / lifecycle management.
- Interaction with encrypted storage backend.

### Deviation risks

- Treating package persistence as consent.
- Treating package persistence as publication.
- Leaking body content in persisted packages.
- Storing Layer 4 content where reference-only was intended.
- Creating package formats that drift from export/profile/lifecycle semantics.
