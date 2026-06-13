"""Chronicle doctor health check models (v0.4)."""

from enum import StrEnum

from pydantic import BaseModel, Field


class DoctorSeverity(StrEnum):
    """Severity for a doctor check."""

    OK = "ok"
    WARNING = "warning"
    ERROR = "error"


class DoctorCheck(BaseModel):
    """Single read-only diagnostic result."""

    check_id: str
    severity: DoctorSeverity
    summary: str
    detail: str = ""
    recommendation: str = ""


class DoctorReport(BaseModel):
    """Read-only health report for a Chronicle project."""

    status: DoctorSeverity
    chronicle_id: str | None = None
    checks: list[DoctorCheck] = Field(default_factory=list)

    @classmethod
    def from_checks(
        cls,
        checks: list[DoctorCheck],
        *,
        chronicle_id: str | None = None,
    ) -> "DoctorReport":
        """Create a report and aggregate status from checks."""
        if any(check.severity == DoctorSeverity.ERROR for check in checks):
            status = DoctorSeverity.ERROR
        elif any(check.severity == DoctorSeverity.WARNING for check in checks):
            status = DoctorSeverity.WARNING
        else:
            status = DoctorSeverity.OK
        return cls(status=status, chronicle_id=chronicle_id, checks=checks)
