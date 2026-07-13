"""Tests for provider-agnostic runtime orchestration."""

from dataclasses import dataclass, field

import pytest

from chronicle.errors import (
    RuntimeProviderExecutionNotEnabledError,
    RuntimeProviderExternalContextNotAllowedError,
    RuntimeProviderNotReadyError,
)
from chronicle.models.runtime import RuntimeConfig, RuntimeProviderKind, default_local_runtime_config
from chronicle.models.summary_job import SummarySourceRef
from chronicle.runtime.backends.fake import FakeRuntimeBackend
from chronicle.runtime.orchestrator import RuntimeOrchestrator


@dataclass
class _FactoryRecorder:
    backend: object
    calls: list[tuple[str, RuntimeProviderKind]] = field(default_factory=list)

    def get_backend(self, *, role: str, config: RuntimeConfig):  # noqa: ANN001
        self.calls.append((role, config.provider_kind))
        return self.backend


def test_runtime_orchestrator_uses_injected_backend_for_summarize() -> None:
    factory = _FactoryRecorder(
        backend=FakeRuntimeBackend(
            output_text="Fake summary output.",
            invocation_mode="fake-summary",
        )
    )
    orchestrator = RuntimeOrchestrator(factory)

    response = orchestrator.summarize(
        config=default_local_runtime_config(),
        text="Summarize this explicitly.",
        max_sentences=3,
        execute_configured_provider=False,
    )

    assert factory.calls == [("summarize", RuntimeProviderKind.LOCAL)]
    assert response.output_text == "Fake summary output."
    assert response.invocation_mode == "fake-summary"


def test_runtime_orchestrator_invoke_requires_explicit_execution_flag() -> None:
    orchestrator = RuntimeOrchestrator(_FactoryRecorder(backend=FakeRuntimeBackend()))

    with pytest.raises(RuntimeProviderExecutionNotEnabledError):
        orchestrator.invoke(
            config=RuntimeConfig(provider_kind=RuntimeProviderKind.HTTP, allow_network=True),
            text="Rewrite this.",
            operation="rewrite",
            execute_configured_provider=False,
            source_refs=[],
            prompt="",
            extra_params={},
        )


def test_runtime_orchestrator_blocks_external_context_without_contract() -> None:
    orchestrator = RuntimeOrchestrator(_FactoryRecorder(backend=FakeRuntimeBackend()))

    with pytest.raises(RuntimeProviderExternalContextNotAllowedError):
        orchestrator.invoke(
            config=RuntimeConfig(provider_kind=RuntimeProviderKind.HTTP, allow_network=True),
            text="Rewrite this with context.",
            operation="rewrite",
            execute_configured_provider=True,
            source_refs=[SummarySourceRef(record_id="evt_1", record_type="event")],
            prompt="",
            extra_params={},
        )


def test_runtime_orchestrator_default_invoke_fails_closed_for_non_http_config() -> None:
    orchestrator = RuntimeOrchestrator()

    with pytest.raises(RuntimeProviderNotReadyError) as exc:
        orchestrator.invoke(
            config=default_local_runtime_config(),
            text="Rewrite this.",
            operation="rewrite",
            execute_configured_provider=True,
            source_refs=[],
            prompt="",
            extra_params={},
        )

    assert "configured_provider_is_not_http" in str(exc.value)
