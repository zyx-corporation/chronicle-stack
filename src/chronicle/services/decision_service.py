"""Decision recording service."""

from datetime import datetime, timezone
from pathlib import Path

from chronicle.errors import ArtifactNotFoundError, DecisionTargetNotFoundError
from chronicle.ids import generate_id
from chronicle.models.decision import Decision, DecisionType
from chronicle.models.event import Actor, ChronicleEvent, EventType
from chronicle.services.artifact_service import ArtifactService
from chronicle.services.chronicle_service import ChronicleService


class DecisionService:
    def __init__(self, root: Path | None = None) -> None:
        self.chronicle = ChronicleService(root)
        self.artifacts = ArtifactService(root)

    def record(
        self,
        decision_type: DecisionType,
        reason: str = "",
        artifact_id: str | None = None,
        decided_by: str = "user",
        alternatives: list[str] | None = None,
        notes: str = "",
    ) -> Decision:
        metadata = self.chronicle.require_initialized()
        if artifact_id:
            try:
                self.artifacts.get(artifact_id)
            except ArtifactNotFoundError as exc:
                raise DecisionTargetNotFoundError(artifact_id) from exc

        now = datetime.now(timezone.utc).astimezone()
        event_id = generate_id("event")
        decision = Decision(
            decision_id=generate_id("decision"),
            chronicle_id=metadata.chronicle_id,
            artifact_id=artifact_id,
            event_id=event_id,
            decision_type=decision_type,
            decided_by=decided_by,
            decided_at=now,
            reason=reason,
            alternatives=alternatives or [],
            notes=notes,
        )

        event = ChronicleEvent(
            event_id=event_id,
            chronicle_id=metadata.chronicle_id,
            timestamp=now,
            event_type=EventType.DECISION_RECORDED,
            actor=Actor.USER,
            summary=f"Decision recorded: {decision_type.value}",
            payload={"decision": decision.model_dump(mode="json")},
            artifact_id=artifact_id,
            decision_id=decision.decision_id,
        )
        self.chronicle.append_event(event)
        self.chronicle.rebuild_indexes()
        return decision
