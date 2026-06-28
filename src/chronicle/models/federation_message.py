"""Federation message envelope models."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class FederationMessageType(StrEnum):
    PUBLISH_CHRONICLE = "publish_chronicle"
    REQUEST_CONTEXT = "request_context"
    GRANT_CONTEXT = "grant_context"
    DENY_CONTEXT = "deny_context"
    REVOKE_CONTEXT = "revoke_context"
    UPDATE_CHRONICLE = "update_chronicle"
    FORK_CHRONICLE = "fork_chronicle"
    REFERENCE_CHRONICLE = "reference_chronicle"
    OBJECT_CHRONICLE = "object_chronicle"
    AUDIT_CHRONICLE = "audit_chronicle"
    DECAY_NOTICE = "decay_notice"
    TRUST_ASSERTION = "trust_assertion"
    TRUST_WITHDRAWAL = "trust_withdrawal"


class FederationMessageBox(StrEnum):
    OUTBOX = "outbox"
    INBOX = "inbox"


class FederationMessageSignatureStatus(StrEnum):
    MANIFEST_SIGNATURE = "manifest_signature"
    UNSIGNED = "unsigned"
    UNKNOWN = "unknown"


class FederationMessagePolicy(BaseModel):
    retention: str = ""
    reshare: bool = False


class FederationMessageEnvelope(BaseModel):
    schema_version: str = "federation-message/v0.1"
    message_id: str
    message_type: FederationMessageType
    source_node: str
    target_node: str
    created_at: datetime
    purpose: str = ""
    object_refs: list[str] = Field(default_factory=list)
    expires_at: datetime | None = None
    signature_status: FederationMessageSignatureStatus = FederationMessageSignatureStatus.UNKNOWN
    policy: FederationMessagePolicy = Field(default_factory=FederationMessagePolicy)
    preview_only: bool = True
    auto_apply: bool = False
    review_required: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class FederationMessageRecord(BaseModel):
    envelope: FederationMessageEnvelope
    box: FederationMessageBox
    stored_at: datetime
    preview_summary: str = ""
    related_review_target_ids: list[str] = Field(default_factory=list)
    audit_recorded: bool = False
