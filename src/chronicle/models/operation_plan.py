"""Operation plan models for Stage 2 preview-first proposal flows."""

from __future__ import annotations

from pydantic import BaseModel, Field


class OperationPlanTargetRef(BaseModel):
    record_id: str
    record_type: str
    expected_version_id: str = ""


class OperationPlanStep(BaseModel):
    step_id: str
    capability: str
    action: str
    parameters: dict[str, str] = Field(default_factory=dict)


class OperationPlanReviewPolicy(BaseModel):
    required: bool = True


class OperationPlanRdePolicy(BaseModel):
    required: bool = True


class OperationPlanRollbackPolicy(BaseModel):
    mode: str = "compensating_event"


class OperationPlan(BaseModel):
    plan_id: str
    plan_type: str
    operation: str
    target_refs: list[OperationPlanTargetRef]
    source_refs: list[str] = Field(default_factory=list)
    steps: list[OperationPlanStep] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    constraints: dict[str, list[str]] = Field(default_factory=lambda: {"preserve": []})
    review: OperationPlanReviewPolicy = Field(default_factory=OperationPlanReviewPolicy)
    rde: OperationPlanRdePolicy = Field(default_factory=OperationPlanRdePolicy)
    rollback: OperationPlanRollbackPolicy = Field(default_factory=OperationPlanRollbackPolicy)
    preview_only: bool = True
