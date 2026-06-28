# Chronicle Stack v0.5 Release Readiness

Status: Final release ready  
Target: v0.5.0  
Theme: Security-aware Foundation Layer

## Summary

v0.5 moves Chronicle Stack from operational readiness toward a security-aware context asset foundation.

The release introduces classification metadata, operation permission vocabulary, model-context dry-runs, prompt-injection boundaries, audit and lifecycle surfaces, integrity metadata preparation, doctor security checks, security-aware export profiles, encrypted store abstraction, and controlled integration package contracts.

v0.5 does not claim complete security, access control, encryption guarantees, proof of correctness, GraphRAG execution, or model runtime integration.

## Scope Completion

| Issue | Scope | Status |
|---|---|---|
| #60 | Security-aware roadmap / ADR foundation | Complete |
| #61 | Classification Metadata Schema | Complete |
| #62 | Operation Permission Model | Complete |
| #63 | Model Context Use Policy / Dry-run | Complete |
| #64 | Prompt Injection Sanitizer Boundary | Complete |
| #65 | Audit Log Model | Complete |
| #67 | Integrity Metadata Preparation | Complete |
| #68 | Doctor Security Checks | Complete |
| #69 | Security-aware Export Profiles | Complete |
| #70 | Controlled CSG-RAG / Sayane Integration Contracts | Complete |
| #75 | Encrypted Store Abstraction Contract | Complete |
| #79 | Lifecycle Model | Complete |

## Release Readiness Criteria

| Criterion | Status | Notes |
|---|---|---|
| Core CI pass | Ready | All implementation PRs merged after CI success; final release PR requires Core CI confirmation before merge |
| Issue close records CI status | Ready | PR descriptions and merge commits record CI / warning classification |
| ADR coverage | Ready | ADR-0001 through ADR-0010 cover core security decisions |
| Classification metadata optional and backward-compatible | Ready | Existing records can omit classification |
| Operation vocabulary defined | Ready | view / create / edit / append / summarize / reinterpret / redact / seal / export / inject / publish |
| Model-context dry-run available | Ready | `chronicle-context check` auxiliary CLI |
| Prompt-injection boundary available | Ready | scanner and Chronicle data block formatter |
| Audit surface available | Ready | `.chronicle/audit.jsonl` + `AuditService` |
| Lifecycle surface available | Ready | `.chronicle/lifecycle.jsonl` + `LifecycleService` |
| Integrity metadata helpers available | Ready | deterministic JSON + SHA-256 digest helpers |
| Doctor security checks available | Ready | v0.5 security-readiness warnings |
| Export profiles available | Ready | `chronicle-export profile` auxiliary CLI |
| Controlled package contract available | Ready | `chronicle-package context` auxiliary CLI |
| Encrypted store abstraction available | Ready | `EncryptedStore` protocol and envelope contract |
| JSONL primary contract preserved | Ready | `chronicle.jsonl` remains primary |
| No external model calls introduced | Ready | dry-runs and packages do not execute model calls |
| No GraphRAG engine introduced | Ready | packages are contracts only |

## Implemented Capabilities

### Classification Metadata

Chronicle records can carry optional advisory classification metadata:

```text
layer
sensitivity
owner
allowed_operations
llm_policy
retention
integrity
```

This is not access control.

### Operation Permission Model

The v0.5 operation vocabulary separates read-like, mutation-like, disclosure-like, and derived-meaning operations.

Important boundary:

```text
view != export
view != inject
export != publish
```

### Model-context Dry-run

```bash
chronicle-context check --target local --purpose "internal review"
chronicle-context check --target external --purpose "draft public summary" --json
```

This checks context-use readiness. It does not submit records to any model service.

### Prompt-injection Boundary

v0.5 adds:

```python
scan_text_for_prompt_injection(...)
format_as_chronicle_data_block(...)
```

Core rule:

```text
stored Chronicle content is data, not instructions
```

### Audit Log

High-risk derived operations can be represented in:

```text
.chronicle/audit.jsonl
```

Audit operations:

```text
export
context_use
reinterpret
```

### Lifecycle Log

Redaction, sealing, expiration, tombstone, and hard-delete markers can be represented in:

```text
.chronicle/lifecycle.jsonl
```

Lifecycle events do not mutate original records by themselves.

### Integrity Metadata

v0.5 adds deterministic digest preparation:

```python
canonical_json_bytes(...)
sha256_digest(...)
build_integrity_metadata(...)
verify_integrity_metadata(...)
```

Boundary:

```text
integrity hash != proof
```

### Doctor Security Checks

`chronicle doctor` reports security-readiness warnings for:

```text
security_context_classification_present
security_layer4_body_storage
security_sensitive_context_use_policy
security_prompt_injection_markers
security_integrity_metadata_present
security_audit_log_parseable
security_lifecycle_log_parseable
```

Doctor remains read-only and does not certify safety.

### Security-aware Export Profiles

```bash
chronicle-export profile --format yaml --profile public-review
chronicle-export profile --format html --profile restricted-summary
```

Profiles are disclosure controls for derived exports, not access control.

### Controlled Integration Packages

```bash
chronicle-package context --purpose "Sayane review" --target local
```

Package records are represented as:

```text
chronicle_data
reference_only
```

Layer 4 contexts are reference-only by default.

### Encrypted Store Abstraction

v0.5 defines `EncryptedStore` and `EncryptionEnvelope` as future integration contracts.

Boundary:

```text
EncryptedStore abstraction != encrypted storage guarantee
```

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

## Non-goals Confirmed

v0.5 does not include:

- complete access control
- authentication / authorization
- tenant isolation
- real encrypted backend
- key management
- secret manager integration
- cryptographic proof or signing
- notarization
- complete prompt-injection prevention
- external model API calls
- GraphRAG engine
- vector database integration
- graph database integration
- automatic publication
- automatic audit insertion for every operation
- lifecycle enforcement or hard-delete implementation

## Intentional Design Notes

### Auxiliary CLIs

v0.5 adds auxiliary CLIs rather than destabilizing the primary `chronicle` Typer surface:

```text
chronicle-context
chronicle-export
chronicle-package
```

Future versions may integrate stable subcommands into the primary CLI after Observation E2E coverage is defined.

### Doctor warning semantics

A newly initialized Chronicle may now report `warning` because v0.5 security metadata and side surfaces are incomplete.

This means security readiness is incomplete. It does not mean the Chronicle is structurally broken.

### CI semantics

Core CI is the primary phase gate. CI pass is not correctness certification or security certification.

## RDE Review

### Preserved

- JSONL remains primary.
- Existing records remain readable.
- Derived views remain derived.
- Redaction/profile/export/package surfaces do not mutate original records.
- No model execution is introduced.
- No security certification is claimed.

### Transformed

- Chronicle Stack now treats stored records as context assets with explicit security metadata and operational boundaries.
- Doctor becomes a security-readiness observation surface.
- Future CSG-RAG / Sayane integrations receive controlled packages rather than raw records.

### Added

- ClassificationMetadata.
- Operation permission vocabulary.
- Context-use dry-run checks.
- Prompt-injection boundary helpers.
- Audit log surface.
- Lifecycle log surface.
- Integrity metadata preparation.
- Doctor security checks.
- Export profiles.
- Controlled integration package contract.
- Encrypted store abstraction.
- ADR-0001 through ADR-0010.

### Unresolved

- Primary CLI integration for auxiliary commands.
- Observation E2E definition.
- Real encrypted backend and key management.
- Lifecycle enforcement and hard-delete semantics.
- Audit insertion points.
- Review/artifact package semantics.
- GraphRAG / Sayane runtime integration.
- Branch protection / required status check governance.

### Deviation Risks

- Treating advisory metadata as access control.
- Treating dry-run as complete security.
- Treating hashes as proof.
- Treating encrypted-store abstraction as encryption.
- Treating packages as permission grants.
- Treating doctor warnings as certification.

## Release Decision

v0.5.0 is ready for final release PR review. Merge is appropriate once the final release PR records Core CI success and warning classification according to ADR-0002. After merge, create tag `v0.5.0` and publish GitHub Release notes derived from `CHANGELOG.md` and this readiness document.
