"""Tests for controlled integration package persistence."""

from datetime import datetime, timezone

from chronicle.models.context import Context, ContextScope
from chronicle.models.event import Actor, ChronicleEvent, EventType
from chronicle.models.lifecycle import LifecycleAction, LifecycleReasonClass
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.integration_package_service import IntegrationPackageService
from chronicle.services.lifecycle_service import LifecycleService


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


def test_package_generation_excludes_tombstoned_contexts(tmp_path):
    ChronicleService(tmp_path).init("Lifecycle Package Test")
    _append_context(
        tmp_path,
        Context(
            context_id="ctx_active",
            title="Active Context",
            summary="Active body",
            scope=ContextScope.TASK,
            created_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
        ),
    )
    _append_context(
        tmp_path,
        Context(
            context_id="ctx_tombstone",
            title="Tombstoned Context",
            summary="Tombstoned body should not be packaged",
            scope=ContextScope.TASK,
            created_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
        ),
    )
    LifecycleService(tmp_path).record(
        action=LifecycleAction.TOMBSTONE,
        target_id="ctx_tombstone",
        target_kind="context",
        actor="test",
        reason_class=LifecycleReasonClass.PRIVACY,
        reason="test tombstone",
    )

    package = IntegrationPackageService(tmp_path).build_context_package(purpose="Lifecycle test")

    assert package.manifest.referenced_records == ["ctx_active"]
    assert [record.record_id for record in package.records] == ["ctx_active"]
    assert "lifecycle_tombstoned_records_excluded" in package.manifest.warnings
    assert package.manifest.metadata["excluded_lifecycle_tombstone_count"] == "1"


def test_package_generation_warns_on_sealed_contexts(tmp_path):
    ChronicleService(tmp_path).init("Lifecycle Seal Package Test")
    _append_context(
        tmp_path,
        Context(
            context_id="ctx_sealed",
            title="Sealed Context",
            summary="Sealed body remains advisory",
            scope=ContextScope.TASK,
            created_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
        ),
    )
    LifecycleService(tmp_path).record(
        action=LifecycleAction.SEAL,
        target_id="ctx_sealed",
        target_kind="context",
        actor="test",
        reason_class=LifecycleReasonClass.RETENTION,
        reason="test seal",
    )

    package = IntegrationPackageService(tmp_path).build_context_package(purpose="Lifecycle seal test")

    assert package.manifest.referenced_records == ["ctx_sealed"]
    assert package.records[0].record_id == "ctx_sealed"
    assert "lifecycle_sealed_record" in package.records[0].warnings
    assert "lifecycle_sealed_record" in package.manifest.warnings
