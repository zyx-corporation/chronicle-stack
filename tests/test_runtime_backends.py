"""Tests for runtime backend implementations."""

import pytest

from chronicle.errors import RuntimeProviderNotReadyError
from chronicle.models.runtime import RuntimeConfig, RuntimeProviderKind, default_local_runtime_config
from chronicle.runtime.backends.disabled import DisabledRuntimeBackend
from chronicle.runtime.backends.fake import FakeRuntimeBackend
from chronicle.runtime.backends.local import LocalRuntimeBackend
from chronicle.runtime.contracts import RuntimeBackendRequest


def test_local_runtime_backend_summarizes_without_network() -> None:
    backend = LocalRuntimeBackend()

    response = backend.execute(
        config=default_local_runtime_config(),
        request=RuntimeBackendRequest(
            text="First sentence. Second sentence. Third sentence.",
            operation="summarize",
            max_sentences=2,
        ),
    )

    assert response.provider_kind == RuntimeProviderKind.LOCAL
    assert response.external_call_made is False
    assert response.output_text == "First sentence. Second sentence."


def test_disabled_runtime_backend_fails_closed() -> None:
    backend = DisabledRuntimeBackend()

    with pytest.raises(RuntimeProviderNotReadyError) as exc:
        backend.execute(
            config=RuntimeConfig(provider_kind=RuntimeProviderKind.DISABLED),
            request=RuntimeBackendRequest(text="Blocked.", operation="rewrite"),
        )

    assert "runtime_provider_disabled" in str(exc.value)


def test_fake_runtime_backend_returns_fixed_response() -> None:
    backend = FakeRuntimeBackend(
        provider_kind=RuntimeProviderKind.HTTP,
        provider_name="fake-http",
        model_name="fake-model",
        invocation_mode="fake-http-manual",
        external_call_made=True,
        output_text="Fake provider output.",
        response_metadata={"response_id": "fake-1"},
        response_keys=["output_text", "response_id"],
    )

    response = backend.execute(
        config=RuntimeConfig(provider_kind=RuntimeProviderKind.HTTP),
        request=RuntimeBackendRequest(text="Rewrite this.", operation="rewrite"),
    )

    assert response.provider_kind == RuntimeProviderKind.HTTP
    assert response.provider_name == "fake-http"
    assert response.model_name == "fake-model"
    assert response.invocation_mode == "fake-http-manual"
    assert response.external_call_made is True
    assert response.output_text == "Fake provider output."
    assert response.response_metadata["response_id"] == "fake-1"
