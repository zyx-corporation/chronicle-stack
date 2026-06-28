"""Tests for Chronicle object expansion service."""

import json

from chronicle.models.artifact import ArtifactType
from chronicle.models.chronicle_object import ChronicleObjectType
from chronicle.models.decision import DecisionType
from chronicle.models.visibility import VisibilityHint
from chronicle.services.artifact_service import ArtifactService
from chronicle.services.chronicle_object_service import ChronicleObjectService
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.context_service import ContextService
from chronicle.services.decision_service import DecisionService
from chronicle.services.rde_service import RdeService


def test_chronicle_object_service_records_explicit_question_and_hypothesis(tmp_path):
    ChronicleService(tmp_path).init("Object Test")

    service = ChronicleObjectService(tmp_path)
    question = service.record(
        object_type=ChronicleObjectType.QUESTION,
        summary="Why should this policy exist?",
        created_by="tester",
        detail="Need an explicit problem statement.",
        visibility_hint=VisibilityHint.PRIVATE,
        evidence=["customer escalation", "design review"],
    )
    hypothesis = service.record(
        object_type=ChronicleObjectType.HYPOTHESIS,
        summary="The issue is caused by stale cache state.",
        created_by="tester",
        origin_question_id=question.object_id,
        evidence=["observed after deploy"],
    )

    rows = service.list_objects()

    assert any(row.object_id == question.object_id and row.object_type == ChronicleObjectType.QUESTION for row in rows)
    assert any(
        row.object_id == hypothesis.object_id
        and row.origin_question_id == question.object_id
        and row.object_type == ChronicleObjectType.HYPOTHESIS
        for row in rows
    )


def test_chronicle_object_service_derives_artifact_decision_conversation_and_delta(tmp_path):
    ChronicleService(tmp_path).init("Derived Object Test")
    context = ContextService(tmp_path).add_context(
        title="Discussion Context",
        summary="Captured discussion state.",
        visibility_hint=VisibilityHint.PUBLIC,
    )
    artifact_file = tmp_path / "artifact.md"
    artifact_file.write_text("v1", encoding="utf-8")
    artifact, version_1 = ArtifactService(tmp_path).create(
        title="Spec",
        artifact_type=ArtifactType.DOCUMENT,
        source_file=artifact_file,
    )
    artifact_file.write_text("v2", encoding="utf-8")
    _artifact, version_2 = ArtifactService(tmp_path).update(
        artifact_id=artifact.artifact_id,
        source_file=artifact_file,
        summary="update",
    )
    decision = DecisionService(tmp_path).record(
        decision_type=DecisionType.ACCEPTED,
        reason="Adopt the new spec.",
        artifact_id=artifact.artifact_id,
    )
    rde = RdeService(tmp_path).record(
        artifact_id=artifact.artifact_id,
        from_version_id=version_1.version_id,
        to_version_id=version_2.version_id,
        created_by="tester",
        summary="Meaning changed",
    )

    rows = ChronicleObjectService(tmp_path).list_objects()
    by_type = {row.object_type.value: row for row in rows if row.object_type.value in {"conversation", "artifact", "decision", "delta"}}

    assert by_type["conversation"].context_id == context.context_id
    assert by_type["artifact"].artifact_id == artifact.artifact_id
    assert by_type["decision"].decision_id == decision.decision_id
    assert by_type["delta"].rde_record_id == rde.rde_record_id
    assert "to_version_id" in by_type["delta"].detail


def test_chronicle_object_record_persists_in_event_payload(tmp_path):
    ChronicleService(tmp_path).init("Payload Test")
    record = ChronicleObjectService(tmp_path).record(
        object_type=ChronicleObjectType.OBJECTION,
        summary="We should not ship this yet.",
        created_by="reviewer",
    )

    payload = ChronicleService(tmp_path).jsonl.read_all()[-1].payload
    dumped = json.dumps(payload, ensure_ascii=False)

    assert payload["chronicle_object"]["object_id"] == record.object_id
    assert payload["chronicle_object"]["object_type"] == "objection"
    assert record.source_event_id in dumped
