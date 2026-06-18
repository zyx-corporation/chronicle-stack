"""Explicit local runtime service with placeholder summarization."""

import re
from pathlib import Path

from chronicle.models.event import Actor, Confidence, ReviewStatus
from chronicle.models.runtime import (
    RuntimeProviderKind,
    RuntimeRecordPreview,
    RuntimeRetrievalHandoff,
    RuntimeRetrievalHit,
    RuntimeRetrievalPlan,
    RuntimeStatus,
    RuntimeSummaryResult,
)
from chronicle.models.source import SourceProvenance
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.graph_export_service import GraphExportService
from chronicle.services.search_service import SearchService
from chronicle.services.vector_index_service import VectorIndexService


class RuntimeService:
    """Provide explicit local runtime actions without external calls."""

    def __init__(self, root: Path | None = None) -> None:
        self.chronicle = ChronicleService(root)
        self.vector_index = VectorIndexService(root)
        self.graph_export = GraphExportService(root)
        self.search = SearchService(root)

    def status(self) -> RuntimeStatus:
        return RuntimeStatus()

    def summarize(self, *, text: str, max_sentences: int = 3, record: bool = False) -> RuntimeSummaryResult:
        generated_text = _summarize_text(text, max_sentences=max_sentences)
        result = RuntimeSummaryResult(
            source_text_length=len(text),
            generated_text=generated_text,
            recorded=record,
        )
        if not record:
            return result

        event = self.chronicle.record_event(
            event_type=self._assistant_output_event_type(),
            actor=Actor.ASSISTANT,
            summary=f"Runtime summary generated: {_truncate_summary(generated_text)}",
            payload={
                "runtime_summary": result.model_dump(mode="json"),
                "runtime_provider": RuntimeProviderKind.LOCAL.value,
            },
            source=SourceProvenance(
                source_type="runtime",
                source_ref="local-placeholder-summary",
                source_tool="chronicle-runtime",
                source_model="local-placeholder",
            ),
            review_status=ReviewStatus.NEEDS_REVIEW,
            confidence=Confidence.LOW,
        )
        result.recorded = True
        result.event_id = event.event_id
        return result

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
