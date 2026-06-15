"""Storage and derived index doctor checks."""

from chronicle.doctor.check_factory import err, ok, warn
from chronicle.models.doctor import DoctorCheck
from chronicle.models.event import ChronicleEvent, EventType
from chronicle.store.paths import ChroniclePaths


def check_required_files(paths: ChroniclePaths) -> list[DoctorCheck]:
    checks: list[DoctorCheck] = []
    if paths.chronicle_dir.exists():
        checks.append(ok("chronicle_dir_exists", ".chronicle directory exists"))
    else:
        checks.append(
            err(
                "chronicle_dir_exists",
                ".chronicle directory is missing",
                recommendation="run `chronicle init --title ...`",
            )
        )

    if paths.events_file.exists():
        checks.append(ok("chronicle_jsonl_exists", "chronicle.jsonl exists"))
    else:
        checks.append(
            err(
                "chronicle_jsonl_exists",
                "chronicle.jsonl is missing",
                recommendation="run `chronicle init --title ...`",
            )
        )

    if paths.metadata_file.exists():
        checks.append(ok("metadata_exists", "metadata.yaml exists"))
    else:
        checks.append(
            warn(
                "metadata_exists",
                "metadata.yaml is missing",
                recommendation="restore metadata.yaml or re-initialize carefully",
            )
        )
    return checks


def check_known_event_types(events: list[ChronicleEvent]) -> DoctorCheck:
    known = {event_type.value for event_type in EventType}
    unknown = sorted({event.event_type.value for event in events if event.event_type.value not in known})
    if unknown:
        return warn(
            "known_event_types",
            "chronicle.jsonl contains unknown event types",
            detail=", ".join(unknown),
        )
    return ok("known_event_types", "all event types are known")


def check_indexes(paths: ChroniclePaths) -> DoctorCheck:
    expected = [
        paths.artifact_index_file,
        paths.context_index_file,
        paths.decision_index_file,
        paths.rde_index_file,
        paths.boundary_rule_index_file,
    ]
    missing = [path.name for path in expected if not path.exists()]
    if missing:
        return warn(
            "indexes_present",
            "one or more derived indexes are missing",
            detail=", ".join(missing),
            recommendation="run `chronicle index rebuild`",
        )
    return ok("indexes_present", "derived indexes are present")
