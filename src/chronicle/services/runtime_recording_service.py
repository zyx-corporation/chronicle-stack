"""Chronicle-side persistence for runtime outcomes and plans."""

from __future__ import annotations

from pathlib import Path

from chronicle.models.artifact import ArtifactType
from chronicle.models.event import Actor, Confidence, EventType, ReviewStatus
from chronicle.models.runtime import (
    RuntimeConfig,
    RuntimeExecutionResult,
    RuntimeInvocationPlan,
    RuntimeProviderKind,
    RuntimeRetrievalPlan,
    RuntimeSummaryResult,
)
from chronicle.models.summary_job import SummarySourceRef
from chronicle.models.source import SourceProvenance
from chronicle.services.artifact_service import ArtifactService
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.summary_job_service import SummaryJobService


class RuntimeRecordingService:
    """Persist runtime-facing derived records without performing execution."""

    def __init__(self, root: Path | None = None) -> None:
        self.chronicle = ChronicleService(root)
        self.summary_jobs = SummaryJobService(root)
        self.artifacts = ArtifactService(root)

    def create_summary_draft(
        self,
        *,
        title: str,
        result: RuntimeSummaryResult,
        runtime_config: RuntimeConfig,
        prompt: str,
        operator: str,
        source_refs: list[SummarySourceRef],
        tags: list[str],
    ):
        return self.summary_jobs.create_runtime_draft(
            title=title,
            summary_text=result.generated_text,
            runtime_config=runtime_config,
            invocation_mode=result.invocation_mode,
            external_call_made=result.external_call_made,
            generated_by="runtime_http_manual" if result.external_call_made else "runtime_manual",
            prompt=prompt,
            operator=operator,
            response_metadata=result.response_metadata,
            response_keys=result.response_keys,
            source_refs=source_refs,
            tags=tags,
        )

    def create_execution_draft_summary(
        self,
        *,
        title: str,
        result: RuntimeExecutionResult,
        runtime_config: RuntimeConfig,
        prompt: str,
        operator: str,
        source_refs: list[SummarySourceRef],
        tags: list[str],
    ):
        return self.summary_jobs.create_runtime_draft(
            title=title,
            summary_text=result.output_text,
            runtime_config=runtime_config,
            invocation_mode=result.invocation_mode,
            external_call_made=result.external_call_made,
            generated_by="runtime_http_manual" if result.external_call_made else "runtime_manual",
            prompt=prompt,
            operator=operator,
            response_metadata=result.response_metadata,
            response_keys=result.response_keys,
            source_refs=source_refs,
            tags=tags,
        )

    def create_execution_artifact(
        self,
        *,
        title: str,
        artifact_type: ArtifactType,
        result: RuntimeExecutionResult,
    ):
        return self.artifacts.create(
            title=title,
            artifact_type=artifact_type,
            content=result.output_text,
            tags=["runtime-output", result.operation, result.provider_kind.value],
            source=SourceProvenance(
                source_type="runtime",
                source_ref=f"configured-provider-{result.operation}",
                source_tool="chronicle-runtime",
                source_model=result.model_name,
            ),
            actor=Actor.ASSISTANT,
        )

    def persist_summary_result(self, result: RuntimeSummaryResult) -> str:
        event = self.chronicle.record_event(
            event_type=EventType.ASSISTANT_OUTPUT,
            actor=Actor.ASSISTANT,
            summary=f"Runtime summary generated: {_truncate_summary(result.generated_text)}",
            payload={
                "runtime_summary": result.model_dump(mode="json"),
                "runtime_provider": result.provider_kind.value,
            },
            source=SourceProvenance(
                source_type="runtime",
                source_ref="configured-provider-summary" if result.external_call_made else "local-placeholder-summary",
                source_tool="chronicle-runtime",
                source_model=result.model_name,
            ),
            review_status=ReviewStatus.NEEDS_REVIEW,
            confidence=Confidence.LOW,
        )
        return event.event_id

    def persist_execution_result(self, result: RuntimeExecutionResult) -> str:
        event = self.chronicle.record_event(
            event_type=EventType.ASSISTANT_OUTPUT,
            actor=Actor.ASSISTANT,
            summary=f"Runtime {result.operation} generated: {_truncate_summary(result.output_text)}",
            payload={
                "runtime_execution": result.model_dump(mode="json"),
                "runtime_provider": result.provider_kind.value,
            },
            source=SourceProvenance(
                source_type="runtime",
                source_ref=f"configured-provider-{result.operation}",
                source_tool="chronicle-runtime",
                source_model=result.model_name,
            ),
            review_status=ReviewStatus.NEEDS_REVIEW,
            confidence=Confidence.LOW,
        )
        return event.event_id

    def persist_retrieval_plan(self, plan: RuntimeRetrievalPlan) -> str:
        event = self.chronicle.record_event(
            event_type=EventType.ASSISTANT_OUTPUT,
            actor=Actor.ASSISTANT,
            summary=f"Runtime retrieval plan generated: {_truncate_summary(plan.query)}",
            payload={
                "runtime_retrieval_plan": plan.model_dump(mode="json"),
                "runtime_provider": RuntimeProviderKind.LOCAL.value,
            },
            source=SourceProvenance(
                source_type="runtime",
                source_ref="local-placeholder-retrieve-plan",
                source_tool="chronicle-runtime",
                source_model="local-placeholder",
            ),
            review_status=ReviewStatus.NEEDS_REVIEW,
            confidence=Confidence.LOW,
        )
        return event.event_id

    def persist_invocation_plan(self, plan: RuntimeInvocationPlan, *, summary_label: str | None = None) -> str:
        event = self.chronicle.record_event(
            event_type=EventType.ASSISTANT_OUTPUT,
            actor=Actor.ASSISTANT,
            summary=(
                f"Runtime invocation plan generated: {summary_label}"
                if summary_label
                else f"Runtime invocation plan generated: {plan.provider_kind.value} {plan.operation}"
            ),
            payload={
                "runtime_invocation_plan": plan.model_dump(mode="json"),
                "runtime_provider": plan.provider_kind.value,
            },
            source=SourceProvenance(
                source_type="runtime",
                source_ref="runtime-invocation-plan",
                source_tool="chronicle-runtime",
                source_model=plan.model_name,
            ),
            review_status=ReviewStatus.NEEDS_REVIEW,
            confidence=Confidence.LOW,
        )
        return event.event_id


def _truncate_summary(text: str, limit: int = 80) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."
