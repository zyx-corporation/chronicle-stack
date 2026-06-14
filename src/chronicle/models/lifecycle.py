"""Lifecycle event model for redact / seal / tombstone workflows."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class LifecycleAction(StrEnum):
    """Lifecycle actions for records and derived artifacts."""

    REDACT = "redact"
    SEAL = "seal"
    EXPIRE = "expire"
    TOMBSTONE = "tombstone"
    HARD_DELETE = "hard_delete"


class LifecycleReasonClass(StrEnum):
    """Reason category for a lifecycle event."""

    PRIVACY = "privacy"
    LEGAL = "legal"
    SAFETY = "safety"
    SECRET = "secret"
    USER_REQUEST = "user_request"
    RETENTION = "retention"
    ERROR_CORRECTION = "error_correction"
    OTHER = "other"


class LifecycleVisibility(StrEnum):
    """How much detail should remain visible after the lifecycle action."""

    FULL = "full"
    SUMMARY_ONLY = "summary_only"
    TOMBSTONE_ONLY = "tombstone_only"
    HIDDEN = "hidden"


class LifecycleEvent(BaseModel):
    """Append-only lifecycle event.

    LifecycleEvent records a redact / seal / tombstone / deletion decision. It
    does not mutate the original Chronicle record by itself.
    """

    lifecycle_id: str
    chronicle_id: str
    created_at: datetime
    action: LifecycleAction
    target_id: str
    target_kind: str = "unknown"
    actor: str = "unknown"
    reason_class: LifecycleReasonClass = LifecycleReasonClass.OTHER
    reason: str = ""
    replacement_ref: str | None = None
    visible_detail_level: LifecycleVisibility = LifecycleVisibility.TOMBSTONE_ONLY
    preserve_tombstone: bool = True
    metadata: dict[str, str] = Field(default_factory=dict)

    def to_jsonl(self) -> str:
        """Serialize as one JSONL line."""
        return self.model_dump_json(exclude_none=True)
