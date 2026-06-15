"""Tests for lifecycle-aware behavior in derived YAML exports."""

from datetime import datetime, timezone

import yaml

from chronicle.exporters.yaml_exporter import YamlExporter
from chronicle.models.context import Context, ContextScope
from chronicle.models.event import Actor, ChronicleEvent, EventType
from chronicle.models.lifecycle import LifecycleAction, LifecycleReasonClass
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.lifecycle_service import LifecycleService


def _append_context(root, context: Context) -> None:
    service = ChronicleService(root)
    metadata = service.load_metadata()
    event = ChronicleEvent(
        event_id=f"evt_{context.context_id}",
        chronicle_id=metadata.chronicle_id,
        timestamp=datetime(2026, 6, 15, tzinfo=timezone.utc),
        event_type=EventType.CONTEXT_ADDED,
        actor=Actor.USER,
        summary=f"Add {context.title}",
        payload={"context": context.model_dump(mode="json")},
    )
    service.append_event(event)
    service.rebuild_indexes()


def test_yaml_export_excludes_tombstoned_contexts_and_referencing_events(tmp_path):
    ChronicleService(tmp_path).init("Lifecycle YAML Test")
    _append_context(
        tmp_path,
        Context(
            context_id="ctx_active_yaml",
            title="Active YAML Context",
            summary="Active body remains visible",
            scope=ContextScope.TASK,
            created_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
        ),
    )
    _append_context(
        tmp_path,
        Context(
            context_id="ctx_tombstone_yaml",
            title="Tombstoned YAML Context",
            summary="Tombstoned body should not be exported",
            scope=ContextScope.TASK,
            created_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
        ),
    )
    LifecycleService(tmp_path).record(
        action=LifecycleAction.TOMBSTONE,
        target_id="ctx_tombstone_yaml",
        target_kind="context",
        actor="test",
        reason_class=LifecycleReasonClass.PRIVACY,
        reason="test tombstone",
    )

    content = YamlExporter(tmp_path).export()
    payload = yaml.safe_load(content)

    assert "ctx_active_yaml" in payload["contexts"]
    assert "ctx_tombstone_yaml" not in payload["contexts"]
    assert "Tombstoned YAML Context" not in content
    assert "Tombstoned body should not be exported" not in content
    assert "lifecycle_tombstoned_records_excluded" in payload["export_manifest"]["warnings"]
    assert "lifecycle_tombstoned_events_excluded" in payload["export_manifest"]["warnings"]
    assert payload["export_manifest"]["metadata"]["excluded_lifecycle_tombstone_count"] == "1"
    assert payload["export_manifest"]["metadata"]["excluded_lifecycle_event_count"] == "1"


def test_yaml_export_marks_sealed_contexts_without_excluding(tmp_path):
    ChronicleService(tmp_path).init("Lifecycle YAML Seal Test")
    _append_context(
        tmp_path,
        Context(
            context_id="ctx_sealed_yaml",
            title="Sealed YAML Context",
            summary="Sealed body remains advisory",
            scope=ContextScope.TASK,
            created_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
        ),
    )
    LifecycleService(tmp_path).record(
        action=LifecycleAction.SEAL,
        target_id="ctx_sealed_yaml",
        target_kind="context",
        actor="test",
        reason_class=LifecycleReasonClass.RETENTION,
        reason="test seal",
    )

    payload = yaml.safe_load(YamlExporter(tmp_path).export())

    assert "ctx_sealed_yaml" in payload["contexts"]
    assert payload["contexts"]["ctx_sealed_yaml"]["warnings"] == ["lifecycle_sealed_record"]
    assert "lifecycle_sealed_record" in payload["export_manifest"]["warnings"]
    assert payload["export_manifest"]["metadata"]["sealed_lifecycle_count"] == "1"


def test_yaml_lifecycle_export_does_not_mutate_primary_jsonl(tmp_path):
    ChronicleService(tmp_path).init("Lifecycle YAML Mutation Test")
    _append_context(
        tmp_path,
        Context(
            context_id="ctx_jsonl_yaml",
            title="JSONL YAML Context",
            summary="Primary JSONL must remain unchanged",
            scope=ContextScope.TASK,
            created_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
        ),
    )
    LifecycleService(tmp_path).record(
        action=LifecycleAction.HARD_DELETE,
        target_id="ctx_jsonl_yaml",
        target_kind="context",
        actor="test",
        reason_class=LifecycleReasonClass.USER_REQUEST,
        reason="marker only",
    )
    events_file = tmp_path / ".chronicle" / "chronicle.jsonl"
    before = events_file.read_text(encoding="utf-8")

    YamlExporter(tmp_path).export()

    after = events_file.read_text(encoding="utf-8")
    assert after == before
