"""Tests for lifecycle event model and store."""

import json
from datetime import datetime, timezone

from chronicle.models.lifecycle import LifecycleAction, LifecycleEvent, LifecycleReasonClass, LifecycleVisibility
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.lifecycle_service import LifecycleService
from chronicle.store.lifecycle_store import LifecycleStore


def test_lifecycle_event_serializes_to_jsonl_without_none_fields():
    event = LifecycleEvent(
        lifecycle_id="lc_1",
        chronicle_id="chr_1",
        created_at=datetime(2026, 6, 14, tzinfo=timezone.utc),
        action=LifecycleAction.REDACT,
        target_id="ctx_1",
        target_kind="context",
        actor="user",
        reason_class=LifecycleReasonClass.PRIVACY,
        reason="Remove personal detail.",
        visible_detail_level=LifecycleVisibility.SUMMARY_ONLY,
    )

    data = json.loads(event.to_jsonl())

    assert data["lifecycle_id"] == "lc_1"
    assert data["action"] == "redact"
    assert data["target_id"] == "ctx_1"
    assert data["reason_class"] == "privacy"
    assert data["visible_detail_level"] == "summary_only"
    assert "replacement_ref" not in data


def test_lifecycle_store_append_and_read(tmp_path):
    store = LifecycleStore(tmp_path / "lifecycle.jsonl")
    event = LifecycleEvent(
        lifecycle_id="lc_1",
        chronicle_id="chr_1",
        created_at=datetime(2026, 6, 14, tzinfo=timezone.utc),
        action=LifecycleAction.SEAL,
        target_id="evt_1",
        target_kind="event",
        reason_class=LifecycleReasonClass.SAFETY,
    )

    store.append(event)
    loaded = store.read_all()

    assert len(loaded) == 1
    assert loaded[0].lifecycle_id == "lc_1"
    assert loaded[0].action == LifecycleAction.SEAL
    assert loaded[0].target_id == "evt_1"


def test_lifecycle_store_counts_corrupt_lines(tmp_path):
    lifecycle_file = tmp_path / "lifecycle.jsonl"
    lifecycle_file.write_text('{"bad": true}\nnot-json\n', encoding="utf-8")
    store = LifecycleStore(lifecycle_file)

    assert store.count_corrupt_lines() == 2
    assert store.read_all() == []


def test_lifecycle_service_records_to_separate_lifecycle_file(tmp_path):
    ChronicleService(tmp_path).init("Lifecycle Test")
    lifecycle = LifecycleService(tmp_path)

    event = lifecycle.record(
        action=LifecycleAction.TOMBSTONE,
        target_id="ctx_1",
        target_kind="context",
        actor="owner",
        reason_class=LifecycleReasonClass.USER_REQUEST,
        reason="User requested removal from ordinary use.",
    )

    assert event.lifecycle_id.startswith("lc_")
    assert (tmp_path / ".chronicle" / "lifecycle.jsonl").exists()
    assert len(lifecycle.list_events()) == 1
    assert ChronicleService(tmp_path).show()["event_count"] == 1
