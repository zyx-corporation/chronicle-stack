"""Contract tests for JSONL primary records and EventType-to-payload shapes."""

import json

import pytest

from chronicle.models.event import EventType
from chronicle.services.chronicle_service import ChronicleService

# All EventTypes that produce structured payloads
STRUCTURED_EVENT_TYPES = [
    EventType.CHRONICLE_CREATED,
    EventType.CONTEXT_ADDED,
    EventType.ARTIFACT_CREATED,
    EventType.ARTIFACT_UPDATED,
    EventType.ARTIFACT_VERSIONED,
    EventType.DECISION_RECORDED,
    EventType.RDE_DIFF_RECORDED,
    EventType.BOUNDARY_RULE_ADDED,
]


@pytest.fixture
def chronicle_jsonl(tmp_path):
    """Create a Chronicle with typical events and return the JSONL path."""
    svc = ChronicleService(tmp_path)
    svc.init("Contract Test")
    return svc.paths.events_file


def test_jsonl_is_primary_record(chronicle_jsonl):
    """chronicle.jsonl must exist and be readable after init."""
    assert chronicle_jsonl.exists()
    lines = chronicle_jsonl.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) >= 1
    for line in lines:
        data = json.loads(line)
        # Basic contract fields must be present
        for field in ["event_id", "chronicle_id", "timestamp", "event_type", "actor", "summary"]:
            assert field in data, f"Missing required field '{field}' in event: {data.get('event_id')}"


def test_chronicle_created_event(chronicle_jsonl):
    """chronicle_created event must have title in payload."""
    lines = chronicle_jsonl.read_text(encoding="utf-8").strip().splitlines()
    created_events = [
        json.loads(line) for line in lines
        if json.loads(line).get("event_type") == "chronicle_created"
    ]
    assert len(created_events) == 1
    event = created_events[0]
    assert "payload" in event
    assert "title" in event["payload"]


def test_context_added_payload_shape(tmp_path):
    """context_added must have payload.context."""
    svc = ChronicleService(tmp_path)
    svc.init("Payload Test")
    from chronicle.models.event import Actor, EventType
    svc.record_event(
        event_type=EventType.CONTEXT_ADDED,
        actor=Actor.USER,
        summary="Test context",
        payload={"context": {"context_id": "ctx_test", "title": "T", "scope": "project",
                             "visibility_hint": "unknown", "confidence": "medium",
                             "created_at": "2026-06-13T12:00:00+09:00", "tags": []}},
    )
    events = svc.jsonl.read_all()
    ctx_events = [e for e in events if e.event_type == EventType.CONTEXT_ADDED]
    assert len(ctx_events) >= 1
    payload = ctx_events[-1].payload
    assert "context" in payload


def test_artifact_created_payload_shape(tmp_path):
    """artifact_created must have payload.artifact and may have payload.version."""
    from chronicle.services.artifact_service import ArtifactService
    from chronicle.services.chronicle_service import ChronicleService
    from chronicle.models.artifact import ArtifactType
    ChronicleService(tmp_path).init("Artifact Contract")
    svc = ArtifactService(tmp_path)
    f = tmp_path / "spec.md"
    f.write_text("# Test", encoding="utf-8")
    svc.create(title="Contract Artifact", artifact_type=ArtifactType.SPECIFICATION, source_file=f)
    events = svc.chronicle.jsonl.read_all()
    art_events = [e for e in events if e.event_type == EventType.ARTIFACT_CREATED]
    assert len(art_events) >= 1
    payload = art_events[-1].payload
    assert "artifact" in payload
    # version may or may not be present per contract


def test_artifact_versioned_payload_shape(tmp_path):
    """artifact_versioned must have payload.version."""
    svc = ChronicleService(tmp_path)
    svc.init("Versioned Test")
    from chronicle.services.artifact_service import ArtifactService
    from chronicle.models.artifact import ArtifactType
    art_svc = ArtifactService(tmp_path)
    f1 = tmp_path / "v1.md"
    f1.write_text("v1", encoding="utf-8")
    art, _ = art_svc.create(title="V Contract", artifact_type=ArtifactType.DOCUMENT, source_file=f1)
    f2 = tmp_path / "v2.md"
    f2.write_text("v2", encoding="utf-8")
    art_svc.update(artifact_id=art.artifact_id, source_file=f2, summary="updated")
    events = svc.jsonl.read_all()
    ver_events = [e for e in events if e.event_type == EventType.ARTIFACT_VERSIONED]
    assert len(ver_events) >= 1
    payload = ver_events[-1].payload
    assert "version" in payload


def test_decision_recorded_payload_shape(tmp_path):
    """decision_recorded must have payload.decision."""
    svc = ChronicleService(tmp_path)
    svc.init("Decision Test")
    from chronicle.services.decision_service import DecisionService
    from chronicle.models.decision import DecisionType
    dec_svc = DecisionService(tmp_path)
    dec_svc.record(decision_type=DecisionType.ACCEPTED, reason="Contract test")
    events = svc.jsonl.read_all()
    dec_events = [e for e in events if e.event_type == EventType.DECISION_RECORDED]
    assert len(dec_events) >= 1
    payload = dec_events[-1].payload
    assert "decision" in payload


def test_rde_diff_recorded_payload_shape(tmp_path):
    """rde_diff_recorded must have payload.rde."""
    svc = ChronicleService(tmp_path)
    svc.init("RDE Test")
    from chronicle.services.artifact_service import ArtifactService
    from chronicle.services.rde_service import RdeService
    from chronicle.models.artifact import ArtifactType
    art_svc = ArtifactService(tmp_path)
    f1 = tmp_path / "v1.md"
    f1.write_text("v1", encoding="utf-8")
    f2 = tmp_path / "v2.md"
    f2.write_text("v2", encoding="utf-8")
    art, v1 = art_svc.create(title="RDE Contract", artifact_type=ArtifactType.DOCUMENT, source_file=f1)
    _, v2 = art_svc.update(artifact_id=art.artifact_id, source_file=f2, summary="v2")
    rde_svc = RdeService(tmp_path)
    rde_svc.record(artifact_id=art.artifact_id, from_version_id=v1.version_id,
                   to_version_id=v2.version_id, summary="Contract RDE")
    events = svc.jsonl.read_all()
    rde_events = [e for e in events if e.event_type == EventType.RDE_DIFF_RECORDED]
    assert len(rde_events) >= 1
    payload = rde_events[-1].payload
    assert "rde" in payload


def test_boundary_rule_added_payload_shape(tmp_path):
    """boundary_rule_added must have payload.boundary_rule."""
    svc = ChronicleService(tmp_path)
    svc.init("Boundary Test")
    from chronicle.services.boundary_service import BoundaryService
    from chronicle.models.boundary import BoundaryRuleType, BoundaryConditionField, BoundaryOperator
    bsvc = BoundaryService(tmp_path)
    bsvc.add_rule(rule_type=BoundaryRuleType.WARN, field=BoundaryConditionField.VISIBILITY,
                  operator=BoundaryOperator.EQUALS, value="sensitive", reason="Contract test")
    events = svc.jsonl.read_all()
    br_events = [e for e in events if e.event_type == EventType.BOUNDARY_RULE_ADDED]
    assert len(br_events) >= 1
    payload = br_events[-1].payload
    assert "boundary_rule" in payload
