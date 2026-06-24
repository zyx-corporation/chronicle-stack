"""Tests for Chronicle local UI i18n catalogs and helper invariants."""

from chronicle.ui_i18n import (
    DEFAULT_UI_LOCALE,
    FALLBACK_UI_LOCALE,
    SUPPORTED_UI_LOCALES,
    normalize_ui_locale,
)
from chronicle.ui_server import UI_I18N_CATALOG


def test_ui_i18n_catalog_supports_expected_locales():
    assert SUPPORTED_UI_LOCALES == ("ja", "en", "zh-CN")
    assert DEFAULT_UI_LOCALE == "ja"
    assert FALLBACK_UI_LOCALE == "en"
    assert set(UI_I18N_CATALOG) == set(SUPPORTED_UI_LOCALES)


def test_ui_i18n_catalog_contains_core_shell_and_navigation_keys():
    required_keys = {
        "label.language",
        "locale.ja",
        "locale.en",
        "locale.zh-CN",
        "shell.title",
        "shell.root",
        "shell.warning_title",
        "shell.warning_body",
        "button.copy_cli",
        "button.copy_recovery_cli",
        "button.open_runtime_records",
        "button.open_review_queue",
        "button.open_summary_jobs",
        "status.not_found",
        "label.record_json",
        "label.response_json",
        "section.metrics",
        "section.reviewer_boundary",
        "overview.warning_priority",
        "overview.reviewer_runtime_enforcement_counts",
        "overview.reviewer_runtime_gate_counts",
        "ui.label.status_prefix",
        "ui.label.route_prefix",
        "ui.label.enforcement_status",
        "ui.label.validation_gate_status",
        "ui.label.reviewer",
        "ui.label.detail_heading",
        "ui.label.dataset",
        "ui.label.empty_runtime_records",
        "ui.label.empty_review_rows",
        "ui.label.empty_summary_jobs",
        "ui.dataset.runtime_records",
        "ui.dataset.review_queue",
        "ui.dataset.summary_jobs",
        "ui.template.reviewer_boundary_overview_message",
        "ui.message.reviewer_boundary_drilldown",
        "ui.template.reviewer_boundary_drilldown_message",
        "ui.template.reviewer_boundary_fact_line",
        "ui.template.reviewer_boundary_dominant_fact_line",
        "ui.reviewer_boundary_status.descriptive_only",
        "ui.reviewer_boundary_status.local_route_enforced",
        "ui.reviewer_boundary_status.read_only_preview",
        "ui.reviewer_boundary_status.unknown",
        "badge.reviewer_enforcement",
        "badge.reviewer_gate",
    }
    for locale, catalog in UI_I18N_CATALOG.items():
        missing = required_keys.difference(catalog)
        assert not missing, f"{locale} missing keys: {sorted(missing)}"


def test_ui_i18n_catalog_contains_exact_and_prefix_maps_for_each_locale():
    for locale, catalog in UI_I18N_CATALOG.items():
        if "exact" in catalog:
            assert isinstance(catalog["exact"], dict), locale
        if "prefix" in catalog:
            assert isinstance(catalog["prefix"], dict), locale


def test_ui_i18n_catalog_covers_mutation_readiness_and_related_link_labels():
    required_exact = {
        "Capability flag enabled",
        "Session enable flag enabled",
        "Auth boundary configured",
        "Authorization boundary configured",
        "Reviewer identity recorded",
        "Session labels recorded",
        "All explicit local mutation prerequisites are currently satisfied.",
        "Explicit local mutation prerequisites remain unsatisfied.",
        "Open matching review detail",
        "Open matching runtime record",
    }
    for locale in ("ja", "zh-CN"):
        exact = UI_I18N_CATALOG[locale]["exact"]
        missing = required_exact.difference(exact)
        assert not missing, f"{locale} missing exact keys: {sorted(missing)}"


def test_ui_i18n_catalog_covers_package_preview_and_review_preview_messages():
    required_exact = {
        "No context records were selected by the retrieval dry-run, so package preview is advisory only.",
        "Read-only package preview derived from retrieval-plan context hits.",
        "Target event is not available for package readiness derivation.",
        "No context-linked records are available for package/export preview from this review target.",
        "Read-only package readiness derived from context-linked review target records.",
        "Review target is already resolved in the current derived queue view.",
        "Boundary and reviewer identity conditions are aligned for future mutation-capable review.",
        "Review remains CLI-led and read-only in UI; see warnings for unmet boundary conditions.",
        "Package readiness unavailable.",
        "Use the equivalent chronicle review CLI command for recovery or inspection.",
        "Use the equivalent chronicle review CLI command for follow-up inspection.",
        "UI mutation is enabled for this local session; review actions still require explicit reviewer context.",
        "UI mutation is enabled, but boundary warnings still block review until reviewer context aligns.",
        "UI mutation is not enabled; use the equivalent CLI command.",
        "UI mutation is not enabled; boundary warnings still require CLI-led review.",
        "UI preview commands match the current append-only review CLI contract.",
        "UI preview commands drifted from the append-only review CLI contract.",
        "Request reviewer metadata is required local context, but it is not sufficient proof of authority on its own.",
        "Reviewer label must identify the local operator consistently enough for audit and review history drilldown.",
        "Session label is required because the current local mutation boundary is session-gated.",
        "Session label is optional while session-gated review is disabled.",
        "Local reviewer/session enforcement is active only for the explicit loopback-local mutation route.",
        "Reviewer/session enforcement requirements are defined for the local route contract, but read-only surfaces remain descriptive until GUI mutation is explicitly enabled.",
        "Reviewer/session fields remain descriptive local metadata until explicit route enforcement is enabled.",
        "Read-only UI surfaces expose current local enforcement expectations, but they do not grant or prove authority on their own.",
        "Recorded reviewer/session metadata supports local auditability and boundary inspection, but it does not imply hosted authentication, multi-user-safe authority, or default-on GUI mutation.",
        "Reviewer/session validation and gate checks are actively enforced on the local browser-triggered write route.",
        "Reviewer/session validation and gate checks are defined for the local route contract, but the current UI surface remains preview-only.",
        "Reviewer/session validation and gate checks are exposed for inspection, while read-only UI surfaces remain non-authoritative previews.",
        "The same reviewer/session validation families should stay aligned across readiness, preview, apply, and recovery-facing surfaces.",
        "Local reviewer identity proof currently means loopback-local operator context plus reviewer/session metadata.",
        "No durable GUI review result is reported as applied unless both review decision persistence and audit insertion succeed.",
        "GUI mutation is explicitly enabled for loopback-local reviewer-declared actions.",
        "GUI mutation remains disabled; capability flag is noted as preview intent only.",
        "GUI mutation remains disabled; read-only preview only.",
        "Preserve review-ready signals as preview-only until browser-triggered write ADR and audit semantics are explicit.",
        "GUI mutation remains disabled.",
    }
    required_prefix = {
        "Open summary job ",
        "Open artifact ",
        "Response ",
        "sources: ",
        "More ",
        "Sort: ",
        "Hit counts: vector=",
        ", graph=",
        ", chronicle=",
        "prev=",
        "trail=",
        "Package preview available for ",
        "review status is ",
        "runtime retrieval handoff: ",
        "review target handoff: ",
    }
    for locale in ("ja", "zh-CN"):
        exact = UI_I18N_CATALOG[locale]["exact"]
        exact_missing = required_exact.difference(exact)
        assert not exact_missing, f"{locale} missing exact keys: {sorted(exact_missing)}"
        prefix = UI_I18N_CATALOG[locale]["prefix"]
        prefix_missing = required_prefix.difference(prefix)
        assert not prefix_missing, f"{locale} missing prefix keys: {sorted(prefix_missing)}"


def test_ui_i18n_catalog_covers_generic_helper_empty_and_fallback_copy():
    required_exact = {
        "No records.",
        "(none)",
        "(not available)",
        "(no response_id)",
    }
    for locale in ("ja", "zh-CN"):
        exact = UI_I18N_CATALOG[locale]["exact"]
        missing = required_exact.difference(exact)
        assert not missing, f"{locale} missing exact keys: {sorted(missing)}"


def test_normalize_ui_locale_matches_supported_locale_rules():
    assert normalize_ui_locale("ja") == "ja"
    assert normalize_ui_locale("ja-JP") == "ja"
    assert normalize_ui_locale("en") == "en"
    assert normalize_ui_locale("zh") == "zh-CN"
    assert normalize_ui_locale("zh-TW") == "zh-CN"
    assert normalize_ui_locale("fr") == "en"
    assert normalize_ui_locale("") == "en"
    assert normalize_ui_locale(None) == "en"
