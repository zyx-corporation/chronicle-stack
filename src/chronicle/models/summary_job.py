"""Summarization job models.

Summary jobs represent AI-assisted or manually supplied summary drafts. They do
not imply that an LLM has been called, and they are not accepted Chronicle
records until reviewed.
"""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from chronicle.models.runtime import RuntimeConfig


class SummaryJobStatus(StrEnum):
    """Review state for generated or prepared summaries."""

    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUEST_CHANGES = "request_changes"


class SummarySourceRef(BaseModel):
    """Source record reference for a summary job."""

    record_id: str
    record_type: str = "event"
    note: str = ""


class SummaryJobProvenance(BaseModel):
    """Generation provenance for a summary job."""

    runtime: RuntimeConfig = Field(default_factory=RuntimeConfig)
    invocation_mode: str = "explicit-manual"
    prompt: str = ""
    operator: str = "user"
    generated_by: str = "manual"
    external_call_made: bool = False
    generated_at: datetime


class SummaryJob(BaseModel):
    """Local summary job.

    The summary text is a draft artifact. It is not accepted output unless a
    later review workflow approves it.
    """

    summary_job_id: str
    chronicle_id: str
    title: str
    summary_text: str
    status: SummaryJobStatus = SummaryJobStatus.DRAFT
    source_refs: list[SummarySourceRef] = Field(default_factory=list)
    provenance: SummaryJobProvenance
    artifact_id: str | None = None
    version_id: str | None = None
    event_id: str | None = None
    tags: list[str] = Field(default_factory=list)
