"""Explicit local runtime service with placeholder summarization."""

import json
import os
import re
from pathlib import Path
from urllib import error as urllib_error
from urllib import request as urllib_request

from chronicle.errors import (
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
    RuntimeConfig,
    RuntimeExecutionResult,
    RuntimeInvocationPlan,
    RuntimeProviderKind,
    RuntimeRecordPreview,
    RuntimeRetrievalHandoff,
    RuntimeRetrievalHit,
    RuntimeRetrievalPlan,
    RuntimeStatus,
    RuntimeSummaryResult,
)
from chronicle.models.summary_job import SummarySourceRef
from chronicle.models.source import SourceProvenance
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.artifact_service import ArtifactService
from chronicle.services.graph_export_service import GraphExportService
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

        graph = self.graph_export.export_graph()
        query_lower = query.lower()
        graph_hits: list[RuntimeRetrievalHit] = []
        for node in graph.nodes:
            haystack = f"{node.title} {node.summary} {node.node_type} {node.metadata}".lower()
            if query_lower in haystack:
                graph_hits.append(
                    RuntimeRetrievalHit(
                        source="graph_export",
                        identifier=node.source_id,
                        summary=node.title or node.summary or node.node_type,
                        detail=node.node_type,
                    )
                )
        graph_hits = graph_hits[:limit]

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
        plan = RuntimeRetrievalPlan(
            query=query,
            vector_hits=vector_hits,
            graph_hits=graph_hits,
            chronicle_hits=chronicle_hits,
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
        source_ref_count: int = 0,
        extra_params: dict[str, str] | None = None,
    ) -> RuntimeInvocationPlan:
        return self._invocation_plan(
            text=text,
            operation=operation,
            record=record,
            source_ref_count=source_ref_count,
            extra_params=extra_params or {},
        )

    def invocation_plan_from_summary(
        self,
        *,
        summary_job_id: str,
        summary_title: str,
        summary_text: str,
        prompt: str = "",
        source_ref_count: int = 0,
        operation: str = "summarize",
        record: bool = False,
    ) -> RuntimeInvocationPlan:
        return self._invocation_plan(
            text=summary_text,
            operation=operation,
            record=record,
            source_ref_count=source_ref_count,
            request_context={
                "summary_job_id": summary_job_id,
                "summary_title": summary_title,
                "prompt": prompt,
                "source_ref_count": str(source_ref_count),
            },
            summary_label=f"summary {summary_job_id} {operation}",
        )

    def _invocation_plan(
        self,
        *,
        text: str,
        operation: str,
        record: bool,
        source_ref_count: int = 0,
        extra_params: dict[str, str] | None = None,
        request_context: dict[str, str] | None = None,
        summary_label: str | None = None,
    ) -> RuntimeInvocationPlan:
        config_state = self.runtime_config.show()
        config = config_state.config
        blocking_reasons: list[str] = []
        would_use_network = config.provider_kind == RuntimeProviderKind.HTTP
        network_allowed = bool(config.allow_network)

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
        return plan

    def _assistant_output_event_type(self):
        from chronicle.models.event import EventType

        return EventType.ASSISTANT_OUTPUT

    def record_preview(self, event: object) -> RuntimeRecordPreview:
        payload = getattr(event, "payload", {})
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
    seen: set[str] = set()
    identifiers: list[str] = []
    for hit in [*plan.vector_hits, *plan.graph_hits, *plan.chronicle_hits]:
        if hit.identifier and hit.identifier not in seen:
            identifiers.append(hit.identifier)
            seen.add(hit.identifier)
    return identifiers
