"""Contract tests for encrypted store abstraction."""

from datetime import datetime, timezone

import pytest

from chronicle.store.encrypted_store import (
    EncryptedStore,
    EncryptedStoreCapability,
    EncryptedStoreWriteResult,
    EncryptionEnvelope,
)


class FakeEncryptedStore:
    """In-memory fake used only to verify the protocol contract."""

    store_id = "fake-memory"
    capabilities = {
        EncryptedStoreCapability.READ,
        EncryptedStoreCapability.WRITE,
        EncryptedStoreCapability.DELETE,
        EncryptedStoreCapability.LIST,
    }

    def __init__(self) -> None:
        self._objects: dict[str, EncryptionEnvelope] = {}

    def write_envelope(self, object_id: str, envelope: EncryptionEnvelope) -> EncryptedStoreWriteResult:
        self._objects[object_id] = envelope
        return EncryptedStoreWriteResult(object_id=object_id, envelope=envelope)

    def read_envelope(self, object_id: str) -> EncryptionEnvelope:
        return self._objects[object_id]

    def exists(self, object_id: str) -> bool:
        return object_id in self._objects

    def delete_envelope(self, object_id: str) -> bool:
        if object_id not in self._objects:
            return False
        del self._objects[object_id]
        return True

    def list_object_ids(self) -> list[str]:
        return sorted(self._objects)


def test_fake_encrypted_store_satisfies_protocol():
    store = FakeEncryptedStore()

    assert isinstance(store, EncryptedStore)


def test_envelope_round_trip_without_plaintext_contract():
    store = FakeEncryptedStore()
    envelope = EncryptionEnvelope(
        store_id=store.store_id,
        object_id="obj_1",
        key_id="key_1",
        algorithm="test-only",
        nonce=b"nonce",
        aad=b"aad",
        ciphertext=b"encrypted-bytes",
        tag=b"tag",
        created_at=datetime(2026, 6, 14, tzinfo=timezone.utc),
        metadata={"classification_layer": "3"},
    )

    result = store.write_envelope("obj_1", envelope)
    loaded = store.read_envelope("obj_1")

    assert result.object_id == "obj_1"
    assert loaded.ciphertext == b"encrypted-bytes"
    assert not hasattr(loaded, "plaintext")
    assert loaded.metadata["classification_layer"] == "3"


def test_delete_and_list_contract():
    store = FakeEncryptedStore()
    envelope = EncryptionEnvelope(object_id="obj_1", ciphertext=b"bytes")

    store.write_envelope("obj_1", envelope)

    assert store.exists("obj_1") is True
    assert store.list_object_ids() == ["obj_1"]
    assert store.delete_envelope("obj_1") is True
    assert store.delete_envelope("obj_1") is False
    assert store.exists("obj_1") is False


def test_envelope_requires_object_id_and_ciphertext():
    with pytest.raises(ValueError):
        EncryptionEnvelope(object_id="obj_missing_ciphertext")
