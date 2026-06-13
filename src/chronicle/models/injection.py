"""Context Injection Plan model (v0.2).

An InjectionPlan is a rule-based *suggestion* for which Contexts
should be used for a given task.  It does NOT inject anything into
an LLM — it is a human-reviewable context selection aid.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class InjectionPlanContextRef(BaseModel):
    context_id: str
    title: str
    scope: str
    visibility_hint: str
    reason: str = ""
    matched_rules: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class InjectionPlan(BaseModel):
    plan_id: str
    task: str
    created_at: datetime
    selected: list[InjectionPlanContextRef] = Field(default_factory=list)
    warned: list[InjectionPlanContextRef] = Field(default_factory=list)
    excluded: list[InjectionPlanContextRef] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
