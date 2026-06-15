"""Context management service."""

import hashlib
from datetime import datetime, timezone
from pathlib import Path

from chronicle.ids import generate_id
from chronicle.models.classification import ClassificationLayer, ClassificationMetadata, Sensitivity
from chronicle.models.context import Confidence, Context, ContextScope, ScopeHint
from chronicle.models.event import Actor, EventType
from chronicle.models.source import SourceProvenance
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
        source: SourceProvenance | None = None,
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
            source=source,
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

    def classify_context(
        self,
        *,
        context_id: str,
        layer: ClassificationLayer,
        sensitivity: Sensitivity,
        owner: str = "",
        reason: str = "",
    ) -> Context:
        """Attach advisory classification metadata to a Context.

        This records a new Context snapshot with the same context_id so the
        derived context index resolves to the latest classified version. It does
        not implement access control or mutate earlier primary events.
        """
        self.chronicle.require_initialized()
        self.chronicle.rebuild_indexes()
        contexts = self.chronicle.index.load_contexts()
        if context_id not in contexts:
            raise ValueError(f"Context not found: {context_id}")

        context = contexts[context_id].model_copy(deep=True)
        now = datetime.now(timezone.utc).astimezone()
        digest = hashlib.sha256(
            f"{context.context_id}\n{context.title}\n{context.summary}\n{layer.value}\n{sensitivity.value}".encode("utf-8")
        ).hexdigest()
        context.classification = ClassificationMetadata(
            layer=layer,
            sensitivity=sensitivity,
            owner=owner,
            created_at=now,
            source_type="manual",
            source_refs=[reason] if reason else [],
        )
        context.classification.integrity.hash = digest
        if reason and reason not in context.tags:
            context.tags.append("classified")

        self.chronicle.record_event(
            event_type=EventType.CONTEXT_ADDED,
            actor=Actor.USER,
            summary=f"Context classified: {context.title}",
            payload={"context": context.model_dump(mode="json")},
            context_ids=[context.context_id],
        )
        self.chronicle.rebuild_indexes()
        return context

    def list_missing_classification(self) -> list[Context]:
        """Return Context records without advisory classification metadata."""
        self.chronicle.require_initialized()
        self.chronicle.rebuild_indexes()
        contexts = self.chronicle.index.load_contexts()
        return sorted(
            (context for context in contexts.values() if context.classification is None),
            key=lambda context: context.context_id,
        )

    def get_context(self, context_id: str) -> Context:
        """Return a Context from the derived index."""
        self.chronicle.require_initialized()
        self.chronicle.rebuild_indexes()
        contexts = self.chronicle.index.load_contexts()
        if context_id not in contexts:
            raise ValueError(f"Context not found: {context_id}")
        return contexts[context_id]
