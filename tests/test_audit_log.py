"""Tests for audit log models and store."""

import json
from datetime import datetime, timezone

from chronicle.models.audit import AuditEvent, AuditOperation, AuditSeverity, AuditTargetEnvironment
from chronicle.services.audit_service import AuditService
from chronicle.services.chronicle_service import ChronicleService
from chronicle.store.audit_log_store import AuditLogStore


def test_audit_event_serializes_to_jsonl_without_none_fields():
    event = AuditEvent(
        audit_id="aud_1",
        chronicle_id="chr_1",
        created_at=datetime(2026, 6, 14, tzinfo=timezone.utc),
        operation=AuditOperation.EXPORT,
        actor="user",
        purpose="public review",
        target_environment=AuditTargetEnvironment.FILE,
        referenced_records=["ctx_1"],
        result=AuditSeverity.INFO,
        summary="Exported YAML for review.",
    )

    data = json.loads(event.to_jsonl())

    assert data["audit_id"] == "aud_1"
    assert data["operation"] == "export"
    assert data["target_environment"] == "file"
    assert data["referenced_records"] == ["ctx_1"]
    assert "source_event_id" not in data


def test_audit_log_store_append_and_read(tmp_path):
    store = AuditLogStore(tmp_path / "audit.jsonl")
    event = AuditEvent(
        audit_id="aud_1",
        chronicle_id="chr_1",
        created_at=datetime(2026, 6, 14, tzinfo=timezone.utc),
        operation=AuditOperation.CONTEXT_USE,
        target_environment=AuditTargetEnvironment.EXTERNAL,
        referenced_records=["ctx_1", "ctx_2"],
        result=AuditSeverity.WARNING,
        summary="External context-use warning.",
    )

    store.append(event)
    loaded = store.read_all()

    assert len(loaded) == 1
    assert loaded[0].audit_id == "aud_1"
    assert loaded[0].operation == AuditOperation.CONTEXT_USE
    assert loaded[0].referenced_records == ["ctx_1", "ctx_2"]


def test_audit_log_store_counts_corrupt_lines(tmp_path):
    audit_file = tmp_path / "audit.jsonl"
    audit_file.write_text('{"bad": true}\nnot-json\n', encoding="utf-8")
    store = AuditLogStore(audit_file)

    assert store.count_corrupt_lines() == 2
    assert store.read_all() == []


def test_audit_service_records_to_separate_audit_file(tmp_path):
    ChronicleService(tmp_path).init("Audit Test")
    audit = AuditService(tmp_path)

    event = audit.record(
        operation=AuditOperation.REINTERPRET,
        actor="reviewer",
        purpose="RDE review",
        target_environment=AuditTargetEnvironment.LOCAL,
        referenced_records=["evt_1"],
        result=AuditSeverity.INFO,
        summary="Reinterpretation reviewed.",
    )

    assert event.audit_id.startswith("aud_")
    assert (tmp_path / ".chronicle" / "audit.jsonl").exists()
    assert len(audit.list_events()) == 1
    assert ChronicleService(tmp_path).show()["event_count"] == 1
