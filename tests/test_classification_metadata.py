"""Tests for v0.5 classification metadata models."""

from datetime import datetime, timezone

from chronicle.models.artifact import Artifact, ArtifactType
from chronicle.models.classification import (
    AllowedOperation,
    ClassificationLayer,
    ClassificationMetadata,
    LlmPolicy,
    RetentionMode,
    Sensitivity,
)
from chronicle.models.context import Context, ContextScope
from chronicle.models.event import Actor, ChronicleEvent, EventType


def test_classification_metadata_serializes_layer_and_policy():
    classification = ClassificationMetadata(
        layer=ClassificationLayer.SENSITIVE_CONTEXT,
        sensitivity=Sensitivity.SENSITIVE,
        owner="owner@example.test",
        source_refs=["ctx_1"],
        allowed_operations=[AllowedOperation.VIEW, AllowedOperation.REINTERPRET],
        llm_policy=LlmPolicy(local_allowed=True, external_allowed=False, masking_required=True),
    )

    dumped = classification.model_dump(mode="json")

    assert dumped["layer"] == 3
    assert dumped["sensitivity"] == "sensitive"
    assert dumped["allowed_operations"] == ["view", "reinterpret"]
    assert dumped["llm_policy"] == {
        "local_allowed": True,
        "external_allowed": False,
        "masking_required": True,
    }
    assert dumped["retention"]["mode"] == "keep"


def test_restricted_secret_defaults_to_view_only_and_no_model_context():
    classification = ClassificationMetadata(layer=ClassificationLayer.RESTRICTED_SECRET, sensitivity=Sensitivity.RESTRICTED)

    assert classification.allowed_operations == [AllowedOperation.VIEW]
    assert classification.llm_policy.local_allowed is False
    assert classification.llm_policy.external_allowed is False
    assert classification.llm_policy.masking_required is True


def test_context_accepts_optional_classification_metadata():
    ctx = Context(
        context_id="ctx_classified",
        title="Classified Context",
        scope=ContextScope.TASK,
        created_at=datetime(2026, 6, 14, tzinfo=timezone.utc),
        classification=ClassificationMetadata(layer=ClassificationLayer.INTERNAL, sensitivity=Sensitivity.INTERNAL),
    )

    dumped = ctx.model_dump(mode="json")

    assert dumped["classification"]["layer"] == 2
    assert dumped["classification"]["sensitivity"] == "internal"


def test_artifact_accepts_optional_classification_metadata():
    artifact = Artifact(
        artifact_id="art_classified",
        chronicle_id="chr_test",
        title="Classified Artifact",
        artifact_type=ArtifactType.DOCUMENT,
        current_version_id="ver_1",
        created_at=datetime(2026, 6, 14, tzinfo=timezone.utc),
        updated_at=datetime(2026, 6, 14, tzinfo=timezone.utc),
        path="docs/classified.md",
        classification=ClassificationMetadata(layer=ClassificationLayer.SHAREABLE, sensitivity=Sensitivity.SHAREABLE),
    )

    dumped = artifact.model_dump(mode="json")

    assert dumped["classification"]["layer"] == 1
    assert dumped["classification"]["sensitivity"] == "shareable"


def test_event_accepts_optional_classification_metadata_and_jsonl_excludes_none():
    event = ChronicleEvent(
        event_id="evt_classified",
        chronicle_id="chr_test",
        timestamp=datetime(2026, 6, 14, tzinfo=timezone.utc),
        event_type=EventType.USER_INPUT,
        actor=Actor.USER,
        summary="Classified event",
        classification=ClassificationMetadata(layer=ClassificationLayer.INTERNAL),
    )

    jsonl = event.to_jsonl()

    assert '"classification"' in jsonl
    assert '"layer":2' in jsonl


def test_retention_review_at_serializes_when_present():
    classification = ClassificationMetadata(
        layer=ClassificationLayer.INTERNAL,
        retention={
            "mode": RetentionMode.REVIEW,
            "review_at": datetime(2026, 7, 1, tzinfo=timezone.utc),
        },
    )

    dumped = classification.model_dump(mode="json")

    assert dumped["retention"]["mode"] == "review"
    assert dumped["retention"]["review_at"] == "2026-07-01T00:00:00Z"
