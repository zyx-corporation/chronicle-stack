"""RDE Diff Record model."""

from datetime import datetime

from pydantic import BaseModel, Field


class RdeDiffRecord(BaseModel):
    rde_record_id: str
    artifact_id: str
    from_version_id: str
    to_version_id: str
    created_at: datetime
    created_by: str
    summary: str = ""
    preserved: list[str] = Field(default_factory=list)
    transformed: list[str] = Field(default_factory=list)
    supplemented: list[str] = Field(default_factory=list)
    unresolved: list[str] = Field(default_factory=list)
    deviation_risks: list[str] = Field(default_factory=list)
    next_update_policy: list[str] = Field(default_factory=list)
