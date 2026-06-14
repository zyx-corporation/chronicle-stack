# ADR-0003: Encrypted Store Abstraction Boundary

Status: Accepted  
Date: 2026-06-14  
Scope: Chronicle Stack v0.5 and later  
Related: ADR-0001, ADR-0002, `docs/encrypted-store-contract.md`

## Context

Chronicle Stack records may include high-value context assets. Some deployments will eventually require encrypted storage, key separation, external secret managers, or protected storage backends.

However, Chronicle Stack core currently uses JSONL and filesystem-backed derived indexes. Introducing a concrete encryption backend too early would couple the core system to a specific storage implementation and risk false security claims.

Therefore v0.5 defines an abstraction boundary first.

## Decision

Chronicle Stack will define an `EncryptedStore` abstraction and an `EncryptionEnvelope` metadata contract before introducing any concrete encrypted storage backend.

The abstraction is a boundary for future integrations. It does not change the current JSONL primary store.

```text
Current primary record:
  .chronicle/chronicle.jsonl

Encrypted store abstraction:
  future protected object storage boundary
```

## Contract

The encrypted store contract operates on encrypted envelopes, not plaintext.

Core contract operations:

```text
write_envelope(object_id, envelope)
read_envelope(object_id)
exists(object_id)
delete_envelope(object_id)
list_object_ids()
```

The `EncryptionEnvelope` carries metadata such as:

```text
schema_version
store_id
object_id
key_id
algorithm
nonce
aad
ciphertext
tag
created_at
metadata
```

## Boundary Rules

Chronicle core must not assume:

- which encryption algorithm is used
- how keys are managed
- where keys are stored
- whether a backend is local, remote, hardware-backed, or secret-manager-backed
- that an envelope proves confidentiality by itself

Encrypted store implementations must not expose plaintext through `read_envelope`.

Plaintext conversion must be an explicit operation owned by a concrete backend or adapter.

## Non-goals

This ADR does not implement:

- concrete encryption
- key management
- key rotation
- secret manager integration
- encrypted JSONL migration
- encrypted indexes
- access control
- confidentiality certification

## Consequences

### Positive

- Chronicle core remains backend-agnostic.
- Future encrypted stores have a stable interface target.
- Documentation can distinguish abstraction from protection guarantees.
- Contract tests can verify interface behavior without depending on a cryptographic backend.

### Negative / Cost

- No real confidentiality improvement exists until a concrete backend is implemented.
- Developers must avoid treating the abstraction as encryption.
- Metadata leakage must be considered when a concrete backend is designed.

## RDE Review

### Preserved

- JSONL remains primary.
- Existing filesystem store remains unchanged.
- No encryption guarantee is claimed.

### Transformed

- Encrypted storage becomes an explicit architecture boundary.

### Added

- `EncryptedStore` abstraction.
- `EncryptionEnvelope` metadata contract.
- Contract-testable storage boundary.

### Unresolved

- Concrete backend selection.
- Key management.
- Key rotation.
- Migration strategy.
- Doctor checks for encrypted storage configuration.

### Deviation Risks

- Treating abstraction as real encryption.
- Storing sensitive metadata in envelope fields.
- Coupling Chronicle core to a specific backend.
- Moving to encrypted storage before redact / seal / tombstone policy is clear.
