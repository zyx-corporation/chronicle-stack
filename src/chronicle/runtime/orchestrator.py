"""Provider-agnostic runtime orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from chronicle.errors import (
    RuntimeProviderExecutionNotEnabledError,
    RuntimeProviderExternalContextNotAllowedError,
)
from chronicle.models.runtime import RuntimeConfig, RuntimeProviderKind
from chronicle.runtime.backends.disabled import DisabledRuntimeBackend
from chronicle.runtime.backends.http import HttpRuntimeBackend
from chronicle.runtime.backends.local import LocalRuntimeBackend
from chronicle.runtime.contracts import RuntimeBackend, RuntimeBackendRequest, RuntimeBackendResponse


class RuntimeBackendFactory(Protocol):
    """Resolve a backend for the requested runtime role."""

    def get_backend(self, *, role: str, config: RuntimeConfig) -> RuntimeBackend: ...


@dataclass
class DefaultRuntimeBackendFactory:
    """Default backend resolution for the current runtime contract."""

    def get_backend(self, *, role: str, config: RuntimeConfig) -> RuntimeBackend:
        if role == "summarize":
            if config.provider_kind == RuntimeProviderKind.HTTP:
                return HttpRuntimeBackend()
            return LocalRuntimeBackend()
        if role == "invoke":
            if config.provider_kind == RuntimeProviderKind.DISABLED:
                return DisabledRuntimeBackend()
            return HttpRuntimeBackend()
        raise ValueError(f"Unknown runtime backend role: {role}")


class RuntimeOrchestrator:
    """Coordinate runtime execution without embedding provider-specific logic."""

    def __init__(self, backend_factory: RuntimeBackendFactory | None = None) -> None:
        self.backend_factory = backend_factory or DefaultRuntimeBackendFactory()

    def summarize(
        self,
        *,
        config: RuntimeConfig,
        text: str,
        max_sentences: int,
        execute_configured_provider: bool,
    ) -> RuntimeBackendResponse:
        if config.provider_kind == RuntimeProviderKind.HTTP and not execute_configured_provider:
            raise RuntimeProviderExecutionNotEnabledError()
        request = RuntimeBackendRequest(
            text=text,
            operation="summarize",
            max_sentences=max_sentences,
        )
        return self._execute(role="summarize", config=config, request=request)

    def invoke(
        self,
        *,
        config: RuntimeConfig,
        text: str,
        operation: str,
        execute_configured_provider: bool,
        source_refs: list,
        prompt: str,
        extra_params: dict[str, str],
    ) -> RuntimeBackendResponse:
        if not execute_configured_provider:
            raise RuntimeProviderExecutionNotEnabledError()
        if source_refs and not config.allow_external_context:
            raise RuntimeProviderExternalContextNotAllowedError()
        request = RuntimeBackendRequest(
            text=text,
            operation=operation,
            source_refs=list(source_refs),
            prompt=prompt,
            extra_params=dict(extra_params),
        )
        return self._execute(role="invoke", config=config, request=request)

    def _execute(
        self,
        *,
        role: str,
        config: RuntimeConfig,
        request: RuntimeBackendRequest,
    ) -> RuntimeBackendResponse:
        backend = self.backend_factory.get_backend(role=role, config=config)
        return backend.execute(config=config, request=request)
