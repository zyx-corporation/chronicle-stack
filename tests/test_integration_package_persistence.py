"""Tests for controlled integration package persistence."""

from datetime import datetime, timezone

from chronicle.models.context import Context, ContextScope
from chronicle.models.event import Actor, ChronicleEvent, EventType
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.integration_package_service import IntegrationPackageService


def _append_context(root, context: Context) -> None:
    service = ChronicleService(root)
    metadata = service.load_metadata()
    event = ChronicleEvent(
        event_id=f"evt_{context.context_id}",
        chronicle_id=metadata.chronicle_id,
        timestamp=datetime(2026, 6, 15, tzinfo=timezone.utc),
        event_type=EventType.CONTEXT_ADDED,
        actor=Actor.USER,
        summary=f"Add {context.title}",
        payload={"context": context.model_dump(mode="json")},
    )
    service.append_event(event)
    service.rebuild_indexes()


def test_package_persistence_writes_manifest_and_records(tmp_path):
    ChronicleService(tmp_path).init("Package Persistence Test")
    _append_context(
        tmp_path,
        Context(
            context_id="ctx_persist",
            title="Persistent Context",
            summary="Persist this package body",
            scope=ContextScope.TASK,
            created_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
        ),
    )

    service = IntegrationPackageService(tmp_path)
    package = service.build_context_package(purpose="Persistence test")
    package_dir = service.save_package(package)

    assert package_dir.exists()
    assert (package_dir / "manifest.json").exists()
    assert (package_dir / "records.json").exists()

    loaded = service.load_package(package.manifest.package_id)
    assert loaded.manifest.package_id == package.manifest.package_id
    assert loaded.manifest.referenced_records == ["ctx_persist"]
    assert loaded.records[0].record_id == "ctx_persist"
    assert loaded.records[0].content is not None
    assert "Persist this package body" in loaded.records[0].content


def test_package_persistence_audit_metadata_does_not_copy_record_content(tmp_path):
    ChronicleService(tmp_path).init("Package Audit Test")
    _append_context(
        tmp_path,
        Context(
            context_id="ctx_audit_pkg",
            title="Audit Package Context",
            summary="Sensitive body should stay out of audit metadata",
            scope=ContextScope.TASK,
            created_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
        ),
    )

    service = IntegrationPackageService(tmp_path)
    package = service.build_context_package(purpose="Audit metadata test")
    service.save_package(package)

    audit_text = (tmp_path / ".chronicle" / "audit.jsonl").read_text(encoding="utf-8")
    assert package.manifest.package_id in audit_text
    assert "ctx_audit_pkg" in audit_text
    assert "Sensitive body should stay out of audit metadata" not in audit_text
    assert "Audit Package Context" not in audit_text
