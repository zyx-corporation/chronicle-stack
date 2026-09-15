"""Framework-neutral contracts for the planned Chronicle-native API.

The API roadmap requires schemas before a daemon implementation.  These
Pydantic models are intentionally transport-free: tests can validate request
shape, idempotency metadata, and boundary-aware selectors without opening a
network socket.
"""

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from chronicle.models.classification import AllowedOperation, ClassificationMetadata
from chronicle.models.event import Actor, Confidence, EventType, ReviewStatus
from chronicle.models.source import SourceProvenance

API_SCHEMA_VERSION = "chronicle-api/v0.1-draft"


class ApiEndpoint(StrEnum):
    POST_EVENTS = "POST /events"
    GET_CONTEXT = "GET /context"
    POST_DIFFS = "POST /diffs"
    GET_TIMELINE = "GET /timeline"
    POST_ASSERTIONS = "POST /assertions"
    GET_BOUNDARIES = "GET /boundaries"


class ApiActorKind(StrEnum):
    HUMAN = "human"
    AI_ASSISTANT = "ai_assistant"
    AGENT = "agent"
    TOOL = "tool"
    BUSINESS_SYSTEM = "business_system"
    IMPORTER = "importer"


class AssertionKind(StrEnum):
    CLAIM = "claim"
    EVIDENCE = "evidence"
    CAVEAT = "caveat"
    UNKNOWN = "unknown"
    VERIFICATION_STATUS = "verification_status"


class AssertionVerificationStatus(StrEnum):
    UNVERIFIED = "unverified"
    SUPPORTED = "supported"
    CONTESTED = "contested"
    DISPROVEN = "disproven"
    UNKNOWN = "unknown"


class ApiErrorCode(StrEnum):
    VALIDATION_ERROR = "validation_error"
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    CONFLICT = "conflict"
    DUPLICATE = "duplicate"
    BOUNDARY_WARNING = "boundary_warning"
    PARTIAL_PERSISTENCE_BLOCKED = "partial_persistence_blocked"


class ApiOriginMetadata(BaseModel):
    """Audit metadata required for API-originated access.

    This records who or what initiated the request.  It is provenance metadata,
    not identity proof or an authorization grant.
    """

    source_tool: str = Field(min_length=1)
    actor_id: str = Field(min_length=1)
    actor_kind: ApiActorKind
    source_session: str | None = None
    capability_id: str | None = None
    request_id: str | None = None


class ApiWarning(BaseModel):
    code: str
    severity: str = "warning"
    message: str
    next_action: str = ""


class ApiError(BaseModel):
    code: ApiErrorCode
    message: str
    field: str | None = None
    retryable: bool = False


class ApiWriteRequest(BaseModel):
    """Shared write contract for local API writes.

    Write endpoints require an idempotency key and origin metadata at contract
    level.  A later service adapter decides whether a dry-run or commit is
    allowed for the caller.
    """

    schema_version: Literal["chronicle-api/v0.1-draft"] = API_SCHEMA_VERSION
    idempotency_key: str = Field(min_length=8)
    origin: ApiOriginMetadata
    dry_run: bool = True
    review_status: ReviewStatus = ReviewStatus.NEEDS_REVIEW
    audit_reason: str = ""


class EventWriteRequest(ApiWriteRequest):
    event_type: EventType
    actor: Actor
    summary: str = Field(min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)
    parent_event_id: str | None = None
    artifact_id: str | None = None
    context_ids: list[str] = Field(default_factory=list)
    decision_id: str | None = None
    rde_record_id: str | None = None
    source: SourceProvenance | None = None
    classification: ClassificationMetadata | None = None
    confidence: Confidence = Confidence.UNKNOWN
    tags: list[str] = Field(default_factory=list)


class DiffWriteRequest(ApiWriteRequest):
    artifact_id: str = Field(min_length=1)
    from_version_id: str = Field(min_length=1)
    to_version_id: str = Field(min_length=1)
    created_by: str = Field(min_length=1)
    summary: str = ""
    preserved: list[str] = Field(default_factory=list)
    transformed: list[str] = Field(default_factory=list)
    supplemented: list[str] = Field(default_factory=list)
    unresolved: list[str] = Field(default_factory=list)
    deviation_risks: list[str] = Field(default_factory=list)
    next_update_policy: list[str] = Field(default_factory=list)


class AssertionWriteRequest(ApiWriteRequest):
    assertion_kind: AssertionKind
    statement: str = Field(min_length=1)
    verification_status: AssertionVerificationStatus = AssertionVerificationStatus.UNVERIFIED
    subject_ref: str | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)
    context_ids: list[str] = Field(default_factory=list)
    artifact_id: str | None = None
    source: SourceProvenance | None = None
    confidence: Confidence = Confidence.UNKNOWN


class ContextQueryRequest(BaseModel):
    schema_version: Literal["chronicle-api/v0.1-draft"] = API_SCHEMA_VERSION
    subject_ref: str | None = None
    matter_ref: str | None = None
    stakeholder_ref: str | None = None
    artifact_id: str | None = None
    decision_id: str | None = None
    context_ids: list[str] = Field(default_factory=list)
    operation: AllowedOperation = AllowedOperation.VIEW
    boundary_preview: bool = True
    include_payload: bool = False
    limit: int = Field(default=50, ge=1, le=200)

    @model_validator(mode="after")
    def _requires_selector(self) -> "ContextQueryRequest":
        selectors = [
            self.subject_ref,
            self.matter_ref,
            self.stakeholder_ref,
            self.artifact_id,
            self.decision_id,
            *self.context_ids,
        ]
        if not any(selectors):
            raise ValueError("at least one context selector is required")
        return self


class TimelineQueryRequest(BaseModel):
    schema_version: Literal["chronicle-api/v0.1-draft"] = API_SCHEMA_VERSION
    subject_ref: str | None = None
    context_ids: list[str] = Field(default_factory=list)
    artifact_id: str | None = None
    decision_id: str | None = None
    from_timestamp: str | None = None
    to_timestamp: str | None = None
    boundary_preview: bool = True
    include_payload: bool = False
    limit: int = Field(default=100, ge=1, le=500)

    @model_validator(mode="after")
    def _requires_selector(self) -> "TimelineQueryRequest":
        selectors = [self.subject_ref, self.artifact_id, self.decision_id, *self.context_ids]
        if not any(selectors):
            raise ValueError("at least one timeline selector is required")
        return self


class BoundariesQueryRequest(BaseModel):
    schema_version: Literal["chronicle-api/v0.1-draft"] = API_SCHEMA_VERSION
    company_ref: str | None = None
    matter_ref: str | None = None
    context_ids: list[str] = Field(default_factory=list)
    operation: AllowedOperation = AllowedOperation.INJECT
    target_use: str = Field(default="context_access", min_length=1)
    include_rules: bool = True


class ApiWriteResponse(BaseModel):
    schema_version: Literal["chronicle-api/v0.1-draft"] = API_SCHEMA_VERSION
    accepted: bool
    dry_run: bool = True
    duplicate: bool = False
    idempotency_key: str | None = None
    event_id: str | None = None
    rde_record_id: str | None = None
    assertion_id: str | None = None
    warnings: list[ApiWarning] = Field(default_factory=list)
    errors: list[ApiError] = Field(default_factory=list)


class ApiReadResponse(BaseModel):
    schema_version: Literal["chronicle-api/v0.1-draft"] = API_SCHEMA_VERSION
    boundary_preview: bool = True
    records: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[ApiWarning] = Field(default_factory=list)
    errors: list[ApiError] = Field(default_factory=list)


class EndpointContract(BaseModel):
    endpoint: ApiEndpoint
    request_model: str
    response_model: str
    write: bool = False
    idempotency_required: bool = False
    opens_network_socket: bool = False
    semantics: str


def list_endpoint_contracts() -> list[EndpointContract]:
    """Return the planned minimum API surface in roadmap order."""

    return [
        EndpointContract(
            endpoint=ApiEndpoint.POST_EVENTS,
            request_model="EventWriteRequest",
            response_model="ApiWriteResponse",
            write=True,
            idempotency_required=True,
            semantics="structured Chronicle event write through Core validation",
        ),
        EndpointContract(
            endpoint=ApiEndpoint.GET_CONTEXT,
            request_model="ContextQueryRequest",
            response_model="ApiReadResponse",
            semantics="boundary-aware context read model, not unrestricted memory export",
        ),
        EndpointContract(
            endpoint=ApiEndpoint.POST_DIFFS,
            request_model="DiffWriteRequest",
            response_model="ApiWriteResponse",
            write=True,
            idempotency_required=True,
            semantics="RDE diff registration mapped to artifact/version lineage",
        ),
        EndpointContract(
            endpoint=ApiEndpoint.GET_TIMELINE,
            request_model="TimelineQueryRequest",
            response_model="ApiReadResponse",
            semantics="time-ordered derived view over JSONL-backed records",
        ),
        EndpointContract(
            endpoint=ApiEndpoint.POST_ASSERTIONS,
            request_model="AssertionWriteRequest",
            response_model="ApiWriteResponse",
            write=True,
            idempotency_required=True,
            semantics="claims, evidence, caveats, unknowns, and verification status",
        ),
        EndpointContract(
            endpoint=ApiEndpoint.GET_BOUNDARIES,
            request_model="BoundariesQueryRequest",
            response_model="ApiReadResponse",
            semantics="advisory boundary rules, not access-control proof",
        ),
    ]
