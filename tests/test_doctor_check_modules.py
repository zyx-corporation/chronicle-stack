"""Unit tests for doctor check-family modules."""

from datetime import datetime, timezone

from chronicle.doctor.artifact_checks import check_artifact_files
from chronicle.doctor.injection_checks import check_injection_plan_refs
from chronicle.doctor.storage_checks import check_indexes, check_known_event_types, check_required_files
from chronicle.models.event import Actor, ChronicleEvent, EventType
from chronicle.models.doctor import DoctorSeverity
from chronicle.store.paths import ChroniclePaths


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


def test_required_file_checks_report_missing_chronicle_files(tmp_path):
    paths = ChroniclePaths(tmp_path)

    checks = check_required_files(paths)
    by_id = {check.check_id: check for check in checks}

    assert by_id["chronicle_dir_exists"].severity == DoctorSeverity.ERROR
    assert by_id["chronicle_jsonl_exists"].severity == DoctorSeverity.ERROR
    assert by_id["metadata_exists"].severity == DoctorSeverity.WARNING


def test_index_check_warns_when_indexes_are_missing(tmp_path):
    paths = ChroniclePaths(tmp_path)

    check = check_indexes(paths)

    assert check.check_id == "indexes_present"
    assert check.severity == DoctorSeverity.WARNING
    assert "run `chronicle index rebuild`" in check.recommendation


def test_known_event_types_reports_ok_for_valid_events():
    check = check_known_event_types([
        _event(EventType.CONTEXT_ADDED, {"context": {"context_id": "ctx_1"}}),
    ])

    assert check.check_id == "known_event_types"
    assert check.severity == DoctorSeverity.OK


def test_artifact_file_check_warns_for_missing_artifact_files(tmp_path):
    paths = ChroniclePaths(tmp_path)
    event = _event(
        EventType.ARTIFACT_CREATED,
        {
            "artifact": {"artifact_id": "art_1"},
            "version": {"artifact_id": "art_1", "version_id": "ver_1"},
        },
    )

    check = check_artifact_files(paths, [event])

    assert check.check_id == "artifact_files_present"
    assert check.severity == DoctorSeverity.WARNING
    assert "art_1: current.md" in check.detail
    assert "art_1: versions/ver_1.md" in check.detail


def test_injection_plan_check_warns_for_missing_context_refs():
    plan_event = _event(
        EventType.INJECTION_PLAN_RECORDED,
        {
            "injection_plan": {
                "plan_id": "plan_1",
                "selected": [{"context_id": "ctx_missing"}],
                "warned": [],
                "excluded": [],
            }
        },
    )

    check = check_injection_plan_refs([plan_event])

    assert check.check_id == "recorded_injection_plan_context_refs"
    assert check.severity == DoctorSeverity.WARNING
    assert "plan_1:selected:ctx_missing" in check.detail


def test_injection_plan_check_accepts_existing_context_refs():
    context_event = _event(
        EventType.CONTEXT_ADDED,
        {"context": {"context_id": "ctx_present"}},
    )
    plan_event = _event(
        EventType.INJECTION_PLAN_RECORDED,
        {
            "injection_plan": {
                "plan_id": "plan_1",
                "selected": [{"context_id": "ctx_present"}],
                "warned": [],
                "excluded": [],
            }
        },
    )

    check = check_injection_plan_refs([context_event, plan_event])

    assert check.check_id == "recorded_injection_plan_context_refs"
    assert check.severity == DoctorSeverity.OK
