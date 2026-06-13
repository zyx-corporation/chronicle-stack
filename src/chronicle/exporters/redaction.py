"""Opt-in redaction helpers for derived exports."""

from dataclasses import dataclass
from typing import Any

from chronicle.models.visibility import VisibilityHint

REDACTED = "[REDACTED:sensitive]"


@dataclass(frozen=True)
class RedactionOptions:
    """Explicit export redaction options.

    These options are disclosure controls for derived exports, not access control.
    """

    redact_sensitive: bool = False
    exclude_sensitive: bool = False

    def as_manifest_options(self) -> dict[str, bool]:
        return {
            "redact_sensitive": self.redact_sensitive,
            "exclude_sensitive": self.exclude_sensitive,
        }

    @property
    def enabled(self) -> bool:
        return self.redact_sensitive or self.exclude_sensitive


def is_sensitive_value(value: Any) -> bool:
    if isinstance(value, VisibilityHint):
        return value == VisibilityHint.SENSITIVE
    return str(value) == VisibilityHint.SENSITIVE.value


def model_is_sensitive(model: Any) -> bool:
    visibility = getattr(model, "visibility_hint", None)
    return is_sensitive_value(visibility) if visibility is not None else False


def dict_is_sensitive(data: dict[str, Any]) -> bool:
    visibility = data.get("visibility_hint") or data.get("visibility")
    return is_sensitive_value(visibility) if visibility is not None else False


def redact_sensitive_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Return a redacted copy of a sensitive model dump."""
    redacted = dict(data)
    for key in (
        "title",
        "summary",
        "source",
        "source_ref",
        "source_type",
        "path",
        "tags",
    ):
        if key in redacted:
            redacted[key] = REDACTED
    return redacted


def transform_model_dump(model: Any, options: RedactionOptions) -> dict[str, Any] | None:
    data = model.model_dump(mode="json")
    if not model_is_sensitive(model):
        return data
    if options.exclude_sensitive:
        return None
    if options.redact_sensitive:
        return redact_sensitive_dict(data)
    return data


def transform_event_dump(event: Any, options: RedactionOptions) -> dict[str, Any] | None:
    data = event.model_dump(mode="json")
    payload = data.get("payload")
    if not isinstance(payload, dict):
        return data

    sensitive_payload = False
    for key in ("context", "artifact"):
        value = payload.get(key)
        if isinstance(value, dict) and dict_is_sensitive(value):
            sensitive_payload = True
            if options.redact_sensitive:
                payload[key] = redact_sensitive_dict(value)

    if sensitive_payload and options.exclude_sensitive:
        return None
    data["payload"] = payload
    return data
