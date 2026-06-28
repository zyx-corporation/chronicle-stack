"""Federation message queue service for Phase 5."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from chronicle.errors import ChronicleError
from chronicle.ids import generate_id
from chronicle.models.audit import AuditOperation, AuditSeverity, AuditTargetEnvironment
from chronicle.models.federation_message import (
    FederationMessageBox,
    FederationMessageEnvelope,
    FederationMessagePolicy,
    FederationMessageRecord,
    FederationMessageSignatureStatus,
    FederationMessageType,
)
from chronicle.services.audit_service import AuditService
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.trust_service import TrustService
from chronicle.store.federation_message_store import FederationMessageStore


class FederationMessageNotFoundError(ChronicleError):
    def __init__(self, box: FederationMessageBox, message_id: str) -> None:
        super().__init__(
            code="FEDERATION_MESSAGE_NOT_FOUND",
            message=f"Federation message not found in {box.value}: {message_id}",
            hint="Use `chronicle federation inbox inspect --json` or the matching outbox inspect command to list available message ids.",
        )


class FederationMessageService:
    def __init__(self, root: Path | None = None) -> None:
        self.chronicle = ChronicleService(root)
        self.store = FederationMessageStore(self.chronicle.paths)
        self.audit = AuditService(root)
        self.trust = TrustService(root)

    def create_message(
        self,
        *,
        message_type: FederationMessageType | str,
        source_node: str,
        target_node: str,
        purpose: str,
        object_refs: list[str] | None = None,
        retention: str = "",
        reshare: bool = False,
        signature_status: FederationMessageSignatureStatus | str = FederationMessageSignatureStatus.UNSIGNED,
        expires_at: datetime | None = None,
        box: FederationMessageBox | str = FederationMessageBox.OUTBOX,
        metadata: dict[str, str] | None = None,
    ) -> FederationMessageRecord:
        self.chronicle.require_initialized()
        message_type = FederationMessageType(message_type)
        signature_status = FederationMessageSignatureStatus(signature_status)
        box = FederationMessageBox(box)
        envelope = FederationMessageEnvelope(
            message_id=generate_id("message"),
            message_type=message_type,
            source_node=source_node,
            target_node=target_node,
            created_at=datetime.now(timezone.utc).astimezone(),
            purpose=purpose,
            object_refs=object_refs or [],
            expires_at=expires_at,
            signature_status=signature_status,
            policy=FederationMessagePolicy(retention=retention, reshare=reshare),
            preview_only=True,
            auto_apply=False,
            review_required=True,
            metadata={
                **(metadata or {}),
                "trust_summary": self.trust.summarize_for_target(
                    target_node=target_node,
                    purpose=purpose,
                ).model_dump(mode="json"),
            },
        )
        record = FederationMessageRecord(
            envelope=envelope,
            box=box,
            stored_at=datetime.now(timezone.utc).astimezone(),
            preview_summary=self._preview_summary(envelope, box=box),
            audit_recorded=False,
        )
        self.store.save(record)
        if box == FederationMessageBox.INBOX and message_type in {
            FederationMessageType.REVOKE_CONTEXT,
            FederationMessageType.DECAY_NOTICE,
        }:
            self._record_revoke_or_decay_audit(record)
            record.audit_recorded = True
            self.store.save(record)
        return record

    def inspect_box(self, box: FederationMessageBox) -> list[FederationMessageRecord]:
        self.chronicle.require_initialized()
        rows = self.store.list(box)
        return sorted(rows, key=lambda item: item.envelope.created_at, reverse=True)

    def get_message(self, box: FederationMessageBox, message_id: str) -> FederationMessageRecord:
        self.chronicle.require_initialized()
        try:
            return self.store.load(box, message_id)
        except FileNotFoundError as exc:
            raise FederationMessageNotFoundError(box, message_id) from exc

    def _preview_summary(
        self,
        envelope: FederationMessageEnvelope,
        *,
        box: FederationMessageBox,
    ) -> str:
        return (
            f"{box.value} preview-only federation message "
            f"{envelope.message_type.value} for {envelope.target_node}; "
            "no automatic import or local primary-record mutation occurs."
        )

    def _record_revoke_or_decay_audit(self, record: FederationMessageRecord) -> None:
        envelope = record.envelope
        self.audit.record(
            operation=AuditOperation.REINTERPRET,
            actor="federation-message-service",
            purpose=envelope.purpose,
            target_environment=AuditTargetEnvironment.FILE,
            referenced_records=envelope.object_refs,
            result=AuditSeverity.INFO,
            summary=(
                f"Received {envelope.message_type.value} federation message for preview/review only."
            ),
            metadata={
                "message_id": envelope.message_id,
                "message_type": envelope.message_type.value,
                "box": record.box.value,
                "source_node": envelope.source_node,
                "target_node": envelope.target_node,
                "preview_only": str(envelope.preview_only).lower(),
                "review_required": str(envelope.review_required).lower(),
            },
        )
