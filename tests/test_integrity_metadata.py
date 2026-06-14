"""Tests for integrity metadata preparation helpers."""

from datetime import datetime, timezone

from chronicle.models.classification import ClassificationMetadata, ClassificationLayer, Sensitivity
from chronicle.models.context import Context, ContextScope
from chronicle.security.integrity import (
    build_integrity_metadata,
    canonical_json_bytes,
    sha256_digest,
    verify_integrity_metadata,
)


def test_canonical_json_bytes_are_order_stable():
    left = {"b": 2, "a": 1}
    right = {"a": 1, "b": 2}

    assert canonical_json_bytes(left) == canonical_json_bytes(right)
    assert canonical_json_bytes(left) == b'{"a":1,"b":2}'


def test_sha256_digest_changes_when_value_changes():
    original = {"context_id": "ctx_1", "summary": "original"}
    changed = {"context_id": "ctx_1", "summary": "changed"}

    assert sha256_digest(original) != sha256_digest(changed)


def test_build_and_verify_integrity_metadata_for_dict():
    value = {"context_id": "ctx_1", "summary": "stable"}

    metadata = build_integrity_metadata(value, previous_hash="prev", snapshot_id="snap_1")

    assert metadata.hash
    assert metadata.previous_hash == "prev"
    assert metadata.snapshot_id == "snap_1"
    assert verify_integrity_metadata(value, metadata) is True
    assert verify_integrity_metadata({"context_id": "ctx_1", "summary": "changed"}, metadata) is False


def test_build_integrity_metadata_for_pydantic_model():
    ctx = Context(
        context_id="ctx_integrity",
        title="Integrity Context",
        scope=ContextScope.TASK,
        created_at=datetime(2026, 6, 14, tzinfo=timezone.utc),
        classification=ClassificationMetadata(
            layer=ClassificationLayer.INTERNAL,
            sensitivity=Sensitivity.INTERNAL,
        ),
    )

    metadata = build_integrity_metadata(ctx)

    assert metadata.hash == sha256_digest(ctx)
    assert verify_integrity_metadata(ctx, metadata) is True


def test_empty_integrity_metadata_does_not_verify():
    value = {"context_id": "ctx_1"}
    metadata = build_integrity_metadata(value)
    metadata.hash = ""

    assert verify_integrity_metadata(value, metadata) is False
