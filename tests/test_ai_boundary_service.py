from datetime import datetime, timezone
import json
import os

from typer.testing import CliRunner

from chronicle.cli import app
from chronicle.models.context import Context, ContextScope
from chronicle.models.ai_boundary import (
    AiBoundaryPersistencePolicy,
    AiInterpretationWarningCode,
)
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
    warning_codes = {warning.code for warning in preview.interpretation_warnings}
    assert warning_codes == {
        AiInterpretationWarningCode.NOT_PRIMARY_FACT,
        AiInterpretationWarningCode.REVIEW_REQUIRED,
        AiInterpretationWarningCode.DECAY_CANDIDATE,
        AiInterpretationWarningCode.EXTERNAL_CONTEXT_DISCLOSURE,
    }


def test_ai_boundary_persistence_warning_is_structured(tmp_path):
    ChronicleService(tmp_path).init("AI Persistence Warning")

    preview = AiBoundaryService(tmp_path).preview(
        task="review persistent output",
        model_id="external:test-model",
        response_text="Derived response",
        persistence_policy=AiBoundaryPersistencePolicy(persist_response=True),
    )

    warnings = {warning.code: warning for warning in preview.interpretation_warnings}
    persisted = warnings[AiInterpretationWarningCode.DERIVED_CONTENT_PERSISTED]
    assert persisted.severity.value == "warning"
    assert "retention" in persisted.next_safe_action
    assert preview.response_text == "Derived response"


def test_runtime_preview_surfaces_interpretation_warnings(tmp_path):
    service = ChronicleService(tmp_path)
    service.init("AI Runtime Surface")
    preview = AiBoundaryService(tmp_path).preview(
        task="surface warnings",
        model_id="external:test-model",
        record=True,
    )
    event = next(event for event in service.jsonl.read_all() if event.event_id == preview.event_id)

    from chronicle.services.runtime_service import RuntimeService

    runtime_preview = RuntimeService(tmp_path).record_preview(event)

    assert any("not primary Chronicle facts" in note for note in runtime_preview.boundary_notes)
    assert any("decay-target" in note for note in runtime_preview.boundary_notes)


def test_ai_boundary_cli_json_exposes_stable_warning_contract(tmp_path):
    ChronicleService(tmp_path).init("AI Warning CLI")
    os.chdir(tmp_path)

    result = CliRunner().invoke(
        app,
        [
            "ai-boundary",
            "preview",
            "--task",
            "inspect warnings",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    warnings = {warning["code"]: warning for warning in payload["interpretation_warnings"]}
    assert warnings["not_primary_fact"]["severity"] == "warning"
    assert warnings["review_required"]["next_safe_action"]
    assert warnings["decay_candidate"]["severity"] == "advisory"
