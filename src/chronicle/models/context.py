"""Context object model."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, model_validator

from chronicle.models.source import SourceProvenance
from chronicle.models.visibility import VisibilityHint


class ContextScope(StrEnum):
    """Formal scope of a Context (v0.2).

    Replaces the v0.1 ScopeHint.  The old scope hint is still accepted
    for backward compatibility; Context.model_validate() will populate
    ``scope`` from ``scope_hint`` when ``scope`` is missing.
    """

    GLOBAL = "global"
    PROJECT = "project"
    SESSION = "session"
    TASK = "task"
    ARTIFACT = "artifact"
    TEMPORARY = "temporary"
    UNKNOWN = "unknown"


class ScopeHint(StrEnum):
    """Deprecated scope hint (v0.1 compatibility).

    Kept for reading legacy JSONL payloads.  New code should use
    :class:`ContextScope` via the ``scope`` field.
    """

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
    scope: ContextScope = ContextScope.UNKNOWN
    scope_hint: ScopeHint | None = None
    visibility_hint: VisibilityHint = VisibilityHint.UNKNOWN
    source: SourceProvenance | None = None
    confidence: Confidence = Confidence.MEDIUM
    created_at: datetime
    tags: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _ensure_scope(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "scope" not in data and "scope_hint" in data:
                data["scope"] = data["scope_hint"]
            # Keep scope_hint in the dict so legacy consumers still see it
        return data
