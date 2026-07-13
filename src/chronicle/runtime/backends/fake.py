"""Deterministic backend for orchestrator tests."""

from __future__ import annotations

from chronicle.models.runtime import RuntimeConfig, RuntimeProviderKind
from chronicle.runtime.contracts import RuntimeBackendRequest, RuntimeBackendResponse


class FakeRuntimeBackend:
    """Return a fixed response without network or Chronicle writes."""

    def __init__(
        self,
        *,
        provider_kind: RuntimeProviderKind = RuntimeProviderKind.LOCAL,
        provider_name: str = "fake-runtime",
        model_name: str = "fake-model",
        invocation_mode: str = "fake-manual",
        external_call_made: bool = False,
        output_text: str = "Fake runtime output.",
        response_metadata: dict[str, str | int | float | bool] | None = None,
        response_keys: list[str] | None = None,
    ) -> None:
        self.provider_kind = provider_kind
        self.provider_name = provider_name
        self.model_name = model_name
        self.invocation_mode = invocation_mode
        self.external_call_made = external_call_made
        self.output_text = output_text
        self.response_metadata = response_metadata or {}
        self.response_keys = response_keys or []

    def execute(
        self,
        *,
        config: RuntimeConfig,
        request: RuntimeBackendRequest,
    ) -> RuntimeBackendResponse:
        del config, request
        return RuntimeBackendResponse(
            provider_kind=self.provider_kind,
            provider_name=self.provider_name,
            model_name=self.model_name,
            invocation_mode=self.invocation_mode,
            external_call_made=self.external_call_made,
            output_text=self.output_text,
            response_metadata=dict(self.response_metadata),
            response_keys=list(self.response_keys),
        )
