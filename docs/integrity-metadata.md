# Chronicle Stack Integrity Metadata

Status: v0.5 preparation contract  
Related: #67, [ADR-0007](adr/0007-integrity-metadata-preparation.md)

## Purpose

Integrity metadata prepares Chronicle Stack for future drift detection, export/package verification, and hash-chain workflows.

It is not a proof system.

## Boundary

Important:

```text
integrity hash != proof
integrity metadata != signature
integrity metadata != tamper-proof storage
integrity metadata != correctness certification
```

## Helpers

v0.5 introduces deterministic helpers:

```python
canonical_json_bytes(value)
sha256_digest(value)
build_integrity_metadata(value)
verify_integrity_metadata(value, metadata)
```

They are implemented in:

```text
chronicle.security.integrity
```

## IntegrityMetadata

`IntegrityMetadata` currently contains:

| Field | Meaning |
|---|---|
| `hash` | SHA-256 digest of canonical JSON. |
| `previous_hash` | Optional previous digest for future chain workflows. |
| `signature` | Optional placeholder for future signatures. |
| `snapshot_id` | Optional snapshot/package identifier. |

## Canonicalization

Canonical JSON uses:

```text
sort_keys=True
separators=(",", ":")
ensure_ascii=False
Pydantic model_dump(mode="json", exclude_none=True)
```

Changing canonicalization is an interface-sensitive change.

## Non-goals

The v0.5 integrity metadata layer does not provide:

- digital signatures
- key management
- remote verification
- notarization
- immutable ledger
- complete tamper-proof guarantees

## Relationship to Other v0.5 Work

Integrity metadata supports future work:

- Doctor security checks.
- Security-aware export profiles.
- Controlled CSG-RAG / Sayane package manifests.
- Encrypted store snapshots.
- Audit and lifecycle consistency checks.

## RDE Review

### Preserved

- JSONL remains primary.
- Existing records may omit integrity metadata.
- No proof or signing claim is introduced.

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
