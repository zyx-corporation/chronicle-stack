"""Append-only proposal records for proposal-first editing flows."""

import hashlib
from pathlib import Path
from typing import Any

from chronicle.errors import (
    ArtifactNotFoundError,
    ContextNotFoundError,
    ProposalChangeMissingError,
    SourceFileNotFoundError,
)
from chronicle.models.context import ContextScope
from chronicle.models.event import Actor, EventType, ReviewStatus
from chronicle.services.chronicle_service import ChronicleService


def _content_preview(value: str, *, limit: int = 280) -> str:
    if len(value) <= limit:
        return value
    return f"{value[:limit]}…"


class ProposalService:
    """Record append-only proposal events for later review/apply flows."""

    def __init__(self, root: Path | None = None) -> None:
        self.chronicle = ChronicleService(root)

    def propose_artifact_update(
        self,
        *,
        artifact_id: str,
        summary: str,
        source_file: Path | None = None,
        content: str | None = None,
        proposed_title: str = "",
        actor: Actor = Actor.USER,
    ):
        self.chronicle.require_initialized()
        artifacts, _versions = self.chronicle.index.load_artifacts()
        artifact = artifacts.get(artifact_id)
        if artifact is None:
            raise ArtifactNotFoundError(artifact_id)

        proposed_content = content
        if source_file is not None:
            if not source_file.exists():
                raise SourceFileNotFoundError(str(source_file))
            proposed_content = source_file.read_text(encoding="utf-8")

        if not any([proposed_title.strip(), summary.strip(), proposed_content is not None]):
            raise ProposalChangeMissingError("artifact")

        payload: dict[str, Any] = {
            "proposal": {
                "proposal_kind": "artifact_update",
                "target_kind": "artifact",
                "target_id": artifact_id,
                "target_title": artifact.title,
                "proposal_summary": summary or f"Propose artifact update for {artifact.title}",
                "proposed_fields": {},
                "requires_apply_step": True,
                "apply_mode": "cli_apply_after_review",
                "cli_review_hint": "chronicle review approve --event <proposal_event_id> --reviewer <name>",
                "cli_apply_hint": f"chronicle artifact update --artifact {artifact_id} --file <path> --summary {summary or 'Apply approved proposal'}",
                "boundary_note": "Proposal records are append-only Chronicle events; approval does not apply the target change automatically.",
            }
        }
        if proposed_title.strip():
            payload["proposal"]["proposed_fields"]["title"] = proposed_title
        if proposed_content is not None:
            payload["proposal"]["proposed_content"] = {
                "length": len(proposed_content),
                "sha256": hashlib.sha256(proposed_content.encode("utf-8")).hexdigest(),
                "preview": _content_preview(proposed_content),
                "source_file": str(source_file) if source_file is not None else None,
            }

        event = self.chronicle.record_event(
            event_type=EventType.PROPOSAL_RECORDED,
            actor=actor,
            summary=summary or f"Artifact update proposed: {artifact.title}",
            payload=payload,
            artifact_id=artifact_id,
            review_status=ReviewStatus.NEEDS_REVIEW,
        )
        self.chronicle.rebuild_indexes()
        return event

    def propose_context_update(
        self,
        *,
        context_id: str,
        summary: str,
        proposed_title: str = "",
        proposed_summary: str = "",
        proposed_scope: ContextScope | None = None,
        proposed_tags: list[str] | None = None,
        actor: Actor = Actor.USER,
    ):
        self.chronicle.require_initialized()
        contexts = self.chronicle.index.load_contexts()
        context = contexts.get(context_id)
        if context is None:
            raise ContextNotFoundError(context_id)

        proposed_fields: dict[str, Any] = {}
        if proposed_title.strip():
            proposed_fields["title"] = proposed_title
        if proposed_summary.strip():
            proposed_fields["summary"] = proposed_summary
        if proposed_scope is not None:
            proposed_fields["scope"] = proposed_scope.value
        if proposed_tags:
            proposed_fields["tags"] = [tag for tag in proposed_tags if tag]
        if not proposed_fields and not summary.strip():
            raise ProposalChangeMissingError("context")

        payload: dict[str, Any] = {
            "proposal": {
                "proposal_kind": "context_update",
                "target_kind": "context",
                "target_id": context_id,
                "target_title": context.title,
                "proposal_summary": summary or f"Propose context update for {context.title}",
                "proposed_fields": proposed_fields,
                "requires_apply_step": True,
                "apply_mode": "cli_apply_after_review",
                "cli_review_hint": "chronicle review approve --event <proposal_event_id> --reviewer <name>",
                "boundary_note": "Proposal records are append-only Chronicle events; approval does not apply the target change automatically.",
            }
        }

        event = self.chronicle.record_event(
            event_type=EventType.PROPOSAL_RECORDED,
            actor=actor,
            summary=summary or f"Context update proposed: {context.title}",
            payload=payload,
            context_ids=[context_id],
            review_status=ReviewStatus.NEEDS_REVIEW,
        )
        self.chronicle.rebuild_indexes()
        return event

    def list_proposals(self) -> list[dict[str, Any]]:
        self.chronicle.require_initialized()
        rows: list[dict[str, Any]] = []
        for event in self.chronicle.jsonl.read_all():
            proposal = getattr(event, "payload", {}).get("proposal")
            if not isinstance(proposal, dict):
                continue
            rows.append(
                {
                    "event_id": event.event_id,
                    "timestamp": event.timestamp.isoformat(),
                    "summary": event.summary,
                    "review_status": getattr(event.review_status, "value", None),
                    "proposal": proposal,
                    "artifact_id": event.artifact_id,
                    "context_ids": list(event.context_ids),
                }
            )
        rows.sort(key=lambda item: item["timestamp"])
        return rows

    def proposals_for_target(self, *, target_kind: str, target_id: str) -> list[dict[str, Any]]:
        return [
            row
            for row in self.list_proposals()
            if row.get("proposal", {}).get("target_kind") == target_kind
            and row.get("proposal", {}).get("target_id") == target_id
        ]
