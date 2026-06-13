"""Artifact create, update, and history service."""

from datetime import datetime, timezone
from pathlib import Path

from chronicle.errors import ArtifactContentMissingError, ArtifactNotFoundError
from chronicle.ids import generate_id
from chronicle.models.artifact import Artifact, ArtifactStatus, ArtifactType, ArtifactVersion
from chronicle.models.event import Actor, ChronicleEvent, EventType
from chronicle.models.source import SourceProvenance
from chronicle.models.visibility import VisibilityHint
from chronicle.services.chronicle_service import ChronicleService


class ArtifactService:
    def __init__(self, root: Path | None = None) -> None:
        self.chronicle = ChronicleService(root)

    def create(
        self,
        title: str,
        artifact_type: ArtifactType,
        source_file: Path | None = None,
        content: str | None = None,
        tags: list[str] | None = None,
        visibility_hint: VisibilityHint = VisibilityHint.UNKNOWN,
        source: SourceProvenance | None = None,
        actor: Actor = Actor.ASSISTANT,
    ) -> tuple[Artifact, ArtifactVersion]:
        metadata = self.chronicle.require_initialized()
        now = datetime.now(timezone.utc).astimezone()
        artifact_id = generate_id("artifact")
        version_id = generate_id("version")
        event_id = generate_id("event")

        artifact = Artifact(
            artifact_id=artifact_id,
            chronicle_id=metadata.chronicle_id,
            title=title,
            artifact_type=artifact_type,
            current_version_id=version_id,
            created_at=now,
            updated_at=now,
            status=ArtifactStatus.DRAFT,
            path=f"artifacts/{artifact_id}/current.md",
            visibility_hint=visibility_hint,
            source=source,
            tags=tags or [],
        )
        version = ArtifactVersion(
            version_id=version_id,
            artifact_id=artifact_id,
            created_at=now,
            created_by=actor.value,
            source_event_id=event_id,
            path=f"artifacts/{artifact_id}/versions/{version_id}.md",
            change_summary="created",
        )

        self.chronicle.artifact_store.create_artifact_files(
            artifact, version, source_file=source_file, content=content
        )

        event = ChronicleEvent(
            event_id=event_id,
            chronicle_id=metadata.chronicle_id,
            timestamp=now,
            event_type=EventType.ARTIFACT_CREATED,
            actor=actor,
            summary=f"Artifact created: {title}",
            payload={
                "artifact": artifact.model_dump(mode="json"),
                "version": version.model_dump(mode="json"),
            },
            artifact_id=artifact_id,
        )
        self.chronicle.append_event(event)
        self.chronicle.rebuild_indexes()
        return artifact, version

    def update(
        self,
        artifact_id: str,
        source_file: Path | None = None,
        content: str | None = None,
        summary: str = "",
        actor: Actor = Actor.ASSISTANT,
    ) -> tuple[Artifact, ArtifactVersion]:
        if source_file is None and content is None:
            raise ArtifactContentMissingError()

        metadata = self.chronicle.require_initialized()
        artifacts, _versions = self.chronicle.index.load_artifacts()
        if artifact_id not in artifacts:
            raise ArtifactNotFoundError(artifact_id)

        artifact = artifacts[artifact_id]
        now = datetime.now(timezone.utc).astimezone()
        version_id = generate_id("version")
        event_id = generate_id("event")
        parent_version_id = artifact.current_version_id

        version = ArtifactVersion(
            version_id=version_id,
            artifact_id=artifact_id,
            created_at=now,
            created_by=actor.value,
            source_event_id=event_id,
            parent_version_id=parent_version_id,
            path=f"artifacts/{artifact_id}/versions/{version_id}.md",
            change_summary=summary or "updated",
        )

        updated_artifact = artifact.model_copy(
            update={"current_version_id": version_id, "updated_at": now}
        )

        self.chronicle.artifact_store.update_artifact_files(
            artifact_id, version, source_file=source_file, content=content
        )

        event = ChronicleEvent(
            event_id=event_id,
            chronicle_id=metadata.chronicle_id,
            timestamp=now,
            event_type=EventType.ARTIFACT_VERSIONED,
            actor=actor,
            summary=f"Artifact updated: {artifact.title}",
            payload={
                "artifact": updated_artifact.model_dump(mode="json"),
                "version": version.model_dump(mode="json"),
            },
            artifact_id=artifact_id,
        )
        self.chronicle.append_event(event)
        self.chronicle.rebuild_indexes()
        return updated_artifact, version

    def history(
        self, artifact_id: str
    ) -> tuple[Artifact, list[ArtifactVersion]]:
        artifacts, versions = self.chronicle.index.load_artifacts()
        if artifact_id not in artifacts:
            raise ArtifactNotFoundError(artifact_id)
        artifact = artifacts[artifact_id]
        artifact_versions = versions.get(artifact_id, [])
        artifact_versions.sort(key=lambda v: v.created_at)
        return artifact, artifact_versions

    def list_artifacts(self) -> list[Artifact]:
        self.chronicle.require_initialized()
        artifacts, _ = self.chronicle.index.load_artifacts()
        return list(artifacts.values())

    def get(self, artifact_id: str) -> Artifact:
        artifacts, _ = self.chronicle.index.load_artifacts()
        if artifact_id not in artifacts:
            raise ArtifactNotFoundError(artifact_id)
        return artifacts[artifact_id]
