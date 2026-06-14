# ADR-0007: Integrity Metadata Preparation

Status: Accepted  
Date: 2026-06-14  
Scope: Chronicle Stack v0.5 and later  
Related: ADR-0001, ADR-0002, ADR-0003, `docs/integrity-metadata.md`

## Context

Chronicle Stack records are context assets. Future workflows need ways to detect accidental drift, serialization changes, unexpected mutation, and export/package mismatch.

However, v0.5 does not implement cryptographic signing, remote verification, notarization, or tamper-proof storage.

Therefore Chronicle Stack needs an integrity metadata preparation layer, not a proof layer.

## Decision

Chronicle Stack will provide deterministic canonical JSON helpers and SHA-256 digest helpers for optional integrity metadata.

This prepares future hash-chain, doctor, export, and package verification workflows.

It does not prove that data is correct, complete, authentic, or tamper-proof.

## Boundary Rule

```text
integrity hash != proof
integrity metadata != signature
integrity metadata != tamper-proof storage
integrity metadata != correctness certification
```

## Implementation Direction

v0.5 introduces:

```python
canonical_json_bytes(...)
sha256_digest(...)
build_integrity_metadata(...)
verify_integrity_metadata(...)
```

These helpers operate on dictionaries and Pydantic models.

## Non-goals

This ADR does not implement:

- digital signatures
- key management
- remote verification
- immutable ledger
- notarization
- Git history rewriting
- complete tamper-proof guarantees

## Consequences

### Positive

- Future doctor checks can compare stored and computed digests.
- Export/package workflows can include stable digest metadata.
- Hash-chain preparation can be built without committing to a backend.

### Negative / Cost

- Users may overestimate the meaning of hashes.
- Canonicalization must remain stable.
- Metadata can become stale if records are rewritten without lifecycle/audit events.

## RDE Review

### Preserved

- JSONL remains primary.
- No signing or proof claim is introduced.
- Existing records may omit integrity metadata.

### Transformed

- Chronicle Stack gains deterministic digest preparation.

### Added

- Canonical JSON helper.
- SHA-256 digest helper.
- IntegrityMetadata build/verify helper.

### Unresolved

- Hash-chain strategy.
- Export manifest integration.
- Doctor integrity checks.
- Signature/key management.

### Deviation Risks

- Treating hashes as proof of correctness.
- Treating metadata as tamper-proof.
- Breaking canonicalization compatibility.
