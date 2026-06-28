"""Meaningful reaction service for the Context SNS surface."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from chronicle.errors import ChronicleError
from chronicle.ids import generate_id
from chronicle.models.event import Actor, ChronicleEvent, EventType
from chronicle.models.reaction import ChronicleReactionRecord, ChronicleReactionType
from chronicle.services.chronicle_service import ChronicleService


class ChronicleReactionNotFoundError(ChronicleError):
    def __init__(self, reaction_id: str) -> None:
        super().__init__(
            code="CHRONICLE_REACTION_NOT_FOUND",
            message=f"Chronicle reaction not found: {reaction_id}",
            hint="Run `chronicle reaction list` or inspect `/api/reactions` to see available reactions.",
        )


class ReactionService:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path.cwd()
        self.chronicle = ChronicleService(self.root)

    def record(
        self,
        *,
        reaction_type: ChronicleReactionType,
        created_by: str,
        target_object_id: str,
        summary: str,
        detail: str = "",
        source_object_id: str | None = None,
        target_context_id: str | None = None,
        target_artifact_id: str | None = None,
        target_decision_id: str | None = None,
        related_object_ids: list[str] | None = None,
        metadata: dict[str, str] | None = None,
    ) -> ChronicleReactionRecord:
        chronicle = self.chronicle.require_initialized()
        now = datetime.now(timezone.utc).astimezone()
        reaction = ChronicleReactionRecord(
            reaction_id=generate_id("reaction"),
            chronicle_id=chronicle.chronicle_id,
            reaction_type=reaction_type,
            created_at=now,
            created_by=created_by,
            target_object_id=target_object_id,
            source_object_id=source_object_id,
            target_context_id=target_context_id,
            target_artifact_id=target_artifact_id,
            target_decision_id=target_decision_id,
            summary=summary,
            detail=detail,
            related_object_ids=related_object_ids or [],
            metadata=metadata or {},
        )
        event = ChronicleEvent(
            event_id=generate_id("event"),
            chronicle_id=chronicle.chronicle_id,
            timestamp=now,
            event_type=EventType.CHRONICLE_REACTION_RECORDED,
            actor=Actor.USER,
            summary=summary,
            payload={"chronicle_reaction": reaction.model_dump(mode="json")},
            artifact_id=target_artifact_id,
            context_ids=[target_context_id] if target_context_id else [],
            decision_id=target_decision_id,
        )
        self.chronicle.append_event(event)
        return reaction

    def list_reactions(self) -> list[ChronicleReactionRecord]:
        self.chronicle.require_initialized()
        rows: list[ChronicleReactionRecord] = []
        for event in self.chronicle.jsonl.read_all():
            if event.event_type != EventType.CHRONICLE_REACTION_RECORDED:
                continue
            payload = event.payload.get("chronicle_reaction")
            if isinstance(payload, dict):
                rows.append(ChronicleReactionRecord.model_validate(payload))
        return sorted(rows, key=lambda item: (item.created_at, item.reaction_id))

    def get(self, reaction_id: str) -> ChronicleReactionRecord:
        for reaction in self.list_reactions():
            if reaction.reaction_id == reaction_id:
                return reaction
        raise ChronicleReactionNotFoundError(reaction_id)

