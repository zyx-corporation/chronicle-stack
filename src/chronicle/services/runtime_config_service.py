"""Runtime provider configuration surface without implicit execution."""

from datetime import datetime, timezone
from pathlib import Path

import yaml

from chronicle.models.runtime import (
    RuntimeBoundary,
    RuntimeCapability,
    RuntimeConfig,
    RuntimeConfigState,
    RuntimeProviderKind,
    default_local_runtime_config,
)
from chronicle.services.chronicle_service import ChronicleService


class RuntimeConfigService:
    """Persist explicit runtime provider configuration without invoking it."""

    def __init__(self, root: Path | None = None) -> None:
        self.chronicle = ChronicleService(root)
        self.paths = self.chronicle.paths

    def show(self) -> RuntimeConfigState:
        path = self.paths.runtime_config_file
        if not path.exists():
            return RuntimeConfigState(
                source="implicit-default",
                config=default_local_runtime_config(),
                boundary=RuntimeBoundary(),
                warnings=[
                    "No stored runtime provider configuration found.",
                    "Default local placeholder config remains explicit/manual only.",
                    "Configuration alone does not invoke any model or external runtime.",
                ],
            )

        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        state = RuntimeConfigState.model_validate(raw)
        state.warnings = self._warnings_for(state.config)
        return state

    def set_local(
        self,
        *,
        model_name: str = "local-placeholder",
        provider_name: str = "local-placeholder",
    ) -> RuntimeConfigState:
        self.chronicle.require_initialized()
        state = RuntimeConfigState(
            source="stored",
            configured_at=datetime.now(timezone.utc).astimezone(),
            config=RuntimeConfig(
                provider_kind=RuntimeProviderKind.LOCAL,
                provider_name=provider_name,
                model_name=model_name,
                capabilities=[
                    RuntimeCapability.LLM,
                    RuntimeCapability.SUMMARIZATION,
                ],
                allow_network=False,
                allow_external_context=False,
                review_required=True,
            ),
            boundary=RuntimeBoundary(),
        )
        state.warnings = self._warnings_for(state.config)
        self._write(state)
        return state

    def set_http(
        self,
        *,
        base_url: str,
        model_name: str,
        api_key_env: str,
        provider_name: str = "http-manual",
        allow_network: bool = False,
        allow_external_context: bool = False,
    ) -> RuntimeConfigState:
        self.chronicle.require_initialized()
        state = RuntimeConfigState(
            source="stored",
            configured_at=datetime.now(timezone.utc).astimezone(),
            config=RuntimeConfig(
                provider_kind=RuntimeProviderKind.HTTP,
                provider_name=provider_name,
                model_name=model_name,
                base_url=base_url,
                api_key_env=api_key_env,
                capabilities=[
                    RuntimeCapability.LLM,
                    RuntimeCapability.SUMMARIZATION,
                ],
                allow_network=allow_network,
                allow_external_context=allow_external_context,
                review_required=True,
            ),
            boundary=RuntimeBoundary(),
        )
        state.warnings = self._warnings_for(state.config)
        self._write(state)
        return state

    def disable(self) -> RuntimeConfigState:
        self.chronicle.require_initialized()
        state = RuntimeConfigState(
            source="stored",
            configured_at=datetime.now(timezone.utc).astimezone(),
            config=RuntimeConfig(),
            boundary=RuntimeBoundary(),
        )
        state.warnings = self._warnings_for(state.config)
        self._write(state)
        return state

    def _write(self, state: RuntimeConfigState) -> None:
        self.paths.runtime_config_file.write_text(
            yaml.dump(
                state.model_dump(mode="json"),
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
            ),
            encoding="utf-8",
        )

    def _warnings_for(self, config: RuntimeConfig) -> list[str]:
        warnings = [
            "Configuration alone does not invoke any model or external runtime.",
            "Explicit manual invocation remains required before generated output exists.",
            "Primary Chronicle records remain authoritative.",
        ]
        if config.provider_kind == RuntimeProviderKind.HTTP:
            warnings.append("HTTP provider config is a stored contract only, not an active network session.")
            if not config.allow_network:
                warnings.append("allow_network is false, so downstream HTTP invocation should remain blocked.")
        if config.provider_kind == RuntimeProviderKind.DISABLED:
            warnings.append("Runtime provider is disabled until reconfigured.")
        return warnings
