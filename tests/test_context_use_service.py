"""Tests for model-context use dry-run checks."""

from datetime import datetime, timezone

from chronicle.models.classification import AllowedOperation, ClassificationLayer, ClassificationMetadata, LlmPolicy, Sensitivity
from chronicle.models.context import Context, ContextScope
from chronicle.models.context_use import ContextUseSeverity, ContextUseTarget
from chronicle.models.event import Actor, ChronicleEvent, EventType
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.context_use_service import ContextUseService


def _append_context(root, context: Context) -> None:
    service = ChronicleService(root)
    metadata = service.load_metadata()
    event = ChronicleEvent(
        event_id=f"evt_{context.context_id}",
        chronicle_id=metadata.chronicle_id,
        timestamp=datetime(2026, 6, 14, tzinfo=timezone.utc),
        event_type=EventType.CONTEXT_ADDED,
        actor=Actor.USER,
        summary=f"Add {context.title}",
        payload={"context": context.model_dump(mode="json")},
    )
    service.append_event(event)
    service.rebuild_indexes()


def test_context_use_warns_for_unclassified_context(tmp_path):
    ChronicleService(tmp_path).init("Context Use")
    _append_context(
        tmp_path,
        Context(
            context_id="ctx_unclassified",
            title="Unclassified",
            scope=ContextScope.TASK,
            created_at=datetime(2026, 6, 14, tzinfo=timezone.utc),
        ),
    )

    report = ContextUseService(tmp_path).check(target=ContextUseTarget.EXTERNAL, purpose="public summary")

    assert report.status == ContextUseSeverity.WARNING
    assert report.findings[0].context_id == "ctx_unclassified"
    assert "unclassified" in report.findings[0].summary.lower()


def test_context_use_blocks_layer_4_context(tmp_path):
    ChronicleService(tmp_path).init("Context Use")
    _append_context(
        tmp_path,
        Context(
            context_id="ctx_secret",
            title="Secret",
            scope=ContextScope.TASK,
            created_at=datetime(2026, 6, 14, tzinfo=timezone.utc),
            classification=ClassificationMetadata(layer=ClassificationLayer.RESTRICTED_SECRET, sensitivity=Sensitivity.RESTRICTED),
        ),
    )

    report = ContextUseService(tmp_path).check(target=ContextUseTarget.LOCAL, purpose="internal review")

    assert report.status == ContextUseSeverity.BLOCKED
    assert report.findings[0].severity == ContextUseSeverity.BLOCKED


def test_context_use_ok_for_explicit_local_context(tmp_path):
    ChronicleService(tmp_path).init("Context Use")
    _append_context(
        tmp_path,
        Context(
            context_id="ctx_local",
            title="Local OK",
            scope=ContextScope.TASK,
            created_at=datetime(2026, 6, 14, tzinfo=timezone.utc),
            classification=ClassificationMetadata(
                layer=ClassificationLayer.INTERNAL,
                allowed_operations=[AllowedOperation.VIEW, AllowedOperation.INJECT],
                llm_policy=LlmPolicy(local_allowed=True, external_allowed=False, masking_required=True),
            ),
        ),
    )

    report = ContextUseService(tmp_path).check(target=ContextUseTarget.LOCAL, purpose="internal review")

    assert report.status == ContextUseSeverity.OK
    assert report.findings[0].severity == ContextUseSeverity.OK


def test_context_use_external_warns_when_not_explicitly_allowed(tmp_path):
    ChronicleService(tmp_path).init("Context Use")
    _append_context(
        tmp_path,
        Context(
            context_id="ctx_internal",
            title="Internal",
            scope=ContextScope.TASK,
            created_at=datetime(2026, 6, 14, tzinfo=timezone.utc),
            classification=ClassificationMetadata(layer=ClassificationLayer.INTERNAL),
        ),
    )

    report = ContextUseService(tmp_path).check(target=ContextUseTarget.EXTERNAL, purpose="public summary")

    assert report.status == ContextUseSeverity.WARNING
    summaries = [finding.summary for finding in report.findings]
    assert any("External model-context use" in summary for summary in summaries)


def test_context_use_can_filter_to_selected_context_ids(tmp_path):
    ChronicleService(tmp_path).init("Context Use")
    _append_context(
        tmp_path,
        Context(
            context_id="ctx_local",
            title="Local OK",
            scope=ContextScope.TASK,
            created_at=datetime(2026, 6, 14, tzinfo=timezone.utc),
            classification=ClassificationMetadata(
                layer=ClassificationLayer.INTERNAL,
                allowed_operations=[AllowedOperation.VIEW, AllowedOperation.INJECT],
                llm_policy=LlmPolicy(local_allowed=True, external_allowed=False, masking_required=True),
            ),
        ),
    )
    _append_context(
        tmp_path,
        Context(
            context_id="ctx_unclassified",
            title="Unclassified",
            scope=ContextScope.TASK,
            created_at=datetime(2026, 6, 14, tzinfo=timezone.utc),
        ),
    )

    report = ContextUseService(tmp_path).check(target=ContextUseTarget.LOCAL, purpose="internal review", context_ids=["ctx_local"])

    assert report.status == ContextUseSeverity.OK
    assert report.context_count == 1
    assert report.findings[0].context_id == "ctx_local"
