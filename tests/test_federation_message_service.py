"""Tests for federation message Phase 5 service."""

from chronicle.models.federation_message import FederationMessageBox, FederationMessageType
from chronicle.services.audit_service import AuditService
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.federation_message_service import FederationMessageService


def test_federation_message_service_creates_outbox_preview_record(tmp_path):
    ChronicleService(tmp_path).init("Federation Test")

    record = FederationMessageService(tmp_path).create_message(
        message_type=FederationMessageType.REQUEST_CONTEXT,
        source_node="node:local:alpha",
        target_node="node:local:beta",
        purpose="project review",
        object_refs=["ctx_1"],
        retention="90d",
        reshare=False,
        box=FederationMessageBox.OUTBOX,
    )

    assert record.envelope.message_id.startswith("msg_")
    assert record.envelope.preview_only is True
    assert record.envelope.auto_apply is False
    assert record.box == FederationMessageBox.OUTBOX
    assert record.audit_recorded is False


def test_revoke_or_decay_inbox_message_records_audit(tmp_path):
    ChronicleService(tmp_path).init("Federation Audit Test")

    record = FederationMessageService(tmp_path).create_message(
        message_type=FederationMessageType.REVOKE_CONTEXT,
        source_node="node:local:alpha",
        target_node="node:local:beta",
        purpose="withdraw shared context",
        object_refs=["ctx_sensitive"],
        box=FederationMessageBox.INBOX,
    )

    audits = AuditService(tmp_path).list_events()

    assert record.audit_recorded is True
    assert audits[-1].metadata["message_id"] == record.envelope.message_id
    assert audits[-1].metadata["preview_only"] == "true"
    assert audits[-1].summary.startswith("Received revoke_context federation message")


def test_federation_message_service_inspects_box_in_reverse_time_order(tmp_path):
    ChronicleService(tmp_path).init("Federation Inspect Test")
    service = FederationMessageService(tmp_path)
    first = service.create_message(
        message_type=FederationMessageType.PUBLISH_CHRONICLE,
        source_node="node:1",
        target_node="node:2",
        purpose="publish",
        box=FederationMessageBox.OUTBOX,
    )
    second = service.create_message(
        message_type=FederationMessageType.OBJECT_CHRONICLE,
        source_node="node:1",
        target_node="node:2",
        purpose="object follow-up",
        object_refs=["obj_x"],
        box=FederationMessageBox.OUTBOX,
    )

    rows = service.inspect_box(FederationMessageBox.OUTBOX)

    assert rows[0].envelope.message_id == second.envelope.message_id
    assert rows[1].envelope.message_id == first.envelope.message_id


def test_federation_message_includes_trust_summary_for_target_node(tmp_path):
    ChronicleService(tmp_path).init("Federation Trust Test")
    from chronicle.services.trust_service import TrustService
    from chronicle.models.trust import TrustLevel

    TrustService(tmp_path).assert_relation(
        target_node="node:partner:beta",
        target_subject_id="subject:beta",
        domain="technical_review",
        purpose="project review",
        level=TrustLevel.TRUSTED,
        capabilities=["review"],
    )

    record = FederationMessageService(tmp_path).create_message(
        message_type=FederationMessageType.REQUEST_CONTEXT,
        source_node="node:local:alpha",
        target_node="node:partner:beta",
        purpose="project review",
        box=FederationMessageBox.OUTBOX,
    )

    trust_summary = record.envelope.metadata["trust_summary"]
    assert trust_summary["active_relation_count"] == 1
    assert trust_summary["dominant_level"] == "trusted"
