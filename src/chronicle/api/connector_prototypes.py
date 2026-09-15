"""Local connector prototype simulator for the Chronicle API roadmap.

These helpers do not integrate with external applications.  They generate or
submit structured API requests so connector uncertainty can be tested without
turning prototypes into production surfaces.
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from chronicle.api.contracts import (
    ApiActorKind,
    ApiOriginMetadata,
    ApiWriteResponse,
    AssertionKind,
    AssertionWriteRequest,
    EventWriteRequest,
)
from chronicle.models.event import Actor, EventType
from chronicle.models.source import SourceProvenance
from chronicle.services.api_adapter_service import ApiAdapterService


class ConnectorPrototypeKind(StrEnum):
    OBSIDIAN_CAPTURE = "obsidian_capture"
    GIT_EVIDENCE = "git_evidence"
    BROWSER_CAPTURE = "browser_capture"
    AGENT_ASSERTION = "agent_assertion"
    BUSINESS_FACT = "business_fact"


class ConnectorPrototypeSimulation(BaseModel):
    connector: ConnectorPrototypeKind
    production_surface: bool = False
    request_model: str
    request_payload: dict[str, Any]
    response: dict[str, Any] | None = None
    carry_forward: list[str] = Field(default_factory=list)
    do_not_carry_forward: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ConnectorPrototypeSimulator:
    """Build and optionally submit local connector prototype requests."""

    def __init__(self, root: Path | None = None) -> None:
        self.adapter = ApiAdapterService(root)

    def simulate(
        self,
        *,
        connector: ConnectorPrototypeKind,
        title: str,
        body: str,
        idempotency_key: str,
        commit: bool = False,
        context_ids: list[str] | None = None,
        source_ref: str = "",
        source_url: str | None = None,
        subject_ref: str | None = None,
    ) -> ConnectorPrototypeSimulation:
        request = self._build_request(
            connector=connector,
            title=title,
            body=body,
            idempotency_key=idempotency_key,
            commit=commit,
            context_ids=context_ids or [],
            source_ref=source_ref,
            source_url=source_url,
            subject_ref=subject_ref,
        )
        response: ApiWriteResponse | None = None
        if isinstance(request, EventWriteRequest):
            response = (
                self.adapter.commit_event_write(request)
                if commit
                else self.adapter.preview_event_write(request)
            )
        else:
            response = (
                self.adapter.commit_assertion_write(request)
                if commit
                else self.adapter.preview_assertion_write(request)
            )
        return ConnectorPrototypeSimulation(
            connector=connector,
            request_model=request.__class__.__name__,
            request_payload=request.model_dump(mode="json"),
            response=response.model_dump(mode="json"),
            carry_forward=self._carry_forward(connector),
            do_not_carry_forward=self._do_not_carry_forward(connector),
            warnings=[
                "prototype_only_not_production_connector",
                "no_external_application_was_contacted",
                *([] if commit else ["dry_run_no_primary_record_changed"]),
            ],
        )

    def _build_request(
        self,
        *,
        connector: ConnectorPrototypeKind,
        title: str,
        body: str,
        idempotency_key: str,
        commit: bool,
        context_ids: list[str],
        source_ref: str,
        source_url: str | None,
        subject_ref: str | None,
    ) -> EventWriteRequest | AssertionWriteRequest:
        origin = ApiOriginMetadata(
            source_tool=f"prototype:{connector.value}",
            actor_id=f"prototype:{connector.value}",
            actor_kind=(
                ApiActorKind.AGENT
                if connector == ConnectorPrototypeKind.AGENT_ASSERTION
                else ApiActorKind.TOOL
            ),
        )
        if connector in {
            ConnectorPrototypeKind.AGENT_ASSERTION,
            ConnectorPrototypeKind.BUSINESS_FACT,
        }:
            return AssertionWriteRequest(
                idempotency_key=idempotency_key,
                origin=origin,
                dry_run=not commit,
                assertion_kind=(
                    AssertionKind.CLAIM
                    if connector == ConnectorPrototypeKind.BUSINESS_FACT
                    else AssertionKind.CAVEAT
                ),
                statement=body,
                subject_ref=subject_ref or title,
                context_ids=context_ids,
                source=SourceProvenance(
                    source_type=connector.value,
                    source_ref=source_ref or title,
                    source_url=source_url,
                    source_tool=origin.source_tool,
                ),
                audit_reason=f"connector prototype simulation: {connector.value}",
            )
        return EventWriteRequest(
            idempotency_key=idempotency_key,
            origin=origin,
            dry_run=not commit,
            event_type=EventType.NOTE_ADDED,
            actor=Actor.TOOL,
            summary=title,
            payload={
                "connector_prototype": connector.value,
                "body": body,
                "source_ref": source_ref,
                "source_url": source_url,
            },
            context_ids=context_ids,
            source=SourceProvenance(
                source_type=connector.value,
                source_ref=source_ref or title,
                source_url=source_url,
                source_tool=origin.source_tool,
            ),
            tags=["connector_prototype", connector.value],
            audit_reason=f"connector prototype simulation: {connector.value}",
        )

    @staticmethod
    def _carry_forward(connector: ConnectorPrototypeKind) -> list[str]:
        common = [
            "idempotency_key_required",
            "origin_metadata_required",
            "api_write_audit_required",
        ]
        specific = {
            ConnectorPrototypeKind.OBSIDIAN_CAPTURE: [
                "local_file_or_note_reference",
                "structured_note_summary",
            ],
            ConnectorPrototypeKind.GIT_EVIDENCE: [
                "repository_ref",
                "commit_or_pr_reference",
                "secret_exclusion_check",
            ],
            ConnectorPrototypeKind.BROWSER_CAPTURE: [
                "source_url_required",
                "external_disclosure_warning",
            ],
            ConnectorPrototypeKind.AGENT_ASSERTION: [
                "human_vs_agent_metadata",
                "review_required_for_agent_claims",
            ],
            ConnectorPrototypeKind.BUSINESS_FACT: [
                "subject_ref_required",
                "reject_arbitrary_webhook_dump",
            ],
        }
        return [*common, *specific[connector]]

    @staticmethod
    def _do_not_carry_forward(connector: ConnectorPrototypeKind) -> list[str]:
        common = [
            "no_external_app_runtime",
            "no_background_sync",
            "no_production_credentials",
            "no_hosted_cloud_dependency",
        ]
        if connector == ConnectorPrototypeKind.BUSINESS_FACT:
            return [*common, "no_generic_log_ingestion"]
        return common
