"""Decision model."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class DecisionType(StrEnum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    REVISED = "revised"
    DEFERRED = "deferred"
    SUPERSEDED = "superseded"
    MERGED = "merged"
    SPLIT = "split"
    NEEDS_REVIEW = "needs_review"


class Decision(BaseModel):
    decision_id: str
    chronicle_id: str
    artifact_id: str | None = None
    event_id: str | None = None
    decision_type: DecisionType
    decided_by: str
    decided_at: datetime
    reason: str = ""
    alternatives: list[str] = Field(default_factory=list)
    notes: str = ""
