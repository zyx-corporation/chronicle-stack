import json

import pytest

from chronicle.models.event import Actor, EventType
from chronicle.services.chronicle_service import ChronicleService


@pytest.fixture
def chronicle(tmp_path):
    service = ChronicleService(tmp_path)
    service.init("Event Test")
    return service


def test_record_event(chronicle):
    event = chronicle.record_event(
        event_type=EventType.USER_INPUT,
        actor=Actor.USER,
        summary="Test input",
    )
    assert event.event_id.startswith("evt_")
    assert event.summary == "Test input"

    events = chronicle.jsonl.read_all()
    assert len(events) == 2  # init + record


def test_corrupt_jsonl_line_skipped(chronicle):
    chronicle.record_event(
        event_type=EventType.NOTE_ADDED,
        actor=Actor.USER,
        summary="Valid event",
    )

    with chronicle.paths.events_file.open("a", encoding="utf-8") as f:
        f.write("{invalid json\n")
        f.write(
            json.dumps(
                {
                    "event_id": "evt_manual",
                    "chronicle_id": "chr_test",
                    "timestamp": "2026-06-09T12:00:00+09:00",
                    "event_type": "note_added",
                    "actor": "user",
                    "summary": "After corrupt",
                    "payload": {},
                }
            )
            + "\n"
        )

    events = chronicle.jsonl.read_all(skip_corrupt=True)
    assert len(events) >= 2
    assert chronicle.jsonl.count_corrupt_lines() == 1
