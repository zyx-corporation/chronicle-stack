"""Package review models for v0.8 verified export workflows."""

from enum import StrEnum

from pydantic import BaseModel, Field


class PackageReviewStatus(StrEnum):
    """Overall package review status."""

    PASS = "pass"
    WARNING = "warning"
    BLOCKED = "blocked"


class PackageReviewFinding(BaseModel):
    """A package review finding for one warning or boundary condition."""

    severity: PackageReviewStatus
    code: str
    summary: str
    record_id: str | None = None
    recommendation: str = ""


class PackageReviewReport(BaseModel):
    """Review report for a controlled integration package."""

    status: PackageReviewStatus
    purpose: str
    target_environment: str
    record_count: int
    output_classification: str
    package_warnings: list[str] = Field(default_factory=list)
    findings: list[PackageReviewFinding] = Field(default_factory=list)

    @property
    def blocked(self) -> bool:
        return self.status == PackageReviewStatus.BLOCKED
