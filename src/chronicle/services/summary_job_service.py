"""Summary job service.

This service creates local summary draft jobs and draft summary artifacts. It
does not invoke LLMs, embedding providers, vector DBs, graph DBs, GraphRAG
runtimes, or external services.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from chronicle.ids import generate_id
from chronicle.models.artifact import ArtifactType
from chronicle.models.event import Actor, EventType, ReviewStatus
from chronicle.models.runtime import RuntimeConfig, disabled_runtime_status
from chronicle.models.summary_job import SummaryJob, SummaryJobProvenance, SummaryJobStatus, SummarySourceRef
from chronicle.services.artifact_service import ArtifactService
from chronicle.services.chronicle_service import ChronicleService


class SummaryJobService:
    def __init__(self, root: Path | None = None) -> None:
        self.chronicle = ChronicleService(root)
        self.artifacts = ArtifactService(root)

    def create_manual_draft(
        self,
        title: str,
        summary_text: str,
        source_refs: list[SummarySourceRef] | None = None,
        prompt: str = "",
        operator: str = "user",
        tags: list[str] | None = None,
    ) -> SummaryJob:
        """Create a local summary draft without invoking any AI runtime."""

        metadata = self.chronicle.require_initialized()
        now = datetime.now(timezone.utc).astimezone()
        summary_job_id = generate_id("summary_job")

        runtime_status = disabled_runtime_status()
        runtime_config = RuntimeConfig.model_validate(runtime_status.config.model_dump(mode="json"))

        provenance = SummaryJobProvenance(
            runtime=runtime_config,
            prompt=prompt,
            operator=operator,
            generated_by="manual",
            external_call_made=False,
            generated_at=now,
        )

        artifact, version = self.artifacts.create(
            title=title,
            artifact_type=ArtifactType.SUMMARY,
            content=summary_text,
            tags=["summary-job", summary_job_id, *(tags or [])],
            actor=Actor.USER,
        )

        event = self.chronicle.record_event(
            event_type=EventType.SUMMARY_JOB_CREATED,
            actor=Actor.USER,
            summary=f"Summary job created: {title}",
            payload={
                "summary_job_id": summary_job_id,
                "artifact_id": artifact.artifact_id,
                "version_id": version.version_id,
                "status": SummaryJobStatus.PENDING_REVIEW.value,
                "external_call_made": False,
            },
            artifact_id=artifact.artifact_id,
            review_status=ReviewStatus.NEEDS_REVIEW,
            tags=["summary-job", "pending-review"],
        )

        job = SummaryJob(
            summary_job_id=summary_job_id,
            chronicle_id=metadata.chronicle_id,
            title=title,
            summary_text=summary_text,
            status=SummaryJobStatus.PENDING_REVIEW,
            source_refs=source_refs or [],
            provenance=provenance,
            artifact_id=artifact.artifact_id,
            version_id=version.version_id,
            event_id=event.event_id,
            tags=tags or [],
        )

        self.chronicle.paths.summary_jobs_dir.mkdir(parents=True, exist_ok=True)
        self.chronicle.paths.summary_job_path(summary_job_id).write_text(
            json.dumps(job.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return job

    def list_jobs(self) -> list[SummaryJob]:
        self.chronicle.require_initialized()
        jobs_dir = self.chronicle.paths.summary_jobs_dir
        if not jobs_dir.exists():
            return []
        jobs: list[SummaryJob] = []
        for path in sorted(jobs_dir.glob("sum_*.json")):
            jobs.append(SummaryJob.model_validate_json(path.read_text(encoding="utf-8")))
        return jobs

    def get(self, summary_job_id: str) -> SummaryJob:
        self.chronicle.require_initialized()
        path = self.chronicle.paths.summary_job_path(summary_job_id)
        return SummaryJob.model_validate_json(path.read_text(encoding="utf-8"))
