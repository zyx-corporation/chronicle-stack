"""Configured HTTP runtime backend."""

from __future__ import annotations

import json
import os
from urllib import error as urllib_error
from urllib import request as urllib_request

from chronicle.errors import (
    RuntimeProviderCredentialMissingError,
    RuntimeProviderNotReadyError,
    RuntimeProviderResponseError,
    RuntimeProviderTransportError,
)
from chronicle.models.runtime import RuntimeConfig, RuntimeProviderKind
from chronicle.runtime.contracts import RuntimeBackendRequest, RuntimeBackendResponse


class HttpRuntimeBackend:
    """Execute an explicit request against a configured HTTP provider."""

    def __init__(self, invoker=None) -> None:  # noqa: ANN001
        self._invoker = invoker or self._invoke_http_operation

    def execute(
        self,
        *,
        config: RuntimeConfig,
        request: RuntimeBackendRequest,
    ) -> RuntimeBackendResponse:
        self._require_ready_config(config)
        invoker_kwargs = {
            "config": config,
            "text": request.text,
            "operation": request.operation,
            "max_sentences": request.max_sentences,
        }
        if request.source_refs:
            invoker_kwargs["source_refs"] = request.source_refs
        if request.prompt:
            invoker_kwargs["prompt"] = request.prompt
        if request.extra_params:
            invoker_kwargs["extra_params"] = request.extra_params
        response_payload = self._invoker(**invoker_kwargs)
        output_text, response_metadata, response_keys = self._extract_http_response_details(response_payload)
        return RuntimeBackendResponse(
            provider_kind=config.provider_kind,
            provider_name=config.provider_name,
            model_name=config.model_name,
            invocation_mode="explicit-http-manual",
            external_call_made=True,
            output_text=output_text,
            response_metadata=response_metadata,
            response_keys=response_keys,
        )

    def _require_ready_config(self, config: RuntimeConfig) -> None:
        blocking_reasons: list[str] = []
        if config.provider_kind != RuntimeProviderKind.HTTP:
            blocking_reasons.append("configured_provider_is_not_http")
        if not config.allow_network:
            blocking_reasons.append("network_not_allowed_by_contract")
        if not config.base_url:
            blocking_reasons.append("base_url_not_configured")
        if not config.model_name or config.model_name == "disabled":
            blocking_reasons.append("model_not_configured")
        if not config.api_key_env:
            blocking_reasons.append("api_key_env_not_configured")
        if blocking_reasons:
            raise RuntimeProviderNotReadyError(blocking_reasons)
        if not os.environ.get(config.api_key_env or ""):
            raise RuntimeProviderCredentialMissingError(config.api_key_env or "")

    @staticmethod
    def _invoke_http_operation(
        *,
        config: RuntimeConfig,
        text: str,
        operation: str,
        max_sentences: int | None,
        source_refs=None,  # noqa: ANN001
        prompt: str = "",
        extra_params=None,  # noqa: ANN001
    ) -> dict[str, object]:
        payload: dict[str, object] = {
            "operation": operation,
            "model": config.model_name,
            "input_text": text,
        }
        if max_sentences is not None:
            payload["max_sentences"] = max_sentences
        if source_refs:
            payload["source_refs"] = [ref.model_dump(mode="json") for ref in source_refs]
        if prompt:
            payload["prompt"] = prompt
        if extra_params:
            payload["params"] = extra_params

        body = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.environ[config.api_key_env or '']}",
        }
        http_request = urllib_request.Request(
            config.base_url or "",
            data=body,
            headers=headers,
            method="POST",
        )
        try:
            with urllib_request.urlopen(http_request, timeout=30) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
        except urllib_error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace").strip() or f"HTTP {exc.code}"
            raise RuntimeProviderTransportError(detail) from exc
        except urllib_error.URLError as exc:
            raise RuntimeProviderTransportError(str(exc.reason)) from exc
        except OSError as exc:
            raise RuntimeProviderTransportError(str(exc)) from exc
        except json.JSONDecodeError as exc:
            raise RuntimeProviderResponseError(f"invalid JSON: {exc}") from exc

        if not isinstance(response_payload, dict):
            raise RuntimeProviderResponseError("response JSON must be an object")
        return response_payload

    @staticmethod
    def _extract_http_response_details(
        payload: dict[str, object] | str,
    ) -> tuple[str, dict[str, str | int | float | bool], list[str]]:
        if isinstance(payload, str):
            return payload, {}, []
        output_text = ""
        for key in ("output_text", "generated_text", "summary"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                output_text = value.strip()
                break
        if not output_text:
            raise RuntimeProviderResponseError("missing textual output field")

        metadata: dict[str, str | int | float | bool] = {}
        for key in ("response_id", "finish_reason", "provider_status"):
            value = payload.get(key)
            if isinstance(value, (str, int, float, bool)):
                metadata[key] = value
        usage = payload.get("usage")
        if isinstance(usage, dict):
            for key, value in usage.items():
                if isinstance(value, (str, int, float, bool)):
                    metadata[f"usage_{key}"] = value
        return output_text, metadata, sorted(payload.keys())
