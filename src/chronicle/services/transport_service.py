"""Safe recording and explicit command promotion for external interactions."""

from __future__ import annotations

from pathlib import Path

from chronicle.models.event import Actor, Confidence, EventType, ReviewStatus
from chronicle.models.source import SourceProvenance
from chronicle.models.transport import (
    CommandPromotion,
    ExternalInteractionEnvelope,
    TransportReceipt,
)
from chronicle.services.capability_registry_service import CapabilityRegistryService
from chronicle.services.chronicle_service import ChronicleService


class ExternalInteractionService:
    """Accept external messages without treating them as executable commands."""

    def __init__(self, root: Path | None = None) -> None:
        self.chronicle = ChronicleService(root)
        self.capabilities = CapabilityRegistryService()

    def record_user_input(self, envelope: ExternalInteractionEnvelope) -> TransportReceipt:
        event = self.chronicle.record_event(
            event_type=EventType.USER_INPUT,
            actor=Actor.IMPORTER,
            summary=f"External input received via {envelope.transport}",
            payload={
                "external_interaction": envelope.model_dump(mode="json"),
                "transport_identity_is_actor": False,
                "command_executed": False,
            },
            source=SourceProvenance(
                source_type="external_transport",
                source_ref=envelope.message_id,
                source_tool=envelope.transport,
            ),
            confidence=Confidence.UNKNOWN,
            review_status=ReviewStatus.NEEDS_REVIEW,
            tags=["external-input", "transport-envelope"],
        )
        return TransportReceipt(envelope=envelope, event_id=event.event_id)

    def promote_command_candidate(
        self,
        *,
        receipt: TransportReceipt,
        capability_id: str,
        operator: str,
        reason: str,
    ) -> CommandPromotion:
        """Record explicit operator intent without executing the capability."""

        self.capabilities.get_capability(capability_id)
        event = self.chronicle.record_event(
            event_type=EventType.ASSISTANT_OUTPUT,
            actor=Actor.USER,
            summary=f"External input promoted for review: {capability_id}",
            parent_event_id=receipt.event_id,
            payload={
                "external_command_promotion": {
                    "envelope_message_id": receipt.envelope.message_id,
                    "requested_capability_id": capability_id,
                    "operator": operator,
                    "reason": reason,
                    "execution_status": "not_executed",
                }
            },
            review_status=ReviewStatus.NEEDS_REVIEW,
            confidence=Confidence.UNKNOWN,
            tags=["external-input", "command-promotion", "preview-only"],
        )
        return CommandPromotion(
            envelope_message_id=receipt.envelope.message_id,
            requested_capability_id=capability_id,
            operator=operator,
            reason=reason,
            event_id=event.event_id,
        )


class MockTransportAdapter:
    """Deterministic adapter used to validate the transport boundary."""

    def __init__(self, service: ExternalInteractionService) -> None:
        self.service = service

    def deliver(self, envelope: ExternalInteractionEnvelope) -> TransportReceipt:
        return self.service.record_user_input(envelope)
