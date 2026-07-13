"""Shared runtime backend contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from chronicle.models.runtime import RuntimeConfig, RuntimeProviderKind
from chronicle.models.summary_job import SummarySourceRef


@dataclass(frozen=True)
class RuntimeBackendRequest:
    """Provider-agnostic request passed from the orchestrator to a backend."""

    text: str
    operation: str
    max_sentences: int | None = None
    source_refs: list[SummarySourceRef] = field(default_factory=list)
    prompt: str = ""
    extra_params: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class RuntimeBackendResponse:
    """Normalized backend response returned to the orchestrator."""

    provider_kind: RuntimeProviderKind
    provider_name: str
    model_name: str
    invocation_mode: str
    external_call_made: bool
    output_text: str
    response_metadata: dict[str, str | int | float | bool] = field(default_factory=dict)
    response_keys: list[str] = field(default_factory=list)


class RuntimeBackend(Protocol):
    """Backend contract for provider-specific execution."""

    def execute(
        self,
        *,
        config: RuntimeConfig,
        request: RuntimeBackendRequest,
    ) -> RuntimeBackendResponse: ...
