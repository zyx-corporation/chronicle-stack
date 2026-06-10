"""Chronicle core service — init, record, show, index rebuild."""

from datetime import datetime, timezone
from pathlib import Path

import yaml

from chronicle.errors import ChronicleNotInitializedError
from chronicle.ids import generate_id
from chronicle.models.event import Actor, ChronicleEvent, EventType
from chronicle.models.metadata import ChronicleMetadata
from chronicle.store.artifact_store import ArtifactStore
from chronicle.store.index_store import IndexStore
from chronicle.store.jsonl_store import JsonlStore
from chronicle.store.paths import ChroniclePaths


class ChronicleService:
    def __init__(self, root: Path | None = None) -> None:
        self.paths = ChroniclePaths(root)
        self.jsonl = JsonlStore(self.paths.events_file)
        self.index = IndexStore(
            self.paths.indexes_dir,
            self.paths.artifact_index_file,
            self.paths.context_index_file,
            self.paths.decision_index_file,
        )
        self.artifact_store = ArtifactStore(self.paths.artifacts_dir)

    def require_initialized(self) -> ChronicleMetadata:
        if not self.paths.is_initialized():
            raise ChronicleNotInitializedError()
        return self.load_metadata()

    def init(self, title: str) -> ChronicleMetadata:
        self.paths.chronicle_dir.mkdir(parents=True, exist_ok=True)
        self.paths.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.paths.indexes_dir.mkdir(parents=True, exist_ok=True)
        self.paths.reports_dir.mkdir(parents=True, exist_ok=True)

        now = datetime.now(timezone.utc).astimezone()
        metadata = ChronicleMetadata(
            chronicle_id=generate_id("chronicle"),
            title=title,
            created_at=now,
        )

        self.paths.metadata_file.write_text(
            yaml.dump(
                metadata.model_dump(mode="json"),
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
            ),
            encoding="utf-8",
        )

        if not self.paths.events_file.exists():
            self.paths.events_file.touch()

        event = ChronicleEvent(
            event_id=generate_id("event"),
            chronicle_id=metadata.chronicle_id,
            timestamp=now,
            event_type=EventType.CHRONICLE_CREATED,
            actor=Actor.USER,
            summary=f"{title} created",
            payload={"title": title},
        )
        self.jsonl.append(event)
        self.rebuild_indexes()
        return metadata

    def load_metadata(self) -> ChronicleMetadata:
        raw = yaml.safe_load(
            self.paths.metadata_file.read_text(encoding="utf-8")
        )
        return ChronicleMetadata.model_validate(raw)

    def record_event(
        self,
        event_type: EventType,
        actor: Actor,
        summary: str,
        payload: dict | None = None,
        event_id: str | None = None,
        **kwargs,
    ) -> ChronicleEvent:
        metadata = self.require_initialized()
        now = datetime.now(timezone.utc).astimezone()
        event = ChronicleEvent(
            event_id=event_id or generate_id("event"),
            chronicle_id=metadata.chronicle_id,
            timestamp=now,
            event_type=event_type,
            actor=actor,
            summary=summary,
            payload=payload or {},
            **kwargs,
        )
        self.jsonl.append(event)
        return event

    def show(self) -> dict:
        metadata = self.require_initialized()
        events = self.jsonl.read_all()
        artifacts, _ = self.index.load_artifacts()
        contexts = self.index.load_contexts()
        decisions = self.index.load_decisions()
        corrupt = self.jsonl.count_corrupt_lines()

        return {
            "metadata": metadata,
            "event_count": len(events),
            "artifact_count": len(artifacts),
            "context_count": len(contexts),
            "decision_count": len(decisions),
            "corrupt_lines": corrupt,
        }

    def rebuild_indexes(self) -> None:
        events = self.jsonl.read_all(skip_corrupt=True)
        artifacts: dict = {}
        versions: dict = {}
        contexts: dict = {}
        decisions: dict = {}

        for event in events:
            payload = event.payload
            if (
                event.event_type == EventType.CONTEXT_ADDED
                and "context" in payload
            ):
                ctx_data = payload["context"]
                contexts[ctx_data["context_id"]] = ctx_data
            elif (
                event.event_type == EventType.ARTIFACT_CREATED
                and "artifact" in payload
            ):
                art_data = payload["artifact"]
                artifacts[art_data["artifact_id"]] = art_data
                if "version" in payload:
                    ver_data = payload["version"]
                    aid = ver_data["artifact_id"]
                    versions.setdefault(aid, []).append(ver_data)
            elif event.event_type in (
                EventType.ARTIFACT_UPDATED,
                EventType.ARTIFACT_VERSIONED,
            ) and "version" in payload:
                ver_data = payload["version"]
                aid = ver_data["artifact_id"]
                versions.setdefault(aid, []).append(ver_data)
                if "artifact" in payload:
                    art_data = payload["artifact"]
                    artifacts[art_data["artifact_id"]] = art_data
            elif (
                event.event_type == EventType.DECISION_RECORDED
                and "decision" in payload
            ):
                dec_data = payload["decision"]
                decisions[dec_data["decision_id"]] = dec_data

        from chronicle.models.artifact import Artifact, ArtifactVersion
        from chronicle.models.context import Context
        from chronicle.models.decision import Decision

        self.index.save_artifacts(
            {k: Artifact.model_validate(v) for k, v in artifacts.items()},
            {
                aid: [ArtifactVersion.model_validate(v) for v in vlist]
                for aid, vlist in versions.items()
            },
        )
        self.index.save_contexts(
            {k: Context.model_validate(v) for k, v in contexts.items()}
        )
        self.index.save_decisions(
            {k: Decision.model_validate(v) for k, v in decisions.items()}
        )
