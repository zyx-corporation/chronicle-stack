# Chronicle Stack Encrypted Store Contract

Status: v0.5 interface contract  
Related: #75, [ADR-0003](adr/0003-encrypted-store-abstraction.md)

## Purpose

This document defines the interface contract for future encrypted storage backends in Chronicle Stack.

It does not define a concrete encryption implementation.

The contract exists to keep Chronicle core backend-agnostic while preparing for protected storage in future releases.

## Scope

The v0.5 scope is:

```text
- interface boundary
- envelope metadata
- contract tests
- documentation
```

The v0.5 scope is not:

```text
- real encryption
- key management
- secret manager integration
- encrypted JSONL migration
- encrypted indexes
- confidentiality guarantee
```

## Interface

The Python protocol is `chronicle.store.encrypted_store.EncryptedStore`.

Required operations:

```python
write_envelope(object_id, envelope)
read_envelope(object_id)
exists(object_id)
delete_envelope(object_id)
list_object_ids()
```

The interface operates on `EncryptionEnvelope`, not plaintext.

## Envelope

`EncryptionEnvelope` contains:

| Field | Meaning |
|---|---|
| `schema_version` | Envelope schema version. |
| `store_id` | Backend/store identifier. |
| `object_id` | Object identifier. |
| `key_id` | Key identifier or key reference. |
| `algorithm` | Algorithm identifier. |
| `nonce` | Backend-specific nonce bytes. |
| `aad` | Additional authenticated data bytes. |
| `ciphertext` | Encrypted payload bytes. |
| `tag` | Backend-specific tag bytes. |
| `created_at` | Envelope creation timestamp. |
| `metadata` | String metadata map. |

The envelope may contain sensitive metadata. Concrete backends must review metadata leakage risk.

## Responsibilities

### EncryptedStore implementer

An implementation is responsible for:

- persisting encrypted envelopes
- returning encrypted envelopes without decrypting them implicitly
- declaring capabilities
- preserving object identifiers consistently
- handling backend-specific errors safely

### Chronicle core

Chronicle core is responsible for:

- depending only on the interface contract
- not assuming a specific algorithm
- not assuming a key-management design
- not treating envelope presence as confidentiality proof
- keeping JSONL primary unless a future ADR changes that

## Capabilities

Implementations advertise capabilities:

```text
read
write
delete
list
rotate
```

Capabilities are descriptive. A caller must check whether a backend supports an operation before depending on it.

## Security Boundary

Important:

```text
EncryptedStore abstraction != encrypted storage guarantee
EncryptionEnvelope != confidentiality proof
key_id != key material
metadata != safe to disclose by default
```

The abstraction is a contract boundary. Actual security depends on the concrete backend, key handling, operational controls, and threat model.

## Contract Testing

v0.5 includes fake in-memory contract tests.

The fake implementation proves:

- the protocol can be implemented
- encrypted envelopes can be round-tripped
- plaintext is not part of the envelope contract
- delete/list semantics are testable

It does not prove encryption.

## RDE Review

### Preserved

- JSONL remains primary.
- Existing stores remain unchanged.
- No encryption guarantee is claimed.

### Transformed

- Encrypted storage becomes an explicit future integration surface.

### Added

- EncryptedStore interface contract.
- EncryptionEnvelope metadata contract.
- Capability vocabulary.
- Contract testing boundary.

### Unresolved

- Concrete backend.
- Key management.
- Key rotation.
- Envelope canonical serialization.
- Metadata leakage policy.
- Migration strategy.

### Deviation Risks

- Treating abstraction as encryption.
- Treating key identifiers as secrets.
- Leaking sensitive context through envelope metadata.
- Introducing a concrete backend before lifecycle policies are stable.
