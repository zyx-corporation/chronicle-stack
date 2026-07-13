"""Transport-neutral external interaction models for Stage 2."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


_FORBIDDEN_METADATA_KEYS = {
    "authorization",
    "cookie",
    "password",
    "secret",
    "signature",
    "token",
    "webhook_secret",
}


class TransportIdentityEvidence(BaseModel):
    """Untrusted transport identity evidence, never a Chronicle actor mapping."""

    transport_subject: str
    display_label: str = ""
    verification_method: str = "mock"
    verified: bool = False


class TransportAttachmentRef(BaseModel):
    """Bounded attachment metadata; attachment bytes stay outside Chronicle events."""

    attachment_id: str
    media_type: str = "application/octet-stream"
    size_bytes: int = Field(ge=0)
    digest: str = ""
    external_ref: str = ""


class ExternalInteractionEnvelope(BaseModel):
    """Validated, transport-neutral message accepted by Chronicle."""

    schema_version: str = "external-interaction/v1"
    message_id: str
    transport: str
    received_at: datetime
    identity_evidence: TransportIdentityEvidence
    text: str = Field(min_length=1, max_length=100_000)
    attachments: list[TransportAttachmentRef] = Field(default_factory=list, max_length=32)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def reject_secret_metadata(cls, value: dict[str, Any]) -> dict[str, Any]:
        keys = {str(key).lower() for key in value}
        forbidden = sorted(keys & _FORBIDDEN_METADATA_KEYS)
        if forbidden:
            raise ValueError(f"secret-bearing metadata keys are forbidden: {', '.join(forbidden)}")
        return value

    @model_validator(mode="after")
    def reject_embedded_attachment_bytes(self) -> "ExternalInteractionEnvelope":
        for attachment in self.attachments:
            if attachment.external_ref.startswith("data:"):
                raise ValueError("embedded attachment bytes are forbidden")
        return self


class TransportReceipt(BaseModel):
    envelope: ExternalInteractionEnvelope
    event_id: str
    recorded_as: str = "user_input"
    command_executed: bool = False


class CommandPromotion(BaseModel):
    envelope_message_id: str
    requested_capability_id: str
    operator: str
    reason: str
    event_id: str
    execution_status: str = "not_executed"
    review_required: bool = True
