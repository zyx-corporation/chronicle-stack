"""Integrity metadata preparation helpers.

These helpers provide deterministic serialization and digest preparation.
They do not provide tamper-proof storage, signatures, or remote verification.
"""

import hashlib
import json
from typing import Any

from pydantic import BaseModel

from chronicle.models.classification import IntegrityMetadata


def canonical_json_bytes(value: Any) -> bytes:
    """Return deterministic UTF-8 JSON bytes for supported values.

    Pydantic models are dumped in JSON mode before canonical serialization.
    """
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json", exclude_none=True)
    text = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return text.encode("utf-8")


def sha256_digest(value: Any) -> str:
    """Return a SHA-256 hex digest for a canonical JSON representation."""
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def build_integrity_metadata(
    value: Any,
    *,
    previous_hash: str = "",
    snapshot_id: str = "",
    signature: str = "",
) -> IntegrityMetadata:
    """Build optional integrity metadata for future change-detection workflows.

    This does not sign the value and does not make the value tamper-proof.
    """
    return IntegrityMetadata(
        hash=sha256_digest(value),
        previous_hash=previous_hash,
        signature=signature,
        snapshot_id=snapshot_id,
    )


def verify_integrity_metadata(value: Any, metadata: IntegrityMetadata) -> bool:
    """Return whether the value currently matches the stored digest."""
    if not metadata.hash:
        return False
    return sha256_digest(value) == metadata.hash
