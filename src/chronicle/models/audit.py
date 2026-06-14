"""Audit event model for high-risk derived operations."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class AuditOperation(StrEnum):
    """Operations that should be visible in the audit surface."""

    EXPORT = "export"
    CONTEXT_USE = "context_use"
    REINTERPRET = "reinterpret"


class AuditTargetEnvironment(StrEnum):
    """Target environment for an audited operation."""

    LOCAL = "local"
    EXTERNAL = "external"
    FILE = "file"
    PACKAGE = "package"
    UNKNOWN = "unknown"


class AuditSeverity(StrEnum):
    """Severity recorded with an audit event."""

    INFO = "info"
    WARNING = "warning"
    BLOCKED = "blocked"


class AuditEvent(BaseModel):
    """Append-only audit event for derived operations.

    AuditEvent records the fact that an operation occurred or was checked. It
    must not store redacted/deleted secret content by default.
    """

    audit_id: str
    chronicle_id: str
    created_at: datetime
    operation: AuditOperation
    actor: str = "unknown"
    purpose: str = ""
    target_environment: AuditTargetEnvironment = AuditTargetEnvironment.UNKNOWN
    target_layer: int | None = None
    output_classification: str = "unknown"
    referenced_records: list[str] = Field(default_factory=list)
    source_event_id: str | None = None
    result: AuditSeverity = AuditSeverity.INFO
    summary: str = ""
    metadata: dict[str, str] = Field(default_factory=dict)

    def to_jsonl(self) -> str:
        """Serialize as one JSONL line."""
        return self.model_dump_json(exclude_none=True)
