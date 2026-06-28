"""Persistence for local federation message inbox/outbox queues."""

import json
from pathlib import Path

from chronicle.models.federation_message import FederationMessageBox, FederationMessageRecord
from chronicle.store.paths import ChroniclePaths


class FederationMessageStore:
    """Store federation message records as local queue files."""

    def __init__(self, paths: ChroniclePaths) -> None:
        self.paths = paths

    def save(self, record: FederationMessageRecord) -> Path:
        box_dir = self._box_dir(record.box)
        box_dir.mkdir(parents=True, exist_ok=True)
        path = box_dir / f"{record.envelope.message_id}.json"
        path.write_text(
            json.dumps(record.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return path

    def list_ids(self, box: FederationMessageBox) -> list[str]:
        box_dir = self._box_dir(box)
        if not box_dir.exists():
            return []
        return sorted(
            path.stem
            for path in box_dir.iterdir()
            if path.is_file() and path.suffix == ".json"
        )

    def load(self, box: FederationMessageBox, message_id: str) -> FederationMessageRecord:
        path = self._box_dir(box) / f"{message_id}.json"
        raw = json.loads(path.read_text(encoding="utf-8"))
        return FederationMessageRecord.model_validate(raw)

    def list(self, box: FederationMessageBox) -> list[FederationMessageRecord]:
        return [self.load(box, message_id) for message_id in self.list_ids(box)]

    def _box_dir(self, box: FederationMessageBox) -> Path:
        if box == FederationMessageBox.INBOX:
            return self.paths.federation_inbox_dir
        return self.paths.federation_outbox_dir
