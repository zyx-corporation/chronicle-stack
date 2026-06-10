"""RDE Diff Record service."""

from datetime import datetime, timezone
from pathlib import Path

from chronicle.errors import ArtifactNotFoundError, RdeVersionNotFoundError
from chronicle.exporters.rde_report import format_rde_report
from chronicle.ids import generate_id
from chronicle.models.event import Actor, EventType
from chronicle.models.rde import RdeDiffRecord
from chronicle.services.artifact_service import ArtifactService
from chronicle.services.chronicle_service import ChronicleService


class RdeService:
    def __init__(self, root: Path | None = None) -> None:
        self.chronicle = ChronicleService(root)
        self.artifacts = ArtifactService(root)

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
