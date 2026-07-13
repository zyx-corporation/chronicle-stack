"""Static capability registry models for Stage 2."""

from enum import StrEnum

from pydantic import BaseModel, Field


class CapabilityExposure(StrEnum):
    INTERNAL = "internal"
    CLI = "cli"
    UI = "ui"
    STABLE_ISH = "stable-ish"


class CapabilityManifest(BaseModel):
    capability_id: str
    version: str = "1"
    title: str
    summary: str
    operation_family: str
    exposure: CapabilityExposure = CapabilityExposure.INTERNAL
    input_schema_ref: str = ""
    output_schema_ref: str = ""
    context_scope: str = "none"
    reads_record_kinds: list[str] = Field(default_factory=list)
    emits_proposal_kinds: list[str] = Field(default_factory=list)
    uses_network: bool = False
    mutates_primary_record: bool = False
    review_required: bool = True
    enabled_by_default: bool = True
    implementation_status: str = "available"
    notes: list[str] = Field(default_factory=list)
