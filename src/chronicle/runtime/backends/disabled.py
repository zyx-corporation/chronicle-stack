"""Fail-closed backend used for explicitly disabled runtime execution."""

from __future__ import annotations

from chronicle.errors import RuntimeProviderNotReadyError
from chronicle.models.runtime import RuntimeConfig
from chronicle.runtime.contracts import RuntimeBackendRequest, RuntimeBackendResponse


class DisabledRuntimeBackend:
    """Reject every execution attempt."""

    def execute(
        self,
        *,
        config: RuntimeConfig,
        request: RuntimeBackendRequest,
    ) -> RuntimeBackendResponse:
        del config, request
        raise RuntimeProviderNotReadyError(["runtime_provider_disabled"])
