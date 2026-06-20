"""Tests for explicit local Chronicle UI server."""

import http.client
import json
import threading

import pytest
from typer.testing import CliRunner

from chronicle.cli import app
from chronicle.models.artifact import ArtifactType
from chronicle.models.audit import AuditOperation, AuditSeverity, AuditTargetEnvironment
from chronicle.models.boundary import BoundaryConditionField, BoundaryOperator, BoundaryRuleType
from chronicle.models.decision import DecisionType
from chronicle.models.lifecycle import LifecycleAction, LifecycleReasonClass
from chronicle.models.visibility import VisibilityHint
from chronicle.services.artifact_service import ArtifactService
from chronicle.services.audit_service import AuditService
from chronicle.services.boundary_service import BoundaryService
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.context_service import ContextService
from chronicle.services.decision_service import DecisionService
from chronicle.services.graph_index_service import GraphIndexService
from chronicle.services.lifecycle_service import LifecycleService
from chronicle.services.review_service import ReviewService
from chronicle.services.runtime_config_service import RuntimeConfigService
from chronicle.services.runtime_service import RuntimeService
from chronicle.services.summary_job_service import SummaryJobService
from chronicle.services.vector_index_service import VectorIndexService
from chronicle.models.review import ReviewerIdentityKind
from chronicle.ui_server import (
    ChronicleUIDataService,
    UIAuthMode,
    UIAuthorizationMode,
    build_startup_metadata,
    make_server,
)


def _http_get(host: str, port: int, path: str) -> tuple[int, str]:
    connection = http.client.HTTPConnection(host, port, timeout=5)
    try:
        connection.request("GET", path)
        response = connection.getresponse()
        return response.status, response.read().decode("utf-8")
    finally:
        connection.close()


def _populate(root):
    ChronicleService(root).init("UI Test")
    context = ContextService(root).add_context(title="UI Context", visibility_hint=VisibilityHint.PUBLIC)
    artifact_file = root / "artifact.md"
    artifact_file.write_text("artifact body", encoding="utf-8")
    artifact, _version = ArtifactService(root).create(
        title="UI Artifact",
        artifact_type=ArtifactType.DOCUMENT,
        source_file=artifact_file,
        visibility_hint=VisibilityHint.PRIVATE,
    )
    decision = DecisionService(root).record(
        decision_type=DecisionType.ACCEPTED,
        reason="UI decision",
        artifact_id=artifact.artifact_id,
    )
    boundary_rule = BoundaryService(root).add_rule(
        rule_type=BoundaryRuleType.WARN,
        field=BoundaryConditionField.VISIBILITY,
        operator=BoundaryOperator.EQUALS,
        value="private",
        reason="UI boundary",
    )
    audit_event = AuditService(root).record(
        operation=AuditOperation.EXPORT,
        actor="test",
        purpose="ui audit",
        target_environment=AuditTargetEnvironment.LOCAL,
        result=AuditSeverity.INFO,
        summary="UI audit event",
    )
    lifecycle_marker = LifecycleService(root).record(
        action=LifecycleAction.SEAL,
        target_id=context.context_id,
        target_kind="context",
        actor="test",
        reason_class=LifecycleReasonClass.PRIVACY,
        reason="UI lifecycle marker",
    )
    event_id = ChronicleService(root).jsonl.read_all()[0].event_id
    VectorIndexService(root).add_entry(
        record_id=event_id,
        text="UI placeholder vector entry for local ai index visibility",
        record_type="event",
        metadata={"source": "ui-test"},
    )
    GraphIndexService(root).add_node(
        node_id=event_id,
        labels=["event"],
        properties={"title": "UI event"},
    )
    GraphIndexService(root).add_node(
        node_id=context.context_id,
        labels=["context"],
        properties={"title": "UI Context"},
    )
    GraphIndexService(root).add_edge(
        source_id=event_id,
        target_id=context.context_id,
        relation="references",
        properties={"source": "ui-test"},
    )
    runtime_summary = RuntimeService(root).summarize(
        text="Runtime summary for UI visibility. It stays local.",
        record=True,
    )
    runtime_plan = RuntimeService(root).retrieve_plan(
        query="UI Context",
        record=True,
    )
    summary_job = SummaryJobService(root).create_manual_draft(
        title="UI Summary Draft",
        summary_text="UI summary draft body.",
        prompt="UI summary prompt.",
    )
    return {
        "event_id": event_id,
        "context_id": context.context_id,
        "artifact_id": artifact.artifact_id,
        "decision_id": decision.decision_id,
        "rule_id": boundary_rule.rule_id,
        "audit_id": audit_event.audit_id,
        "lifecycle_id": lifecycle_marker.lifecycle_id,
        "runtime_summary_event_id": runtime_summary.event_id,
        "runtime_plan_event_id": runtime_plan.event_id,
        "summary_job_id": summary_job.summary_job_id,
    }


def test_startup_metadata(tmp_path):
    metadata = build_startup_metadata(host="127.0.0.1", port=8765, root=tmp_path)
    payload = json.loads(metadata.to_json())
    assert payload["host"] == "127.0.0.1"
    assert payload["port"] == 8765
    assert payload["url"] == "http://127.0.0.1:8765"
    assert payload["root"] == str(tmp_path.resolve())
    assert payload["bind_scope"] == "loopback-only"
    assert payload["read_only"] is True
    assert payload["runtime"] == "foreground-local-ui"
    assert payload["external_runtime"] is False
    assert payload["mutation_enabled"] is False
    assert payload["mutation_capability_flag"] is False
    assert payload["auth_mode"] == "not_enabled"
    assert payload["authorization_mode"] == "not_enabled"
    assert payload["ui_boundary"]["loopback_only"] is True
    assert payload["ui_boundary"]["mutation_readiness_status"] == "preview_only"
    assert "write_routes_disabled" in payload["ui_boundary"]["mutation_blockers"]
    assert payload["ui_boundary"]["auth_boundary_summary"]["status"] == "auth_not_enabled"
    assert "auth_not_enabled" in payload["ui_boundary"]["auth_boundary_summary"]["blockers"]


def test_startup_metadata_with_configured_auth_mode(tmp_path):
    metadata = build_startup_metadata(
        host="127.0.0.1",
        port=8765,
        root=tmp_path,
        auth_mode=UIAuthMode.LOOPBACK_LOCAL,
        authorization_mode=UIAuthorizationMode.REVIEWER_DECLARED,
    )
    payload = json.loads(metadata.to_json())
    assert payload["auth_mode"] == "loopback_local"
    assert payload["authorization_mode"] == "reviewer_declared"
    assert payload["ui_boundary"]["session_gating"] is True
    assert payload["ui_boundary"]["auth_boundary_summary"]["status"] == "reviewer_declared_preview"


def test_startup_metadata_with_mutation_capability_flag(tmp_path):
    metadata = build_startup_metadata(
        host="127.0.0.1",
        port=8765,
        root=tmp_path,
        mutation_capability_flag=True,
    )
    payload = json.loads(metadata.to_json())
    assert payload["mutation_capability_flag"] is True
    assert payload["mutation_enabled"] is False
    assert payload["ui_boundary"]["mutation_capability_flag"] is True
    assert "preview intent only" in payload["ui_boundary"]["mutation_readiness_message"]


def test_ui_overview_data(tmp_path):
    _populate(tmp_path)
    RuntimeConfigService(tmp_path).set_http(
        base_url="https://runtime.example.invalid/v1",
        model_name="manual-http-model",
        api_key_env="OPENAI_API_KEY",
        allow_network=True,
    )

    overview = ChronicleUIDataService(tmp_path).overview()

    assert overview["chronicle"]["title"] == "UI Test"
    assert overview["counts"]["contexts"] == 1
    assert overview["counts"]["artifacts"] == 2
    assert overview["counts"]["decisions"] == 1
    assert overview["counts"]["boundary_rules"] == 1
    assert overview["counts"]["audit_events"] == 1
    assert overview["counts"]["lifecycle_markers"] == 1
    assert overview["counts"]["summary_jobs"] == 1
    assert overview["runtime_boundary"]["read_only"] is True
    assert overview["runtime_boundary"]["daemon"] is False
    assert overview["runtime_boundary"]["external_model_api"] is False
    assert overview["runtime_boundary"]["graphrag_runtime"] is False
    assert overview["runtime_boundary"]["vector_db"] is False
    assert overview["runtime_boundary"]["graph_db"] is False
    assert overview["runtime_config"]["config"]["provider_kind"] == "http"
    assert overview["runtime_config"]["config"]["model_name"] == "manual-http-model"
    assert overview["runtime_config"]["config"]["allow_network"] is True
    assert overview["ui_boundary"]["mutation_enabled"] is False
    assert overview["ui_boundary"]["mutation_capability_flag"] is False
    assert overview["ui_boundary"]["auth_mode"] == "not_enabled"
    assert overview["auth_boundary_summary"]["status"] == "auth_not_enabled"
    assert "Define explicit local auth boundary." in overview["auth_boundary_summary"]["next_steps"]
    assert overview["auth_boundary_overview"]["auth_warning_count"] == 3
    assert overview["auth_boundary_overview"]["authorization_warning_count"] == 3
    assert overview["auth_boundary_overview"]["missing_identity_count"] == 3
    assert overview["auth_boundary_overview"]["review_capability_counts"]["advisory_only"] == 3
    assert overview["identity_boundary_summary"]["status"] == "identity_unavailable"
    assert overview["identity_boundary_summary"]["missing_identity_count"] == 3
    assert overview["mutation_readiness"]["status"] == "preview_only"
    assert "Define explicit local auth boundary." in overview["mutation_readiness"]["next_steps"]
    assert overview["runtime_records_summary"]["kind_counts"]["summary"] == 1
    assert overview["runtime_records_summary"]["kind_counts"]["retrieval_plan"] == 1
    assert overview["runtime_records_summary"]["auth_readiness_counts"]["advisory_only"] == 2
    assert overview["summary_jobs_summary"]["status_counts"]["pending_review"] == 1
    assert overview["summary_jobs_summary"]["review_capability_counts"]["advisory_only"] == 1
    assert overview["summary_jobs_summary"]["auth_readiness_counts"]["advisory_only"] == 1
    assert overview["summary_jobs_summary"]["package_readiness_counts"]["no_context_records"] == 1
    assert overview["summary_jobs_summary"]["runtime_provider_counts"]["disabled"] == 1
    assert overview["summary_jobs_summary"]["summary_source_total"] == 0
    assert overview["triage"]["needs_attention_reviews"] == 3
    assert overview["triage"]["runtime_record_kinds"]["summary"] == 1
    assert overview["triage"]["runtime_record_kinds"]["retrieval_plan"] == 1
    assert overview["triage"]["review_capability_counts"]["advisory_only"] == 3
    assert overview["triage"]["package_readiness_counts"]["package_context_available"] >= 1


def test_ui_data_service_read_endpoints(tmp_path):
    _populate(tmp_path)
    RuntimeConfigService(tmp_path).set_local(model_name="ui-local-model", provider_name="ui-local")
    service = ChronicleUIDataService(tmp_path)

    assert service.contexts()["contexts"][0]["title"] == "UI Context"
    assert service.artifacts()["artifacts"][0]["title"] == "UI Artifact"
    assert service.decisions()["decisions"][0]["reason"] == "UI decision"
    assert service.boundary_rules()["boundary_rules"][0]["reason"] == "UI boundary"
    assert service.audit_events()["audit_events"][0]["summary"] == "UI audit event"
    assert service.lifecycle_markers()["lifecycle_markers"][0]["reason"] == "UI lifecycle marker"
    assert len(service.runtime_records()["runtime_records"]) == 2
    assert service.runtime_records()["runtime_records"][0]["runtime_record_preview"]["title"]
    assert service.runtime_records()["runtime_records"][0]["runtime_record_preview"]["suggested_cli_family"].startswith(
        "chronicle runtime"
    )
    assert service.runtime_records()["runtime_records"][0]["auth_readiness_status"] in {"advisory_only", ""}
    assert len(service.review_queue()["review_queue"]) == 3
    assert len(service.summary_jobs_list()["summary_jobs"]) == 1
    assert service.summary_jobs_list()["summary_jobs"][0]["summary_job_id"].startswith("sum_")
    assert service.summary_jobs_list()["summary_jobs"][0]["review_target_event_id"].startswith("evt_")
    assert service.summary_jobs_list()["summary_jobs"][0]["review_capability_status"] == "advisory_only"
    assert service.summary_jobs_list()["summary_jobs"][0]["auth_readiness_status"] == "advisory_only"
    assert service.summary_jobs_list()["summary_jobs"][0]["package_readiness_status"] == "no_context_records"
    assert service.summary_jobs_list()["summary_jobs"][0]["cli_parity_status"] == "aligned"
    assert service.runtime_config_state()["runtime_config"]["config"]["provider_name"] == "ui-local"
    assert service.review_queue()["review_queue"][0]["review_preview_only"] is True
    assert service.review_queue()["review_queue"][0]["target_event_id"].startswith("evt_")
    assert service.review_queue()["review_queue"][0]["review_capability"]["status"] == "advisory_only"
    assert service.review_queue()["review_queue"][0]["auth_boundary_notice"]["status"] == "advisory_only"
    assert service.review_queue()["review_queue"][0]["package_readiness_summary"]["label"].startswith("package:")
    assert service.review_queue()["review_queue"][0]["package_readiness_summary"]["message"]
    assert service.review_queue()["review_queue"][0]["cli_parity_summary"]["status"] == "aligned"
    assert service.review_queue()["review_queue"][0]["cli_parity_summary"]["expected_actions"] == [
        "approve",
        "reject",
        "request_changes",
    ]
    overview = service.overview()
    assert overview["triage"]["cli_parity_aligned_reviews"] == 3
    assert overview["triage"]["cli_parity_drift_reviews"] == 0
    assert overview["triage"]["cli_parity_counts"]["aligned"] == 3
    assert overview["triage"]["identity_assurance_counts"]["unknown"] == 3
    assert overview["triage"]["reviewer_kind_counts"]["unknown"] == 3
    assert overview["triage"]["warning_counts"]["ui_auth_not_enabled"] == 3
    assert overview["triage"]["warning_counts"]["ui_authorization_not_enabled"] == 3
    assert overview["triage"]["warning_summaries"][0]["code"] == "ui_auth_not_enabled"
    assert overview["triage"]["warning_summaries"][1]["code"] == "ui_authorization_not_enabled"
    assert "ui_auth_not_enabled" in service.review_queue()["review_queue"][0]["review_capability"]["warnings"]
    assert service.review_queue()["review_queue"][0]["review_capability"]["warning_details"][0]["message"]
    assert "latest_identity_assurance" not in service.review_queue()["review_queue"][0]
    assert service.ui_boundary()["ui_boundary"]["loopback_only"] is True
    assert "events" in service.events()
    assert "rde_records" in service.rde_records()
    assert "status" in service.package_review_snapshot()
    assert "nodes" in service.graph_summary()
    assert service.ai_index_status()["ai_index_status"]["vector"]["entry_count"] == 1
    assert service.ai_index_vector_entries()["vector_entries"][0]["record_id"] == service.events()["events"][-1]["event_id"]
    assert service.ai_index_graph_nodes()["graph_nodes"]
    assert service.ai_index_graph_edges()["graph_edges"]


def test_ui_data_service_detail_endpoints(tmp_path):
    ids = _populate(tmp_path)
    ReviewService(tmp_path).request_changes(
        event_id=ids["runtime_summary_event_id"],
        reviewer="alice",
        reviewer_kind=ReviewerIdentityKind.LOCAL_OPERATOR,
        session_label="ui-test",
        note="revise wording",
    )
    service = ChronicleUIDataService(tmp_path)

    assert service.detail_payload(f"/api/events/{ids['event_id']}")["record"]["event_id"] == ids["event_id"]
    assert service.detail_payload(f"/api/contexts/{ids['context_id']}")["record"]["title"] == "UI Context"
    artifact_detail = service.detail_payload(f"/api/artifacts/{ids['artifact_id']}")["record"]
    assert artifact_detail["title"] == "UI Artifact"
    assert artifact_detail["versions"]
    assert service.detail_payload(f"/api/decisions/{ids['decision_id']}")["record"]["reason"] == "UI decision"
    assert service.detail_payload(f"/api/boundary/{ids['rule_id']}")["record"]["reason"] == "UI boundary"
    assert service.detail_payload(f"/api/audit/{ids['audit_id']}")["record"]["summary"] == "UI audit event"
    assert service.detail_payload(f"/api/lifecycle/{ids['lifecycle_id']}")["record"]["reason"] == "UI lifecycle marker"
    summary_detail = service.detail_payload(f"/api/summary-jobs/{ids['summary_job_id']}")["record"]
    assert summary_detail["title"] == "UI Summary Draft"
    assert summary_detail["suggested_cli_family"] == "chronicle summary show --id"
    assert summary_detail["runtime_provider_kind"] == "disabled"
    assert summary_detail["review_target_event_id"].startswith("evt_")
    assert summary_detail["review_capability"]["status"] == "advisory_only"
    assert summary_detail["auth_boundary_notice"]["status"] == "advisory_only"
    assert "auth_not_enabled" in summary_detail["auth_boundary_notice"]["blockers"]
    assert summary_detail["package_readiness"]["status"] == "no_context_records"
    assert summary_detail["cli_parity"]["status"] == "aligned"
    assert summary_detail["action_preview"]["status"] == "preview_only"
    assert any(link["path"] == f"/api/review-queue/{summary_detail['review_target_event_id']}" for link in summary_detail["related_links"])
    runtime_detail = service.detail_payload(f"/api/runtime-records/{ids['runtime_summary_event_id']}")["record"]
    assert "runtime_summary" in runtime_detail["payload"]
    assert runtime_detail["runtime_record_preview"]["record_kind"] == "summary"
    assert runtime_detail["auth_boundary_notice"]["status"] == "advisory_only"
    assert runtime_detail["suggested_cli_family"] == "chronicle runtime summarize --record"
    assert runtime_detail["related_links"][0]["path"] == f"/api/review-queue/{ids['runtime_summary_event_id']}"
    assert runtime_detail["related_links"][0]["label"] == "Open matching review detail"
    retrieval_detail = service.detail_payload(f"/api/runtime-records/{ids['runtime_plan_event_id']}")["record"]
    assert "runtime_retrieval_plan" in retrieval_detail["payload"]
    assert retrieval_detail["runtime_record_preview"]["record_kind"] == "retrieval_plan"
    assert retrieval_detail["retrieval_handoff"]["query"] == "UI Context"
    assert retrieval_detail["retrieval_handoff"]["package_review_required"] is True
    assert retrieval_detail["retrieval_handoff"]["downstream_commands"][0].startswith("chronicle package review")
    assert retrieval_detail["package_handoff_preview"]["status"] == "package_context_available"
    assert ids["context_id"] in retrieval_detail["package_handoff_preview"]["eligible_context_ids"]
    assert retrieval_detail["package_handoff_preview"]["package_review"]["status"] in {"pass", "warning", "blocked"}
    assert ids["context_id"] in retrieval_detail["package_handoff_preview"]["package_manifest_preview"]["referenced_records"]
    assert any(link["path"] == f"/api/contexts/{ids['context_id']}" for link in retrieval_detail["related_links"])
    assert any(link["label"] == f"Open context {ids['context_id']}" for link in retrieval_detail["related_links"])
    assert retrieval_detail["auth_boundary_notice"]["status"] == "advisory_only"
    review_detail = service.detail_payload(f"/api/review-queue/{ids['runtime_summary_event_id']}")["record"]
    assert review_detail["target_event_id"] == ids["runtime_summary_event_id"]
    assert review_detail["review_preview_only"] is True
    assert review_detail["package_readiness"]["status"] == "no_context_records"
    assert review_detail["package_readiness"]["suggested_commands"][0] == "chronicle show --json"
    assert review_detail["latest_audit_id"].startswith("aud_")
    assert review_detail["latest_reviewer_identity"]["kind"] == "local_operator"
    assert review_detail["review_capability"]["status"] == "advisory_only"
    assert review_detail["review_capability"]["warning_details"][0]["code"] == "ui_auth_not_enabled"
    assert review_detail["auth_boundary_notice"]["status"] == "advisory_only"
    assert "authorization_not_enabled" in review_detail["auth_boundary_notice"]["blockers"]
    assert review_detail["latest_identity_assurance"]["status"] == "local_session_unverified"
    assert review_detail["history"][0]["disposition"] == "request_changes"
    assert review_detail["history"][0]["reviewer_identity"]["session_label"] == "ui-test"
    assert review_detail["history"][0]["identity_assurance"]["boundary_auth_mode"] == "not_enabled"
    assert review_detail["history"][0]["audit_summary"]
    assert review_detail["related_links"][0]["path"] == f"/api/runtime-records/{ids['runtime_summary_event_id']}"
    assert review_detail["related_links"][0]["label"] == "Open matching runtime record"
    review_plan_detail = service.detail_payload(f"/api/review-queue/{ids['runtime_plan_event_id']}")["record"]
    assert review_plan_detail["package_readiness"]["status"] == "package_context_available"
    assert ids["context_id"] in review_plan_detail["package_readiness"]["eligible_context_ids"]
    assert review_plan_detail["package_readiness"]["package_review"]["status"] in {"pass", "warning", "blocked"}
    assert review_plan_detail["package_readiness_summary"]["status"] == "package_context_available"
    assert any(link["path"] == f"/api/contexts/{ids['context_id']}" for link in review_plan_detail["related_links"])
    assert any(link["label"] == f"Open context {ids['context_id']}" for link in review_plan_detail["related_links"])
    assert service.detail_payload(f"/api/ai-index/vector/{ids['event_id']}")["record"]["record_id"] == ids["event_id"]
    graph_detail = service.detail_payload(f"/api/ai-index/graph-nodes/{ids['event_id']}")["record"]
    assert graph_detail["node_id"] == ids["event_id"]
    assert graph_detail["neighbors"]["outgoing"][0]["relation"] == "references"
    assert service.detail_payload("/api/contexts/missing") is None


def test_ui_runtime_detail_supports_invocation_plan(tmp_path):
    ChronicleService(tmp_path).init("UI Invocation Plan")
    RuntimeConfigService(tmp_path).set_http(
        base_url="https://runtime.example.invalid/v1",
        model_name="manual-http-model",
        api_key_env="OPENAI_API_KEY",
    )
    summary_job = SummaryJobService(tmp_path).create_manual_draft(
        title="Invocation Source Draft",
        summary_text="Invocation plan detail text.",
        prompt="Invocation summary prompt.",
    )
    invocation_plan = RuntimeService(tmp_path).invocation_plan_from_summary(
        summary_job_id=summary_job.summary_job_id,
        summary_title=summary_job.title,
        summary_text=summary_job.summary_text,
        prompt=summary_job.provenance.prompt,
        source_ref_count=len(summary_job.source_refs),
        record=True,
    )

    service = ChronicleUIDataService(tmp_path)
    detail = service.detail_payload(f"/api/runtime-records/{invocation_plan.event_id}")["record"]

    assert detail["runtime_record_preview"]["record_kind"] == "invocation_plan"
    assert detail["suggested_cli_family"] == "chronicle runtime invoke-plan --record"
    assert detail["invocation_plan"]["provider_kind"] == "http"
    assert detail["invocation_plan"]["invocation_ready"] is False
    assert "network_not_allowed_by_contract" in detail["invocation_plan"]["blocking_reasons"]
    assert any(link["path"].startswith("/api/summary-jobs/") for link in detail["related_links"])


def test_ui_detail_assurance_can_align_with_configured_boundary(tmp_path):
    ids = _populate(tmp_path)
    ReviewService(tmp_path).request_changes(
        event_id=ids["runtime_summary_event_id"],
        reviewer="alice",
        reviewer_kind=ReviewerIdentityKind.LOCAL_OPERATOR,
        session_label="ui-test",
        note="revise wording",
    )
    service = ChronicleUIDataService(
        tmp_path,
        auth_mode=UIAuthMode.LOOPBACK_LOCAL,
        authorization_mode=UIAuthorizationMode.REVIEWER_DECLARED,
    )

    review_detail = service.detail_payload(f"/api/review-queue/{ids['runtime_summary_event_id']}")["record"]

    assert review_detail["review_capability"]["status"] == "ready"
    assert review_detail["review_capability"]["can_review_now"] is True
    assert review_detail["action_preview"]["status"] == "preview_only"
    assert review_detail["action_preview"]["ui_mutation_enabled"] is False
    assert "chronicle review approve --event" in review_detail["action_preview"]["actions"][0]["command"]
    assert review_detail["cli_parity"]["status"] == "aligned"
    assert review_detail["cli_parity"]["expected_actions"] == [
        "approve",
        "reject",
        "request_changes",
    ]
    assert review_detail["cli_parity"]["missing_preview_commands"] == []
    assert review_detail["cli_parity"]["missing_queue_commands"] == []
    assert review_detail["review_capability"]["warning_details"] == []
    assert review_detail["auth_boundary_notice"]["status"] == "boundary_aligned"
    assert review_detail["auth_boundary_notice"]["blockers"] == []
    assert review_detail["latest_identity_assurance"]["status"] == "boundary_aligned"
    assert review_detail["history"][0]["identity_assurance"]["boundary_auth_mode"] == "loopback_local"
    overview = service.overview()
    assert overview["identity_boundary_summary"]["status"] == "partially_aligned"
    assert overview["identity_boundary_summary"]["assurance_counts"]["boundary_aligned"] >= 1
    assert overview["triage"]["identity_assurance_counts"]["boundary_aligned"] >= 1


def test_ui_shell_contains_interactive_local_ui(tmp_path):
    ChronicleService(tmp_path).init("UI Shell")

    html = ChronicleUIDataService(tmp_path).html_shell()

    assert "Chronicle Stack Local UI" in html
    assert "Read-only foreground local UI" in html
    assert "loadDetail" in html
    assert "Runtime Preview" in html
    assert "Retrieval Handoff" in html
    assert "Invocation Plan" in html
    assert "Package Handoff Preview" in html
    assert "Review Package Readiness" in html
    assert "Related Links" in html
    assert "Back to current list" in html
    assert "Back to previous detail" in html
    assert "currentFilterLabel" in html
    assert "hasActiveFilters" in html
    assert "resetFilters" in html
    assert "currentSortValue" in html
    assert "stateLabel" in html
    assert "currentSortLabel" in html
    assert "warning-first:" in html
    assert "jumpBadge" in html
    assert "sourceCountBadges" in html
    assert "reviewWarningBadges" in html
    assert "reviewerIdentityBadge" in html
    assert "sortSelect" in html
    assert "sortRuntimeRows" in html
    assert "sortReviewRows" in html
    assert "sortSummaryJobRows" in html
    assert "activeReviewWarningFilter" in html
    assert "reviewWarningFilterRank" in html
    assert "reviewParityRank" in html
    assert "overviewJumpButton" in html
    assert "relatedListButtons" in html
    assert "activeViewSummary" in html
    assert "Mutation Readiness" in html
    assert "Runtime Config" in html
    assert "Summary Jobs" in html
    assert "Auth Boundary" in html
    assert "Identity Boundary" in html
    assert "Summary Jobs" in html
    assert "Runtime Records" in html
    assert "Auth warnings" in html
    assert "Authorization warnings" in html
    assert "Missing identity" in html
    assert "Session label missing" in html
    assert "Mutation capability flag:" in html
    assert "currentTrailLabel" in html
    assert "currentTrailButtons" in html
    assert "sliceBadge" in html
    assert "sliceChip" in html
    assert "openListButton" in html
    assert "sliceActionButton" in html
    assert "moreSliceButton" in html
    assert "panelTitle" in html
    assert "noticeTitle" in html
    assert "detailLine" in html
    assert "detailListLine" in html
    assert "summaryJsonLine" in html
    assert "detailListLine('Auth blockers', authBoundary.blockers, ' | ')" in html
    assert "summaryJsonLine('Identity assurance counts', identityBoundary.assurance_counts)" in html
    assert "summaryJsonLine('Auth review capability counts', authBoundaryOverview.review_capability_counts)" in html
    assert "runtimeRecordsFilterChips" in html
    assert "reviewQueueFilterChips" in html
    assert "summaryJobsFilterChips" in html
    assert "humanizeDetailPath" in html
    assert "Related Links" in html
    assert "__chronicleDetailTrail" in html
    assert "readinessBadge" in html
    assert "reviewCapabilityBadge" in html
    assert "packageReadinessBadge" in html
    assert "reviewParityBadge" in html
    assert "detailListLine('Blockers', mutationReadiness.blockers, ' | ')" in html
    assert "review_requested" in html
    assert "ready" in html
    assert "CLI Parity" in html
    assert "CLI drift first" in html
    assert "summaryJsonLine('CLI parity counts', triage.cli_parity_counts)" in html
    assert "summaryJsonLine('Identity assurance counts', triage.identity_assurance_counts)" in html
    assert "summaryJsonLine('Reviewer kind counts', triage.reviewer_kind_counts)" in html
    assert "summaryJsonLine('Warning counts', triage.warning_counts)" in html
    assert "summaryJsonLine('Status counts', summaryJobs.status_counts)" in html
    assert "summaryJsonLine('Auth readiness counts', runtimeRecords.auth_readiness_counts)" in html
    assert "summaryJsonLine('Auth readiness counts', summaryJobs.auth_readiness_counts)" in html
    assert "summaryJsonLine('Runtime provider counts', summaryJobs.runtime_provider_counts)" in html
    assert "Runtime auth advisory" in html
    assert "Summary advisory" in html
    assert "Summary auth advisory" in html
    assert "Summary package ready" in html
    assert "Warning priority:" in html
    assert "summaryJsonLine('Runtime kinds', triage.runtime_record_kinds)" in html
    assert "detailLine('Status', parity.status || '')" in html
    assert "detailListLine('Expected actions', parity.expected_actions)" in html
    assert "openListButton('Open Review Queue', '/api/review-queue')" in html
    assert "openListButton('Open Runtime Records', '/api/runtime-records')" in html
    assert "openListButton('Open Summary Jobs', '/api/summary-jobs')" in html
    assert "openListButton('Open Runtime Config', '/api/runtime-config')" in html
    assert "openListButton('Open Package Review', '/api/package-review')" in html
    assert "buttons.push(openListButton('Open Review Queue', '/api/review-queue'));" in html
    assert "<th>review</th><th>auth</th><th>package</th>" in html
    assert "textInput('summaryJobs', 'Filter summary jobs...')" in html
    assert "sortSelect('summaryJobs', currentSortValue('/api/summary-jobs')" in html
    assert "<th>auth</th>" in html
    assert "Auth aligned" in html
    assert "Auth advisory" in html
    assert "Open review" in html
    assert "package:no_context_records" in html
    assert 'data-reset-filters="all"' in html
    assert "sliceActionButton('Advisory Reviews', '/api/review-queue', 'reviewQueue', 'advisory')" in html
    assert "sliceActionButton('CLI Aligned Reviews', '/api/review-queue', 'reviewQueue', 'aligned')" in html
    assert "sliceActionButton('Identity Aligned Reviews', '/api/review-queue', 'reviewQueue', 'boundary_aligned')" in html
    assert "sliceActionButton('Auth Boundary Warnings', '/api/review-queue', 'reviewQueue', 'ui_auth_not_enabled')" in html
    assert "sliceActionButton('Declared Identity Warnings', '/api/review-queue', 'reviewQueue', 'reviewer_identity_declared_only')" in html
    assert "sliceActionButton('Retrieval Plans', '/api/runtime-records', 'runtimeRecords', 'retrieval_plan')" in html
    assert "data-detail-nav" in html
    assert "data-detail-trail" in html
    assert "data-back-view" in html
    assert "No matching runtime records for current filter." in html
    assert "No matching review rows for current filter." in html
    assert "CLI aligned" in html
    assert "Open Runtime Records" in html
    assert "Open Review Queue" in html
    assert "Open Package Review" in html
    assert "CLI Aligned Reviews" in html
    assert "Auth Boundary Warnings" in html
    assert "warnings.slice(0, 2).forEach" in html
    assert "const previewButtons = [];" in html
    assert "const parityButtons = [];" in html
    assert "const assuranceButtons = [];" in html
    assert "const readinessButtons = [];" in html
    assert "const timelineButtons = [];" in html
    assert "Declared Identity Warnings" in html
    assert 'data-reset-filter="runtimeRecords"' in html
    assert 'data-reset-filter="reviewQueue"' in html
    assert "runtimeRecords" in html
    assert "reviewQueue" in html
    assert "textInput('runtimeRecords'" in html
    assert "<th>auth</th>" in html
    assert "textInput('reviewQueue'" in html
    assert "__chronicleFilters" in html
    assert "summaryJobs: ''" in html
    assert "summaryJobs: 'latest'" in html
    assert "__chronicleSorts" in html
    assert "Active view:" in html
    assert "jumpBadge(" in html
    assert "Auth Readiness" in html
    assert "Review Capability" in html
    assert "Action Preview" in html
    assert "<button disabled>Approve</button>" in html
    assert "<button disabled>Reject</button>" in html
    assert "<button disabled>Request Changes</button>" in html
    assert "Identity Assurance" in html
    assert "warning_details" in html
    assert "/api/events" in html
    assert "/api/runtime-records" in html
    assert "/api/summary-jobs" in html
    assert "/api/runtime-config" in html
    assert "/api/review-queue" in html
    assert "/api/ui-boundary" in html
    assert "/api/package-review" in html
    assert "/api/ai-index-status" in html
    assert "does not write records" in html


def test_http_root_and_read_only_endpoints(tmp_path):
    ids = _populate(tmp_path)
    try:
        server = make_server(host="127.0.0.1", port=0, root=tmp_path)
    except PermissionError as exc:
        pytest.skip(f"local socket bind unavailable in this environment: {exc}")
    host, port = server.server_address
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        status, html = _http_get(host, port, "/")
        assert status == 200
        assert "Chronicle Stack Local UI" in html

        expected_keys = {
            "/api/overview": "counts",
            "/api/events": "events",
            "/api/contexts": "contexts",
            "/api/artifacts": "artifacts",
            "/api/decisions": "decisions",
            "/api/rde": "rde_records",
            "/api/boundary": "boundary_rules",
            "/api/audit": "audit_events",
            "/api/lifecycle": "lifecycle_markers",
            "/api/runtime-records": "runtime_records",
            "/api/review-queue": "review_queue",
            "/api/summary-jobs": "summary_jobs",
            "/api/ui-boundary": "ui_boundary",
            "/api/runtime-config": "runtime_config",
            "/api/package-review": "package_review",
            "/api/graph-summary": "graph_summary",
            "/api/ai-index-status": "ai_index_status",
            "/api/ai-index-vector": "vector_entries",
            "/api/ai-index-graph-nodes": "graph_nodes",
            "/api/ai-index-graph-edges": "graph_edges",
        }
        for endpoint, key in expected_keys.items():
            status, body = _http_get(host, port, endpoint)
            assert status == 200, endpoint
            payload = json.loads(body)
            assert key in payload, endpoint

        detail_paths = [
            f"/api/events/{ids['event_id']}",
            f"/api/contexts/{ids['context_id']}",
            f"/api/artifacts/{ids['artifact_id']}",
            f"/api/decisions/{ids['decision_id']}",
            f"/api/boundary/{ids['rule_id']}",
            f"/api/audit/{ids['audit_id']}",
            f"/api/lifecycle/{ids['lifecycle_id']}",
            f"/api/runtime-records/{ids['runtime_summary_event_id']}",
            f"/api/runtime-records/{ids['runtime_plan_event_id']}",
            f"/api/review-queue/{ids['runtime_summary_event_id']}",
            f"/api/summary-jobs/{ids['summary_job_id']}",
            f"/api/ai-index/vector/{ids['event_id']}",
            f"/api/ai-index/graph-nodes/{ids['event_id']}",
        ]
        for endpoint in detail_paths:
            status, body = _http_get(host, port, endpoint)
            assert status == 200, endpoint
            payload = json.loads(body)
            assert "record" in payload, endpoint

        status, _body = _http_get(host, port, "/api/contexts/missing")
        assert status == 404

        status, review_console = _http_get(host, port, "/review-console")
        assert status == 200
        assert "Chronicle Stack Review Console" in review_console
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_chronicle_ui_help():
    runner = CliRunner()
    result = runner.invoke(app, ["ui", "--help"])
    assert result.exit_code == 0
    for option in ("host", "port", "open", "root", "json"):
        assert option in result.stdout.lower()
