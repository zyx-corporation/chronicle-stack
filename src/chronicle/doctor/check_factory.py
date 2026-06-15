"""Helpers for constructing doctor checks."""

from chronicle.models.doctor import DoctorCheck, DoctorSeverity


def check(
    check_id: str,
    severity: DoctorSeverity,
    summary: str,
    detail: str = "",
    recommendation: str = "",
) -> DoctorCheck:
    return DoctorCheck(
        check_id=check_id,
        severity=severity,
        summary=summary,
        detail=detail,
        recommendation=recommendation,
    )


def ok(check_id: str, summary: str, detail: str = "") -> DoctorCheck:
    return check(check_id, DoctorSeverity.OK, summary, detail)


def warn(
    check_id: str,
    summary: str,
    detail: str = "",
    recommendation: str = "",
) -> DoctorCheck:
    return check(check_id, DoctorSeverity.WARNING, summary, detail, recommendation)


def err(
    check_id: str,
    summary: str,
    detail: str = "",
    recommendation: str = "",
) -> DoctorCheck:
    return check(check_id, DoctorSeverity.ERROR, summary, detail, recommendation)
