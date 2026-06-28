"""Chronicle object models for federated meaning units."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from chronicle.models.visibility import VisibilityHint


class ChronicleObjectType(StrEnum):
    QUESTION = "question"
    CONVERSATION = "conversation"
    DECISION = "decision"
    ARTIFACT = "artifact"
    DELTA = "delta"
    OBJECTION = "objection"
    HYPOTHESIS = "hypothesis"
    DECAY = "decay"


class ChronicleObjectLifecycleState(StrEnum):
    ACTIVE = "active"
    EXPIRED = "expired"
    RETRACTED = "retracted"
    TOMBSTONED = "tombstoned"
    HIDDEN = "hidden"


class ChronicleObjectAiInvolvement(BaseModel):
    involved: bool = False
    models: list[str] = Field(default_factory=list)


class ChronicleObjectLifecycle(BaseModel):
    state: ChronicleObjectLifecycleState = ChronicleObjectLifecycleState.ACTIVE
    retention: str | None = None


class ChronicleObjectRecord(BaseModel):
    object_id: str
    object_type: ChronicleObjectType
    chronicle_id: str
    created_at: datetime
    created_by: str
    summary: str
    detail: str = ""
    visibility_hint: VisibilityHint = VisibilityHint.UNKNOWN
    source_event_id: str | None = None
    origin_question_id: str | None = None
    artifact_id: str | None = None
    context_id: str | None = None
    decision_id: str | None = None
    rde_record_id: str | None = None
    evidence: list[str] = Field(default_factory=list)
    related_object_ids: list[str] = Field(default_factory=list)
    ai_involvement: ChronicleObjectAiInvolvement = Field(
        default_factory=ChronicleObjectAiInvolvement
    )
    lifecycle: ChronicleObjectLifecycle = Field(default_factory=ChronicleObjectLifecycle)
    derived: bool = False
