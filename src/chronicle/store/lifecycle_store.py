"""Append-only lifecycle event storage."""

import json
from pathlib import Path

from chronicle.models.lifecycle import LifecycleEvent


class LifecycleStore:
    """JSONL-backed lifecycle store.

    This store is separate from both primary Chronicle events and audit events.
    It records lifecycle decisions such as redact, seal, tombstone, and delete
    markers without silently rewriting original records.
    """

    def __init__(self, lifecycle_file: Path) -> None:
        self.lifecycle_file = lifecycle_file

    def append(self, event: LifecycleEvent) -> None:
        self.lifecycle_file.parent.mkdir(parents=True, exist_ok=True)
        with self.lifecycle_file.open("a", encoding="utf-8") as f:
            f.write(event.to_jsonl() + "\n")

    def read_all(self, *, skip_corrupt: bool = True) -> list[LifecycleEvent]:
        if not self.lifecycle_file.exists():
            return []

        events: list[LifecycleEvent] = []
        with self.lifecycle_file.open(encoding="utf-8") as f:
            for line_number, line in enumerate(f, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    data = json.loads(stripped)
                    events.append(LifecycleEvent.model_validate(data))
                except (json.JSONDecodeError, ValueError) as exc:
                    if skip_corrupt:
                        continue
                    raise ValueError(f"Invalid lifecycle JSONL at line {line_number}: {exc}") from exc
        return events

    def count_corrupt_lines(self) -> int:
        if not self.lifecycle_file.exists():
            return 0

        corrupt = 0
        with self.lifecycle_file.open(encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    LifecycleEvent.model_validate(json.loads(stripped))
                except (json.JSONDecodeError, ValueError):
                    corrupt += 1
        return corrupt
