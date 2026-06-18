"""Local runtime boundary and explicit invocation models."""

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


class RuntimeSummaryResult(BaseModel):
    provider_kind: RuntimeProviderKind = RuntimeProviderKind.LOCAL
    model_name: str = "local-placeholder"
    invocation_mode: str = "explicit-manual"
    external_call_made: bool = False
    requires_review: bool = True
    source_text_length: int
    generated_text: str
    recorded: bool = False
    event_id: str | None = None


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


def disabled_runtime_status() -> DisabledRuntimeStatus:
    return DisabledRuntimeStatus()
