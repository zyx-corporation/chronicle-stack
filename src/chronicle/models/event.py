"""Chronicle Event model."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from chronicle.models.classification import ClassificationMetadata
from chronicle.models.source import SourceProvenance


class EventType(StrEnum):
    CHRONICLE_CREATED = "chronicle_created"
    CONTEXT_ADDED = "context_added"
    USER_INPUT = "user_input"
    ASSISTANT_OUTPUT = "assistant_output"
    ARTIFACT_CREATED = "artifact_created"
    ARTIFACT_UPDATED = "artifact_updated"
    ARTIFACT_VERSIONED = "artifact_versioned"
    DECISION_RECORDED = "decision_recorded"
    RDE_DIFF_RECORDED = "rde_diff_recorded"
    NOTE_ADDED = "note_added"
    TAG_UPDATED = "tag_updated"
    METADATA_UPDATED = "metadata_updated"
    BOUNDARY_RULE_ADDED = "boundary_rule_added"
    INJECTION_PLAN_RECORDED = "injection_plan_recorded"


class Actor(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"
    REVIEWER = "reviewer"
    IMPORTER = "importer"


class Confidence(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class ReviewStatus(StrEnum):
    UNREVIEWED = "unreviewed"
    REVIEWED = "reviewed"
    NEEDS_REVIEW = "needs_review"


# Backward-compatible alias for v0.1 consumers.
SourceRef = SourceProvenance


class ChronicleEvent(BaseModel):
    event_id: str
    chronicle_id: str
    timestamp: datetime
    event_type: EventType
    actor: Actor
    summary: str
    payload: dict[str, Any] = Field(default_factory=dict)
    parent_event_id: str | None = None
    artifact_id: str | None = None
    context_ids: list[str] = Field(default_factory=list)
    decision_id: str | None = None
    rde_record_id: str | None = None
    source: SourceProvenance | None = None
    classification: ClassificationMetadata | None = None
    confidence: Confidence | None = None
    review_status: ReviewStatus | None = None
    tags: list[str] = Field(default_factory=list)

    def to_jsonl(self) -> str:
        return self.model_dump_json(exclude_none=True)
