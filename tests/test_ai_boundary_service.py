from datetime import datetime, timezone

from chronicle.models.context import Context, ContextScope
from chronicle.models.event import Actor, ChronicleEvent, EventType
from chronicle.services.ai_boundary_service import AiBoundaryService
from chronicle.services.chronicle_service import ChronicleService


def _append_context(root, context: Context) -> None:
    service = ChronicleService(root)
    metadata = service.load_metadata()
    event = ChronicleEvent(
        event_id=f"evt_{context.context_id}",
        chronicle_id=metadata.chronicle_id,
        timestamp=datetime(2026, 6, 28, tzinfo=timezone.utc),
        event_type=EventType.CONTEXT_ADDED,
        actor=Actor.USER,
        summary=f"Add {context.title}",
        payload={"context": context.model_dump(mode="json")},
    )
    service.append_event(event)
    service.rebuild_indexes()


def test_ai_boundary_preview_can_record_reviewable_event(tmp_path):
    ChronicleService(tmp_path).init("AI Boundary Test")
    _append_context(
        tmp_path,
        Context(
            context_id="ctx_ai_boundary",
            title="AI Boundary Context",
            summary="Preview-safe context for external adapter review.",
            scope=ContextScope.TASK,
            created_at=datetime(2026, 6, 28, tzinfo=timezone.utc),
        ),
    )

    preview = AiBoundaryService(tmp_path).preview(
        task="summarize for external model",
        model_id="external:test-model",
        context_ids=["ctx_ai_boundary"],
        prompt_text="Summarize carefully.",
        response_text="Draft response.",
        occurred_at=datetime(2026, 6, 28, 12, 0, tzinfo=timezone.utc),
        record=True,
    )

    assert preview.recorded is True
    assert preview.event_id is not None
    assert preview.included_context_ids == ["ctx_ai_boundary"]
    assert preview.sayane_contract.export_command.startswith("chronicle ai-boundary preview")
    assert "no automatic external send" in preview.sayane_contract.boundaries[1]

