"""Artifact file doctor checks."""

from chronicle.doctor.check_factory import ok, warn
from chronicle.models.doctor import DoctorCheck
from chronicle.models.event import ChronicleEvent
from chronicle.store.paths import ChroniclePaths


def check_artifact_files(paths: ChroniclePaths, events: list[ChronicleEvent]) -> DoctorCheck:
    missing: set[str] = set()
    for artifact_id, version_id in _artifact_refs(events):
        if not paths.artifact_current(artifact_id).exists():
            missing.add(f"{artifact_id}: current.md")
        if version_id:
            version_path = paths.artifact_version_path(artifact_id, version_id)
            if not version_path.exists():
                missing.add(f"{artifact_id}: versions/{version_id}.md")

    if missing:
        return warn(
            "artifact_files_present",
            "one or more artifact files are missing",
            detail="; ".join(sorted(missing)),
        )
    return ok("artifact_files_present", "artifact files are present")


def _artifact_refs(events: list[ChronicleEvent]) -> set[tuple[str, str | None]]:
    refs: set[tuple[str, str | None]] = set()
    for event in events:
        artifact = event.payload.get("artifact")
        if isinstance(artifact, dict) and artifact.get("artifact_id"):
            refs.add((artifact["artifact_id"], None))
        version = event.payload.get("version")
        if isinstance(version, dict) and version.get("artifact_id"):
            refs.add((version["artifact_id"], version.get("version_id")))
    return refs
