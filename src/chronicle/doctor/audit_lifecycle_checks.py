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
            recommendation="repair or remove corrupted audit JSONL lines",
        )
    if paths.audit_file.exists():
        return ok("security_audit_log_parseable", "audit.jsonl is parseable")
    return warn(
        "security_audit_log_parseable",
        "audit.jsonl is not present",
        recommendation="record audit events for export, context-use, and reinterpretation workflows",
    )


def check_lifecycle_surface(paths: ChroniclePaths) -> DoctorCheck:
    store = LifecycleStore(paths.lifecycle_file)
    corrupt = store.count_corrupt_lines()
    if corrupt:
        return warn(
            "security_lifecycle_log_parseable",
            "lifecycle.jsonl contains parse errors",
            detail=f"{corrupt} corrupt line(s)",
            recommendation="repair or remove corrupted lifecycle JSONL lines",
        )
    if paths.lifecycle_file.exists():
        return ok("security_lifecycle_log_parseable", "lifecycle.jsonl is parseable")
    return warn(
        "security_lifecycle_log_parseable",
        "lifecycle.jsonl is not present",
        recommendation="record lifecycle events for redact, seal, tombstone, and retention workflows",
    )
