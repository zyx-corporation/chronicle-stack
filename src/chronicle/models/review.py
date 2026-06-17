"""Review decision models.

Review decisions are local records that move generated or prepared outputs
through approve / reject / request-changes states. They do not invoke any AI
runtime and do not imply correctness certification.
"""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel

from chronicle.models.summary_job import SummaryJobStatus


class ReviewAction(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_CHANGES = "request_changes"


class ReviewTargetType(StrEnum):
    SUMMARY_JOB = "summary_job"


class ReviewDecision(BaseModel):
    review_id: str
    chronicle_id: str
    target_type: ReviewTargetType
    target_id: str
    action: ReviewAction
    resulting_status: SummaryJobStatus
    reviewer: str = "reviewer"
    reason: str = ""
    created_at: datetime
    event_id: str | None = None
