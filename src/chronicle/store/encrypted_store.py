"""Encrypted store abstraction and envelope contract.

This module defines interfaces and metadata contracts only. It does not
implement encryption, key management, or a concrete secure backend.
"""

from datetime import datetime
from enum import StrEnum
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, Field


class EncryptedStoreCapability(StrEnum):
    """Capability advertised by an encrypted store implementation."""

    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    LIST = "list"
    ROTATE = "rotate"


class EncryptionEnvelope(BaseModel):
    """Metadata envelope for encrypted bytes.

    The ciphertext field is intentionally bytes. Concrete backends may choose
    how to serialize it, but JSON-facing exports should encode bytes explicitly.
    """

    schema_version: str = "0.5"
    store_id: str = ""
    object_id: str
    key_id: str = ""
    algorithm: str = ""
    nonce: bytes = b""
    aad: bytes = b""
    ciphertext: bytes
    tag: bytes = b""
    created_at: datetime | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class EncryptedStoreWriteResult(BaseModel):
    """Result returned by write operations."""

    object_id: str
    envelope: EncryptionEnvelope


@runtime_checkable
class EncryptedStore(Protocol):
    """Protocol for encrypted byte storage backends.

    Implementations must not expose plaintext from `read_envelope`. Plaintext
    conversion belongs to an explicit higher-level decrypt operation owned by a
    concrete backend or adapter, not by Chronicle core.
    """

    store_id: str
    capabilities: set[EncryptedStoreCapability]

    def write_envelope(self, object_id: str, envelope: EncryptionEnvelope) -> EncryptedStoreWriteResult:
        """Persist an already encrypted envelope."""
        ...

    def read_envelope(self, object_id: str) -> EncryptionEnvelope:
        """Read an encrypted envelope without decrypting it."""
        ...

    def exists(self, object_id: str) -> bool:
        """Return whether an encrypted object exists."""
        ...

    def delete_envelope(self, object_id: str) -> bool:
        """Delete an encrypted envelope if supported.

        Returns True when an object was removed, False when it did not exist.
        """
        ...

    def list_object_ids(self) -> list[str]:
        """List stored encrypted object identifiers if supported."""
        ...
