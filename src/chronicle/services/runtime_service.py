"""Explicit local runtime service with placeholder summarization."""

import json
import os
import re
from pathlib import Path
from urllib import error as urllib_error
from urllib import request as urllib_request

from chronicle.errors import (
    RuntimeInvocationPlanExecutionRequestMissingError,
    RuntimeInvocationPlanNotFoundError,
    RuntimeProviderCredentialMissingError,
    RuntimeProviderExternalContextNotAllowedError,
    RuntimeProviderExecutionNotEnabledError,
    RuntimeProviderNotReadyError,
    RuntimeProviderResponseError,
    RuntimeProviderTransportError,
)
from chronicle.models.event import Actor, Confidence, ReviewStatus
from chronicle.models.artifact import ArtifactType
from chronicle.models.runtime import (
    RuntimeComposedRetrievalHit,
    RuntimeConfig,
    RuntimeExecutionResult,
    RuntimeInvocationPlan,
    RuntimeProviderKind,
    RuntimeQueryEngineHandoff,
    RuntimeQueryEngineImportCheck,
    RuntimeQueryEngineImportValidation,
    RuntimeRecordPreview,
    RuntimeRetrievalComposition,
    RuntimeRetrievalHandoff,
    RuntimeRetrievalHit,
    RuntimeRetrievalPlan,
    RuntimeRetrievalSourceSummary,
    RuntimeStatus,
    RuntimeSummaryResult,
)
from chronicle.models.summary_job import SummarySourceRef
from chronicle.models.source import SourceProvenance
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.artifact_service import ArtifactService
from chronicle.services.graph_export_service import GraphExportService
from chronicle.services.local_graph_retrieval_adapter import LocalGraphRetrievalAdapter
from chronicle.services.runtime_config_service import RuntimeConfigService
from chronicle.services.search_service import SearchService
from chronicle.services.summary_job_service import SummaryJobService
from chronicle.services.vector_index_service import VectorIndexService


class RuntimeService:
    """Provide explicit local runtime actions without external calls."""

    def __init__(self, root: Path | None = None) -> None:
        self.chronicle = ChronicleService(root)
        self.vector_index = VectorIndexService(root)
        self.graph_export = GraphExportService(root)
        self.graph_adapter = LocalGraphRetrievalAdapter(root)
        self.search = SearchService(root)
        self.summary_jobs = SummaryJobService(root)
        self.runtime_config = RuntimeConfigService(root)
        self.artifacts = ArtifactService(root)

    def status(self) -> RuntimeStatus:
        config_state = self.runtime_config.show()
        return RuntimeStatus(
            configured_provider_kind=config_state.config.provider_kind,
            configured_model_name=config_state.config.model_name,
        )

    def summarize(
        self,
        *,
        text: str,
        max_sentences: int = 3,
        record: bool = False,
        draft_title: str | None = None,
        execute_configured_provider: bool = False,
        source_refs: list[SummarySourceRef] | None = None,
        tags: list[str] | None = None,
        prompt: str = "runtime summarize",
        operator: str = "runtime",
    ) -> RuntimeSummaryResult:
        config_state = self.runtime_config.show()
        config = config_state.config
        result = self._summarize_with_active_boundary(
            config=config,
            text=text,
            max_sentences=max_sentences,
            execute_configured_provider=execute_configured_provider,
        )
        result.recorded = record
        if draft_title:
            draft_job = self.summary_jobs.create_runtime_draft(
                title=draft_title,
                summary_text=result.generated_text,
                runtime_config=config if result.external_call_made else self._local_runtime_config(),
                invocation_mode=result.invocation_mode,
                external_call_made=result.external_call_made,
                generated_by="runtime_http_manual" if result.external_call_made else "runtime_manual",
                prompt=prompt,
                operator=operator,
                response_metadata=getattr(result, "response_metadata", {}),
                response_keys=getattr(result, "response_keys", []),
                source_refs=source_refs or [],
                tags=["runtime-summary-draft", *(tags or [])],
            )
            result.draft_summary_job_id = draft_job.summary_job_id
            result.draft_artifact_id = draft_job.artifact_id
            result.draft_version_id = draft_job.version_id

        if not record:
            return result

        event = self.chronicle.record_event(
            event_type=self._assistant_output_event_type(),
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
        result.recorded = True
        result.event_id = event.event_id
        return result

    def invoke(
        self,
        *,
        text: str,
        operation: str,
        record: bool = False,
        execute_configured_provider: bool = False,
        draft_summary_title: str | None = None,
        artifact_title: str | None = None,
        artifact_type: ArtifactType = ArtifactType.OTHER,
        source_refs: list[SummarySourceRef] | None = None,
        prompt: str = "",
        extra_params: dict[str, str] | None = None,
    ) -> RuntimeExecutionResult:
        config_state = self.runtime_config.show()
        config = config_state.config
        if not execute_configured_provider:
            raise RuntimeProviderExecutionNotEnabledError()
        source_refs = source_refs or []
        extra_params = extra_params or {}
        if source_refs and not config.allow_external_context:
            raise RuntimeProviderExternalContextNotAllowedError()
        self._require_ready_http_config(config)
        response_payload = self._invoke_http_operation(
            config=config,
            text=text,
            operation=operation,
            max_sentences=None,
            source_refs=source_refs,
            prompt=prompt,
            extra_params=extra_params,
        )
        output_text, response_metadata, response_keys = self._extract_http_response_details(response_payload)
        result = RuntimeExecutionResult(
            provider_kind=config.provider_kind,
            provider_name=config.provider_name,
            model_name=config.model_name,
            operation=operation,
            invocation_mode="explicit-http-manual",
            external_call_made=True,
            source_text_length=len(text),
            output_text=output_text,
            source_refs=[ref.model_dump(mode="json") for ref in source_refs],
            prompt=prompt,
            params=extra_params,
            response_metadata=response_metadata,
            response_keys=response_keys,
            recorded=record,
        )
        if draft_summary_title:
            draft_job = self.summary_jobs.create_runtime_draft(
                title=draft_summary_title,
                summary_text=output_text,
                runtime_config=config,
                invocation_mode="explicit-http-manual",
                external_call_made=True,
                generated_by="runtime_http_manual",
                prompt=prompt,
                operator=f"runtime-invoke:{operation}",
                response_metadata=response_metadata,
                response_keys=response_keys,
                source_refs=source_refs,
                tags=["runtime-invoke-summary", operation, config.provider_kind.value],
            )
            result.draft_summary_job_id = draft_job.summary_job_id
        if artifact_title:
            artifact, version = self.artifacts.create(
                title=artifact_title,
                artifact_type=artifact_type,
                content=output_text,
                tags=["runtime-output", operation, config.provider_kind.value],
                source=SourceProvenance(
                    source_type="runtime",
                    source_ref=f"configured-provider-{operation}",
                    source_tool="chronicle-runtime",
                    source_model=result.model_name,
                    source_url=config.base_url,
                ),
                actor=Actor.ASSISTANT,
            )
            result.artifact_id = artifact.artifact_id
            result.version_id = version.version_id
        if not record:
            return result

        event = self.chronicle.record_event(
            event_type=self._assistant_output_event_type(),
            actor=Actor.ASSISTANT,
            summary=f"Runtime {operation} generated: {_truncate_summary(output_text)}",
            payload={
                "runtime_execution": result.model_dump(mode="json"),
                "runtime_provider": result.provider_kind.value,
            },
            source=SourceProvenance(
                source_type="runtime",
                source_ref=f"configured-provider-{operation}",
                source_tool="chronicle-runtime",
                source_model=result.model_name,
            ),
            review_status=ReviewStatus.NEEDS_REVIEW,
            confidence=Confidence.LOW,
        )
        result.recorded = True
        result.event_id = event.event_id
        return result

    def _local_runtime_config(self):
        status = self.status()
        from chronicle.models.runtime import RuntimeCapability, RuntimeConfig

        return RuntimeConfig(
            provider_kind=status.provider_kind,
            provider_name="local-placeholder",
            model_name=status.model_name,
            capabilities=[RuntimeCapability(capability) for capability in status.capabilities],
            allow_network=False,
            allow_external_context=False,
            review_required=True,
        )

    def retrieve_plan(self, *, query: str, limit: int = 5, record: bool = False) -> RuntimeRetrievalPlan:
        self.chronicle.require_initialized()
        vector_hits = [
            RuntimeRetrievalHit(
                source="vector_index",
                identifier=result.record_id,
                summary=result.text,
                detail=result.record_type,
                score=result.score,
            )
            for result in self.vector_index.search(query=query, limit=limit)
        ]

        graph_adapter = self.graph_adapter.retrieve(query=query, limit=limit)
        graph_hits = graph_adapter.hits

        chronicle_hits = [
            RuntimeRetrievalHit(
                source="chronicle_search",
                identifier=result.identifier,
                summary=result.summary,
                detail=result.detail,
            )
            for result in self.search.search(query)[:limit]
        ]

        notes = [
            "dry-run retrieval plan only",
            "no LLM invoked",
            "no external runtime invoked",
            "primary Chronicle record remains authoritative",
        ]
        composition = _compose_retrieval_hits(vector_hits, graph_hits, chronicle_hits)
        query_engine_handoff = _build_query_engine_handoff(
            query=query,
            graph= self.graph_export.export_graph(),
            graph_adapter_result=graph_adapter,
            composition=composition,
            referenced_record_ids=_unique_identifiers_from_hits(vector_hits, graph_hits, chronicle_hits),
        )
        plan = RuntimeRetrievalPlan(
            query=query,
            vector_hits=vector_hits,
            graph_hits=graph_hits,
            chronicle_hits=chronicle_hits,
            graph_adapter=graph_adapter,
            composition=composition,
            query_engine_handoff=query_engine_handoff,
            notes=notes,
        )
        if not record:
            return plan

        event = self.chronicle.record_event(
            event_type=self._assistant_output_event_type(),
            actor=Actor.ASSISTANT,
            summary=f"Runtime retrieval plan generated: {_truncate_summary(query)}",
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
        plan.recorded = True
        plan.event_id = event.event_id
        return plan

    def invocation_plan(
        self,
        *,
        text: str,
        operation: str = "summarize",
        record: bool = False,
        source_refs: list[SummarySourceRef] | None = None,
        prompt: str = "",
        extra_params: dict[str, str] | None = None,
    ) -> RuntimeInvocationPlan:
        return self._invocation_plan(
            text=text,
            operation=operation,
            record=record,
            source_refs=source_refs or [],
            prompt=prompt,
            source_ref_count_override=None,
            extra_params=extra_params or {},
        )

    def invocation_plan_from_summary(
        self,
        *,
        summary_job_id: str,
        summary_title: str,
        summary_text: str,
        prompt: str = "",
        source_refs: list[SummarySourceRef] | None = None,
        source_ref_count: int | None = None,
        operation: str = "summarize",
        record: bool = False,
    ) -> RuntimeInvocationPlan:
        return self._invocation_plan(
            text=summary_text,
            operation=operation,
            record=record,
            source_refs=source_refs or [],
            prompt=prompt,
            source_ref_count_override=source_ref_count,
            request_context={
                "summary_job_id": summary_job_id,
                "summary_title": summary_title,
                "prompt": prompt,
            },
            summary_label=f"summary {summary_job_id} {operation}",
        )

    def _invocation_plan(
        self,
        *,
        text: str,
        operation: str,
        record: bool,
        source_refs: list[SummarySourceRef],
        prompt: str,
        source_ref_count_override: int | None,
        extra_params: dict[str, str] | None = None,
        request_context: dict[str, str] | None = None,
        summary_label: str | None = None,
    ) -> RuntimeInvocationPlan:
        config_state = self.runtime_config.show()
        config = config_state.config
        blocking_reasons: list[str] = []
        would_use_network = config.provider_kind == RuntimeProviderKind.HTTP
        network_allowed = bool(config.allow_network)
        source_ref_count = source_ref_count_override if source_ref_count_override is not None else len(source_refs)

        if config.provider_kind == RuntimeProviderKind.DISABLED:
            blocking_reasons.append("runtime_provider_disabled")
        if would_use_network and not network_allowed:
            blocking_reasons.append("network_not_allowed_by_contract")
        if would_use_network and source_ref_count > 0 and not config.allow_external_context:
            blocking_reasons.append("external_context_not_allowed_by_contract")
        if not config.model_name or config.model_name == "disabled":
            blocking_reasons.append("model_not_configured")

        invocation_ready = len(blocking_reasons) == 0
        request_preview = self._request_preview(
            config=config,
            operation=operation,
            text=text,
            request_context={
                **(request_context or {}),
                "prompt": prompt,
                "source_ref_count": str(source_ref_count),
                "param_count": str(len(extra_params or {})),
                "param_keys": ",".join(sorted((extra_params or {}).keys())),
            },
        )
        plan = RuntimeInvocationPlan(
            provider_kind=config.provider_kind,
            provider_name=config.provider_name,
            model_name=config.model_name,
            operation=operation,
            source_text_length=len(text),
            would_use_network=would_use_network,
            network_allowed_by_contract=network_allowed,
            invocation_ready=invocation_ready,
            blocking_reasons=blocking_reasons,
            request_preview=request_preview,
            execution_request={
                "text": text,
                "operation": operation,
                "prompt": prompt,
                "params": extra_params or {},
                "source_refs": [ref.model_dump(mode="json") for ref in source_refs],
            },
            downstream_commands=self._invocation_downstream_commands(operation, invocation_ready),
            notes=self._invocation_notes(config=config, invocation_ready=invocation_ready),
        )
        if not record:
            return plan

        event = self.chronicle.record_event(
            event_type=self._assistant_output_event_type(),
            actor=Actor.ASSISTANT,
            summary=(
                f"Runtime invocation plan generated: {summary_label}"
                if summary_label
                else f"Runtime invocation plan generated: {config.provider_kind.value} {operation}"
            ),
            payload={
                "runtime_invocation_plan": plan.model_dump(mode="json"),
                "runtime_provider": config.provider_kind.value,
            },
            source=SourceProvenance(
                source_type="runtime",
                source_ref="runtime-invocation-plan",
                source_tool="chronicle-runtime",
                source_model=config.model_name,
            ),
            review_status=ReviewStatus.NEEDS_REVIEW,
            confidence=Confidence.LOW,
        )
        plan.recorded = True
        plan.event_id = event.event_id
        plan.downstream_commands = self._recorded_plan_downstream_commands(
            event_id=event.event_id,
            operation=plan.operation,
            invocation_ready=plan.invocation_ready,
            commands=plan.downstream_commands,
        )
        return plan

    def invoke_recorded_plan(
        self,
        *,
        event_id: str,
        record: bool = False,
        draft_summary_title: str | None = None,
        artifact_title: str | None = None,
        artifact_type: ArtifactType = ArtifactType.OTHER,
        execute_configured_provider: bool = False,
    ) -> RuntimeExecutionResult:
        event = self._event_by_id(event_id)
        payload = getattr(event, "payload", {})
        if "runtime_invocation_plan" not in payload:
            raise RuntimeInvocationPlanNotFoundError(event_id)

        plan = RuntimeInvocationPlan.model_validate(payload["runtime_invocation_plan"])
        execution_request = plan.execution_request
        if not execution_request:
            raise RuntimeInvocationPlanExecutionRequestMissingError(event_id)

        text = execution_request.get("text")
        operation = execution_request.get("operation")
        if not isinstance(text, str) or not isinstance(operation, str):
            raise RuntimeInvocationPlanExecutionRequestMissingError(event_id)

        prompt = execution_request.get("prompt", "")
        params = execution_request.get("params", {})
        source_ref_payloads = execution_request.get("source_refs", [])
        if not isinstance(prompt, str) or not isinstance(params, dict) or not isinstance(source_ref_payloads, list):
            raise RuntimeInvocationPlanExecutionRequestMissingError(event_id)

        source_refs = [
            SummarySourceRef.model_validate(item)
            for item in source_ref_payloads
            if isinstance(item, dict)
        ]
        return self.invoke(
            text=text,
            operation=operation,
            record=record,
            execute_configured_provider=execute_configured_provider,
            draft_summary_title=draft_summary_title,
            artifact_title=artifact_title,
            artifact_type=artifact_type,
            source_refs=source_refs,
            prompt=prompt,
            extra_params={str(key): str(value) for key, value in params.items()},
        )

    def _assistant_output_event_type(self):
        from chronicle.models.event import EventType

        return EventType.ASSISTANT_OUTPUT

    def record_preview(self, event: object) -> RuntimeRecordPreview:
        payload = getattr(event, "payload", {})
        if "query_engine_trial_record" in payload:
            trial = payload["query_engine_trial_record"]
            query = str(trial.get("query", ""))
            reviewer = str(trial.get("reviewer", ""))
            downstream_consumer = str(trial.get("downstream_consumer", ""))
            sufficient = bool(trial.get("sufficient", False))
            return RuntimeRecordPreview(
                record_kind="query_engine_trial",
                title=f"Query-engine trial: {query}",
                preview_text=(
                    f"{downstream_consumer} / reviewer={reviewer} / sufficient={sufficient}"
                ).strip(),
                source_counts={
                    "files_reviewed": len(trial.get("files_reviewed", [])),
                    "notes": len(trial.get("notes", [])),
                },
                referenced_record_ids=[],
                suggested_cli_family="chronicle package query-engine-trial-record",
                boundary_notes=[
                    "recorded downstream trial outcome only",
                    "no downstream import execution happened inside Chronicle core",
                    "primary Chronicle records remain authoritative",
                ],
            )
        if "runtime_summary" in payload:
            summary = payload["runtime_summary"]
            generated_text = str(summary.get("generated_text", ""))
            return RuntimeRecordPreview(
                record_kind="summary",
                title="Runtime summary",
                preview_text=generated_text,
                source_counts={"sentences": _sentence_count(generated_text)},
                referenced_record_ids=[],
                suggested_cli_family="chronicle runtime summarize --record",
                boundary_notes=[
                    "explicit manual invocation only",
                    "generated output requires review",
                    "no external runtime invoked",
                ],
            )

        if "runtime_execution" in payload:
            execution = RuntimeExecutionResult.model_validate(payload["runtime_execution"])
            return RuntimeRecordPreview(
                record_kind="execution",
                title=f"Runtime execution: {execution.operation}",
                preview_text=execution.output_text,
                source_counts={
                    "source_text_length": execution.source_text_length,
                    "response_metadata": len(execution.response_metadata),
                    "response_keys": len(execution.response_keys),
                },
                referenced_record_ids=[],
                suggested_cli_family=f"chronicle runtime invoke --operation {execution.operation}",
                boundary_notes=[
                    "explicit configured-provider execution",
                    "generated output requires review",
                    "external provider call was recorded",
                ],
            )

        if "runtime_retrieval_plan" in payload:
            plan = RuntimeRetrievalPlan.model_validate(payload["runtime_retrieval_plan"])
            return RuntimeRecordPreview(
                record_kind="retrieval_plan",
                title=f"Runtime retrieval plan: {plan.query}",
                preview_text=plan.query,
                source_counts={
                    "vector_hits": len(plan.vector_hits),
                    "graph_hits": len(plan.graph_hits),
                    "chronicle_hits": len(plan.chronicle_hits),
                },
                referenced_record_ids=_unique_identifiers(plan),
                suggested_cli_family="chronicle runtime retrieve-plan --record",
                boundary_notes=plan.notes,
            )

        if "runtime_invocation_plan" in payload:
            plan = RuntimeInvocationPlan.model_validate(payload["runtime_invocation_plan"])
            return RuntimeRecordPreview(
                record_kind="invocation_plan",
                title=f"Runtime invocation plan: {plan.provider_kind.value} {plan.operation}",
                preview_text=f"{plan.provider_name} / {plan.model_name}",
                source_counts={
                    "source_text_length": plan.source_text_length,
                    "blocking_reasons": len(plan.blocking_reasons),
                    "downstream_commands": len(plan.downstream_commands),
                },
                referenced_record_ids=[],
                suggested_cli_family="chronicle runtime invoke-plan --record",
                boundary_notes=plan.notes,
            )

        return RuntimeRecordPreview(
            record_kind="unknown",
            title="Runtime record",
            suggested_cli_family="chronicle show --json",
            boundary_notes=["read-only runtime record"],
        )

    def retrieval_handoff(self, plan: RuntimeRetrievalPlan) -> RuntimeRetrievalHandoff:
        return RuntimeRetrievalHandoff(
            query=plan.query,
            vector_hit_count=len(plan.vector_hits),
            graph_hit_count=len(plan.graph_hits),
            chronicle_hit_count=len(plan.chronicle_hits),
            referenced_record_ids=_unique_identifiers(plan),
            composition=plan.composition or _compose_retrieval_hits(
                plan.vector_hits,
                plan.graph_hits,
                plan.chronicle_hits,
            ),
            downstream_commands=[
                'chronicle package review --purpose "runtime retrieval handoff"',
                'chronicle package context --purpose "runtime retrieval handoff" --persist',
                "chronicle review queue --json",
            ],
            notes=[
                "dry-run handoff contract only",
                "package review should precede downstream sharing",
                "primary Chronicle records remain authoritative",
                "no GraphRAG runtime is implied by this plan",
            ],
        )

    @staticmethod
    def _request_preview(
        *,
        config: RuntimeConfig,
        operation: str,
        text: str,
        request_context: dict[str, str],
    ) -> dict[str, str]:
        preview = {
            "operation": operation,
            "provider_kind": config.provider_kind.value,
            "model_name": config.model_name,
            "text_excerpt": _truncate_summary(text, limit=120),
        }
        preview.update({key: value for key, value in request_context.items() if value})
        if config.base_url:
            preview["base_url"] = config.base_url
        if config.api_key_env:
            preview["api_key_env"] = config.api_key_env
        return preview

    @staticmethod
    def _invocation_downstream_commands(operation: str, invocation_ready: bool) -> list[str]:
        commands = [
            "chronicle runtime config show --json",
            "chronicle review queue --json",
        ]
        if invocation_ready:
            commands.append(f"chronicle runtime {operation} --text ... --execute-configured-provider")
        return commands

    @staticmethod
    def _invocation_notes(*, config: RuntimeConfig, invocation_ready: bool) -> list[str]:
        notes = [
            "dry-run invocation contract only",
            "configuration alone does not invoke any model or external runtime",
            "primary Chronicle records remain authoritative",
            "generated output still requires explicit/manual invocation and review",
        ]
        if config.provider_kind == RuntimeProviderKind.HTTP:
            notes.append("HTTP provider configuration does not create an active network session.")
        if invocation_ready:
            notes.append("contract boundary is ready for explicit/manual invocation, but no provider execution happens here")
        else:
            notes.append("contract boundary is blocked until configuration warnings are resolved")
        return notes

    @staticmethod
    def _recorded_plan_downstream_commands(
        *,
        event_id: str,
        operation: str,
        invocation_ready: bool,
        commands: list[str],
    ) -> list[str]:
        recorded_commands = list(commands)
        if invocation_ready:
            recorded_commands.append(
                f"chronicle runtime execute-plan --event {event_id} --execute-configured-provider"
            )
        else:
            recorded_commands.append(f"chronicle runtime execute-plan --event {event_id}")
        return recorded_commands

    def _event_by_id(self, event_id: str):
        for event in self.chronicle.jsonl.read_all():
            if event.event_id == event_id:
                return event
        raise RuntimeInvocationPlanNotFoundError(event_id)

    def _summarize_with_active_boundary(
        self,
        *,
        config: RuntimeConfig,
        text: str,
        max_sentences: int,
        execute_configured_provider: bool,
    ) -> RuntimeSummaryResult:
        if config.provider_kind == RuntimeProviderKind.HTTP:
            if not execute_configured_provider:
                raise RuntimeProviderExecutionNotEnabledError()
            self._require_ready_http_config(config)
            response_payload = self._invoke_http_operation(
                config=config,
                text=text,
                operation="summarize",
                max_sentences=max_sentences,
            )
            generated_text, response_metadata, response_keys = self._extract_http_response_details(response_payload)
            return RuntimeSummaryResult(
                provider_kind=config.provider_kind,
                provider_name=config.provider_name,
                model_name=config.model_name,
                invocation_mode="explicit-http-manual",
                external_call_made=True,
                source_text_length=len(text),
                generated_text=generated_text,
                response_metadata=response_metadata,
                response_keys=response_keys,
            )

        generated_text = _summarize_text(text, max_sentences=max_sentences)
        return RuntimeSummaryResult(
            provider_kind=RuntimeProviderKind.LOCAL,
            provider_name="local-placeholder",
            model_name="local-placeholder",
            invocation_mode="explicit-manual",
            external_call_made=False,
            source_text_length=len(text),
            generated_text=generated_text,
            response_metadata={},
            response_keys=[],
        )

    def _require_ready_http_config(self, config: RuntimeConfig) -> None:
        blocking_reasons: list[str] = []
        if config.provider_kind != RuntimeProviderKind.HTTP:
            blocking_reasons.append("configured_provider_is_not_http")
        if not config.allow_network:
            blocking_reasons.append("network_not_allowed_by_contract")
        if not config.base_url:
            blocking_reasons.append("base_url_not_configured")
        if not config.model_name or config.model_name == "disabled":
            blocking_reasons.append("model_not_configured")
        if not config.api_key_env:
            blocking_reasons.append("api_key_env_not_configured")
        if blocking_reasons:
            raise RuntimeProviderNotReadyError(blocking_reasons)
        if not os.environ.get(config.api_key_env or ""):
            raise RuntimeProviderCredentialMissingError(config.api_key_env or "")

    @staticmethod
    def _invoke_http_operation(
        *,
        config: RuntimeConfig,
        text: str,
        operation: str,
        max_sentences: int | None,
        source_refs: list[SummarySourceRef] | None = None,
        prompt: str = "",
        extra_params: dict[str, str] | None = None,
    ) -> dict[str, object]:
        payload = {
            "operation": operation,
            "model": config.model_name,
            "input_text": text,
        }
        if max_sentences is not None:
            payload["max_sentences"] = max_sentences
        if source_refs:
            payload["source_refs"] = [ref.model_dump(mode="json") for ref in source_refs]
        if prompt:
            payload["prompt"] = prompt
        if extra_params:
            payload["params"] = extra_params
        body = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.environ[config.api_key_env or '']}",
        }
        request = urllib_request.Request(
            config.base_url or "",
            data=body,
            headers=headers,
            method="POST",
        )
        try:
            with urllib_request.urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib_error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace").strip() or f"HTTP {exc.code}"
            raise RuntimeProviderTransportError(detail) from exc
        except urllib_error.URLError as exc:
            raise RuntimeProviderTransportError(str(exc.reason)) from exc
        except OSError as exc:
            raise RuntimeProviderTransportError(str(exc)) from exc
        except json.JSONDecodeError as exc:
            raise RuntimeProviderResponseError(f"invalid JSON: {exc}") from exc

        if not isinstance(payload, dict):
            raise RuntimeProviderResponseError("response JSON must be an object")
        return payload

    @staticmethod
    def _extract_http_response_details(
        payload: dict[str, object] | str,
    ) -> tuple[str, dict[str, str | int | float | bool], list[str]]:
        if isinstance(payload, str):
            return payload, {}, []
        generated_text = ""
        for key in ("output_text", "generated_text", "summary"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                generated_text = value.strip()
                break
        if not generated_text:
            raise RuntimeProviderResponseError("missing textual output field")

        metadata: dict[str, str | int | float | bool] = {}
        for key in ("response_id", "finish_reason", "provider_status"):
            value = payload.get(key)
            if isinstance(value, (str, int, float, bool)):
                metadata[key] = value
        usage = payload.get("usage")
        if isinstance(usage, dict):
            for key, value in usage.items():
                if isinstance(value, (str, int, float, bool)):
                    metadata[f"usage_{key}"] = value
        return generated_text, metadata, sorted(payload.keys())


def _summarize_text(text: str, *, max_sentences: int) -> str:
    cleaned = " ".join(part.strip() for part in text.splitlines() if part.strip())
    if not cleaned:
        return ""

    sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?。！？])\s+", cleaned) if sentence.strip()]
    if sentences:
        return " ".join(sentences[:max_sentences])

    words = cleaned.split()
    if len(words) <= 30:
        return cleaned
    return " ".join(words[:30]) + "..."


def _truncate_summary(text: str, limit: int = 80) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _sentence_count(text: str) -> int:
    sentences = [sentence for sentence in re.split(r"(?<=[.!?。！？])\s+", text.strip()) if sentence]
    return len(sentences)


def _unique_identifiers(plan: RuntimeRetrievalPlan) -> list[str]:
    return _unique_identifiers_from_hits(plan.vector_hits, plan.graph_hits, plan.chronicle_hits)


def _unique_identifiers_from_hits(
    vector_hits: list[RuntimeRetrievalHit],
    graph_hits: list[RuntimeRetrievalHit],
    chronicle_hits: list[RuntimeRetrievalHit],
) -> list[str]:
    seen: set[str] = set()
    identifiers: list[str] = []
    for hit in [*vector_hits, *graph_hits, *chronicle_hits]:
        if hit.identifier and hit.identifier not in seen:
            identifiers.append(hit.identifier)
            seen.add(hit.identifier)
    return identifiers


def _compose_retrieval_hits(
    vector_hits: list[RuntimeRetrievalHit],
    graph_hits: list[RuntimeRetrievalHit],
    chronicle_hits: list[RuntimeRetrievalHit],
) -> RuntimeRetrievalComposition:
    grouped_hits = [
        ("vector_index", vector_hits),
        ("graph_export_adapter", graph_hits),
        ("chronicle_search", chronicle_hits),
    ]
    source_summaries: list[RuntimeRetrievalSourceSummary] = []
    composed: dict[str, dict[str, object]] = {}

    for source_name, hits in grouped_hits:
        identifiers = {hit.identifier for hit in hits if hit.identifier}
        scores = [hit.score for hit in hits if hit.score is not None]
        source_summaries.append(
            RuntimeRetrievalSourceSummary(
                source=source_name,
                hit_count=len(hits),
                unique_identifier_count=len(identifiers),
                max_score=max(scores) if scores else None,
            )
        )
        for hit in hits:
            if not hit.identifier:
                continue
            entry = composed.setdefault(
                hit.identifier,
                {
                    "identifier": hit.identifier,
                    "summary": hit.summary,
                    "detail": hit.detail,
                    "sources": [],
                    "best_score": hit.score,
                },
            )
            if source_name not in entry["sources"]:
                entry["sources"].append(source_name)
            if not entry.get("summary") and hit.summary:
                entry["summary"] = hit.summary
            if not entry.get("detail") and hit.detail:
                entry["detail"] = hit.detail
            best_score = entry.get("best_score")
            if hit.score is not None and (best_score is None or hit.score > best_score):
                entry["best_score"] = hit.score

    composed_hits = [
        RuntimeComposedRetrievalHit(
            identifier=str(entry["identifier"]),
            summary=str(entry.get("summary", "")),
            detail=str(entry.get("detail", "")),
            sources=sorted(str(source) for source in entry.get("sources", [])),
            source_count=len(entry.get("sources", [])),
            best_score=(round(float(entry["best_score"]), 4) if entry.get("best_score") is not None else None),
        )
        for entry in composed.values()
    ]
    composed_hits.sort(key=lambda hit: (-hit.source_count, -(hit.best_score or 0.0), hit.identifier))
    overlap_identifier_count = sum(1 for hit in composed_hits if hit.source_count > 1)
    total_hit_count = len(vector_hits) + len(graph_hits) + len(chronicle_hits)
    notes = [
        "composed from local vector, graph, and Chronicle search surfaces",
        "shared identifiers highlight cross-surface overlap only",
        "composition remains read-only and dry-run oriented",
    ]
    return RuntimeRetrievalComposition(
        total_hit_count=total_hit_count,
        unique_identifier_count=len(composed_hits),
        overlap_identifier_count=overlap_identifier_count,
        source_summaries=source_summaries,
        composed_hits=composed_hits,
        notes=notes,
    )



def _build_query_engine_handoff(
    *,
    query: str,
    graph,
    graph_adapter_result,
    composition: RuntimeRetrievalComposition,
    referenced_record_ids: list[str],
) -> RuntimeQueryEngineHandoff:
    context_ids = [record_id for record_id in referenced_record_ids if record_id.startswith("ctx_")]
    skipped_ids = [record_id for record_id in referenced_record_ids if not record_id.startswith("ctx_")]
    status = "contract_available" if referenced_record_ids else "advisory_only"
    derived_surfaces = [summary.source for summary in composition.source_summaries if summary.hit_count > 0]
    if not derived_surfaces:
        derived_surfaces = [summary.source for summary in composition.source_summaries]
    import_validation = _build_query_engine_import_validation(
        handoff_contract_version="1.0",
        handoff_status=status,
        graph=graph,
        graph_export_format="graph-json",
        graph_export_contract_version=(graph_adapter_result.export_contract_version if graph_adapter_result is not None else "unknown"),
        graph_incremental_mode=(graph_adapter_result.incremental_mode if graph_adapter_result is not None else "event-driven_rebuildable"),
        primary_record_path=".chronicle/chronicle.jsonl",
        referenced_record_ids=referenced_record_ids,
    )
    return RuntimeQueryEngineHandoff(
        status=status,
        query=query,
        graph_export_contract_version=(graph_adapter_result.export_contract_version if graph_adapter_result is not None else "unknown"),
        graph_incremental_mode=(graph_adapter_result.incremental_mode if graph_adapter_result is not None else "event-driven_rebuildable"),
        derived_surfaces=derived_surfaces,
        referenced_record_ids=referenced_record_ids,
        eligible_context_ids=context_ids,
        skipped_record_ids=skipped_ids,
        source_summaries=composition.source_summaries,
        overlap_identifier_count=composition.overlap_identifier_count,
        suggested_commands=[
            "chronicle graph summary --json",
            'chronicle export --format graph-json -o graph.json',
            'chronicle package review --purpose "runtime query-engine handoff"',
        ],
        prohibited_assumptions=[
            "no hosted query engine is included",
            "no graph runtime or vector runtime is included",
            "no external query execution is implied",
            "primary Chronicle records remain authoritative",
        ],
        import_validation=import_validation,
        notes=[
            "downstream query-engine handoff stays derived and read-only",
            "graph-json export remains rebuildable from Chronicle events",
            "handoff is advisory until a downstream consumer explicitly imports it",
        ],
    )



def _build_query_engine_import_validation(
    *,
    handoff_contract_version: str,
    handoff_status: str,
    graph,
    graph_export_format: str,
    graph_export_contract_version: str,
    graph_incremental_mode: str,
    primary_record_path: str,
    referenced_record_ids: list[str],
) -> RuntimeQueryEngineImportValidation:
    export_contract = getattr(graph, "export_contract", None)
    export_manifest = getattr(graph, "export_manifest", None)
    checks = [
        RuntimeQueryEngineImportCheck(
            name="graph_export_available",
            passed=graph is not None,
            detail="graph-json export is available for downstream inspection" if graph is not None else "graph-json export is unavailable",
        ),
        RuntimeQueryEngineImportCheck(
            name="graph_export_format_matches",
            passed=bool(export_manifest is not None and export_manifest.export_format == graph_export_format),
            detail=(
                f"handoff={graph_export_format}; export={export_manifest.export_format}"
                if export_manifest is not None
                else "graph export manifest unavailable"
            ),
        ),
        RuntimeQueryEngineImportCheck(
            name="graph_contract_version_matches",
            passed=bool(export_contract is not None and export_contract.contract_version == graph_export_contract_version),
            detail=(
                f"handoff={graph_export_contract_version}; export={export_contract.contract_version}"
                if export_contract is not None
                else "graph export contract unavailable"
            ),
        ),
        RuntimeQueryEngineImportCheck(
            name="incremental_mode_matches",
            passed=bool(export_contract is not None and export_contract.incremental_mode == graph_incremental_mode),
            detail=(
                f"handoff={graph_incremental_mode}; export={export_contract.incremental_mode}"
                if export_contract is not None
                else "graph export contract unavailable"
            ),
        ),
        RuntimeQueryEngineImportCheck(
            name="primary_record_matches",
            passed=bool(export_contract is not None and export_contract.primary_record == primary_record_path),
            detail=(
                f"handoff={primary_record_path}; export={export_contract.primary_record}"
                if export_contract is not None
                else "graph export contract unavailable"
            ),
        ),
        RuntimeQueryEngineImportCheck(
            name="runtime_boundaries_preserved",
            passed=bool(
                export_contract is not None
                and not export_contract.graph_runtime_included
                and not export_contract.external_runtime_required
            ),
            detail=(
                "graph export keeps runtime responsibilities outside Chronicle core"
                if export_contract is not None
                else "graph export contract unavailable"
            ),
        ),
        RuntimeQueryEngineImportCheck(
            name="referenced_records_present",
            passed=bool(referenced_record_ids),
            detail=(
                f"referenced records={len(referenced_record_ids)}"
                if referenced_record_ids
                else "no referenced records available for downstream import"
            ),
        ),
    ]
    structural_checks_pass = all(check.passed for check in checks[:-1])
    import_ready = structural_checks_pass and bool(referenced_record_ids)
    if not structural_checks_pass:
        status = "contract_mismatch"
    elif handoff_status == "advisory_only":
        status = "advisory_only"
    else:
        status = "contract_validated"
    return RuntimeQueryEngineImportValidation(
        status=status,
        import_ready=import_ready,
        graph_export_available=graph is not None,
        graph_export_node_count=(len(graph.nodes) if graph is not None else 0),
        graph_export_edge_count=(len(graph.edges) if graph is not None else 0),
        checks=checks,
        notes=[
            "validation inspects derived graph export compatibility only",
            "no downstream import or query execution occurs here",
            "primary Chronicle records remain authoritative over any derived consumer state",
        ],
    )
