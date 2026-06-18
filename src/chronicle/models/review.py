"""Append-only human review workflow models."""

from enum import StrEnum

from pydantic import BaseModel, Field


class ReviewDisposition(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_CHANGES = "request_changes"


class ReviewerIdentityKind(StrEnum):
    USER_DECLARED = "user_declared"
    LOCAL_OPERATOR = "local_operator"


class ReviewerAuthMode(StrEnum):
    NONE = "none"
    LOOPBACK_LOCAL = "loopback_local"


class ReviewerIdentity(BaseModel):
    label: str
    kind: ReviewerIdentityKind = ReviewerIdentityKind.USER_DECLARED
    auth_mode: ReviewerAuthMode = ReviewerAuthMode.NONE
    session_label: str | None = None


class ReviewDecisionResult(BaseModel):
    target_event_id: str
    disposition: ReviewDisposition
    reviewer: str
    reviewer_identity: ReviewerIdentity
    note: str | None = None
    recorded: bool = True
    review_event_id: str
    audit_id: str | None = None


class ReviewQueueEntry(BaseModel):
    target_event_id: str
    target_summary: str
    target_event_type: str
    review_status: str
    pending: bool
    review_kind: str = "assistant_output"
    latest_disposition: ReviewDisposition | None = None
    latest_reviewer: str | None = None
    latest_reviewer_identity: ReviewerIdentity | None = None
    latest_note: str | None = None
    latest_review_event_id: str | None = None
    latest_audit_id: str | None = None
    history_count: int = 0
    available_actions: list[str] = Field(default_factory=list)


class ReviewHistoryEntry(BaseModel):
    review_event_id: str
    audit_id: str | None = None
    disposition: ReviewDisposition
    reviewer: str
    reviewer_identity: ReviewerIdentity
    note: str | None = None
    reviewed_at: str
    audit_summary: str | None = None
