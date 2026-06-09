"""JSONL event store."""

import json
from pathlib import Path

from chronicle.errors import JsonlParseError
from chronicle.models.event import ChronicleEvent


class JsonlStore:
    def __init__(self, events_file: Path) -> None:
        self.events_file = events_file

    def append(self, event: ChronicleEvent) -> None:
        self.events_file.parent.mkdir(parents=True, exist_ok=True)
        with self.events_file.open("a", encoding="utf-8") as f:
            f.write(event.to_jsonl() + "\n")

    def read_all(self, *, skip_corrupt: bool = True) -> list[ChronicleEvent]:
        if not self.events_file.exists():
            return []

        events: list[ChronicleEvent] = []
        with self.events_file.open(encoding="utf-8") as f:
            for line_number, line in enumerate(f, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    data = json.loads(stripped)
                    events.append(ChronicleEvent.model_validate(data))
                except (json.JSONDecodeError, ValueError) as exc:
                    if skip_corrupt:
                        continue
                    raise JsonlParseError(line_number, str(exc)) from exc
        return events

    def count_corrupt_lines(self) -> int:
        if not self.events_file.exists():
            return 0

        corrupt = 0
        with self.events_file.open(encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    ChronicleEvent.model_validate(json.loads(stripped))
                except (json.JSONDecodeError, ValueError):
                    corrupt += 1
        return corrupt
