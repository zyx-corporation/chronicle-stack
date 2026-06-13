"""Context Boundary Rule model (v0.2).

Boundary Rules are *advisory* — they record conditions under which a
Context should be included, excluded, or trigger a warning during
injection planning.  They are NOT an access-control or enforcement
system.
"""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class BoundaryRuleType(StrEnum):
    INCLUDE = "include"
    EXCLUDE = "exclude"
    WARN = "warn"


class BoundaryConditionField(StrEnum):
    SCOPE = "scope"
    VISIBILITY = "visibility"
    SOURCE_TYPE = "source_type"
    SOURCE_TOOL = "source_tool"
    SOURCE_SESSION = "source_session"
    SOURCE_MODEL = "source_model"
    TAG = "tag"


class BoundaryOperator(StrEnum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    IN = "in"
    CONTAINS = "contains"


class BoundaryRule(BaseModel):
    rule_id: str
    rule_type: BoundaryRuleType
    field: BoundaryConditionField
    operator: BoundaryOperator
    value: str | list[str]
    reason: str = ""
    created_at: datetime
    enabled: bool = True
    tags: list[str] = Field(default_factory=list)


class BoundaryEvaluation(BaseModel):
    rule_id: str
    rule_type: BoundaryRuleType
    matched: bool
    reason: str = ""
