"""Model-context use dry-run models.

These models describe a check result for using Chronicle records as model
context. They do not submit records to any model service.
"""

from enum import StrEnum

from pydantic import BaseModel, Field


class ContextUseTarget(StrEnum):
    """Target environment for model-context use."""

    LOCAL = "local"
    EXTERNAL = "external"


class ContextUseSeverity(StrEnum):
    """Severity for model-context use findings."""

    OK = "ok"
    WARNING = "warning"
    BLOCKED = "blocked"


class ContextUseFinding(BaseModel):
    """A finding for one context considered for model-context use."""

    context_id: str
    title: str = ""
    severity: ContextUseSeverity
    summary: str
    detail: str = ""
    recommendation: str = ""


class ContextUseCheckReport(BaseModel):
    """Dry-run report for model-context use."""

    status: ContextUseSeverity
    target: ContextUseTarget
    purpose: str
    context_count: int = 0
    findings: list[ContextUseFinding] = Field(default_factory=list)
