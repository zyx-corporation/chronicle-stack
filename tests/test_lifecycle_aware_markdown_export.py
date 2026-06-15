"""Tests for lifecycle-aware behavior in derived markdown exports."""

from datetime import datetime, timezone

from chronicle.exporters.markdown_exporter import MarkdownExporter
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


def test_markdown_export_excludes_tombstoned_contexts(tmp_path):
    ChronicleService(tmp_path).init("Lifecycle Markdown Test")
    _append_context(
        tmp_path,
        Context(
            context_id="ctx_active_md",
            title="Active Markdown Context",
            summary="Active body remains visible",
            scope=ContextScope.TASK,
            created_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
        ),
    )
    _append_context(
        tmp_path,
        Context(
            context_id="ctx_tombstone_md",
            title="Tombstoned Markdown Context",
            summary="Tombstoned body should not be exported",
            scope=ContextScope.TASK,
            created_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
        ),
    )
    LifecycleService(tmp_path).record(
        action=LifecycleAction.TOMBSTONE,
        target_id="ctx_tombstone_md",
        target_kind="context",
        actor="test",
        reason_class=LifecycleReasonClass.PRIVACY,
        reason="test tombstone",
    )

    content = MarkdownExporter(tmp_path).export()

    assert "Active Markdown Context" in content
    assert "ctx_active_md" in content
    assert "Tombstoned Markdown Context" not in content
    assert "Tombstoned body should not be exported" not in content
    assert "lifecycle_tombstoned_records_excluded: 1" in content


def test_markdown_export_marks_sealed_contexts_without_excluding(tmp_path):
    ChronicleService(tmp_path).init("Lifecycle Markdown Seal Test")
    _append_context(
        tmp_path,
        Context(
            context_id="ctx_sealed_md",
            title="Sealed Markdown Context",
            summary="Sealed body remains advisory",
            scope=ContextScope.TASK,
            created_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
        ),
    )
    LifecycleService(tmp_path).record(
        action=LifecycleAction.SEAL,
        target_id="ctx_sealed_md",
        target_kind="context",
        actor="test",
        reason_class=LifecycleReasonClass.RETENTION,
        reason="test seal",
    )

    content = MarkdownExporter(tmp_path).export()

    assert "Sealed Markdown Context [lifecycle: sealed]" in content
    assert "Sealed body remains advisory" in content
    assert "lifecycle_sealed_record: 1" in content


def test_markdown_lifecycle_export_does_not_mutate_primary_jsonl(tmp_path):
    ChronicleService(tmp_path).init("Lifecycle Markdown Mutation Test")
    _append_context(
        tmp_path,
        Context(
            context_id="ctx_jsonl_md",
            title="JSONL Context",
            summary="Primary JSONL must remain unchanged",
            scope=ContextScope.TASK,
            created_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
        ),
    )
    LifecycleService(tmp_path).record(
        action=LifecycleAction.HARD_DELETE,
        target_id="ctx_jsonl_md",
        target_kind="context",
        actor="test",
        reason_class=LifecycleReasonClass.USER_REQUEST,
        reason="marker only",
    )
    events_file = tmp_path / ".chronicle" / "chronicle.jsonl"
    before = events_file.read_text(encoding="utf-8")

    MarkdownExporter(tmp_path).export()

    after = events_file.read_text(encoding="utf-8")
    assert after == before
