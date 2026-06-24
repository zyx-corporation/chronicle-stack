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
        "ui.auth_boundary_blocker.auth_not_enabled",
        "ui.auth_boundary_blocker.authorization_not_enabled",
        "ui.auth_boundary_blocker.reviewer_identity_missing",
        "ui.auth_boundary_blocker.reviewer_identity_declared_only",
        "ui.auth_boundary_blocker.reviewer_session_label_missing",
        "ui.auth_boundary_blocker.shared_machine_session_unhardened",
        "ui.mutation_blocker.write_routes_disabled",
        "ui.mutation_blocker.auth_not_enabled",
        "ui.mutation_blocker.authorization_not_enabled",
        "ui.mutation_blocker.mutation_capability_flag_disabled",
        "ui.mutation_blocker.ui_mutation_enable_flag_disabled",
        "ui.mutation_blocker.reviewer_identity_missing",
        "ui.mutation_blocker.reviewer_identity_declared_only",
        "ui.mutation_blocker.reviewer_session_label_missing",
        "ui.mutation_blocker_source.boundary",
        "ui.mutation_blocker_source.review_queue",
        "ui.mutation_enablement_check.mutation_capability_flag.label",
        "ui.mutation_enablement_check.mutation_capability_flag.detail",
        "ui.mutation_enablement_check.ui_mutation_enable_flag.label",
        "ui.mutation_enablement_check.ui_mutation_enable_flag.detail",
        "ui.mutation_enablement_check.auth_boundary.label",
        "ui.mutation_enablement_check.auth_boundary.detail",
        "ui.mutation_enablement_check.authorization_boundary.label",
        "ui.mutation_enablement_check.authorization_boundary.detail",
        "ui.mutation_enablement_check.reviewer_identity.label",
        "ui.mutation_enablement_check.reviewer_identity.detail",
        "ui.mutation_enablement_check.session_labels.label",
        "ui.mutation_enablement_check.session_labels.detail",
        "ui.template.mutation_enablement_check_summary",
        "ui.auth_readiness.message.boundary_aligned",
        "ui.auth_readiness.message.advisory_only",
        "ui.auth_readiness.message.partially_aligned",
        "ui.auth_readiness.message.unavailable",
        "ui.auth_boundary_summary.message.auth_not_enabled",
        "ui.auth_boundary_summary.message.authorization_not_enabled",
        "ui.auth_boundary_summary.message.reviewer_declared_preview",
        "ui.auth_readiness.scope.auth_not_enabled",
        "ui.auth_readiness.scope.authorization_not_enabled",
        "ui.auth_readiness.scope.session_gated",
        "ui.auth_readiness.scope.descriptive_preview",
        "ui.identity_boundary.message.boundary_aligned",
        "ui.identity_boundary.message.partially_aligned",
        "ui.identity_boundary.message.identity_unavailable",
        "ui.identity_assurance.message.declared_only",
        "ui.identity_assurance.message.local_session_unverified",
        "ui.identity_assurance.message.boundary_aligned",
        "ui.review_capability.message.ready",
        "ui.review_capability.message.advisory_only",
        "ui.review_capability.message.resolved",
        "ui.package_readiness.message.package_context_available",
        "ui.package_readiness.message.no_context_records",
        "ui.package_readiness.message.unavailable",
        "ui.package_handoff.message.package_context_available",
        "ui.package_handoff.message.no_context_records",
        "ui.package_handoff.message.unavailable",
        "ui.action_preview.message.enabled_ready",
        "ui.action_preview.message.enabled_blocked",
        "ui.action_preview.message.preview_only_ready",
        "ui.action_preview.message.preview_only_blocked",
        "ui.cli_parity.message.aligned",
        "ui.cli_parity.message.drift_detected",
        "ui.provider_response.message.present",
        "ui.provider_response.message.unavailable",
        "ui.retrieval_handoff.message.records_available",
        "ui.retrieval_handoff.message.no_records",
        "ui.template.retrieval_handoff.hit_counts",
        "ui.invocation_plan.message.ready",
        "ui.invocation_plan.message.blocked",
        "ui.template.invocation_plan.provider_summary",
        "ui.graph_summary.message.available",
        "ui.graph_summary.message.unavailable",
        "ui.template.graph_summary.counts",
        "ui.graph_summary.note.read_only_derived",
        "ui.ai_index_status.message.available",
        "ui.ai_index_status.message.unavailable",
        "ui.template.ai_index_status.vector_counts",
        "ui.template.ai_index_status.graph_counts",
        "ui.ai_index_status.note.read_only_derived",
        "ui.runtime_preview.title.summary",
        "ui.runtime_preview.title.unknown",
        "ui.template.runtime_preview.title.execution",
        "ui.template.runtime_preview.title.retrieval_plan",
        "ui.template.runtime_preview.title.invocation_plan",
        "ui.related_link.open_matching_review_detail",
        "ui.related_link.open_matching_runtime_record",
        "ui.template.related_link.open_summary_job",
        "ui.template.related_link.open_artifact",
        "ui.template.related_link.open_context",
        "ui.template.related_link.open_event",
        "ui.template.related_link.open_detail",
        "ui.template.related_link.open_matching_detail",
        "ui.template.related_link.open_review_target",
        "ui.reviewer_context.expectation.required",
        "ui.reviewer_context.expectation.optional",
        "ui.reviewer_context.note.authority",
        "ui.reviewer_context.note.reviewer_label",
        "ui.reviewer_context.note.reviewer_kind",
        "ui.reviewer_context.note.session_required",
        "ui.reviewer_context.note.session_optional",
        "ui.reviewer_context.note.ui_intent",
        "ui.reviewer_enforcement.message.enforced_local_session",
        "ui.reviewer_enforcement.message.preview_contract_only",
        "ui.reviewer_enforcement.message.descriptive_only",
        "ui.reviewer_enforcement.note.read_only_scope",
        "ui.reviewer_enforcement.note.descriptive",
        "ui.reviewer_validation_gate.message.local_route_enforced",
        "ui.reviewer_validation_gate.message.preview_route_contract",
        "ui.reviewer_validation_gate.message.read_only_preview",
        "ui.reviewer_validation_gate.note.scope_alignment",
        "ui.template.auth_boundary_blocker_summary",
        "ui.template.mutation_blocker_summary_boundary",
        "ui.template.mutation_blocker_summary_review_queue",
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
        "Retrieval handoff summarizes dry-run record hits for downstream local package review.",
        "Retrieval handoff has no referenced records; downstream package review remains advisory.",
        "Invocation plan is ready for explicit local execution.",
        "Invocation plan remains blocked until local runtime boundary requirements align.",
        "Graph summary is available as a local derived read model.",
        "Graph summary is unavailable; keep using primary Chronicle records for authority.",
        "Graph summary remains derived, read-only, and non-authoritative over primary Chronicle records.",
        "AI index status is available as a local derived read model.",
        "AI index status is unavailable; keep using primary Chronicle records for authority.",
        "AI index status remains derived, read-only, and non-authoritative over primary Chronicle records.",
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
