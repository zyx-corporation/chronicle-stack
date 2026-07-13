"""Preview-only AI boundary service for external adapter workflows."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from chronicle.models.ai_boundary import (
    AiBoundaryPersistencePolicy,
    AiBoundaryPreview,
    AiInterpretationWarning,
    AiInterpretationWarningCode,
    AiInterpretationWarningSeverity,
    SayaneAdapterContract,
)
from chronicle.models.event import Actor, Confidence, ReviewStatus
from chronicle.models.integration_package import IntegrationTargetEnvironment
from chronicle.models.source import SourceProvenance
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.integration_package_service import IntegrationPackageService


class AiBoundaryService:
    """Build advisory previews for external AI boundaries without calling AI."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path.cwd()
        self.chronicle = ChronicleService(self.root)
        self.packages = IntegrationPackageService(self.root)

    def preview(
        self,
        *,
        task: str,
        model_id: str,
        context_ids: list[str] | None = None,
        runtime_label: str = "external-adapter",
        prompt_text: str | None = None,
        response_text: str | None = None,
        occurred_at: datetime | None = None,
        persistence_policy: AiBoundaryPersistencePolicy | None = None,
        record: bool = False,
    ) -> AiBoundaryPreview:
        metadata = self.chronicle.require_initialized()
        persistence = persistence_policy or AiBoundaryPersistencePolicy()
        package = self.packages.build_context_package(
            purpose=task,
            target_environment=IntegrationTargetEnvironment.EXTERNAL,
            context_ids=context_ids,
        )
        requested_context_ids = list(context_ids or package.manifest.referenced_records)
        included_context_ids = [
            record.record_id
            for record in package.records
            if record.record_kind == "context"
        ]
        excluded_context_ids = [
            context_id
            for context_id in requested_context_ids
            if context_id not in included_context_ids
        ]
        redaction_candidates = sorted(
            {
                record.record_id
                for record in package.records
                if record.content is None or bool(record.warnings)
            }
        )
        notes = [
            "Preview is local, read-only, and advisory before any external AI handoff.",
            "AI summaries and responses stay separated from user statements and primary Chronicle facts.",
            "AI interpretations should be recorded as hypothesis or decay-target records, not as durable facts.",
        ]
        if response_text and not persistence.persist_response:
            notes.append("Response text supplied but marked non-persistent by policy.")
        interpretation_warnings = self._interpretation_warnings(
            included_context_ids=included_context_ids,
            persistence=persistence,
        )
        preview = AiBoundaryPreview(
            task=task,
            model_id=model_id,
            runtime_label=runtime_label,
            source_chronicle_id=metadata.chronicle_id,
            requested_context_ids=requested_context_ids,
            included_context_ids=included_context_ids,
            excluded_context_ids=excluded_context_ids,
            redaction_candidates=redaction_candidates,
            package_warnings=package.manifest.warnings,
            interpretation_warnings=interpretation_warnings,
            persistence_policy=persistence,
            prompt_text=prompt_text if persistence.persist_prompt else None,
            response_text=response_text if persistence.persist_response else None,
            occurred_at=occurred_at if persistence.persist_timestamp else None,
            notes=notes,
            sayane_contract=self._sayane_contract(
                task=task,
                model_id=model_id,
                context_ids=included_context_ids,
            ),
            recorded=record,
        )
        if not record:
            return preview

        event = self.chronicle.record_event(
            event_type=self._assistant_output_event_type(),
            actor=Actor.ASSISTANT,
            summary=f"AI boundary preview prepared: {task}",
            payload={"ai_boundary_preview": preview.model_dump(mode="json")},
            source=SourceProvenance(
                source_type="runtime",
                source_ref="ai-boundary-preview",
                source_tool="chronicle-ai-boundary",
                source_model=model_id,
            ),
            review_status=ReviewStatus.NEEDS_REVIEW,
            confidence=Confidence.LOW,
        )
        return preview.model_copy(update={"recorded": True, "event_id": event.event_id})

    @staticmethod
    def _interpretation_warnings(
        *,
        included_context_ids: list[str],
        persistence: AiBoundaryPersistencePolicy,
    ) -> list[AiInterpretationWarning]:
        warnings = [
            AiInterpretationWarning(
                code=AiInterpretationWarningCode.NOT_PRIMARY_FACT,
                severity=AiInterpretationWarningSeverity.WARNING,
                message="AI output and interpretation are derived content, not primary Chronicle facts.",
                next_safe_action="Review provenance and record accepted meaning through proposal, RDE, or decision workflows.",
            ),
            AiInterpretationWarning(
                code=AiInterpretationWarningCode.REVIEW_REQUIRED,
                severity=AiInterpretationWarningSeverity.WARNING,
                message="AI-derived content requires explicit human review before trust or apply.",
                next_safe_action="Keep the result in needs-review state until a named reviewer records a disposition.",
            ),
            AiInterpretationWarning(
                code=AiInterpretationWarningCode.DECAY_CANDIDATE,
                severity=AiInterpretationWarningSeverity.ADVISORY,
                message="AI interpretation may become stale as source context or model behavior changes.",
                next_safe_action="Record interpretation as a hypothesis or decay-target and schedule later review.",
            ),
        ]
        if included_context_ids:
            warnings.append(
                AiInterpretationWarning(
                    code=AiInterpretationWarningCode.EXTERNAL_CONTEXT_DISCLOSURE,
                    severity=AiInterpretationWarningSeverity.WARNING,
                    message="Selected Chronicle context is being prepared for an external AI boundary.",
                    next_safe_action="Confirm classification, masking, purpose, and every included context before sending.",
                )
            )
        if persistence.persist_prompt or persistence.persist_response:
            warnings.append(
                AiInterpretationWarning(
                    code=AiInterpretationWarningCode.DERIVED_CONTENT_PERSISTED,
                    severity=AiInterpretationWarningSeverity.WARNING,
                    message="Prompt or response text is configured for persistence in the boundary preview.",
                    next_safe_action="Confirm retention, sensitivity, and masking before recording the preview.",
                )
            )
        return warnings

    def _sayane_contract(
        self,
        *,
        task: str,
        model_id: str,
        context_ids: list[str],
    ) -> SayaneAdapterContract:
        context_args = " ".join(f"--context {context_id}" for context_id in context_ids)
        export_command = (
            f'chronicle ai-boundary preview --task "{task}" {context_args} --model "{model_id}"'
        ).strip()
        return SayaneAdapterContract(
            export_command=export_command,
            import_command="chronicle rde draft --artifact <ARTIFACT_ID> --from <VERSION_ID> --to <VERSION_ID> --mode ai-assisted",
            accepted_payloads=[
                "ai_boundary_preview",
                "rde_diff_record",
                "chronicle_object:hypothesis",
            ],
            boundaries=[
                "no fixed provider integration inside Chronicle Stack core",
                "no automatic external send from preview generation",
                "import remains reviewable and reconstructable through RDE + Delta Chronicle",
            ],
        )

    @staticmethod
    def _assistant_output_event_type():
        from chronicle.models.event import EventType

        return EventType.ASSISTANT_OUTPUT
