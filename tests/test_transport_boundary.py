from datetime import datetime, timezone
import json

import pytest
from pydantic import ValidationError

from chronicle.models.event import EventType
from chronicle.models.transport import (
    ExternalInteractionEnvelope,
    TransportAttachmentRef,
    TransportIdentityEvidence,
)
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.transport_service import ExternalInteractionService, MockTransportAdapter


@pytest.fixture
def initialized_project(tmp_path):
    ChronicleService(tmp_path).init("Transport Test")
    return tmp_path


def _envelope(**updates) -> ExternalInteractionEnvelope:
    values = {
        "message_id": "mock-message-1",
        "transport": "mock",
        "received_at": datetime.now(timezone.utc),
        "identity_evidence": TransportIdentityEvidence(
            transport_subject="remote-user-1",
            display_label="Remote User",
            verified=True,
        ),
        "text": "Please summarize the selected record.",
    }
    values.update(updates)
    return ExternalInteractionEnvelope(**values)


def test_mock_transport_records_user_input_without_execution(initialized_project):
    service = ExternalInteractionService(initialized_project)
    receipt = MockTransportAdapter(service).deliver(_envelope())

    events = ChronicleService(initialized_project).jsonl.read_all()
    event = events[-1]
    assert event.event_id == receipt.event_id
    assert event.event_type == EventType.USER_INPUT
    assert event.actor.value == "importer"
    assert event.payload["transport_identity_is_actor"] is False
    assert event.payload["command_executed"] is False
    assert receipt.command_executed is False


def test_command_promotion_is_explicit_and_does_not_execute(initialized_project):
    service = ExternalInteractionService(initialized_project)
    receipt = service.record_user_input(_envelope())

    promotion = service.promote_command_candidate(
        receipt=receipt,
        capability_id="runtime.summarize",
        operator="local-operator",
        reason="Reviewed request scope",
    )

    event = ChronicleService(initialized_project).jsonl.read_all()[-1]
    assert event.parent_event_id == receipt.event_id
    assert event.payload["external_command_promotion"]["execution_status"] == "not_executed"
    assert promotion.execution_status == "not_executed"
    assert promotion.review_required is True


@pytest.mark.parametrize("secret_key", ["token", "authorization", "webhook_secret"])
def test_envelope_rejects_secret_metadata(secret_key):
    with pytest.raises(ValidationError, match="secret-bearing metadata"):
        _envelope(metadata={secret_key: "do-not-store"})


def test_envelope_rejects_embedded_attachment_bytes():
    with pytest.raises(ValidationError, match="embedded attachment bytes"):
        _envelope(
            attachments=[
                TransportAttachmentRef(
                    attachment_id="attachment-1",
                    size_bytes=3,
                    external_ref="data:text/plain;base64,YWJj",
                )
            ]
        )


def test_recorded_envelope_contains_references_not_attachment_bytes(initialized_project):
    envelope = _envelope(
        attachments=[
            TransportAttachmentRef(
                attachment_id="attachment-1",
                media_type="text/plain",
                size_bytes=1024,
                digest="sha256:abc",
                external_ref="mock://attachments/attachment-1",
            )
        ]
    )
    ExternalInteractionService(initialized_project).record_user_input(envelope)

    raw = ChronicleService(initialized_project).paths.events_file.read_text(encoding="utf-8")
    payload = json.loads(raw.splitlines()[-1])
    attachment = payload["payload"]["external_interaction"]["attachments"][0]
    assert attachment["external_ref"] == "mock://attachments/attachment-1"
    assert "bytes" not in attachment
