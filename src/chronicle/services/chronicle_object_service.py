"""Chronicle object service for Phase 4 object expansion."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from chronicle.errors import ChronicleError
from chronicle.ids import generate_id
from chronicle.models.chronicle_object import (
    ChronicleObjectAiInvolvement,
    ChronicleObjectLifecycle,
    ChronicleObjectRecord,
    ChronicleObjectType,
)
from chronicle.models.event import Actor, ChronicleEvent, EventType
from chronicle.models.visibility import VisibilityHint
from chronicle.services.chronicle_service import ChronicleService


class ChronicleObjectNotFoundError(ChronicleError):
    def __init__(self, object_id: str) -> None:
        super().__init__(
            code="CHRONICLE_OBJECT_NOT_FOUND",
            message=f"Chronicle object not found: {object_id}",
            hint="Run `chronicle object list` or inspect `/api/chronicle-objects` to see available objects.",
        )


class ChronicleObjectService:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path.cwd()
        self.chronicle = ChronicleService(self.root)

    def record(
        self,
        *,
        object_type: ChronicleObjectType,
        summary: str,
        created_by: str,
        detail: str = "",
        visibility_hint: VisibilityHint = VisibilityHint.UNKNOWN,
        origin_question_id: str | None = None,
        artifact_id: str | None = None,
        context_id: str | None = None,
        decision_id: str | None = None,
        rde_record_id: str | None = None,
        evidence: list[str] | None = None,
        related_object_ids: list[str] | None = None,
        ai_involvement: ChronicleObjectAiInvolvement | None = None,
        lifecycle: ChronicleObjectLifecycle | None = None,
    ) -> ChronicleObjectRecord:
        metadata = self.chronicle.require_initialized()
        now = datetime.now(timezone.utc).astimezone()
        object_id = generate_id("object")
        record = ChronicleObjectRecord(
            object_id=object_id,
            object_type=object_type,
            chronicle_id=metadata.chronicle_id,
            created_at=now,
            created_by=created_by,
            summary=summary,
            detail=detail,
            visibility_hint=visibility_hint,
            source_event_id=None,
            origin_question_id=origin_question_id,
            artifact_id=artifact_id,
            context_id=context_id,
            decision_id=decision_id,
            rde_record_id=rde_record_id,
            evidence=evidence or [],
            related_object_ids=related_object_ids or [],
            ai_involvement=ai_involvement or ChronicleObjectAiInvolvement(),
            lifecycle=lifecycle or ChronicleObjectLifecycle(),
            derived=False,
        )
        event_id = generate_id("event")
        event = ChronicleEvent(
            event_id=event_id,
            chronicle_id=metadata.chronicle_id,
            timestamp=now,
            event_type=EventType.CHRONICLE_OBJECT_RECORDED,
            actor=Actor.USER,
            summary=summary,
            payload={"chronicle_object": record.model_copy(update={"source_event_id": event_id}).model_dump(mode="json")},
            context_ids=[context_id] if context_id else [],
            artifact_id=artifact_id,
            decision_id=decision_id,
            rde_record_id=rde_record_id,
        )
        self.chronicle.append_event(event)
        return record.model_copy(update={"source_event_id": event_id})

    def list_objects(self) -> list[ChronicleObjectRecord]:
        self.chronicle.require_initialized()
        self.chronicle.rebuild_indexes()
        rows = self._derived_objects()
        rows.extend(self._explicit_objects())
        return sorted(rows, key=lambda item: (item.created_at, item.object_id))

    def get(self, object_id: str) -> ChronicleObjectRecord:
        for record in self.list_objects():
            if record.object_id == object_id:
                return record
        raise ChronicleObjectNotFoundError(object_id)

    def _explicit_objects(self) -> list[ChronicleObjectRecord]:
        rows: list[ChronicleObjectRecord] = []
        for event in self.chronicle.jsonl.read_all():
            payload = event.payload
            if event.event_type != EventType.CHRONICLE_OBJECT_RECORDED:
                continue
            object_payload = payload.get("chronicle_object")
            if not isinstance(object_payload, dict):
                continue
            rows.append(ChronicleObjectRecord.model_validate(object_payload))
        return rows

    def _derived_objects(self) -> list[ChronicleObjectRecord]:
        metadata = self.chronicle.require_initialized()
        artifacts, versions = self.chronicle.index.load_artifacts()
        contexts = self.chronicle.index.load_contexts()
        decisions = self.chronicle.index.load_decisions()
        rde_records = self.chronicle.index.load_rde_records()
        rows: list[ChronicleObjectRecord] = []

        for context in contexts.values():
            rows.append(
                ChronicleObjectRecord(
                    object_id=f"obj_conversation_{context.context_id}",
                    object_type=ChronicleObjectType.CONVERSATION,
                    chronicle_id=metadata.chronicle_id,
                    created_at=context.created_at,
                    created_by="derived:index_projection",
                    summary=context.title,
                    detail=context.summary,
                    visibility_hint=context.visibility_hint,
                    context_id=context.context_id,
                    evidence=[],
                    related_object_ids=[],
                    derived=True,
                )
            )

        for artifact in artifacts.values():
            rows.append(
                ChronicleObjectRecord(
                    object_id=f"obj_artifact_{artifact.artifact_id}",
                    object_type=ChronicleObjectType.ARTIFACT,
                    chronicle_id=metadata.chronicle_id,
                    created_at=artifact.created_at,
                    created_by="derived:index_projection",
                    summary=artifact.title,
                    detail=f"Current version: {artifact.current_version_id}; version_count={len(versions.get(artifact.artifact_id, []))}",
                    visibility_hint=artifact.visibility_hint,
                    artifact_id=artifact.artifact_id,
                    evidence=[],
                    related_object_ids=[],
                    derived=True,
                )
            )

        for decision in decisions.values():
            rows.append(
                ChronicleObjectRecord(
                    object_id=f"obj_decision_{decision.decision_id}",
                    object_type=ChronicleObjectType.DECISION,
                    chronicle_id=metadata.chronicle_id,
                    created_at=decision.decided_at,
                    created_by=decision.decided_by,
                    summary=decision.reason or decision.decision_type.value,
                    detail=decision.notes,
                    visibility_hint=VisibilityHint.UNKNOWN,
                    decision_id=decision.decision_id,
                    artifact_id=decision.artifact_id,
                    evidence=list(decision.alternatives),
                    related_object_ids=[],
                    derived=True,
                )
            )

        for rde_record in rde_records.values():
            rows.append(
                ChronicleObjectRecord(
                    object_id=f"obj_delta_{rde_record.rde_record_id}",
                    object_type=ChronicleObjectType.DELTA,
                    chronicle_id=metadata.chronicle_id,
                    created_at=rde_record.created_at,
                    created_by=rde_record.created_by,
                    summary=rde_record.summary or "RDE meaning delta",
                    detail=(
                        f"from_version_id={rde_record.from_version_id}; "
                        f"to_version_id={rde_record.to_version_id}"
                    ),
                    visibility_hint=VisibilityHint.UNKNOWN,
                    artifact_id=rde_record.artifact_id,
                    rde_record_id=rde_record.rde_record_id,
                    evidence=[
                        *rde_record.preserved,
                        *rde_record.transformed,
                        *rde_record.supplemented,
                    ],
                    related_object_ids=[],
                    derived=True,
                )
            )

        return rows
