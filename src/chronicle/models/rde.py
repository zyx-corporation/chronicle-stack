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


class RdeDraftMemo(BaseModel):
    mode: str = "manual"
    source_chronicle_id: str
    artifact_id: str
    from_version_id: str
    to_version_id: str
    summary: str = ""
    preserved: list[str] = Field(default_factory=list)
    transformed: list[str] = Field(default_factory=list)
    supplemented: list[str] = Field(default_factory=list)
    unresolved: list[str] = Field(default_factory=list)
    deviation_risks: list[str] = Field(default_factory=list)
    next_update_policy: list[str] = Field(default_factory=list)
    ai_summary: str = ""
    ai_response: str | None = None
    ai_model: str | None = None
    runtime_label: str | None = None
    interpretation: str | None = None
    interpretation_kind: str = "hypothesis"
    decay_target: bool = True
    recorded_rde_id: str | None = None
    linked_delta_object_id: str | None = None
    linked_hypothesis_object_id: str | None = None
    notes: list[str] = Field(default_factory=list)
