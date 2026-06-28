from datetime import datetime, timezone

from chronicle.models.context import Context, ContextScope
from chronicle.models.federation_package import FederationPackageSignatureMode, FederationPackageSignatureStatus
from chronicle.models.event import Actor, ChronicleEvent, EventType
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.federation_package_service import FederationPackageService


def _append_context(root, context: Context) -> None:
    service = ChronicleService(root)
    metadata = service.load_metadata()
    event = ChronicleEvent(
        event_id=f"evt_{context.context_id}",
        chronicle_id=metadata.chronicle_id,
        timestamp=datetime(2026, 6, 28, tzinfo=timezone.utc),
        event_type=EventType.CONTEXT_ADDED,
        actor=Actor.USER,
        summary=f"Add {context.title}",
        payload={"context": context.model_dump(mode="json")},
    )
    service.append_event(event)
    service.rebuild_indexes()


def test_federation_package_create_and_verify(tmp_path):
    ChronicleService(tmp_path).init("Federation Package Test")
    _append_context(
        tmp_path,
        Context(
            context_id="ctx_fed_pkg",
            title="Federation Package Context",
            summary="Shareable review context",
            scope=ContextScope.TASK,
            created_at=datetime(2026, 6, 28, tzinfo=timezone.utc),
        ),
    )

    output_dir = tmp_path / "federation-package"
    manifest = FederationPackageService(tmp_path).create_package(
        purpose="partner review",
        target_node="node:partner:beta",
        output_dir=output_dir,
    )

    assert manifest.target_node == "node:partner:beta"
    assert (output_dir / "manifest.json").exists()
    assert (output_dir / "records.jsonl").exists()
    assert (output_dir / "redaction-report.json").exists()

    report = FederationPackageService(tmp_path).verify_package(output_dir)
    assert report.valid is True
    assert report.signature_status == FederationPackageSignatureStatus.UNSIGNED
    assert report.warnings == ["signature_unsigned"]


def test_federation_package_create_with_local_dev_signature_verifies_signed(tmp_path):
    ChronicleService(tmp_path).init("Federation Package Signed Test")
    _append_context(
        tmp_path,
        Context(
            context_id="ctx_fed_signed",
            title="Federation Signed Context",
            summary="Signed shareable review context",
            scope=ContextScope.TASK,
            created_at=datetime(2026, 6, 28, tzinfo=timezone.utc),
        ),
    )

    output_dir = tmp_path / "federation-package"
    manifest = FederationPackageService(tmp_path).create_package(
        purpose="partner review",
        target_node="node:partner:beta",
        output_dir=output_dir,
        signature_mode=FederationPackageSignatureMode.LOCAL_DEV,
    )

    assert manifest.signature.status == FederationPackageSignatureStatus.SIGNED
    assert manifest.signature.value

    report = FederationPackageService(tmp_path).verify_package(output_dir)
    assert report.valid is True
    assert report.signature_status == FederationPackageSignatureStatus.SIGNED
    assert report.warnings == []


def test_federation_package_verify_detects_tampering(tmp_path):
    ChronicleService(tmp_path).init("Federation Package Verify Test")
    _append_context(
        tmp_path,
        Context(
            context_id="ctx_fed_verify",
            title="Federation Verify Context",
            summary="Original content",
            scope=ContextScope.TASK,
            created_at=datetime(2026, 6, 28, tzinfo=timezone.utc),
        ),
    )

    output_dir = tmp_path / "federation-package"
    FederationPackageService(tmp_path).create_package(
        purpose="partner review",
        target_node="node:partner:beta",
        output_dir=output_dir,
    )
    records_path = output_dir / "records.jsonl"
    records_path.write_text(records_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    report = FederationPackageService(tmp_path).verify_package(output_dir)
    assert report.valid is False
    changed = next(item for item in report.files_checked if item.path == "records.jsonl")
    assert changed.exists is True
    assert changed.matches is False


def test_federation_package_verify_detects_signature_mismatch(tmp_path):
    ChronicleService(tmp_path).init("Federation Package Signature Mismatch Test")
    _append_context(
        tmp_path,
        Context(
            context_id="ctx_fed_sig_mismatch",
            title="Federation Signature Mismatch Context",
            summary="Signed content that will be modified",
            scope=ContextScope.TASK,
            created_at=datetime(2026, 6, 28, tzinfo=timezone.utc),
        ),
    )

    output_dir = tmp_path / "federation-package"
    FederationPackageService(tmp_path).create_package(
        purpose="partner review",
        target_node="node:partner:beta",
        output_dir=output_dir,
        signature_mode=FederationPackageSignatureMode.LOCAL_DEV,
    )
    manifest_path = output_dir / "manifest.json"
    payload = manifest_path.read_text(encoding="utf-8").replace("partner review", "tampered review", 1)
    manifest_path.write_text(payload, encoding="utf-8")

    report = FederationPackageService(tmp_path).verify_package(output_dir)
    assert report.valid is False
    assert report.signature_status == FederationPackageSignatureStatus.MISMATCH
    assert report.warnings == ["signature_mismatch"]


def test_federation_package_verify_detects_expired_signature(tmp_path):
    ChronicleService(tmp_path).init("Federation Package Signature Expired Test")
    _append_context(
        tmp_path,
        Context(
            context_id="ctx_fed_sig_expired",
            title="Federation Signature Expired Context",
            summary="Expired signature content",
            scope=ContextScope.TASK,
            created_at=datetime(2026, 6, 28, tzinfo=timezone.utc),
        ),
    )

    output_dir = tmp_path / "federation-package"
    FederationPackageService(tmp_path).create_package(
        purpose="partner review",
        target_node="node:partner:beta",
        output_dir=output_dir,
        signature_mode=FederationPackageSignatureMode.LOCAL_DEV,
        signature_expires_at=datetime(2026, 6, 27, tzinfo=timezone.utc),
    )

    report = FederationPackageService(tmp_path).verify_package(output_dir)
    assert report.valid is False
    assert report.signature_status == FederationPackageSignatureStatus.EXPIRED
    assert report.warnings == ["signature_expired"]


def test_federation_package_verify_detects_revoked_signature(tmp_path):
    ChronicleService(tmp_path).init("Federation Package Signature Revoked Test")
    _append_context(
        tmp_path,
        Context(
            context_id="ctx_fed_sig_revoked",
            title="Federation Signature Revoked Context",
            summary="Revoked signature content",
            scope=ContextScope.TASK,
            created_at=datetime(2026, 6, 28, tzinfo=timezone.utc),
        ),
    )

    output_dir = tmp_path / "federation-package"
    manifest = FederationPackageService(tmp_path).create_package(
        purpose="partner review",
        target_node="node:partner:beta",
        output_dir=output_dir,
        signature_mode=FederationPackageSignatureMode.LOCAL_DEV,
        signature_revoked=True,
        signature_revocation_reason="review window closed",
    )

    assert manifest.signature.revocation_reason == "review window closed"

    report = FederationPackageService(tmp_path).verify_package(output_dir)
    assert report.valid is False
    assert report.signature_status == FederationPackageSignatureStatus.REVOKED
    assert report.warnings == ["signature_revoked"]


def test_federation_package_inspect_returns_manifest_and_redaction_report(tmp_path):
    ChronicleService(tmp_path).init("Federation Package Inspect Test")
    _append_context(
        tmp_path,
        Context(
            context_id="ctx_fed_inspect",
            title="Federation Inspect Context",
            summary="Inspectable content",
            scope=ContextScope.TASK,
            created_at=datetime(2026, 6, 28, tzinfo=timezone.utc),
        ),
    )
    output_dir = tmp_path / "federation-package"
    FederationPackageService(tmp_path).create_package(
        purpose="inspect review",
        target_node="node:partner:beta",
        output_dir=output_dir,
    )

    payload = FederationPackageService(tmp_path).inspect_package(output_dir)
    assert payload["manifest"]["target_node"] == "node:partner:beta"
    assert payload["manifest"]["signature"]["status"] == FederationPackageSignatureStatus.UNSIGNED
    assert payload["redaction_report"]["advisory_only"] is True
    assert payload["redaction_report"]["record_count"] == 1
