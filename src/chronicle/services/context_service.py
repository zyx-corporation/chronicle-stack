"""Context management service."""

from datetime import datetime, timezone
from pathlib import Path

from chronicle.ids import generate_id
from chronicle.models.context import Confidence, Context, ContextScope, ScopeHint
from chronicle.models.event import Actor, EventType
from chronicle.models.visibility import VisibilityHint
from chronicle.services.chronicle_service import ChronicleService


class ContextService:
    def __init__(self, root: Path | None = None) -> None:
        self.chronicle = ChronicleService(root)

    def add_context(
        self,
        title: str,
        summary: str = "",
        source_type: str = "conversation",
        source_ref: str = "",
        scope: ContextScope = ContextScope.PROJECT,
        visibility_hint: VisibilityHint = VisibilityHint.UNKNOWN,
        confidence: Confidence = Confidence.MEDIUM,
        tags: list[str] | None = None,
    ) -> Context:
        self.chronicle.require_initialized()
        now = datetime.now(timezone.utc).astimezone()
        context = Context(
            context_id=generate_id("context"),
            title=title,
            summary=summary,
            source_type=source_type,
            source_ref=source_ref,
            scope=scope,
            scope_hint=ScopeHint(scope.value),
            visibility_hint=visibility_hint,
            confidence=confidence,
            created_at=now,
            tags=tags or [],
        )
        self.chronicle.record_event(
            event_type=EventType.CONTEXT_ADDED,
            actor=Actor.USER,
            summary=f"Context added: {title}",
            payload={"context": context.model_dump(mode="json")},
            context_ids=[context.context_id],
        )
        self.chronicle.rebuild_indexes()
        return context
