"""AI runtime boundary models.

These models describe Chronicle Stack's local AI runtime configuration and
status surface. They do not invoke LLMs, embedding providers, vector DBs,
graph DBs, GraphRAG runtimes, or external services.
"""

from enum import StrEnum

from pydantic import BaseModel, Field


class RuntimeProviderKind(StrEnum):
    """Configured provider class for AI runtime features."""

    DISABLED = "disabled"
    LOCAL = "local"
    HTTP = "http"


class RuntimeCapability(StrEnum):
    """Runtime capability slots.

    Capability presence is advisory configuration metadata. It is not proof
    that a provider is healthy or that the operation is safe to execute.
    """

    LLM = "llm"
    EMBEDDING = "embedding"
    VECTOR = "vector"
    GRAPH = "graph"
    SUMMARIZATION = "summarization"


class RuntimeStatusKind(StrEnum):
    """Status for the configured runtime surface."""

    DISABLED = "disabled"
    CONFIGURED = "configured"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


class RuntimeBoundary(BaseModel):
    """Safety boundary flags for AI runtime features."""

    explicit_invocation_required: bool = True
    network_calls_default: bool = False
    model_calls_default: bool = False
    vector_db_default: bool = False
    graph_db_default: bool = False
    generated_output_requires_review: bool = True
    indexes_are_derived: bool = True


class RuntimeConfig(BaseModel):
    """Local AI runtime configuration.

    The default configuration is intentionally disabled and does not contain
    enough information to call any runtime provider.
    """

    provider_kind: RuntimeProviderKind = RuntimeProviderKind.DISABLED
    provider_name: str = "disabled"
    endpoint: str = ""
    capabilities: list[RuntimeCapability] = Field(default_factory=list)
    allow_network: bool = False
    allow_external_context: bool = False
    review_required: bool = True
    notes: str = "Runtime disabled by default. Configure explicitly before invocation."


class RuntimeStatusReport(BaseModel):
    """Runtime status report returned by CLI/UI surfaces."""

    status: RuntimeStatusKind
    config: RuntimeConfig = Field(default_factory=RuntimeConfig)
    boundary: RuntimeBoundary = Field(default_factory=RuntimeBoundary)
    warnings: list[str] = Field(default_factory=list)


def disabled_runtime_status() -> RuntimeStatusReport:
    """Return the default disabled runtime status.

    This helper is deliberately pure and does not inspect external providers,
    open sockets, call models, build indexes, or touch the network.
    """

    return RuntimeStatusReport(
        status=RuntimeStatusKind.DISABLED,
        warnings=[
            "AI runtime providers are disabled by default.",
            "No LLM, embedding, vector DB, graph DB, or GraphRAG runtime is invoked.",
            "Generated output must be treated as draft until reviewed.",
            "Indexes are derived surfaces, not primary Chronicle records.",
        ],
    )
