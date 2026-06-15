"""Tests for lifecycle-aware behavior in derived graph-json exports."""

from datetime import datetime, timezone

from chronicle.models.context import Context, ContextScope
from chronicle.models.event import Actor, ChronicleEvent, EventType
from chronicle.models.lifecycle import LifecycleAction, LifecycleReasonClass
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.graph_export_service import GraphExportService
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


def test_graph_export_excludes_tombstoned_context_nodes_and_referencing_events(tmp_path):
    ChronicleService(tmp_path).init("Lifecycle Graph Test")
    _append_context(
        tmp_path,
        Context(
            context_id="ctx_active_graph",
            title="Active Graph Context",
            summary="Active graph body remains visible",
            scope=ContextScope.TASK,
            created_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
        ),
    )
    _append_context(
        tmp_path,
        Context(
            context_id="ctx_tombstone_graph",
            title="Tombstoned Graph Context",
            summary="Tombstoned graph body should not be exported",
            scope=ContextScope.TASK,
            created_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
        ),
    )
    LifecycleService(tmp_path).record(
        action=LifecycleAction.TOMBSTONE,
        target_id="ctx_tombstone_graph",
        target_kind="context",
        actor="test",
        reason_class=LifecycleReasonClass.PRIVACY,
        reason="test tombstone",
    )

    graph = GraphExportService(tmp_path).export_graph()
    dumped = graph.model_dump(mode="json")
    node_source_ids = {node["source_id"] for node in dumped["nodes"]}
    node_ids = {node["node_id"] for node in dumped["nodes"]}

    assert "ctx_active_graph" in node_source_ids
    assert "ctx_tombstone_graph" not in node_source_ids
    assert "evt_ctx_tombstone_graph" not in node_source_ids
    assert "Tombstoned Graph Context" not in str(dumped)
    assert "Tombstoned graph body should not be exported" not in str(dumped)
    assert "lifecycle_tombstoned_records_excluded=1" in dumped["export_manifest"]["notes"]
    assert "lifecycle_tombstoned_events_excluded=1" in dumped["export_manifest"]["notes"]
    assert all(edge["from_node_id"] in node_ids and edge["to_node_id"] in node_ids for edge in dumped["edges"])


def test_graph_export_marks_sealed_context_nodes_without_excluding(tmp_path):
    ChronicleService(tmp_path).init("Lifecycle Graph Seal Test")
    _append_context(
        tmp_path,
        Context(
            context_id="ctx_sealed_graph",
            title="Sealed Graph Context",
            summary="Sealed graph body remains advisory",
            scope=ContextScope.TASK,
            created_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
        ),
    )
    LifecycleService(tmp_path).record(
        action=LifecycleAction.SEAL,
        target_id="ctx_sealed_graph",
        target_kind="context",
        actor="test",
        reason_class=LifecycleReasonClass.RETENTION,
        reason="test seal",
    )

    graph = GraphExportService(tmp_path).export_graph()
    dumped = graph.model_dump(mode="json")
    context_node = next(node for node in dumped["nodes"] if node["source_id"] == "ctx_sealed_graph")

    assert context_node["metadata"]["lifecycle_warning"] == "lifecycle_sealed_record"
    assert "lifecycle_sealed_record=1" in dumped["export_manifest"]["notes"]


def test_graph_lifecycle_export_does_not_mutate_primary_jsonl(tmp_path):
    ChronicleService(tmp_path).init("Lifecycle Graph Mutation Test")
    _append_context(
        tmp_path,
        Context(
            context_id="ctx_jsonl_graph",
            title="JSONL Graph Context",
            summary="Primary JSONL must remain unchanged",
            scope=ContextScope.TASK,
            created_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
        ),
    )
    LifecycleService(tmp_path).record(
        action=LifecycleAction.HARD_DELETE,
        target_id="ctx_jsonl_graph",
        target_kind="context",
        actor="test",
        reason_class=LifecycleReasonClass.USER_REQUEST,
        reason="marker only",
    )
    events_file = tmp_path / ".chronicle" / "chronicle.jsonl"
    before = events_file.read_text(encoding="utf-8")

    GraphExportService(tmp_path).export_graph()

    after = events_file.read_text(encoding="utf-8")
    assert after == before
