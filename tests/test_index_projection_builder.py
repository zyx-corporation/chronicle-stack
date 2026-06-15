"""Tests for pure derived index projection building."""

from datetime import datetime, timezone

from chronicle.models.event import Actor, ChronicleEvent, EventType
from chronicle.services.index_projection_builder import IndexProjectionBuilder


def _timestamp() -> str:
    return "2026-06-15T00:00:00+00:00"


def _event(event_type: EventType, payload: dict) -> ChronicleEvent:
    return ChronicleEvent(
        event_id="evt_test",
        chronicle_id="chr_test",
        timestamp=datetime(2026, 6, 15, tzinfo=timezone.utc),
        event_type=event_type,
        actor=Actor.USER,
        summary="test",
        payload=payload,
    )


def test_index_projection_builder_projects_contexts_and_decisions():
    events = [
        _event(
            EventType.CONTEXT_ADDED,
            {
                "context": {
                    "context_id": "ctx_1",
                    "title": "Context",
                    "summary": "Summary",
                    "source_type": "conversation",
                    "source_ref": "",
                    "scope": "project",
                    "visibility_hint": "unknown",
                    "created_at": _timestamp(),
                }
            },
        ),
        _event(
            EventType.DECISION_RECORDED,
            {
                "decision": {
                    "decision_id": "dec_1",
                    "chronicle_id": "chr_test",
                    "decision_type": "accepted",
                    "decided_by": "user",
                    "decided_at": _timestamp(),
                    "reason": "Use explicit projection builder",
                    "artifact_id": None,
                    "alternatives": [],
                    "notes": "",
                    "event_id": "evt_decision",
                }
            },
        ),
    ]

    projection = IndexProjectionBuilder().build(events)

    assert projection.contexts["ctx_1"].title == "Context"
    assert projection.decisions["dec_1"].reason == "Use explicit projection builder"


def test_index_projection_builder_links_rde_record_to_target_version():
    artifact_payload = {
        "artifact": {
            "artifact_id": "art_1",
            "chronicle_id": "chr_test",
            "title": "Artifact",
            "artifact_type": "document",
            "current_version_id": "ver_2",
            "created_at": _timestamp(),
            "updated_at": _timestamp(),
            "status": "draft",
            "path": ".chronicle/artifacts/art_1/current.md",
            "visibility_hint": "unknown",
            "tags": [],
        },
        "version": {
            "version_id": "ver_2",
            "artifact_id": "art_1",
            "created_at": _timestamp(),
            "created_by": "user",
            "source_event_id": "evt_version",
            "parent_version_id": "ver_1",
            "path": ".chronicle/artifacts/art_1/current.md",
            "change_summary": "updated",
            "rde_record_id": None,
        },
    }
    rde_payload = {
        "rde": {
            "rde_record_id": "rde_1",
            "artifact_id": "art_1",
            "from_version_id": "ver_1",
            "to_version_id": "ver_2",
            "created_at": _timestamp(),
            "created_by": "user",
            "summary": "Meaning changed",
            "preserved": [],
            "transformed": [],
            "supplemented": [],
            "unresolved": [],
            "deviation_risks": [],
            "next_update_policy": [],
        }
    }

    projection = IndexProjectionBuilder().build([
        _event(EventType.ARTIFACT_UPDATED, artifact_payload),
        _event(EventType.RDE_DIFF_RECORDED, rde_payload),
    ])

    version = projection.versions["art_1"][0]
    assert version.version_id == "ver_2"
    assert version.rde_record_id == "rde_1"
