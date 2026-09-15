"""Framework-neutral service adapter for Chronicle API contract requests.

This adapter is the Phase 2 bridge between transport-free API contracts and
existing Core services.  It deliberately does not open sockets and does not
enable committed API writes yet.
"""

from pathlib import Path
from typing import Any
from datetime import datetime, timezone

from chronicle.api.contracts import (
    ApiError,
    ApiErrorCode,
    ApiReadResponse,
    ApiWarning,
    ApiWriteRequest,
    ApiWriteResponse,
    AssertionWriteRequest,
    BoundariesQueryRequest,
    ContextQueryRequest,
    DiffWriteRequest,
    EventWriteRequest,
    TimelineQueryRequest,
)
from chronicle.ids import generate_id
from chronicle.models.audit import AuditOperation, AuditSeverity, AuditTargetEnvironment
from chronicle.models.boundary import BoundaryRuleType
from chronicle.models.chronicle_object import ChronicleObjectRecord, ChronicleObjectType
from chronicle.models.event import Actor, ChronicleEvent, EventType
from chronicle.models.visibility import VisibilityHint
from chronicle.services.audit_service import AuditService
from chronicle.services.boundary_service import BoundaryService
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.rde_service import RdeService


class ApiAdapterService:
    """Apply API contract semantics without binding them to HTTP."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path.cwd()
        self.chronicle = ChronicleService(self.root)
        self.boundaries = BoundaryService(self.root)
        self.audit = AuditService(self.root)
        self.rde = RdeService(self.root)

    def preview_event_write(self, request: EventWriteRequest) -> ApiWriteResponse:
        return self._preview_write(request, accepted_message="event_write_preview")

    def commit_event_write(self, request: EventWriteRequest) -> ApiWriteResponse:
        self.chronicle.require_initialized()
        duplicate = self._find_duplicate_api_event(
            endpoint="POST /events",
            idempotency_key=request.idempotency_key,
        )
        if duplicate:
            return ApiWriteResponse(
                accepted=True,
                dry_run=False,
                duplicate=True,
                idempotency_key=request.idempotency_key,
                event_id=duplicate.event_id,
                warnings=[
                    ApiWarning(
                        code="duplicate_idempotency_key",
                        severity="info",
                        message="Duplicate API write request returned the existing event.",
                    )
                ],
            )

        payload = dict(request.payload)
        payload["api"] = {
            "schema_version": request.schema_version,
            "endpoint": "POST /events",
            "idempotency_key": request.idempotency_key,
            "origin": request.origin.model_dump(mode="json"),
            "dry_run": False,
            "audit_reason": request.audit_reason,
        }
        event = self.chronicle.record_event(
            event_type=request.event_type,
            actor=request.actor,
            summary=request.summary,
            payload=payload,
            parent_event_id=request.parent_event_id,
            artifact_id=request.artifact_id,
            context_ids=request.context_ids,
            decision_id=request.decision_id,
            rde_record_id=request.rde_record_id,
            source=request.source,
            classification=request.classification,
            confidence=request.confidence,
            review_status=request.review_status,
            tags=request.tags,
        )
        self.chronicle.rebuild_indexes()
        self.audit.record(
            operation=AuditOperation.API_WRITE,
            actor=request.origin.actor_id,
            purpose=request.audit_reason or request.summary,
            target_environment=AuditTargetEnvironment.LOCAL,
            referenced_records=[event.event_id, *request.context_ids],
            source_event_id=event.event_id,
            result=AuditSeverity.INFO,
            summary=f"API write accepted for {event.event_type.value}: {event.summary}",
            metadata={
                "endpoint": "POST /events",
                "idempotency_key": request.idempotency_key,
                "source_tool": request.origin.source_tool,
                "actor_kind": request.origin.actor_kind.value,
                "review_status": request.review_status.value,
            },
        )
        return ApiWriteResponse(
            accepted=True,
            dry_run=False,
            idempotency_key=request.idempotency_key,
            event_id=event.event_id,
            warnings=[
                ApiWarning(
                    code="api_write_recorded",
                    severity="info",
                    message="API event write was recorded through Chronicle Core services.",
                )
            ],
        )

    def preview_diff_write(self, request: DiffWriteRequest) -> ApiWriteResponse:
        return self._preview_write(request, accepted_message="diff_write_preview")

    def commit_diff_write(self, request: DiffWriteRequest) -> ApiWriteResponse:
        self.chronicle.require_initialized()
        duplicate = self._find_duplicate_api_event(
            endpoint="POST /diffs",
            idempotency_key=request.idempotency_key,
        )
        if duplicate:
            return ApiWriteResponse(
                accepted=True,
                dry_run=False,
                duplicate=True,
                idempotency_key=request.idempotency_key,
                event_id=duplicate.event_id,
                rde_record_id=duplicate.rde_record_id,
                warnings=[
                    ApiWarning(
                        code="duplicate_idempotency_key",
                        severity="info",
                        message="Duplicate diff request returned the existing RDE event.",
                    )
                ],
            )

        rde_record = self.rde.record(
            artifact_id=request.artifact_id,
            from_version_id=request.from_version_id,
            to_version_id=request.to_version_id,
            summary=request.summary,
            created_by=request.created_by,
            preserved=request.preserved,
            transformed=request.transformed,
            supplemented=request.supplemented,
            unresolved=request.unresolved,
            deviation_risks=request.deviation_risks,
            next_update_policy=request.next_update_policy,
            api_metadata={
                "schema_version": request.schema_version,
                "endpoint": "POST /diffs",
                "idempotency_key": request.idempotency_key,
                "origin": request.origin.model_dump(mode="json"),
                "dry_run": False,
                "audit_reason": request.audit_reason,
            },
        )
        event = self._find_duplicate_api_event(
            endpoint="POST /diffs",
            idempotency_key=request.idempotency_key,
        )
        event_id = event.event_id if event else None
        self.audit.record(
            operation=AuditOperation.API_WRITE,
            actor=request.origin.actor_id,
            purpose=request.audit_reason or request.summary,
            target_environment=AuditTargetEnvironment.LOCAL,
            referenced_records=[
                *([event_id] if event_id else []),
                rde_record.rde_record_id,
                request.artifact_id,
            ],
            source_event_id=event_id,
            result=AuditSeverity.INFO,
            summary=f"API RDE diff recorded: {request.summary or rde_record.rde_record_id}",
            metadata={
                "endpoint": "POST /diffs",
                "idempotency_key": request.idempotency_key,
                "source_tool": request.origin.source_tool,
                "actor_kind": request.origin.actor_kind.value,
                "review_status": request.review_status.value,
            },
        )
        return ApiWriteResponse(
            accepted=True,
            dry_run=False,
            idempotency_key=request.idempotency_key,
            event_id=event_id,
            rde_record_id=rde_record.rde_record_id,
            warnings=[
                ApiWarning(
                    code="api_diff_recorded",
                    severity="info",
                    message="API RDE diff was recorded through Chronicle RDE service.",
                )
            ],
        )

    def preview_assertion_write(self, request: AssertionWriteRequest) -> ApiWriteResponse:
        return self._preview_write(request, accepted_message="assertion_write_preview")

    def commit_assertion_write(self, request: AssertionWriteRequest) -> ApiWriteResponse:
        metadata = self.chronicle.require_initialized()
        duplicate = self._find_duplicate_api_event(
            endpoint="POST /assertions",
            idempotency_key=request.idempotency_key,
        )
        if duplicate:
            assertion_payload = duplicate.payload.get("chronicle_object", {})
            assertion_id = (
                assertion_payload.get("object_id")
                if isinstance(assertion_payload, dict)
                else None
            )
            return ApiWriteResponse(
                accepted=True,
                dry_run=False,
                duplicate=True,
                idempotency_key=request.idempotency_key,
                event_id=duplicate.event_id,
                assertion_id=assertion_id,
                warnings=[
                    ApiWarning(
                        code="duplicate_idempotency_key",
                        severity="info",
                        message="Duplicate assertion request returned the existing event.",
                    )
                ],
            )

        now = datetime.now(timezone.utc).astimezone()
        event_id = generate_id("event")
        assertion_id = generate_id("object")
        record = ChronicleObjectRecord(
            object_id=assertion_id,
            object_type=self._assertion_object_type(request),
            chronicle_id=metadata.chronicle_id,
            created_at=now,
            created_by=request.origin.actor_id,
            summary=request.statement,
            detail=self._assertion_detail(request),
            visibility_hint=VisibilityHint.UNKNOWN,
            source_event_id=event_id,
            artifact_id=request.artifact_id,
            context_id=request.context_ids[0] if request.context_ids else None,
            evidence=request.evidence_refs,
            derived=False,
        )
        event = ChronicleEvent(
            event_id=event_id,
            chronicle_id=metadata.chronicle_id,
            timestamp=now,
            event_type=EventType.CHRONICLE_OBJECT_RECORDED,
            actor=Actor.TOOL,
            summary=f"API assertion recorded: {request.statement}",
            payload={
                "chronicle_object": record.model_dump(mode="json"),
                "api": {
                    "schema_version": request.schema_version,
                    "endpoint": "POST /assertions",
                    "idempotency_key": request.idempotency_key,
                    "origin": request.origin.model_dump(mode="json"),
                    "assertion_kind": request.assertion_kind.value,
                    "verification_status": request.verification_status.value,
                    "dry_run": False,
                    "audit_reason": request.audit_reason,
                },
            },
            context_ids=request.context_ids,
            artifact_id=request.artifact_id,
            source=request.source,
            confidence=request.confidence,
            review_status=request.review_status,
            tags=["api_assertion", request.assertion_kind.value],
        )
        self.chronicle.append_event(event)
        self.audit.record(
            operation=AuditOperation.API_WRITE,
            actor=request.origin.actor_id,
            purpose=request.audit_reason or request.statement,
            target_environment=AuditTargetEnvironment.LOCAL,
            referenced_records=[event.event_id, assertion_id, *request.context_ids],
            source_event_id=event.event_id,
            result=AuditSeverity.INFO,
            summary=f"API assertion recorded: {request.statement}",
            metadata={
                "endpoint": "POST /assertions",
                "idempotency_key": request.idempotency_key,
                "source_tool": request.origin.source_tool,
                "actor_kind": request.origin.actor_kind.value,
                "assertion_kind": request.assertion_kind.value,
                "verification_status": request.verification_status.value,
                "review_status": request.review_status.value,
            },
        )
        return ApiWriteResponse(
            accepted=True,
            dry_run=False,
            idempotency_key=request.idempotency_key,
            event_id=event.event_id,
            assertion_id=assertion_id,
            warnings=[
                ApiWarning(
                    code="api_assertion_recorded",
                    severity="info",
                    message="API assertion was recorded as a reviewable Chronicle object.",
                )
            ],
        )

    def get_context(self, request: ContextQueryRequest) -> ApiReadResponse:
        self.chronicle.require_initialized()
        self.chronicle.rebuild_indexes()
        contexts = self.chronicle.index.load_contexts()
        selected_ids = set(request.context_ids)
        rows: list[dict[str, Any]] = []
        warnings: list[ApiWarning] = []

        for context_id, context in sorted(contexts.items()):
            if selected_ids and context_id not in selected_ids:
                continue
            row = context.model_dump(mode="json")
            if not request.include_payload:
                row.pop("source_ref", None)
            rows.append(row)
            if len(rows) >= request.limit:
                break

        if selected_ids and len(rows) != len(selected_ids):
            warnings.append(
                ApiWarning(
                    code="context_selector_unresolved",
                    message="One or more requested context_ids were not found.",
                    next_action="Check the context index before using this response.",
                )
            )
        return ApiReadResponse(boundary_preview=request.boundary_preview, records=rows, warnings=warnings)

    def get_timeline(self, request: TimelineQueryRequest) -> ApiReadResponse:
        self.chronicle.require_initialized()
        events = self.chronicle.jsonl.read_all(skip_corrupt=True)
        selected_contexts = set(request.context_ids)
        rows: list[dict[str, Any]] = []

        for event in events:
            if selected_contexts and not selected_contexts.intersection(event.context_ids):
                continue
            if request.artifact_id and event.artifact_id != request.artifact_id:
                continue
            if request.decision_id and event.decision_id != request.decision_id:
                continue
            row = event.model_dump(mode="json")
            if not request.include_payload:
                row.pop("payload", None)
            rows.append(row)
            if len(rows) >= request.limit:
                break

        return ApiReadResponse(boundary_preview=request.boundary_preview, records=rows)

    def get_boundaries(self, request: BoundariesQueryRequest) -> ApiReadResponse:
        self.chronicle.require_initialized()
        rules = self.boundaries.list_rules()
        rows: list[dict[str, Any]] = []
        for rule in sorted(rules, key=lambda item: item.rule_id):
            rows.append(rule.model_dump(mode="json"))

        warnings = []
        if any(rule.rule_type == BoundaryRuleType.WARN for rule in rules):
            warnings.append(
                ApiWarning(
                    code="advisory_boundary_rules",
                    message="Boundary rules are advisory and do not prove authorization.",
                    next_action="Run a preview before disclosing or injecting context.",
                )
            )
        return ApiReadResponse(boundary_preview=True, records=rows, warnings=warnings)

    def _preview_write(self, request: ApiWriteRequest, accepted_message: str) -> ApiWriteResponse:
        if not request.dry_run:
            return ApiWriteResponse(
                accepted=False,
                dry_run=False,
                idempotency_key=request.idempotency_key,
                errors=[
                    ApiError(
                        code=ApiErrorCode.PARTIAL_PERSISTENCE_BLOCKED,
                        message="Committed API writes are blocked until service persistence is specified.",
                    )
                ],
            )

        warnings = [
            ApiWarning(
                code=accepted_message,
                severity="info",
                message="Request validated as a dry-run preview; no primary record was changed.",
            )
        ]
        if request.review_status.value != "reviewed":
            warnings.append(
                ApiWarning(
                    code="review_required",
                    message="API-originated writes require review before trust or apply.",
                    next_action="Route through review, decision, or RDE workflow before relying on it.",
                )
            )
        return ApiWriteResponse(
            accepted=True,
            dry_run=True,
            idempotency_key=request.idempotency_key,
            warnings=warnings,
        )

    def _find_duplicate_api_event(
        self,
        *,
        endpoint: str,
        idempotency_key: str,
    ) -> ChronicleEvent | None:
        for event in self.chronicle.jsonl.read_all(skip_corrupt=True):
            api_metadata = event.payload.get("api")
            if not isinstance(api_metadata, dict):
                continue
            if (
                api_metadata.get("endpoint") == endpoint
                and api_metadata.get("idempotency_key") == idempotency_key
            ):
                return event
        return None

    @staticmethod
    def _assertion_object_type(request: AssertionWriteRequest) -> ChronicleObjectType:
        if request.assertion_kind.value == "caveat":
            return ChronicleObjectType.OBJECTION
        if request.assertion_kind.value == "unknown":
            return ChronicleObjectType.QUESTION
        return ChronicleObjectType.HYPOTHESIS

    @staticmethod
    def _assertion_detail(request: AssertionWriteRequest) -> str:
        sections = [
            f"assertion_kind={request.assertion_kind.value}",
            f"verification_status={request.verification_status.value}",
        ]
        if request.subject_ref:
            sections.append(f"subject_ref={request.subject_ref}")
        if request.caveats:
            sections.append("caveats=" + " | ".join(request.caveats))
        return "\n".join(sections)
