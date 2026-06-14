"""Opt-in redaction helpers for derived exports."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from chronicle.models.visibility import VisibilityHint

REDACTED = "[REDACTED:sensitive]"


class ExportProfile(StrEnum):
    """Security-aware export profiles.

    Profiles are disclosure controls for derived exports. They are not access
    control and do not mutate the primary Chronicle record.
    """

    PUBLIC_REVIEW = "public-review"
    INTERNAL_REVIEW = "internal-review"
    LOCAL_ANALYSIS = "local-analysis"
    RESTRICTED_SUMMARY = "restricted-summary"


@dataclass(frozen=True)
class RedactionOptions:
    """Explicit export redaction options.

    These options are disclosure controls for derived exports, not access control.
    """

    redact_sensitive: bool = False
    exclude_sensitive: bool = False
    profile: ExportProfile | None = None

    @classmethod
    def from_profile(cls, profile: ExportProfile | None) -> "RedactionOptions":
        if profile is None:
            return cls()
        if profile == ExportProfile.PUBLIC_REVIEW:
            return cls(redact_sensitive=True, profile=profile)
        if profile == ExportProfile.RESTRICTED_SUMMARY:
            return cls(exclude_sensitive=True, profile=profile)
        return cls(profile=profile)

    def as_manifest_options(self) -> dict[str, bool | str | None]:
        return {
            "redact_sensitive": self.redact_sensitive,
            "exclude_sensitive": self.exclude_sensitive,
            "profile": self.profile.value if self.profile else None,
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


def event_has_sensitive_payload(event_dump: dict[str, Any]) -> bool:
    payload = event_dump.get("payload")
    if not isinstance(payload, dict):
        return False
    for key in ("context", "artifact"):
        value = payload.get(key)
        if isinstance(value, dict) and dict_is_sensitive(value):
            return True
    return False


def transform_event_dump(event: Any, options: RedactionOptions) -> dict[str, Any] | None:
    data = event.model_dump(mode="json")
    payload = data.get("payload")
    if not isinstance(payload, dict):
        return data

    sensitive_payload = event_has_sensitive_payload(data)
    if sensitive_payload and options.exclude_sensitive:
        return None

    if sensitive_payload and options.redact_sensitive:
        data["summary"] = REDACTED
        for key in ("context", "artifact"):
            value = payload.get(key)
            if isinstance(value, dict) and dict_is_sensitive(value):
                payload[key] = redact_sensitive_dict(value)

    data["payload"] = payload
    return data
