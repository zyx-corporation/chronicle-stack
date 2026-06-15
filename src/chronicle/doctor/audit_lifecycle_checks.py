"""Audit and lifecycle doctor checks."""

from chronicle.doctor.check_factory import ok, warn
from chronicle.models.doctor import DoctorCheck
from chronicle.store.audit_log_store import AuditLogStore
from chronicle.store.lifecycle_store import LifecycleStore
from chronicle.store.paths import ChroniclePaths


def check_audit_lifecycle_surfaces(paths: ChroniclePaths) -> list[DoctorCheck]:
    """Check audit and lifecycle JSONL surfaces."""
    return [
        check_audit_log_surface(paths),
        check_lifecycle_surface(paths),
    ]


def check_audit_log_surface(paths: ChroniclePaths) -> DoctorCheck:
    store = AuditLogStore(paths.audit_file)
    corrupt = store.count_corrupt_lines()
    if corrupt:
        return warn(
            "security_audit_log_parseable",
            "audit.jsonl contains parse errors",
            detail=f"{corrupt} corrupt line(s)",
            recommendation="repair audit.jsonl or recreate audit events with `chronicle audit record ...`",
        )
    if paths.audit_file.exists():
        return ok("security_audit_log_parseable", "audit.jsonl is parseable")
    return warn(
        "security_audit_log_parseable",
        "audit.jsonl is not present",
        recommendation="record a local audit event with `chronicle audit record --operation export --purpose <purpose>`",
    )


def check_lifecycle_surface(paths: ChroniclePaths) -> DoctorCheck:
    store = LifecycleStore(paths.lifecycle_file)
    corrupt = store.count_corrupt_lines()
    if corrupt:
        return warn(
            "security_lifecycle_log_parseable",
            "lifecycle.jsonl contains parse errors",
            detail=f"{corrupt} corrupt line(s)",
            recommendation="repair lifecycle.jsonl or recreate lifecycle markers with `chronicle lifecycle record ...`",
        )
    if paths.lifecycle_file.exists():
        return ok("security_lifecycle_log_parseable", "lifecycle.jsonl is parseable")
    return warn(
        "security_lifecycle_log_parseable",
        "lifecycle.jsonl is not present",
        recommendation="record an advisory lifecycle marker with `chronicle lifecycle record --target <id> --action seal`",
    )
