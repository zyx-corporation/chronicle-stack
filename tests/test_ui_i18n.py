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
        "overview.warning_priority",
        "ui.label.status_prefix",
        "ui.label.route_prefix",
        "ui.label.reviewer",
        "ui.label.detail_heading",
        "ui.label.empty_runtime_records",
        "ui.label.empty_review_rows",
        "ui.label.empty_summary_jobs",
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


def test_normalize_ui_locale_matches_supported_locale_rules():
    assert normalize_ui_locale("ja") == "ja"
    assert normalize_ui_locale("ja-JP") == "ja"
    assert normalize_ui_locale("en") == "en"
    assert normalize_ui_locale("zh") == "zh-CN"
    assert normalize_ui_locale("zh-TW") == "zh-CN"
    assert normalize_ui_locale("fr") == "en"
    assert normalize_ui_locale("") == "en"
    assert normalize_ui_locale(None) == "en"
