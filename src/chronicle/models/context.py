"""Context object model."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ScopeHint(StrEnum):
    GLOBAL = "global"
    PROJECT = "project"
    SESSION = "session"
    TASK = "task"
    ARTIFACT = "artifact"
    TEMPORARY = "temporary"
    UNKNOWN = "unknown"


class Confidence(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class Context(BaseModel):
    context_id: str
    title: str
    summary: str = ""
    source_type: str = "conversation"
    source_ref: str = ""
    scope_hint: ScopeHint = ScopeHint.UNKNOWN
    confidence: Confidence = Confidence.MEDIUM
    created_at: datetime
    tags: list[str] = Field(default_factory=list)
