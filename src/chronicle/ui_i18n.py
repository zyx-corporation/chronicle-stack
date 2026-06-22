"""UI i18n constants for the local Chronicle foreground UI."""

from __future__ import annotations

SUPPORTED_UI_LOCALES: tuple[str, str, str] = ("ja", "en", "zh-CN")
DEFAULT_UI_LOCALE = "ja"
FALLBACK_UI_LOCALE = "en"


def normalize_ui_locale(locale: str | None) -> str:
    value = str(locale or "").strip()
    if value in SUPPORTED_UI_LOCALES:
        return value
    if value.startswith("ja"):
        return "ja"
    if value.startswith("zh"):
        return "zh-CN"
    return FALLBACK_UI_LOCALE

REVIEW_WARNING_TEXT: dict[str, str] = {
    "ui_auth_not_enabled": "UI auth mode is not enabled, so reviewer identity is not enforced by the local UI boundary.",
    "ui_authorization_not_enabled": "UI authorization mode is not enabled, so reviewer permissions remain advisory only.",
    "no_reviewer_identity_recorded": "No reviewer identity metadata is available for this pending target yet.",
    "reviewer_identity_declared_only": "Reviewer identity is self-declared and has not been strengthened by a local auth boundary.",
    "reviewer_session_label_missing": "Session-gated review expects a local session label, but none was recorded.",
}

REVIEW_WARNING_LABELS: dict[str, str] = {
    "ui_auth_not_enabled": "Auth not enabled",
    "ui_authorization_not_enabled": "Authorization advisory",
    "no_reviewer_identity_recorded": "Reviewer missing",
    "reviewer_identity_declared_only": "Declared identity only",
    "reviewer_session_label_missing": "Session label required",
}

REVIEW_WARNING_PRIORITY: dict[str, int] = {
    "ui_auth_not_enabled": 0,
    "ui_authorization_not_enabled": 1,
    "reviewer_session_label_missing": 2,
    "reviewer_identity_declared_only": 3,
    "no_reviewer_identity_recorded": 4,
}

AUTH_BOUNDARY_BLOCKER_TEXT: dict[str, str] = {
    "auth_not_enabled": "Define explicit local auth boundary.",
    "authorization_not_enabled": "Define authorization semantics for reviewer actions.",
    "reviewer_identity_missing": "Record reviewer identity metadata before relying on GUI review signals.",
    "reviewer_identity_declared_only": "Strengthen reviewer identity beyond self-declared metadata.",
    "reviewer_session_label_missing": "Require session labels when session-gated review is expected.",
    "shared_machine_session_unhardened": "Clarify shared-machine expectations for session-gated review.",
}

AUTH_BOUNDARY_WARNING_TO_BLOCKER: dict[str, str] = {
    "ui_auth_not_enabled": "auth_not_enabled",
    "ui_authorization_not_enabled": "authorization_not_enabled",
    "no_reviewer_identity_recorded": "reviewer_identity_missing",
    "reviewer_identity_declared_only": "reviewer_identity_declared_only",
    "reviewer_session_label_missing": "reviewer_session_label_missing",
}

MUTATION_BLOCKER_TEXT: dict[str, str] = {
    "write_routes_disabled": "Keep write routes disabled until all explicit local mutation prerequisites are satisfied.",
    "auth_not_enabled": "Define explicit local auth boundary.",
    "authorization_not_enabled": "Define authorization semantics for reviewer actions.",
    "mutation_capability_flag_disabled": "Require the explicit mutation capability flag before any GUI write path can activate.",
    "ui_mutation_enable_flag_disabled": "Require the explicit UI mutation enable flag for each local write-capable session.",
    "reviewer_identity_missing": "Record reviewer identity metadata before using the local GUI write path.",
    "reviewer_identity_declared_only": "Strengthen reviewer identity beyond self-declared metadata before relying on GUI mutation.",
    "reviewer_session_label_missing": "Require a local session label before session-gated GUI mutation is treated as eligible.",
}

__all__ = [
    "AUTH_BOUNDARY_BLOCKER_TEXT",
    "AUTH_BOUNDARY_WARNING_TO_BLOCKER",
    "MUTATION_BLOCKER_TEXT",
    "normalize_ui_locale",
    "DEFAULT_UI_LOCALE",
    "FALLBACK_UI_LOCALE",
    "REVIEW_WARNING_LABELS",
    "REVIEW_WARNING_PRIORITY",
    "REVIEW_WARNING_TEXT",
    "SUPPORTED_UI_LOCALES",
]
