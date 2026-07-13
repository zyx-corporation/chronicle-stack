"""Local placeholder runtime backend."""

from __future__ import annotations

import re

from chronicle.models.runtime import RuntimeConfig, RuntimeProviderKind
from chronicle.runtime.contracts import RuntimeBackendRequest, RuntimeBackendResponse


class LocalRuntimeBackend:
    """Provider-free local placeholder execution."""

    def execute(
        self,
        *,
        config: RuntimeConfig,
        request: RuntimeBackendRequest,
    ) -> RuntimeBackendResponse:
        del config
        return RuntimeBackendResponse(
            provider_kind=RuntimeProviderKind.LOCAL,
            provider_name="local-placeholder",
            model_name="local-placeholder",
            invocation_mode="explicit-manual",
            external_call_made=False,
            output_text=summarize_text(request.text, max_sentences=request.max_sentences or 3),
            response_metadata={},
            response_keys=[],
        )


def summarize_text(text: str, *, max_sentences: int) -> str:
    cleaned = " ".join(part.strip() for part in text.splitlines() if part.strip())
    if not cleaned:
        return ""

    sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?。！？])\s+", cleaned) if sentence.strip()]
    if sentences:
        return " ".join(sentences[:max_sentences])

    words = cleaned.split()
    if len(words) <= 30:
        return cleaned
    return " ".join(words[:30]) + "..."
