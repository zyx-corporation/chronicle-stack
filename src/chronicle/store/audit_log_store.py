"""Append-only audit log storage."""

import json
from pathlib import Path

from chronicle.models.audit import AuditEvent


class AuditLogStore:
    """JSONL-backed audit log store.

    This store is intentionally separate from the primary ChronicleEvent JSONL
    store so original records and later operational audit events are not
    confused.
    """

    def __init__(self, audit_file: Path) -> None:
        self.audit_file = audit_file

    def append(self, event: AuditEvent) -> None:
        self.audit_file.parent.mkdir(parents=True, exist_ok=True)
        with self.audit_file.open("a", encoding="utf-8") as f:
            f.write(event.to_jsonl() + "\n")

    def read_all(self, *, skip_corrupt: bool = True) -> list[AuditEvent]:
        if not self.audit_file.exists():
            return []

        events: list[AuditEvent] = []
        with self.audit_file.open(encoding="utf-8") as f:
            for line_number, line in enumerate(f, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    data = json.loads(stripped)
                    events.append(AuditEvent.model_validate(data))
                except (json.JSONDecodeError, ValueError) as exc:
                    if skip_corrupt:
                        continue
                    raise ValueError(f"Invalid audit log JSONL at line {line_number}: {exc}") from exc
        return events

    def count_corrupt_lines(self) -> int:
        if not self.audit_file.exists():
            return 0

        corrupt = 0
        with self.audit_file.open(encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    AuditEvent.model_validate(json.loads(stripped))
                except (json.JSONDecodeError, ValueError):
                    corrupt += 1
        return corrupt
