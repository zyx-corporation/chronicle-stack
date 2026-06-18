"""Local file-backed placeholder vector index service."""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from chronicle.errors import AiIndexRecordNotFoundError
from chronicle.models.ai_index import (
    VectorIndexEntry,
    VectorIndexSnapshot,
    VectorIndexStatus,
    VectorSearchResult,
)
from chronicle.services.chronicle_service import ChronicleService


class VectorIndexService:
    """Manage a local placeholder vector index without embeddings or external services."""

    def __init__(self, root: Path | None = None) -> None:
        self.chronicle = ChronicleService(root)
        self.paths = self.chronicle.paths

    def status(self) -> VectorIndexStatus:
        snapshot = self._load_snapshot()
        return VectorIndexStatus(
            path=str(self.paths.vector_index_file),
            entry_count=len(snapshot.entries),
        )

    def add_entry(
        self,
        *,
        record_id: str,
        text: str,
        record_type: str = "event",
        metadata: dict[str, str] | None = None,
    ) -> VectorIndexEntry:
        self.chronicle.require_initialized()
        self._require_record(record_id)
        snapshot = self._load_snapshot()
        entry = VectorIndexEntry(
            record_id=record_id,
            record_type=record_type,
            text=text,
            metadata=metadata or {},
            indexed_at=datetime.now(timezone.utc).astimezone(),
        )
        snapshot.entries = [
            existing
            for existing in snapshot.entries
            if not (existing.record_id == record_id and existing.record_type == record_type)
        ]
        snapshot.entries.append(entry)
        self._save_snapshot(snapshot)
        return entry

    def search(self, *, query: str, limit: int = 5) -> list[VectorSearchResult]:
        self.chronicle.require_initialized()
        snapshot = self.snapshot()
        scored: list[VectorSearchResult] = []
        for entry in snapshot.entries:
            score = _score_text(query, entry.text)
            if score <= 0:
                continue
            scored.append(
                VectorSearchResult(
                    record_id=entry.record_id,
                    record_type=entry.record_type,
                    score=round(score, 4),
                    text=entry.text,
                    metadata=entry.metadata,
                )
            )
        scored.sort(key=lambda item: (-item.score, item.record_id, item.record_type))
        return scored[:limit]

    def snapshot(self) -> VectorIndexSnapshot:
        self.chronicle.require_initialized()
        return self._load_snapshot()

    def get_entry(self, record_id: str) -> VectorIndexEntry | None:
        self.chronicle.require_initialized()
        snapshot = self._load_snapshot()
        return next((entry for entry in snapshot.entries if entry.record_id == record_id), None)

    def _load_snapshot(self) -> VectorIndexSnapshot:
        if not self.paths.vector_index_file.exists():
            return VectorIndexSnapshot()
        raw = json.loads(self.paths.vector_index_file.read_text(encoding="utf-8"))
        return VectorIndexSnapshot.model_validate(raw)

    def _save_snapshot(self, snapshot: VectorIndexSnapshot) -> None:
        self.paths.ai_indexes_dir.mkdir(parents=True, exist_ok=True)
        self.paths.vector_index_file.write_text(
            json.dumps(snapshot.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _require_record(self, record_id: str) -> None:
        if record_id in self._known_record_ids():
            return
        raise AiIndexRecordNotFoundError(record_id)

    def _known_record_ids(self) -> set[str]:
        metadata = self.chronicle.load_metadata()
        events = self.chronicle.jsonl.read_all(skip_corrupt=True)
        artifacts, _ = self.chronicle.index.load_artifacts()
        contexts = self.chronicle.index.load_contexts()
        decisions = self.chronicle.index.load_decisions()
        rde_records = self.chronicle.index.load_rde_records()
        boundary_rules = self.chronicle.index.load_boundary_rules()
        return {
            metadata.chronicle_id,
            *(event.event_id for event in events),
            *artifacts.keys(),
            *contexts.keys(),
            *decisions.keys(),
            *rde_records.keys(),
            *boundary_rules.keys(),
        }


def _score_text(query: str, text: str) -> float:
    normalized_query = query.strip().lower()
    normalized_text = text.lower()
    if not normalized_query:
        return 0.0

    query_tokens = set(_tokenize(normalized_query))
    text_tokens = set(_tokenize(normalized_text))
    overlap = len(query_tokens & text_tokens) / max(len(query_tokens), 1)
    substring_bonus = 1.0 if normalized_query in normalized_text else 0.0
    return overlap + substring_bonus


def _tokenize(value: str) -> list[str]:
    return re.findall(r"[a-z0-9_]+", value.lower())
