"""Local runtime boundary and explicit invocation models."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class RuntimeProviderKind(StrEnum):
    DISABLED = "disabled"
    LOCAL = "local"
    HTTP = "http"


class RuntimeCapability(StrEnum):
    LLM = "llm"
    EMBEDDING = "embedding"
    VECTOR = "vector"
    GRAPH = "graph"
    SUMMARIZATION = "summarization"


class RuntimeConfig(BaseModel):
    provider_kind: RuntimeProviderKind = RuntimeProviderKind.DISABLED
    provider_name: str = "disabled"
    model_name: str = "disabled"
    base_url: str | None = None
    api_key_env: str | None = None
    capabilities: list[RuntimeCapability] = Field(default_factory=list)
    allow_network: bool = False
    allow_external_context: bool = False
    review_required: bool = True


class RuntimeBoundary(BaseModel):
    explicit_invocation_required: bool = True
    network_calls_default: bool = False
    model_calls_default: bool = False
    vector_db_default: bool = False
    graph_db_default: bool = False
    generated_output_requires_review: bool = True
    indexes_are_derived: bool = True


class DisabledRuntimeStatus(BaseModel):
    status: str = "disabled"
    config: RuntimeConfig = Field(default_factory=RuntimeConfig)
    boundary: RuntimeBoundary = Field(default_factory=RuntimeBoundary)
    warnings: list[str] = Field(
        default_factory=lambda: [
            "AI runtime is disabled by default.",
            "No model, embedding, vector, or graph provider is invoked automatically.",
        ]
    )


class RuntimeStatus(BaseModel):
    provider_kind: RuntimeProviderKind = RuntimeProviderKind.LOCAL
    default_enabled: bool = False
    model_name: str = "local-placeholder"
    configured_provider_kind: RuntimeProviderKind = RuntimeProviderKind.LOCAL
    configured_model_name: str = "local-placeholder"
    capabilities: list[RuntimeCapability] = Field(
        default_factory=lambda: [
            RuntimeCapability.LLM,
            RuntimeCapability.EMBEDDING,
            RuntimeCapability.VECTOR,
            RuntimeCapability.GRAPH,
            RuntimeCapability.SUMMARIZATION,
        ]
    )
    external_call_made: bool = False
    requires_explicit_invocation: bool = True
    generated_output_requires_review: bool = True
    primary_record_authoritative: bool = True


class RuntimeConfigState(BaseModel):
    source: str = "implicit-default"
    configured_at: datetime | None = None
    config: RuntimeConfig = Field(default_factory=RuntimeConfig)
    boundary: RuntimeBoundary = Field(default_factory=RuntimeBoundary)
    warnings: list[str] = Field(default_factory=list)


class RuntimeSummaryResult(BaseModel):
    provider_kind: RuntimeProviderKind = RuntimeProviderKind.LOCAL
    provider_name: str = "local-placeholder"
    model_name: str = "local-placeholder"
    invocation_mode: str = "explicit-manual"
    external_call_made: bool = False
    requires_review: bool = True
    source_text_length: int
    generated_text: str
    response_metadata: dict[str, str | int | float | bool] = Field(default_factory=dict)
    response_keys: list[str] = Field(default_factory=list)
    recorded: bool = False
    event_id: str | None = None
    draft_summary_job_id: str | None = None
    draft_artifact_id: str | None = None
    draft_version_id: str | None = None


class RuntimeExecutionResult(BaseModel):
    provider_kind: RuntimeProviderKind
    provider_name: str
    model_name: str
    operation: str
    invocation_mode: str = "explicit-http-manual"
    external_call_made: bool = False
    requires_review: bool = True
    source_text_length: int
    output_text: str
    source_refs: list[dict[str, str]] = Field(default_factory=list)
    prompt: str = ""
    params: dict[str, str] = Field(default_factory=dict)
    response_metadata: dict[str, str | int | float | bool] = Field(default_factory=dict)
    response_keys: list[str] = Field(default_factory=list)
    recorded: bool = False
    event_id: str | None = None
    draft_summary_job_id: str | None = None
    artifact_id: str | None = None
    version_id: str | None = None


class RuntimeRetrievalHit(BaseModel):
    source: str
    identifier: str
    summary: str
    detail: str = ""
    score: float | None = None


class RuntimeRetrievalPlan(BaseModel):
    provider_kind: RuntimeProviderKind = RuntimeProviderKind.LOCAL
    invocation_mode: str = "explicit-manual-dry-run"
    external_call_made: bool = False
    query: str
    vector_hits: list[RuntimeRetrievalHit] = Field(default_factory=list)
    graph_hits: list[RuntimeRetrievalHit] = Field(default_factory=list)
    chronicle_hits: list[RuntimeRetrievalHit] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    primary_record_authoritative: bool = True
    requires_review: bool = True
    recorded: bool = False
    event_id: str | None = None


class RuntimeInvocationPlan(BaseModel):
    provider_kind: RuntimeProviderKind
    provider_name: str
    model_name: str
    operation: str = "summarize"
    invocation_mode: str = "explicit-manual-plan"
    external_call_made: bool = False
    source_text_length: int = 0
    would_use_network: bool = False
    network_allowed_by_contract: bool = False
    invocation_ready: bool = False
    blocking_reasons: list[str] = Field(default_factory=list)
    request_preview: dict[str, str] = Field(default_factory=dict)
    execution_request: dict[str, object] = Field(default_factory=dict)
    downstream_commands: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    recorded: bool = False
    event_id: str | None = None


class RuntimeRecordPreview(BaseModel):
    record_kind: str
    title: str
    preview_text: str = ""
    source_counts: dict[str, int] = Field(default_factory=dict)
    referenced_record_ids: list[str] = Field(default_factory=list)
    suggested_cli_family: str
    boundary_notes: list[str] = Field(default_factory=list)


class RuntimeRetrievalHandoff(BaseModel):
    query: str
    vector_hit_count: int = 0
    graph_hit_count: int = 0
    chronicle_hit_count: int = 0
    referenced_record_ids: list[str] = Field(default_factory=list)
    downstream_commands: list[str] = Field(default_factory=list)
    package_review_required: bool = True
    primary_record_authoritative: bool = True
    notes: list[str] = Field(default_factory=list)


def disabled_runtime_status() -> DisabledRuntimeStatus:
    return DisabledRuntimeStatus()


def default_local_runtime_config() -> RuntimeConfig:
    return RuntimeConfig(
        provider_kind=RuntimeProviderKind.LOCAL,
        provider_name="local-placeholder",
        model_name="local-placeholder",
        capabilities=[
            RuntimeCapability.LLM,
            RuntimeCapability.SUMMARIZATION,
        ],
        allow_network=False,
        allow_external_context=False,
        review_required=True,
    )
