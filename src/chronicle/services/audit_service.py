"""Audit service for high-risk derived operations."""

from datetime import datetime, timezone
from pathlib import Path

from chronicle.ids import generate_id
from chronicle.models.audit import AuditEvent, AuditOperation, AuditSeverity, AuditTargetEnvironment
from chronicle.services.chronicle_service import ChronicleService
from chronicle.store.audit_log_store import AuditLogStore


class AuditService:
    """Append and read operational audit events.

    Audit events record operational facts such as export, model-context use,
    and reinterpretation. They must not be confused with original Chronicle
    records.
    """

    def __init__(self, root: Path | None = None) -> None:
        self.chronicle = ChronicleService(root)
        self.store = AuditLogStore(self.chronicle.paths.audit_file)

    def record(
        self,
        *,
        operation: AuditOperation,
        actor: str = "unknown",
        purpose: str = "",
        target_environment: AuditTargetEnvironment = AuditTargetEnvironment.UNKNOWN,
        target_layer: int | None = None,
        output_classification: str = "unknown",
        referenced_records: list[str] | None = None,
        source_event_id: str | None = None,
        result: AuditSeverity = AuditSeverity.INFO,
        summary: str = "",
        metadata: dict[str, str] | None = None,
    ) -> AuditEvent:
        chronicle_metadata = self.chronicle.require_initialized()
        event = AuditEvent(
            audit_id=generate_id("audit"),
            chronicle_id=chronicle_metadata.chronicle_id,
            created_at=datetime.now(timezone.utc).astimezone(),
            operation=operation,
            actor=actor,
            purpose=purpose,
            target_environment=target_environment,
            target_layer=target_layer,
            output_classification=output_classification,
            referenced_records=referenced_records or [],
            source_event_id=source_event_id,
            result=result,
            summary=summary,
            metadata=metadata or {},
        )
        self.store.append(event)
        return event

    def list_events(self) -> list[AuditEvent]:
        self.chronicle.require_initialized()
        return self.store.read_all()

    def count_corrupt_lines(self) -> int:
        self.chronicle.require_initialized()
        return self.store.count_corrupt_lines()
