"""Meaningful reaction models for the Context SNS surface."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ChronicleReactionType(StrEnum):
    UNDERSTOOD = "understood"
    HOLD = "hold"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    REOPEN_REVIEW = "reopen_review"
    DIFFERS_BY_CONTEXT = "differs_by_context"
    IMPORT_TO_LOCAL_NODE = "import_to_local_node"
    REFERENCE = "reference"
    OBJECT = "object"
    PROPOSE_COLLABORATION = "propose_collaboration"


class ChronicleReactionRecord(BaseModel):
    reaction_id: str
    chronicle_id: str
    reaction_type: ChronicleReactionType
    created_at: datetime
    created_by: str
    target_object_id: str
    source_object_id: str | None = None
    target_context_id: str | None = None
    target_artifact_id: str | None = None
    target_decision_id: str | None = None
    summary: str
    detail: str = ""
    related_object_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)

