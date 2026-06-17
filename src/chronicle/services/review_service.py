"""Review decision service."""

import json
from datetime import datetime, timezone
from pathlib import Path

from chronicle.ids import generate_id
from chronicle.models.event import Actor, EventType, ReviewStatus
from chronicle.models.review import ReviewAction, ReviewDecision, ReviewTargetType
from chronicle.models.summary_job import SummaryJob, SummaryJobStatus
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.summary_job_service import SummaryJobService


class ReviewService:
    def __init__(self, root: Path | None = None) -> None:
        self.chronicle = ChronicleService(root)
        self.summary_jobs = SummaryJobService(root)

    def list_decisions(self) -> list[ReviewDecision]:
        self.chronicle.require_initialized()
        reviews_dir = self.chronicle.paths.reviews_dir
        if not reviews_dir.exists():
            return []
        decisions: list[ReviewDecision] = []
        for path in sorted(reviews_dir.glob("rvw_*.json")):
            decisions.append(ReviewDecision.model_validate_json(path.read_text(encoding="utf-8")))
        return decisions

    def list_review_queue(self) -> list[SummaryJob]:
        return [
            job for job in self.summary_jobs.list_jobs()
            if job.status in {SummaryJobStatus.PENDING_REVIEW, SummaryJobStatus.REQUEST_CHANGES}
        ]

    def decide_summary_job(
        self,
        summary_job_id: str,
        action: ReviewAction,
        reason: str = "",
        reviewer: str = "reviewer",
    ) -> ReviewDecision:
        metadata = self.chronicle.require_initialized()
        job = self.summary_jobs.get(summary_job_id)
        now = datetime.now(timezone.utc).astimezone()
        review_id = generate_id("review")

        resulting_status = {
            ReviewAction.APPROVE: SummaryJobStatus.APPROVED,
            ReviewAction.REJECT: SummaryJobStatus.REJECTED,
            ReviewAction.REQUEST_CHANGES: SummaryJobStatus.REQUEST_CHANGES,
        }[action]

        updated_job = job.model_copy(update={"status": resulting_status})
        self._write_summary_job(updated_job)

        event = self.chronicle.record_event(
            event_type=EventType.REVIEW_DECISION_RECORDED,
            actor=Actor.REVIEWER,
            summary=f"Review decision {action.value}: {summary_job_id}",
            payload={
                "review_id": review_id,
                "target_type": ReviewTargetType.SUMMARY_JOB.value,
                "target_id": summary_job_id,
                "action": action.value,
                "resulting_status": resulting_status.value,
                "reason": reason,
                "reviewer": reviewer,
            },
            artifact_id=job.artifact_id,
            review_status=ReviewStatus.REVIEWED if resulting_status != SummaryJobStatus.REQUEST_CHANGES else ReviewStatus.NEEDS_REVIEW,
            tags=["review", action.value, resulting_status.value],
        )

        decision = ReviewDecision(
            review_id=review_id,
            chronicle_id=metadata.chronicle_id,
            target_type=ReviewTargetType.SUMMARY_JOB,
            target_id=summary_job_id,
            action=action,
            resulting_status=resulting_status,
            reviewer=reviewer,
            reason=reason,
            created_at=now,
            event_id=event.event_id,
        )
        self.chronicle.paths.reviews_dir.mkdir(parents=True, exist_ok=True)
        self.chronicle.paths.review_decision_path(review_id).write_text(
            json.dumps(decision.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return decision

    def _write_summary_job(self, job: SummaryJob) -> None:
        self.chronicle.paths.summary_jobs_dir.mkdir(parents=True, exist_ok=True)
        self.chronicle.paths.summary_job_path(job.summary_job_id).write_text(
            json.dumps(job.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
