"""RDE Diff Record service."""

from datetime import datetime, timezone
from pathlib import Path

from chronicle.errors import ArtifactNotFoundError, RdeVersionNotFoundError
from chronicle.exporters.rde_report import format_rde_report
from chronicle.ids import generate_id
from chronicle.models.chronicle_object import (
    ChronicleObjectAiInvolvement,
    ChronicleObjectLifecycle,
    ChronicleObjectType,
)
from chronicle.models.event import Actor, EventType
from chronicle.models.rde import RdeDiffRecord, RdeDraftMemo
from chronicle.services.artifact_service import ArtifactService
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.chronicle_object_service import ChronicleObjectService


class RdeService:
    def __init__(self, root: Path | None = None) -> None:
        self.chronicle = ChronicleService(root)
        self.artifacts = ArtifactService(root)
        self.objects = ChronicleObjectService(root)

    def record(
        self,
        artifact_id: str,
        from_version_id: str,
        to_version_id: str,
        summary: str = "",
        created_by: str = "assistant",
        preserved: list[str] | None = None,
        transformed: list[str] | None = None,
        supplemented: list[str] | None = None,
        unresolved: list[str] | None = None,
        deviation_risks: list[str] | None = None,
        next_update_policy: list[str] | None = None,
    ) -> RdeDiffRecord:
        self.chronicle.require_initialized()
        try:
            self.artifacts.get(artifact_id)
        except ArtifactNotFoundError as exc:
            raise exc

        store = self.chronicle.artifact_store
        if not store.version_exists(artifact_id, from_version_id):
            raise RdeVersionNotFoundError(from_version_id)
        if not store.version_exists(artifact_id, to_version_id):
            raise RdeVersionNotFoundError(to_version_id)

        now = datetime.now(timezone.utc).astimezone()
        rde_id = generate_id("rde")
        record = RdeDiffRecord(
            rde_record_id=rde_id,
            artifact_id=artifact_id,
            from_version_id=from_version_id,
            to_version_id=to_version_id,
            created_at=now,
            created_by=created_by,
            summary=summary,
            preserved=preserved or [],
            transformed=transformed or [],
            supplemented=supplemented or [],
            unresolved=unresolved or [],
            deviation_risks=deviation_risks or [],
            next_update_policy=next_update_policy or [],
        )

        report_path = self.chronicle.paths.rde_report_path(rde_id)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(format_rde_report(record), encoding="utf-8")

        try:
            actor = Actor(created_by)
        except ValueError:
            actor = Actor.ASSISTANT

        self.chronicle.record_event(
            event_type=EventType.RDE_DIFF_RECORDED,
            actor=actor,
            summary=f"RDE diff recorded: {summary or rde_id}",
            payload={"rde": record.model_dump(mode="json")},
            artifact_id=artifact_id,
            rde_record_id=rde_id,
        )
        return record

    def draft(
        self,
        *,
        artifact_id: str,
        from_version_id: str,
        to_version_id: str,
        summary: str = "",
        created_by: str = "assistant",
        preserved: list[str] | None = None,
        transformed: list[str] | None = None,
        supplemented: list[str] | None = None,
        unresolved: list[str] | None = None,
        deviation_risks: list[str] | None = None,
        next_update_policy: list[str] | None = None,
        mode: str = "manual",
        ai_summary: str = "",
        ai_response: str | None = None,
        ai_model: str | None = None,
        runtime_label: str | None = None,
        interpretation: str | None = None,
        record: bool = False,
    ) -> RdeDraftMemo:
        metadata = self.chronicle.require_initialized()
        memo = RdeDraftMemo(
            mode=mode,
            source_chronicle_id=metadata.chronicle_id,
            artifact_id=artifact_id,
            from_version_id=from_version_id,
            to_version_id=to_version_id,
            summary=summary,
            preserved=preserved or [],
            transformed=transformed or [],
            supplemented=supplemented or [],
            unresolved=unresolved or [],
            deviation_risks=deviation_risks or [],
            next_update_policy=next_update_policy or [],
            ai_summary=ai_summary,
            ai_response=ai_response,
            ai_model=ai_model,
            runtime_label=runtime_label,
            interpretation=interpretation,
            notes=[
                "Draft remains review-oriented and separates AI response text from source record claims.",
                "Linked Delta Chronicle stays derived from the eventual RDE Diff Record.",
                "AI interpretation is treated as a hypothesis and should be decay-reviewed over time.",
            ],
        )
        if not record:
            return memo

        rde_record = self.record(
            artifact_id=artifact_id,
            from_version_id=from_version_id,
            to_version_id=to_version_id,
            summary=summary,
            created_by=created_by,
            preserved=preserved,
            transformed=transformed,
            supplemented=supplemented,
            unresolved=unresolved,
            deviation_risks=deviation_risks,
            next_update_policy=next_update_policy,
        )
        hypothesis_object_id: str | None = None
        if interpretation:
            hypothesis = self.objects.record(
                object_type=ChronicleObjectType.HYPOTHESIS,
                summary=summary or interpretation[:120],
                created_by=created_by,
                detail=interpretation,
                artifact_id=artifact_id,
                rde_record_id=rde_record.rde_record_id,
                ai_involvement=ChronicleObjectAiInvolvement(
                    involved=bool(ai_model),
                    models=[ai_model] if ai_model else [],
                ),
                lifecycle=ChronicleObjectLifecycle(retention="decay-target:ai-interpretation"),
            )
            hypothesis_object_id = hypothesis.object_id
        return memo.model_copy(
            update={
                "recorded_rde_id": rde_record.rde_record_id,
                "linked_delta_object_id": f"obj_delta_{rde_record.rde_record_id}",
                "linked_hypothesis_object_id": hypothesis_object_id,
            }
        )
