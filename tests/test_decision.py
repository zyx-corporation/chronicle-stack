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
