import json

import pytest

from chronicle.errors import DecisionTargetNotFoundError
from chronicle.models.artifact import ArtifactType
from chronicle.models.decision import DecisionType
from chronicle.services.artifact_service import ArtifactService
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.decision_service import DecisionService


@pytest.fixture
def decision_service(tmp_path):
    ChronicleService(tmp_path).init("Decision Test")
    return DecisionService(tmp_path)


def test_record_decision(decision_service, tmp_path):
    artifacts = ArtifactService(tmp_path)
    source = tmp_path / "doc.md"
    source.write_text("Content", encoding="utf-8")
    artifact, _ = artifacts.create(
        title="Decision Target",
        artifact_type=ArtifactType.SPECIFICATION,
        source_file=source,
    )

    decision = decision_service.record(
        decision_type=DecisionType.ACCEPTED,
        reason="Looks good for v0.1",
        artifact_id=artifact.artifact_id,
    )

    assert decision.decision_id.startswith("dec_")
    assert decision.decision_type == DecisionType.ACCEPTED
    assert decision.reason == "Looks good for v0.1"

    decisions = decision_service.chronicle.index.load_decisions()
    assert decision.decision_id in decisions


def test_decision_target_not_found(decision_service):
    with pytest.raises(DecisionTargetNotFoundError):
        decision_service.record(
            decision_type=DecisionType.REJECTED,
            artifact_id="art_missing",
        )


# --- ADR-001 P0 regression: event_id integrity ---

def test_decision_event_id_is_populated(decision_service):
    """Decision.event_id must be a valid evt_ ID immediately after record."""
    decision = decision_service.record(
        decision_type=DecisionType.DEFERRED,
        reason="Policy decision",
    )
    assert decision.event_id is not None
    assert decision.event_id.startswith("evt_")


def test_decision_event_id_is_persisted(decision_service, tmp_path):
    artifacts = ArtifactService(tmp_path)
    source = tmp_path / "doc.md"
    source.write_text("Content", encoding="utf-8")
    artifact, _ = artifacts.create(
        title="Decision Event Link",
        artifact_type=ArtifactType.SPECIFICATION,
        source_file=source,
    )

    decision = decision_service.record(
        decision_type=DecisionType.ACCEPTED,
        reason="Looks good for v0.1",
        artifact_id=artifact.artifact_id,
    )

    assert decision.event_id is not None
    assert decision.event_id.startswith("evt_")

    # Rebuild indexes and check
    decision_service.chronicle.rebuild_indexes()
    decisions = decision_service.chronicle.index.load_decisions()
    loaded = decisions[decision.decision_id]
    assert loaded.event_id is not None
    assert loaded.event_id == decision.event_id

    # Verify chronicle.jsonl
    events_file = decision_service.chronicle.paths.events_file
    found = False
    with events_file.open(encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue
            data = json.loads(stripped)
            if data.get("event_type") == "decision_recorded":
                payload_decision = data.get("payload", {}).get("decision", {})
                assert payload_decision.get("event_id") == data["event_id"]
                found = True
    assert found, "decision_recorded event not found in chronicle.jsonl"


# --- ADR-001 §7 / P1: alternatives and notes ---

def test_decision_record_with_alternatives_and_notes(decision_service):
    """decision record must accept and persist alternatives and notes."""
    decision = decision_service.record(
        decision_type=DecisionType.ACCEPTED,
        reason="Best option",
        alternatives=["Option B", "Option C"],
        notes="Revisit after v0.2",
    )
    assert decision.alternatives == ["Option B", "Option C"]
    assert decision.notes == "Revisit after v0.2"

    decisions = decision_service.chronicle.index.load_decisions()
    rebuilt = decisions[decision.decision_id]
    assert rebuilt.alternatives == ["Option B", "Option C"]
    assert rebuilt.notes == "Revisit after v0.2"
