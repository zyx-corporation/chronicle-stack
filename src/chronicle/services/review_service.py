"""Append-only review workflow service."""

from datetime import datetime, timezone
from pathlib import Path

from chronicle.errors import ChronicleError
from chronicle.ids import generate_id
from chronicle.models.audit import AuditOperation, AuditSeverity, AuditTargetEnvironment
from chronicle.models.event import Actor, ChronicleEvent, EventType
from chronicle.models.review import (
    ReviewDecisionResult,
    ReviewDisposition,
    ReviewHistoryEntry,
    ReviewQueueEntry,
    ReviewerAuthMode,
    ReviewerIdentity,
    ReviewerIdentityKind,
)
from chronicle.models.source import SourceProvenance
from chronicle.services.audit_service import AuditService
from chronicle.services.chronicle_service import ChronicleService


def review_action_commands(
    event_id: str,
    *,
    reviewer_hint: str = "<name>",
    note_hint: str = "<reason>",
) -> list[dict[str, str]]:
    """Return canonical CLI command previews for review actions."""
    return [
        {
            "action": "approve",
            "label": "Approve",
            "command": f"chronicle review approve --event {event_id} --reviewer {reviewer_hint}",
        },
        {
            "action": "reject",
            "label": "Reject",
            "command": f"chronicle review reject --event {event_id} --reviewer {reviewer_hint} --note {note_hint}",
        },
        {
            "action": "request_changes",
            "label": "Request Changes",
            "command": f"chronicle review request-changes --event {event_id} --reviewer {reviewer_hint} --note {note_hint}",
        },
    ]


class ReviewTargetNotFoundError(ChronicleError):
    def __init__(self, event_id: str) -> None:
        super().__init__(
            code="REVIEW_TARGET_NOT_FOUND",
            message=f"Review target event not found: {event_id}",
            hint="Use `chronicle review queue` to list pending review targets.",
        )


class ReviewAuditInsertionError(ChronicleError):
    def __init__(self, event_id: str, detail: str) -> None:
        super().__init__(
            code="REVIEW_AUDIT_INSERTION_FAILED",
            message=f"Audit insertion failed for review target: {event_id}",
            hint=detail,
        )


class ReviewDecisionPersistenceError(ChronicleError):
    def __init__(self, event_id: str, detail: str, audit_id: str | None = None) -> None:
        super().__init__(
            code="REVIEW_DECISION_PERSISTENCE_FAILED",
            message=f"Review decision persistence failed for target: {event_id}",
            hint=detail,
        )
        self.audit_id = audit_id


class ReviewService:
    """Manage append-only review decisions over Chronicle events."""

    def __init__(self, root: Path | None = None) -> None:
        self.chronicle = ChronicleService(root)
        self.audit = AuditService(root)

    def queue(self, *, include_resolved: bool = False) -> list[ReviewQueueEntry]:
        self.chronicle.require_initialized()
        events = self.chronicle.jsonl.read_all()
        latest_reviews = self._latest_reviews(events)
        grouped_reviews = self._group_reviews(events)
        rows: list[ReviewQueueEntry] = []
        for event in reversed(events):
            if getattr(event.review_status, "value", None) != "needs_review":
                continue
            latest_review = latest_reviews.get(event.event_id)
            pending = latest_review is None or latest_review.payload["disposition"] == ReviewDisposition.REQUEST_CHANGES.value
            if not include_resolved and not pending:
                continue
            rows.append(
                ReviewQueueEntry(
                    target_event_id=event.event_id,
                    target_summary=event.summary,
                    target_event_type=event.event_type.value,
                    review_status=getattr(event.review_status, "value", ""),
                    pending=pending,
                    review_kind=self._review_kind(event.payload),
                    latest_disposition=(
                        ReviewDisposition(latest_review.payload["disposition"])
                        if latest_review is not None
                        else None
                    ),
                    latest_reviewer=latest_review.payload.get("reviewer") if latest_review is not None else None,
                    latest_reviewer_identity=(
                        ReviewerIdentity.model_validate(latest_review.payload["reviewer_identity"])
                        if latest_review is not None and "reviewer_identity" in latest_review.payload
                        else None
                    ),
                    latest_note=latest_review.payload.get("note") if latest_review is not None else None,
                    latest_review_event_id=latest_review.event_id if latest_review is not None else None,
                    latest_audit_id=latest_review.payload.get("audit_id") if latest_review is not None else None,
                    history_count=len(grouped_reviews.get(event.event_id, [])),
                    available_actions=[
                        action["command"] for action in review_action_commands(event.event_id)
                    ],
                )
            )
        return rows

    def history(self, *, event_id: str) -> list[ReviewHistoryEntry]:
        target = self._target_event(event_id)
        events = self.chronicle.jsonl.read_all()
        grouped_reviews = self._group_reviews(events)
        audit_by_id = {audit.audit_id: audit for audit in self.audit.list_events()}
        rows: list[ReviewHistoryEntry] = []
        for review_event in grouped_reviews.get(target.event_id, []):
            audit_id = review_event.payload.get("audit_id")
            audit_event = audit_by_id.get(audit_id) if isinstance(audit_id, str) else None
            rows.append(
                ReviewHistoryEntry(
                    review_event_id=review_event.event_id,
                    audit_id=audit_id if isinstance(audit_id, str) else None,
                    disposition=ReviewDisposition(review_event.payload["disposition"]),
                    reviewer=review_event.payload["reviewer"],
                    reviewer_identity=ReviewerIdentity.model_validate(
                        review_event.payload.get(
                            "reviewer_identity",
                            {
                                "label": review_event.payload["reviewer"],
                                "kind": ReviewerIdentityKind.USER_DECLARED.value,
                                "auth_mode": ReviewerAuthMode.NONE.value,
                            },
                        )
                    ),
                    note=review_event.payload.get("note"),
                    reviewed_at=review_event.timestamp.isoformat(),
                    audit_summary=audit_event.summary if audit_event is not None else None,
                )
            )
        return rows

    def approve(
        self,
        *,
        event_id: str,
        reviewer: str,
        reviewer_kind: ReviewerIdentityKind = ReviewerIdentityKind.USER_DECLARED,
        session_label: str | None = None,
        note: str | None = None,
    ) -> ReviewDecisionResult:
        return self._record_decision(
            event_id=event_id,
            reviewer=reviewer,
            reviewer_kind=reviewer_kind,
            session_label=session_label,
            disposition=ReviewDisposition.APPROVE,
            note=note,
        )

    def reject(
        self,
        *,
        event_id: str,
        reviewer: str,
        reviewer_kind: ReviewerIdentityKind = ReviewerIdentityKind.USER_DECLARED,
        session_label: str | None = None,
        note: str | None = None,
    ) -> ReviewDecisionResult:
        return self._record_decision(
            event_id=event_id,
            reviewer=reviewer,
            reviewer_kind=reviewer_kind,
            session_label=session_label,
            disposition=ReviewDisposition.REJECT,
            note=note,
        )

    def request_changes(
        self,
        *,
        event_id: str,
        reviewer: str,
        reviewer_kind: ReviewerIdentityKind = ReviewerIdentityKind.USER_DECLARED,
        session_label: str | None = None,
        note: str | None = None,
    ) -> ReviewDecisionResult:
        return self._record_decision(
            event_id=event_id,
            reviewer=reviewer,
            reviewer_kind=reviewer_kind,
            session_label=session_label,
            disposition=ReviewDisposition.REQUEST_CHANGES,
            note=note,
        )

    def _record_decision(
        self,
        *,
        event_id: str,
        reviewer: str,
        reviewer_kind: ReviewerIdentityKind,
        session_label: str | None,
        disposition: ReviewDisposition,
        note: str | None,
    ) -> ReviewDecisionResult:
        target = self._target_event(event_id)
        metadata = self.chronicle.require_initialized()
        review_event_id = generate_id("event")
        reviewer_identity = ReviewerIdentity(
            label=reviewer,
            kind=reviewer_kind,
            auth_mode=ReviewerAuthMode.LOOPBACK_LOCAL,
            session_label=session_label,
        )
        try:
            audit_event = self.audit.record(
                operation=AuditOperation.REVIEW_DECISION,
                actor=reviewer,
                purpose=f"review decision: {disposition.value}",
                target_environment=AuditTargetEnvironment.LOCAL,
                referenced_records=[target.event_id, review_event_id],
                source_event_id=review_event_id,
                result=AuditSeverity.INFO,
                summary=f"Review {disposition.value} recorded for {target.event_id}",
                metadata={
                    "disposition": disposition.value,
                    "reviewer": reviewer,
                    "reviewer_kind": reviewer_kind.value,
                    "target_event_id": target.event_id,
                    "review_event_id": review_event_id,
                },
            )
        except Exception as exc:
            raise ReviewAuditInsertionError(target.event_id, str(exc)) from exc
        event = ChronicleEvent(
            event_id=review_event_id,
            chronicle_id=metadata.chronicle_id,
            timestamp=datetime.now(timezone.utc).astimezone(),
            event_type=EventType.NOTE_ADDED,
            actor=Actor.REVIEWER,
            summary=f"Review {disposition.value}: {target.summary}",
            payload={
                "review_decision": True,
                "target_event_id": target.event_id,
                "disposition": disposition.value,
                "reviewer": reviewer,
                "reviewer_identity": reviewer_identity.model_dump(mode="json"),
                "note": note,
                "audit_id": audit_event.audit_id,
            },
            parent_event_id=target.event_id,
            source=SourceProvenance(
                source_type="review",
                source_ref=target.event_id,
                source_tool="chronicle-review",
                source_model="human-review",
            ),
        )
        try:
            self.chronicle.append_event(event)
        except Exception as exc:
            raise ReviewDecisionPersistenceError(
                target.event_id,
                str(exc),
                audit_id=audit_event.audit_id,
            ) from exc
        return ReviewDecisionResult(
            target_event_id=target.event_id,
            disposition=disposition,
            reviewer=reviewer,
            reviewer_identity=reviewer_identity,
            note=note,
            review_event_id=event.event_id,
            audit_id=audit_event.audit_id,
        )

    def _target_event(self, event_id: str):
        self.chronicle.require_initialized()
        for event in self.chronicle.jsonl.read_all():
            if event.event_id == event_id:
                return event
        raise ReviewTargetNotFoundError(event_id)

    @staticmethod
    def _latest_reviews(events: list[object]) -> dict[str, object]:
        latest: dict[str, object] = {}
        for event in events:
            payload = getattr(event, "payload", {})
            if getattr(event, "actor", None) != Actor.REVIEWER:
                continue
            if not payload.get("review_decision"):
                continue
            target_event_id = payload.get("target_event_id")
            if isinstance(target_event_id, str) and target_event_id:
                latest[target_event_id] = event
        return latest

    @staticmethod
    def _group_reviews(events: list[object]) -> dict[str, list[object]]:
        grouped: dict[str, list[object]] = {}
        for event in events:
            payload = getattr(event, "payload", {})
            if getattr(event, "actor", None) != Actor.REVIEWER:
                continue
            if not payload.get("review_decision"):
                continue
            target_event_id = payload.get("target_event_id")
            if isinstance(target_event_id, str) and target_event_id:
                grouped.setdefault(target_event_id, []).append(event)
        return grouped

    @staticmethod
    def _review_kind(payload: dict[str, object]) -> str:
        proposal = payload.get("proposal")
        if isinstance(proposal, dict):
            proposal_kind = proposal.get("proposal_kind")
            if isinstance(proposal_kind, str) and proposal_kind:
                return proposal_kind
            return "proposal"
        if "runtime_summary" in payload:
            return "runtime_summary"
        if "runtime_retrieval_plan" in payload:
            return "runtime_retrieval_plan"
        return "assistant_output"
