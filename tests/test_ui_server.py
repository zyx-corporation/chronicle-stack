"""Tests for explicit local Chronicle UI server."""

import http.client
import json
import threading
from pathlib import Path

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


def test_ui_server_avoids_new_inline_localize_text_value_literals():
    source = (Path(__file__).resolve().parents[1] / "src/chronicle/ui_server.py").read_text(
        encoding="utf-8"
    )
    allowed_literals = {
        "localizeTextValue(item.message || '')",
        "localizeTextValue(preview.message || '')",
        "localizeTextValue(message || '')",
        "localizeTextValue(node.nodeValue || '')",
        "localizeTextValue(value)",
        "localizeTextValue(rawText)",
    }
    inline_literals = {
        line.strip()
        for line in source.splitlines()
        if "localizeTextValue('" in line
    }
    assert inline_literals <= allowed_literals


def _http_get(host: str, port: int, path: str) -> tuple[int, str]:
    connection = http.client.HTTPConnection(host, port, timeout=5)
    try:
        connection.request("GET", path)
        response = connection.getresponse()
        return response.status, response.read().decode("utf-8")
    finally:
        connection.close()


def _http_post(host: str, port: int, path: str, body: dict | None = None) -> tuple[int, str]:
    connection = http.client.HTTPConnection(host, port, timeout=5)
    try:
        payload = json.dumps(body or {}).encode("utf-8")
        connection.request(
            "POST",
            path,
            body=payload,
            headers={"Content-Type": "application/json", "Content-Length": str(len(payload))},
        )
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
    assert payload["ui_boundary"]["mutation_blocker_details"][0]["code"] == "write_routes_disabled"
    assert payload["ui_boundary"]["reviewer_context_requirements"]["required_fields"] == [
        "reviewer_label",
        "reviewer_kind",
        "ui_intent",
    ]
    assert payload["ui_boundary"]["reviewer_context_requirements"]["effective_required_fields"] == [
        "reviewer_label",
        "reviewer_kind",
        "ui_intent",
    ]
    assert payload["ui_boundary"]["reviewer_context_requirements"]["reviewer_label_pattern"] == (
        "^[a-z0-9][a-z0-9._-]{1,63}$"
    )
    assert payload["ui_boundary"]["reviewer_context_requirements"]["reviewer_label_examples"] == [
        "alice",
        "desk-operator.01",
    ]
    assert payload["ui_boundary"]["reviewer_context_requirements"]["session_label_required"] is False
    assert payload["ui_boundary"]["reviewer_context_requirements"]["session_label_pattern"] == (
        "^[a-z0-9][a-z0-9._-]{1,63}$"
    )
    assert payload["ui_boundary"]["write_route_contract"]["route_template"] == "/api/review-actions/<event_id>/<action>"
    assert payload["ui_boundary"]["write_route_contract"]["actions"] == [
        "approve",
        "reject",
        "request-changes",
    ]
    assert payload["ui_boundary"]["write_route_contract"]["blocked_status_code"] == 403
    assert payload["ui_boundary"]["write_route_contract"]["identity_proof_contract"]["proof_status"] == "local_operator_advisory"
    assert payload["ui_boundary"]["auth_boundary_summary"]["status"] == "auth_not_enabled"
    assert "auth_not_enabled" in payload["ui_boundary"]["auth_boundary_summary"]["blockers"]
    assert payload["ui_boundary"]["auth_boundary_summary"]["blocker_details"] == [
        {"code": "auth_not_enabled", "message": "Define explicit local auth boundary."},
        {"code": "authorization_not_enabled", "message": "Define authorization semantics for reviewer actions."},
    ]


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
    assert payload["ui_boundary"]["reviewer_context_requirements"]["session_label_required"] is True
    assert payload["ui_boundary"]["reviewer_context_requirements"]["effective_required_fields"] == [
        "reviewer_label",
        "reviewer_kind",
        "ui_intent",
        "session_label",
    ]
    assert payload["ui_boundary"]["reviewer_context_requirements"]["accepted_reviewer_kinds"] == [
        "local_operator"
    ]
    assert payload["ui_boundary"]["write_route_contract"]["identity_proof_contract"]["proof_status"] == "session_gated_local_operator"
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


def test_startup_metadata_with_enabled_ui_mutation(tmp_path):
    metadata = build_startup_metadata(
        host="127.0.0.1",
        port=8765,
        root=tmp_path,
        mutation_capability_flag=True,
        enable_ui_mutation=True,
        auth_mode=UIAuthMode.LOOPBACK_LOCAL,
        authorization_mode=UIAuthorizationMode.REVIEWER_DECLARED,
    )
    payload = json.loads(metadata.to_json())
    assert payload["mutation_enabled"] is True
    assert payload["ui_boundary"]["mutation_enabled"] is True
    assert payload["ui_boundary"]["read_only"] is False
    assert payload["ui_boundary"]["mutation_readiness_status"] == "enabled"
    assert payload["ui_boundary"]["mutation_blockers"] == []


def test_mutation_readiness_summary_can_reach_enablement_ready(tmp_path):
    _populate(tmp_path)
    review_service = ReviewService(tmp_path)
    for entry in review_service.queue():
        review_service.approve(
            event_id=entry.target_event_id,
            reviewer="alice",
            reviewer_kind=ReviewerIdentityKind.LOCAL_OPERATOR,
            session_label="ui-ready-session",
            note="approved for readiness coverage",
        )
    service = ChronicleUIDataService(
        tmp_path,
        mutation_capability_flag=True,
        enable_ui_mutation=True,
        auth_mode=UIAuthMode.LOOPBACK_LOCAL,
        authorization_mode=UIAuthorizationMode.REVIEWER_DECLARED,
    )

    readiness = service.mutation_readiness_summary()

    assert readiness["enablement_ready"] is True
    assert readiness["enablement_satisfied_count"] == readiness["enablement_required_count"] == 6
    assert all(check["satisfied"] is True for check in readiness["enablement_checks"])
    assert readiness["operational_readiness"]["status"] == "ready"
    assert readiness["operational_readiness"]["remaining_count"] == 0


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
    assert overview["auth_boundary_summary"]["blocker_details"][0] == {
        "code": "auth_not_enabled",
        "message": "Define explicit local auth boundary.",
    }
    assert overview["auth_boundary_overview"]["auth_warning_count"] == 3
    assert overview["auth_boundary_overview"]["authorization_warning_count"] == 3
    assert overview["auth_boundary_overview"]["missing_identity_count"] == 3
    assert overview["auth_boundary_overview"]["review_capability_counts"]["advisory_only"] == 3
    assert overview["auth_boundary_overview"]["provider_response_present_count"] == 0
    assert overview["identity_boundary_summary"]["status"] == "identity_unavailable"
    assert overview["identity_boundary_summary"]["missing_identity_count"] == 3
    assert overview["mutation_readiness"]["status"] == "preview_only"
    assert "Define explicit local auth boundary." in overview["mutation_readiness"]["next_steps"]
    assert overview["mutation_readiness"]["blocker_details"][0]["code"] == "write_routes_disabled"
    assert overview["mutation_readiness"]["pending_boundary_warning_counts"]["reviewer_identity_missing"] == 3
    assert overview["mutation_readiness"]["enablement_ready"] is False
    assert overview["mutation_readiness"]["enablement_satisfied_count"] == 1
    assert overview["mutation_readiness"]["enablement_required_count"] == 6
    assert overview["mutation_readiness"]["operational_readiness"]["status"] == "blocked"
    assert overview["mutation_readiness"]["operational_readiness"]["remaining_count"] == 5
    assert overview["mutation_readiness"]["enablement_checks"][0]["code"] == "mutation_capability_flag"
    assert overview["mutation_readiness"]["enablement_checks"][0]["satisfied"] is False
    assert overview["mutation_readiness"]["reviewer_context_requirements"]["required_fields"] == [
        "reviewer_label",
        "reviewer_kind",
        "ui_intent",
    ]
    assert overview["runtime_records_summary"]["kind_counts"]["summary"] == 1
    assert overview["runtime_records_summary"]["kind_counts"]["retrieval_plan"] == 1
    assert overview["runtime_records_summary"]["auth_readiness_counts"]["advisory_only"] == 2
    assert overview["runtime_records_summary"]["mutation_readiness_counts"]["preview_only"] == 2
    assert overview["runtime_records_summary"]["mutation_operational_counts"]["blocked"] == 2
    assert overview["runtime_records_summary"]["provider_response_present_count"] == 0
    assert overview["runtime_records_summary"]["provider_response_absent_count"] == 2
    assert overview["summary_jobs_summary"]["status_counts"]["pending_review"] == 1
    assert overview["summary_jobs_summary"]["review_capability_counts"]["advisory_only"] == 1
    assert overview["summary_jobs_summary"]["auth_readiness_counts"]["advisory_only"] == 1
    assert overview["summary_jobs_summary"]["package_readiness_counts"]["no_context_records"] == 1
    assert overview["summary_jobs_summary"]["mutation_readiness_counts"]["preview_only"] == 1
    assert overview["summary_jobs_summary"]["mutation_operational_counts"]["blocked"] == 1
    assert overview["summary_jobs_summary"]["provider_response_present_count"] == 0
    assert overview["summary_jobs_summary"]["identity_assurance_counts"]["unknown"] == 1
    assert overview["summary_jobs_summary"]["reviewer_kind_counts"]["unknown"] == 1
    assert overview["summary_jobs_summary"]["runtime_provider_counts"]["disabled"] == 1
    assert overview["summary_jobs_summary"]["summary_source_total"] == 0
    assert overview["triage"]["needs_attention_reviews"] == 3
    assert overview["triage"]["runtime_record_kinds"]["summary"] == 1
    assert overview["triage"]["runtime_record_kinds"]["retrieval_plan"] == 1
    assert overview["triage"]["review_capability_counts"]["advisory_only"] == 3
    assert overview["triage"]["package_readiness_counts"]["package_context_available"] >= 1
    assert overview["triage"]["provider_response_present_reviews"] == 0


def test_ui_data_service_read_endpoints(tmp_path):
    ids = _populate(tmp_path)
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
    runtime_summary_row = next(
        row
        for row in service.runtime_records()["runtime_records"]
        if row["event_id"] == ids["runtime_summary_event_id"]
    )
    assert runtime_summary_row["review_target_event_id"] == ids["runtime_summary_event_id"]
    assert runtime_summary_row["action_preview_summary"]["status"] == "preview_only"
    assert runtime_summary_row["mutation_enablement_summary"]["status"] == "preview_only"
    assert runtime_summary_row["mutation_enablement_summary"]["blocked_status_code"] == 403
    assert runtime_summary_row["mutation_enablement_summary"]["identity_proof_status"] == "local_operator_advisory"
    assert len(service.review_queue()["review_queue"]) == 3
    assert len(service.summary_jobs_list()["summary_jobs"]) == 1
    assert service.summary_jobs_list()["summary_jobs"][0]["summary_job_id"].startswith("sum_")
    assert service.summary_jobs_list()["summary_jobs"][0]["review_target_event_id"].startswith("evt_")
    assert service.summary_jobs_list()["summary_jobs"][0]["review_capability_status"] == "advisory_only"
    assert service.summary_jobs_list()["summary_jobs"][0]["auth_readiness_status"] == "advisory_only"
    assert service.summary_jobs_list()["summary_jobs"][0]["package_readiness_status"] == "no_context_records"
    assert service.summary_jobs_list()["summary_jobs"][0]["cli_parity_status"] == "aligned"
    assert service.summary_jobs_list()["summary_jobs"][0]["action_preview_summary"]["status"] == "preview_only"
    assert service.summary_jobs_list()["summary_jobs"][0]["action_preview_summary"]["success_contract"]["follow_up_commands"][0] == "chronicle review queue --include-resolved --json"
    assert service.summary_jobs_list()["summary_jobs"][0]["action_preview_summary"]["write_route_contract"]["route_template"] == "/api/review-actions/<event_id>/<action>"
    assert service.summary_jobs_list()["summary_jobs"][0]["identity_assurance_status"] == "unknown"
    assert service.summary_jobs_list()["summary_jobs"][0]["mutation_enablement_summary"]["status"] == "preview_only"
    assert service.summary_jobs_list()["summary_jobs"][0]["mutation_enablement_summary"]["remaining_count"] >= 1
    assert service.runtime_config_state()["runtime_config"]["config"]["provider_name"] == "ui-local"
    assert service.review_queue()["review_queue"][0]["review_preview_only"] is True
    assert service.review_queue()["review_queue"][0]["target_event_id"].startswith("evt_")
    assert service.review_queue()["review_queue"][0]["review_capability"]["status"] == "advisory_only"
    assert service.review_queue()["review_queue"][0]["auth_boundary_notice"]["status"] == "advisory_only"
    assert service.review_queue()["review_queue"][0]["package_readiness_summary"]["label"].startswith("package:")
    assert service.review_queue()["review_queue"][0]["package_readiness_summary"]["message"]
    assert service.review_queue()["review_queue"][0]["action_preview_summary"]["status"] == "preview_only"
    assert service.review_queue()["review_queue"][0]["action_preview_summary"]["success_contract"]["transaction_status"] == "decision_and_audit_persisted"
    assert service.review_queue()["review_queue"][0]["action_preview_summary"]["write_route_contract"]["expected_request_fields"] == [
        "reviewer_label",
        "reviewer_kind",
        "ui_intent",
    ]
    assert service.review_queue()["review_queue"][0]["action_preview_summary"]["actions"][0]["post_path"].startswith(
        "/api/review-actions/evt_"
    )
    assert service.review_queue()["review_queue"][0]["mutation_enablement_summary"]["operational_status"] == "blocked"
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


def test_ui_data_service_exposes_provider_response_metadata_in_read_only_views(tmp_path, monkeypatch):
    ChronicleService(tmp_path).init("UI Response Metadata")
    RuntimeConfigService(tmp_path).set_http(
        base_url="https://runtime.example.invalid/v1",
        model_name="manual-http-model",
        api_key_env="OPENAI_API_KEY",
        allow_network=True,
    )
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(
        RuntimeService,
        "_invoke_http_operation",
        staticmethod(
            lambda **_kwargs: {
                "output_text": "HTTP provider output for UI metadata visibility.",
                "response_id": "resp_ui_metadata",
                "finish_reason": "stop",
                "provider_status": "ok",
                "usage": {"input_tokens": 14, "output_tokens": 7, "total_tokens": 21},
            }
        ),
    )

    result = RuntimeService(tmp_path).invoke(
        text="Summarize this runtime output for the read-only UI.",
        operation="summarize",
        record=True,
        execute_configured_provider=True,
        draft_summary_title="HTTP UI Summary Draft",
    )
    service = ChronicleUIDataService(tmp_path)

    runtime_row = next(
        row for row in service.runtime_records()["runtime_records"] if row["event_id"] == result.event_id
    )
    assert runtime_row["response_metadata_summary"] == {
        "present": True,
        "response_id": "resp_ui_metadata",
        "finish_reason": "stop",
        "provider_status": "ok",
        "usage_input_tokens": 14,
        "usage_output_tokens": 7,
        "usage_total_tokens": 21,
        "metadata_count": 6,
        "response_key_count": 5,
        "response_keys": [
            "finish_reason",
            "output_text",
            "provider_status",
            "response_id",
            "usage",
        ],
    }

    summary_job_row = service.summary_jobs_list()["summary_jobs"][0]
    assert summary_job_row["response_metadata_summary"]["response_id"] == "resp_ui_metadata"
    assert summary_job_row["response_metadata_summary"]["usage_output_tokens"] == 7
    assert summary_job_row["response_metadata_summary"]["response_key_count"] == 5

    review_row = service.review_queue()["review_queue"][0]
    assert review_row["response_metadata_summary"]["response_id"] == "resp_ui_metadata"
    assert review_row["response_metadata_summary"]["finish_reason"] == "stop"
    assert review_row["response_metadata_summary"]["usage_total_tokens"] == 21

    overview = service.overview()
    assert overview["runtime_records_summary"]["provider_response_present_count"] == 1
    assert overview["runtime_records_summary"]["provider_response_finish_reason_counts"]["stop"] == 1
    assert overview["runtime_records_summary"]["provider_response_status_counts"]["ok"] == 1
    assert overview["runtime_records_summary"]["mutation_readiness_counts"]["preview_only"] == 1
    assert overview["auth_boundary_overview"]["provider_response_present_count"] == 1
    assert overview["auth_boundary_overview"]["provider_response_finish_reason_counts"]["stop"] == 1
    assert overview["auth_boundary_overview"]["provider_response_status_counts"]["ok"] == 1
    assert overview["summary_jobs_summary"]["provider_response_present_count"] == 1
    assert overview["summary_jobs_summary"]["provider_response_finish_reason_counts"]["stop"] == 1
    assert overview["summary_jobs_summary"]["provider_response_status_counts"]["ok"] == 1
    assert overview["summary_jobs_summary"]["mutation_readiness_counts"]["preview_only"] == 1
    assert overview["triage"]["provider_response_present_reviews"] == 1

    runtime_detail = service.detail_payload(f"/api/runtime-records/{result.event_id}")
    assert runtime_detail is not None
    assert runtime_detail["record"]["response_metadata_summary"]["finish_reason"] == "stop"
    assert runtime_detail["record"]["runtime_record_preview"]["record_kind"] == "execution"
    assert any(
        link["path"] == f"/api/summary-jobs/{summary_job_row['summary_job_id']}"
        for link in runtime_detail["record"]["related_links"]
    )

    summary_detail = service.detail_payload(f"/api/summary-jobs/{summary_job_row['summary_job_id']}")
    assert summary_detail is not None
    assert summary_detail["record"]["response_metadata_summary"]["usage_total_tokens"] == 21

    review_detail = service.detail_payload(f"/api/review-queue/{result.event_id}")
    assert review_detail is not None
    assert review_detail["record"]["response_metadata_summary"]["provider_status"] == "ok"


def test_ui_html_filtering_includes_provider_response_metadata_fields(tmp_path, monkeypatch):
    ChronicleService(tmp_path).init("UI Metadata Filter")
    RuntimeConfigService(tmp_path).set_http(
        base_url="https://runtime.example.invalid/v1",
        model_name="manual-http-model",
        api_key_env="OPENAI_API_KEY",
        allow_network=True,
    )
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(
        RuntimeService,
        "_invoke_http_operation",
        staticmethod(
            lambda **_kwargs: {
                "output_text": "HTTP provider output for filter visibility.",
                "response_id": "resp_filter_ui",
                "finish_reason": "stop",
                "provider_status": "ok",
                "usage": {"input_tokens": 18, "output_tokens": 8, "total_tokens": 26},
            }
        ),
    )

    RuntimeService(tmp_path).invoke(
        text="Summarize this runtime output for filter coverage.",
        operation="summarize",
        record=True,
        execute_configured_provider=True,
        draft_summary_title="HTTP Filter Summary Draft",
    )

    html = ChronicleUIDataService(tmp_path).html_shell()

    assert "responseMetadata.response_id || ''" in html
    assert "responseMetadata.finish_reason || ''" in html
    assert "responseMetadata.provider_status || ''" in html
    assert "String(responseMetadata.usage_total_tokens ?? '')" in html
    assert "...(Array.isArray(responseMetadata.response_keys) ? responseMetadata.response_keys : [])" in html
    assert "sliceBadge(label('overview.provider_response', 'Provider response')" in html
    assert "summaryJsonLine('Provider finish reasons', authBoundaryOverview.provider_response_finish_reason_counts)" in html
    assert "summaryJsonLine('Provider statuses', authBoundaryOverview.provider_response_status_counts)" in html
    assert "summaryJsonLine('Provider finish reasons', runtimeRecords.provider_response_finish_reason_counts)" in html
    assert "summaryJsonLine('Provider statuses', summaryJobs.provider_response_status_counts)" in html
    assert "summaryJsonLine('Mutation readiness counts', runtimeRecords.mutation_readiness_counts)" in html
    assert "summaryJsonLine('Mutation operational counts', runtimeRecords.mutation_operational_counts)" in html
    assert "summaryJsonLine('Mutation readiness counts', summaryJobs.mutation_readiness_counts)" in html
    assert "summaryJsonLine('Mutation operational counts', summaryJobs.mutation_operational_counts)" in html
    assert "function renderPreviewContractSummary(preview, previewTarget = 'action-preview-response')" in html
    assert "function mutationEnablementBadge(summary)" in html
    assert "function renderMutationEnablementSummary(summary)" in html
    assert "function sliceButtonRow(buttons)" in html
    assert "function filterValueLabel(target, value)" in html
    assert "function reviewQueueSliceButtons()" in html
    assert "function runtimeRecordsSliceButtons()" in html
    assert "function summaryJobsSliceButtons()" in html
    assert 'id="locale-select"' in html
    assert "const uiI18nCatalog =" in html
    assert "function setLocale(locale, rerender = true)" in html
    assert "applyLocaleToPage();" in html
    assert "Chronicle Stack ローカルUI" in html
    assert "button.copy_recovery_cli" in html
    assert "rollback=" in html
    assert "transaction=" in html
    assert "durable-on-failure=" in html
    assert "write-route=" in html
    assert "request-fields=" in html
    assert "success-status=" in html
    assert "blocked-status=" in html
    assert "proof-status=" in html
    assert "proof-fields=" in html
    assert "errors=" in html
    assert "follow-up=" in html
    assert "detailLine('Enablement ready', mutationReadiness.enablement_ready)" in html
    assert "detailLine('Operational readiness', operationalReadiness.status || '')" in html
    assert "detailListLine('Remaining checks', (operationalReadiness.unsatisfied_checks || []).map(item => ((item.label || item.code || 'check') + ': ' + (item.detail || ''))), ' | ')" in html
    assert "detailListLine('Enablement checks', enablementChecks.map(check => ((check.satisfied ? 'ok: ' : 'blocked: ') + (check.label || check.code || 'check'))), ' | ')" in html
    assert "function renderMutationEnablementNotice(record)" in html
    assert "label('notice.mutation_enablement', 'Mutation Enablement')" in html
    assert "detailListLine('Blocker sources', blockerSummaries.map(item => ((item.source || 'unknown') + ':' + (item.code || 'blocker') + '=' + String(item.affected_count ?? 0))), ' | ')" in html
    assert "detailLine('Reviewer label pattern', reviewerContext.reviewer_label_pattern || '')" in html
    assert "detailLine('Write route', writeRouteContract.route_template || '')" in html
    assert "detailListLine('Write request fields', writeRouteContract.expected_request_fields, ' | ')" in html
    assert "detailListLine('Effective reviewer fields', reviewerContextRequirements.effective_required_fields, ' | ')" in html
    assert "Review queue blocked-route preview stays read-only and returns the CLI fallback contract." in html
    assert "Runtime-record blocked-route preview stays read-only and returns the CLI fallback contract." in html
    assert "Local mutation is enabled for this runtime-record list view." in html


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
    assert summary_detail["action_preview"]["success_contract"]["rollback_status"] == "not_required"
    assert summary_detail["action_preview"]["write_route_contract"]["blocked_status_code"] == 403
    assert summary_detail["action_preview"]["write_route_contract"]["identity_proof_contract"]["required_identity_fields"] == [
        "reviewer_label",
        "reviewer_kind",
        "ui_intent",
    ]
    assert summary_detail["mutation_enablement"]["enablement_ready"] is False
    assert summary_detail["mutation_enablement"]["operational_readiness"]["status"] == "blocked"
    assert any(item["source"] == "boundary" for item in summary_detail["mutation_enablement"]["blocker_summaries"])
    assert summary_detail["mutation_enablement"]["write_route_contract"]["route_template"] == "/api/review-actions/<event_id>/<action>"
    assert any(link["path"] == f"/api/review-queue/{summary_detail['review_target_event_id']}" for link in summary_detail["related_links"])
    runtime_detail = service.detail_payload(f"/api/runtime-records/{ids['runtime_summary_event_id']}")["record"]
    assert "runtime_summary" in runtime_detail["payload"]
    assert runtime_detail["runtime_record_preview"]["record_kind"] == "summary"
    assert runtime_detail["auth_boundary_notice"]["status"] == "advisory_only"
    assert runtime_detail["mutation_enablement"]["enablement_ready"] is False
    assert runtime_detail["mutation_enablement"]["operational_readiness"]["remaining_count"] >= 1
    assert any(item["source"] == "review_queue" for item in runtime_detail["mutation_enablement"]["blocker_summaries"])
    assert runtime_detail["mutation_enablement"]["write_route_contract"]["success_status_code"] == 200
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
    assert review_detail["mutation_enablement"]["enablement_ready"] is False
    assert review_detail["mutation_enablement"]["blocker_summaries"]
    assert review_detail["mutation_enablement"]["write_route_contract"]["actions"] == [
        "approve",
        "reject",
        "request-changes",
    ]
    assert review_detail["mutation_enablement"]["operational_readiness"]["unsatisfied_checks"]
    assert review_detail["action_preview"]["success_contract"]["follow_up_commands"][0] == "chronicle review queue --include-resolved --json"
    assert review_detail["action_preview"]["write_route_contract"]["success_status_code"] == 200
    assert review_detail["action_preview"]["write_route_contract"]["identity_proof_contract"]["proof_status"] == "local_operator_advisory"
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
    assert review_detail["action_preview"]["actions"][0]["post_path"] == (
        f"/api/review-actions/{ids['runtime_summary_event_id']}/approve"
    )
    assert review_detail["action_preview"]["actions"][0]["post_expected_status"] == 403
    assert review_detail["action_preview"]["actions"][0]["post_expected_error_code"] == "mutation_disabled"
    assert review_detail["action_preview"]["failure_contract"]["rollback_status"] == "fail_closed"
    assert review_detail["action_preview"]["failure_contract"]["durable_mutation_reported_on_failure"] is False
    assert review_detail["action_preview"]["failure_contract"]["recovery_commands"] == [
        f"chronicle review approve --event {ids['runtime_summary_event_id']}"
    ]
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
    assert "identity_assurance_counts" in overview["summary_jobs_summary"]
    assert "identity_assurance_status" in service.summary_jobs_list()["summary_jobs"][0]


def test_ui_detail_exposes_enabled_mutation_preview_when_enabled(tmp_path):
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
        mutation_capability_flag=True,
        enable_ui_mutation=True,
        auth_mode=UIAuthMode.LOOPBACK_LOCAL,
        authorization_mode=UIAuthorizationMode.REVIEWER_DECLARED,
    )

    review_detail = service.detail_payload(f"/api/review-queue/{ids['runtime_summary_event_id']}")["record"]

    assert review_detail["action_preview"]["status"] == "enabled"
    assert review_detail["action_preview"]["ui_mutation_enabled"] is True
    assert review_detail["action_preview"]["actions"][0]["post_expected_status"] == 200
    assert review_detail["action_preview"]["actions"][0]["post_expected_error_code"] is None
    assert review_detail["action_preview"]["failure_contract"]["rollback_status"] == "fail_closed"
    assert review_detail["action_preview"]["failure_contract"]["recovery_commands"] == [
        f"chronicle review approve --event {ids['runtime_summary_event_id']}"
    ]
    assert review_detail["ui_mutation_enabled"] is True
    assert review_detail["review_preview_only"] is False


def test_summary_jobs_list_exposes_enabled_mutation_state_when_enabled(tmp_path):
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
        mutation_capability_flag=True,
        enable_ui_mutation=True,
        auth_mode=UIAuthMode.LOOPBACK_LOCAL,
        authorization_mode=UIAuthorizationMode.REVIEWER_DECLARED,
    )

    rows = service.summary_jobs_list()["summary_jobs"]
    assert rows[0]["ui_mutation_enabled"] is True
    assert rows[0]["review_preview_only"] is False
    assert rows[0]["action_preview_summary"]["status"] == "enabled"


def test_ui_shell_contains_interactive_local_ui(tmp_path):
    ChronicleService(tmp_path).init("UI Shell")

    html = ChronicleUIDataService(tmp_path).html_shell()

    assert "Chronicle Stack ローカルUI" in html
    assert "読み取り専用の前景ローカルUIです。" in html
    assert ".shell-grid {" in html
    assert "#detail { position: sticky;" in html
    assert "@media (max-width: 980px)" in html
    assert '<div class="shell-grid">' in html
    assert ".json-block {" in html
    assert ".fact-line {" in html
    assert ".fact-label {" in html
    assert ".fact-value {" in html
    assert ".notice-section {" in html
    assert ".fold-section {" in html
    assert ".cell-title {" in html
    assert ".cell-meta {" in html
    assert ".cell-stack > * + *" in html
    assert ".cell-details {" in html
    assert ".cell-details-body > * + *" in html
    assert ".cell-actions {" in html
    assert "loadDetail" in html
    assert "label('notice.runtime_preview', 'Runtime Preview')" in html
    assert "label('notice.retrieval_handoff', 'Retrieval Handoff')" in html
    assert "label('notice.invocation_plan', 'Invocation Plan')" in html
    assert "label('notice.package_handoff_preview', 'Package Handoff Preview')" in html
    assert "label('notice.review_package_readiness', 'Review Package Readiness')" in html
    assert "label('notice.related_links', 'Related Links')" in html
    assert "label('button.back_current_list', 'Back to current list')" in html
    assert "label('button.back_previous_detail', 'Back to previous detail')" in html
    assert "currentFilterLabel" in html
    assert "stateLabel('filter', value, filterValueLabel(target, value))" in html
    assert "hasActiveFilters" in html
    assert "resetFilters" in html
    assert "currentSortValue" in html
    assert "stateLabel" in html
    assert "currentSortLabel" in html
    assert "function sortValueLabel(endpoint, sortValue)" in html
    assert "stateLabel('sort', sortValue, sortValueLabel(endpoint, sortValue))" in html
    assert "warning-first:" in html
    assert "jumpBadge" in html
    assert "sourceCountBadges" in html
    assert "reviewWarningBadges" in html
    assert "const reviewWarningLabels =" in html
    assert "const uiLabelKeys =" in html
    assert "function uiLabel(text)" in html
    assert "function reviewWarningLabel(code)" in html
    assert "function detailMessages(items, fallbackItems = [])" in html
    assert "localizeTextValue(item.message || '')" in html
    assert "return fallback.map(item => reviewWarningLabel(item)).join(' | ') || '';" in html
    assert "function contractDetailLines(successContract, failureContract, targetId)" in html
    assert "function renderReviewActionResultPanel(title, responseStatus, path, payload, targetId, options = {})" in html
    assert "function renderReviewMutationForm(title, prefix)" in html
    assert "function renderPreviewSummary(preview)" in html
    assert "localizeTextValue(preview.message || '')" in html
    assert "function renderPreviewButtons(previewActions, options = {})" in html
    assert "function authReadinessBadge(status)" in html
    assert "function identityAssuranceBadge(status)" in html
    assert "function summaryReviewStatusBadge(status)" in html
    assert "function renderRuntimeRecordRow(row, endpoint)" in html
    assert "function renderReviewQueueRow(row, endpoint)" in html
    assert "function renderSummaryJobRow(row, endpoint)" in html
    assert "function renderRuntimeRecordsTable(endpoint, rows)" in html
    assert "function renderReviewQueueTable(endpoint, rows)" in html
    assert "function renderSummaryJobsTable(endpoint, rows)" in html
    assert "function renderGenericTable(endpoint, rows)" in html
    assert "const endpointRenderers =" in html
    assert "reviewerIdentityBadge" in html
    assert "sortSelect" in html
    assert "sortRuntimeRows" in html
    assert "function mutationSummaryRank(summary)" in html
    assert "function authStatusRank(status)" in html
    assert "includesQuery" in html
    assert "endpointFilterTargets" in html
    assert "endpointSortDefaults" in html
    assert "endpointFilterTarget" in html
    assert "currentFilterValue" in html
    assert "setFilterValue" in html
    assert "setSortValue" in html
    assert "compareReviewerLabel" in html
    assert "compareReviewTargetDesc" in html
    assert "sortReviewRows" in html
    assert "compareSummaryJobDesc" in html
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
    assert "Auth Boundary Warnings" in html
    assert "Authorization warnings" in html
    assert "Missing identity" in html
    assert "Session label required" in html
    assert "Declared identity only" in html
    assert "Mutation capability flag:" in html
    assert "currentTrailLabel" in html
    assert "currentTrailButtons" in html
    assert "sliceBadge" in html
    assert "sliceChip" in html
    assert "filterChips(target, cls)" in html
    assert "listJumpButton" in html
    assert "sectionTitle" in html
    assert "moreSliceButton" in html
    assert "function renderNotice(title, body)" in html
    assert "function renderNavigationNotice(endpoint, record, options = {})" in html
    assert "function renderRuntimePreviewNotice(record)" in html
    assert "function renderAuthReadinessNotice(record)" in html
    assert "function renderDetailActionPreviewControls(preview, actions, mutationTargetEventId)" in html
    assert "function renderDetailActionPreviewList(preview, actions)" in html
    assert "function renderDetailActionPreviewNotice(record)" in html
    assert "async function responseJsonOrEmpty(response)" in html
    assert "async function postJson(path, body = undefined)" in html
    assert "function appendCommandFeedback(target, command, copied)" in html
    assert "async function tryCopyText(command)" in html
    assert "function reviewActionRequestBody(action, fieldPrefix = 'reviewer')" in html
    assert "function reloadCurrentEndpoint()" in html
    assert "function handleViewClick(event)" in html
    assert "function handleDetailClick(event)" in html
    assert "function handleViewInput(event)" in html
    assert "function handleViewChange(event)" in html
    assert "function renderPanel(body)" in html
    assert "function renderOverviewHeaderPanel(chronicle)" in html
    assert "function renderOverviewCountsPanel(counts)" in html
    assert "function renderOverviewRuntimeBoundaryPanel(runtime)" in html
    assert "function renderOverviewAuthBoundaryPanel(authBoundary, authBoundaryOverview)" in html
    assert "function renderOverviewIdentityBoundaryPanel(identityBoundary)" in html
    assert "function renderOverviewRuntimeRecordsPanel(counts, runtimeRecords)" in html
    assert "function renderOverviewSummaryJobsPanel(counts, summaryJobs)" in html
    assert "function renderOverviewTriagePanel(triage, warningButtons, warningSummaries)" in html
    assert "function overviewWarningButtons(warningSummaries)" in html
    assert "const overviewPanelRenderers = [" in html
    assert "function renderOverviewPanels(data)" in html
    assert "const detailPathResolvers =" in html
    assert "function endpointBody(endpoint, payload)" in html
    assert "function detailNavigationOptions(endpoint, record)" in html
    assert "const detailNoticeRenderers = [" in html
    assert "function renderDetailNotices(record)" in html
    assert "function detailNoticeBody(endpoint, record)" in html
    assert "function detailBody(endpoint, payload)" in html
    assert "function previewButtonsConfig(row, config)" in html
    assert "function detailJsonButton(endpoint, row)" in html
    assert "function stackedCell(parts, separator = '<br>')" in html
    assert "function cellTitle(text)" in html
    assert "function cellMeta(text)" in html
    assert "function cellStack(parts)" in html
    assert "function cellDetails(summary, parts, open = false)" in html
    assert "function responseSummaryLine(responseMetadata)" in html
    assert "function previewCell(preview, previewActions, options)" in html
    assert "function reviewerCell(identity, fallbackLabel = '')" in html
    assert "function summaryIdentityCell(identityBadge, reviewerIdentity)" in html
    assert "function resetFilterButton(query, target)" in html
    assert "function emptyFilterState(query, rows, message)" in html
    assert "function listToolbar(endpoint, target, placeholder, sortOptions, filterChipHtml, query)" in html
    assert "function actionPreviewStatus(targetId, mutationEnabled, enabledMessage, disabledMessage)" in html
    assert "function tableHtml(headers, body)" in html
    assert "function packageReviewButtons(record)" in html
    assert "function runtimeRelatedButtons(record)" in html
    assert "function reviewRelatedButtons(record)" in html
    assert "function summaryRelatedButtons(record)" in html
    assert "function renderCliParityNotice(record)" in html
    assert "function renderReviewTimelineNotice(record)" in html
    assert "sectionTitle" in html
    assert "detailLine" in html
    assert "detailListLine" in html
    assert "summaryJsonLine" in html
    assert "messageParagraph" in html
    assert "localizeTextValue(message || '')" in html
    assert "statusMessageBody" in html
    assert "routeHeading" in html
    assert "prettyJsonPre" in html
    assert "function collapsibleJsonBlock(summaryLabel, value, open = false)" in html
    assert "function noticeSection(title, body)" in html
    assert "function collapsibleSection(title, body, open = false)" in html
    assert "label('button.actions', 'Actions')" in html
    assert "label('button.more_details', 'More details')" in html
    assert "label('label.record_json', 'Record JSON')" in html
    assert "label('label.response_json', 'Response JSON')" in html
    assert "label('label.table_detail', 'Detail')" in html
    assert "label('label.table_event', 'Event')" in html
    assert "label('label.table_latest_reviewer', 'Latest Reviewer')" in html
    assert "label('label.table_summary_job', 'Summary Job')" in html
    assert "label('section.recovery_contract', 'Recovery Contract')" in html
    assert "label('section.review_action', 'Review Action')" in html
    assert "label('section.action_result', 'Current Result')" in html
    assert "label('section.metrics', 'Metrics')" in html
    assert "detailListLine('Auth blockers', authBoundary.blockers, ' | ')" in html
    assert "summaryJsonLine('Identity assurance counts', identityBoundary.assurance_counts)" in html
    assert "summaryJsonLine('Auth review capability counts', authBoundaryOverview.review_capability_counts)" in html
    assert "runtimeRecordsFilterChips" in html
    assert "reviewQueueFilterChips" in html
    assert "summaryJobsFilterChips" in html
    assert "humanizeDetailPath" in html
    assert "label('notice.related_links', 'Related Links')" in html
    assert "__chronicleDetailTrail" in html
    assert "readinessBadge" in html
    assert "reviewCapabilityBadge" in html
    assert "packageReadinessBadge" in html
    assert "reviewParityBadge" in html
    assert "detailListLine('Blockers', mutationReadiness.blockers, ' | ')" in html
    assert "review_requested" in html
    assert "ready" in html
    assert "CLI Parity" in html
    assert "t('sort.review.parity')" in html
    assert "t('sort.runtime.latest')" in html
    assert "t('sort.review.attention')" in html
    assert "t('sort.review.reviewer')" in html
    assert "t('sort.summary.title')" in html
    assert "summaryJsonLine('CLI parity counts', triage.cli_parity_counts)" in html
    assert "summaryJsonLine('Identity assurance counts', triage.identity_assurance_counts)" in html
    assert "summaryJsonLine('Reviewer kind counts', triage.reviewer_kind_counts)" in html
    assert "summaryJsonLine('Warning counts', triage.warning_counts)" in html
    assert "summaryJsonLine('Status counts', summaryJobs.status_counts)" in html
    assert "summaryJsonLine('Auth readiness counts', runtimeRecords.auth_readiness_counts)" in html
    assert "summaryJsonLine('Auth readiness counts', summaryJobs.auth_readiness_counts)" in html
    assert "summaryJsonLine('Identity assurance counts', summaryJobs.identity_assurance_counts)" in html
    assert "summaryJsonLine('Reviewer kind counts', summaryJobs.reviewer_kind_counts)" in html
    assert "summaryJsonLine('Runtime provider counts', summaryJobs.runtime_provider_counts)" in html
    assert "detailListLine('Reviewer fields', reviewerContextRequirements.required_fields, ' | ')" in html
    assert "detailListLine('Accepted reviewer kinds', reviewerContextRequirements.accepted_reviewer_kinds, ' | ')" in html
    assert "detailLine('Session label required', reviewerContextRequirements.session_label_required)" in html
    assert "function renderResponseMetadataNotice(record)" in html
    assert "detailLine('Response ID', summary.response_id || '')" in html
    assert "detailLine('Usage total tokens', summary.usage_total_tokens ?? '')" in html
    assert '"Action": "操作"' in html
    assert '"Rollback status": "ロールバック状態"' in html
    assert '"Response ID": "応答ID"' in html
    assert '"Read-only": "読み取り専用"' in html
    assert '"Runtime records": "ランタイム記録"' in html
    assert '"Audit ID": "監査ID"' in html
    assert '"GUI mutation remains disabled for this session; use the CLI review path instead.": "この session では GUI mutation は無効のままです。代わりに CLI review path を使ってください。"' in html
    assert '"Reviewer identity is self-declared only; UI auth is not enforcing reviewer identity.": "レビュアー本人性は自己申告のみで、UI 認証はレビュアー本人性を強制していません。"' in html
    assert "Runtime auth advisory" in html
    assert "Runtime mutation preview" in html
    assert "Summary advisory" in html
    assert "Summary auth advisory" in html
    assert "Summary package ready" in html
    assert "Summary identity aligned" in html
    assert "Summary mutation preview" in html
    assert "Runtime mutation preview" in html
    assert "Runtime auth advisory" in html
    assert "Runtime identity aligned" in html
    assert "Runtime retrieval plans" in html
    assert "Runtime provider response" in html
    assert "Summary mutation preview" in html
    assert "Summary package ready" in html
    assert "Summary provider response" in html
    assert "sliceButtonRow(runtimeRecordsSliceButtons())" in html
    assert "sliceButtonRow(summaryJobsSliceButtons())" in html
    assert "Review requested" in html
    assert "Review ready" in html
    assert "Review advisory" in html
    assert "CLI drift" in html
    assert "sliceButtonRow(reviewQueueSliceButtons())" in html
    assert "badge('slice:' + filterLabel, cls)" in html
    assert "' <span class=\"id\">' + esc(value) + '</span>'" in html
    assert "label('overview.warning_priority', 'Warning priority')" in html
    assert "reviewWarningLabel('ui_authorization_not_enabled')" in html
    assert "reviewWarningLabel('reviewer_session_label_missing')" in html
    assert "filterValueLabel('runtimeRecords', 'retrieval_plan')" in html
    assert "filterValueLabel('reviewQueue', 'response_id')" in html
    assert "summaryJsonLine('Runtime kinds', triage.runtime_record_kinds)" in html
    assert "statusMessageBody(readiness.status, readiness.message, readinessButtons)" in html
    assert "statusMessageBody(notice.status, notice.message, noticeButtons)" in html
    assert "statusMessageBody(assurance.status, assurance.message, assuranceButtons)" in html
    assert "messageParagraph(parity.message)" in html
    assert "detailListLine('Expected actions', parity.expected_actions)" in html
    assert "label('button.open_review_queue', 'Open Review Queue')" in html
    assert "label('button.open_runtime_records', 'Open Runtime Records')" in html
    assert "label('button.open_summary_jobs', 'Open Summary Jobs')" in html
    assert "label('button.open_runtime_config', 'Open Runtime Config')" in html
    assert "label('button.open_package_review', 'Open Package Review')" in html
    assert "buttons.push(listJumpButton(label('button.open_review_queue', 'Open Review Queue'), '/api/review-queue'));" in html
    assert "label('label.table_runtime', 'Runtime')" in html
    assert "label('label.table_target', 'Target')" in html
    assert "summary-jobs-action-preview-response" in html
    assert "Summary jobs blocked-route preview stays read-only and returns the CLI fallback contract." in html
    assert "Local mutation is enabled for this list view. Each action still requires explicit reviewer context and writes audit-backed review history." in html
    assert "Local mutation is enabled for summary-backed review targets. Actions still require explicit reviewer context and write audit-backed review history." in html
    assert "prefix) + '-reviewer-label" in html
    assert "prefix) + '-reviewer-kind" in html
    assert "prefix) + '-reviewer-session-label" in html
    assert "prefix) + '-reviewer-note" in html
    assert "reviewFieldValue(prefix, suffix, fallback = '')" in html
    assert "fieldPrefix: 'review-queue'" in html
    assert "fieldPrefix: 'summary-jobs'" in html
    assert "data-success-detail" in html
    assert "listToolbar(endpoint, 'summaryJobs', t('placeholder.summary_filter')" in html
    assert "{ value: 'mutation', label: t('sort.runtime.mutation') }" in html
    assert "{ value: 'auth', label: t('sort.runtime.auth') }" in html
    assert "sliceButtonRow(runtimeRecordsSliceButtons())" in html
    assert "sliceButtonRow(reviewQueueSliceButtons())" in html
    assert "sliceButtonRow(summaryJobsSliceButtons())" in html
    assert "label('label.table_review_route', 'Review Route')" in html
    assert "Auth aligned" in html
    assert "Auth advisory" in html
    assert "label('button.open_review', 'Open review')" in html
    assert "package:no_context_records" in html
    assert 'data-reset-filters="all"' in html
    assert "listJumpButton(filterValueLabel('reviewQueue', 'advisory'), '/api/review-queue', 'reviewQueue', 'advisory')" in html
    assert "listJumpButton(filterValueLabel('reviewQueue', 'aligned'), '/api/review-queue', 'reviewQueue', 'aligned')" in html
    assert "listJumpButton(filterValueLabel('reviewQueue', 'boundary_aligned'), '/api/review-queue', 'reviewQueue', 'boundary_aligned')" in html
    assert "listJumpButton(reviewWarningLabel('ui_auth_not_enabled'), '/api/review-queue', 'reviewQueue', 'ui_auth_not_enabled')" in html
    assert "listJumpButton(reviewWarningLabel('reviewer_identity_declared_only'), '/api/review-queue', 'reviewQueue', 'reviewer_identity_declared_only')" in html
    assert "listJumpButton(filterValueLabel('runtimeRecords', 'retrieval_plan'), '/api/runtime-records', 'runtimeRecords', 'retrieval_plan')" in html
    assert "data-detail-nav" in html
    assert "data-detail-trail" in html
    assert "data-back-view" in html
    assert "uiLabel('No matching runtime records for current filter.')" in html
    assert "uiLabel('No matching review rows for current filter.')" in html
    assert "uiLabel('No matching summary jobs for current filter.')" in html
    assert "CLI aligned" in html
    assert "Open Runtime Records" in html
    assert "Open Review Queue" in html
    assert "Open Package Review" in html
    assert "Review advisory" in html
    assert "Auth Boundary Warnings" in html
    assert "warnings.slice(0, 2).forEach" in html
    assert "function buttonRow(buttons)" in html
    assert "function moreStatusButtons(status, endpoint, filterTarget, prefix = '')" in html
    assert "const previewButtons = [" in html
    assert "const parityButtons = moreStatusButtons(parity.status, '/api/review-queue', 'reviewQueue');" in html
    assert "const assuranceButtons = moreStatusButtons(assurance.status, '/api/review-queue', 'reviewQueue');" in html
    assert "const readinessButtons = moreStatusButtons(readiness.status, '/api/review-queue', 'reviewQueue', 'package:');" in html
    assert "const timelineButtons = [" in html
    assert "Declared identity only" in html
    assert "listToolbar(endpoint, 'runtimeRecords', t('placeholder.runtime_filter')" in html
    assert "listToolbar(endpoint, 'reviewQueue', t('placeholder.review_filter')" in html
    assert "runtimeRecords" in html
    assert "reviewQueue" in html
    assert "listToolbar(endpoint, 'runtimeRecords', t('placeholder.runtime_filter')" in html
    assert "label('label.table_event', 'Event')" in html
    assert "label('label.table_kind', 'Kind')" in html
    assert "label('label.table_auth', 'Auth')" in html
    assert "label('label.table_preview', 'Preview')" in html
    assert "listToolbar(endpoint, 'reviewQueue', t('placeholder.review_filter')" in html
    assert "review-queue-action-preview-response" in html
    assert "Review queue blocked-route preview stays read-only and returns the CLI fallback contract." in html
    assert "previewTarget: 'review-queue-action-preview-response'" in html
    assert "__chronicleFilters" in html
    assert "summaryJobs: ''" in html
    assert "summaryJobs: 'latest'" in html
    assert "__chronicleSorts" in html
    assert "Active view:" in html
    assert "jumpBadge(" in html
    assert "label('notice.auth_readiness', 'Auth Readiness')" in html
    assert "label('notice.review_capability', 'Review Capability')" in html
    assert "label('notice.action_preview', 'Action Preview')" in html
    assert "uiLabel('Approve')" in html
    assert "uiLabel('Reject')" in html
    assert "uiLabel('Request Changes')" in html
    assert "uiLabel('Preview blocked route')" in html
    assert "data-preview-post" in html
    assert "Blocked route preview stays read-only and returns the CLI fallback contract." in html
    assert "uiLabel('Status: ')" in html
    assert "uiLabel('Route: ')" in html
    assert "uiLabel('No matching runtime records for current filter.')" in html
    assert "uiLabel('Chronicle ID')" in html
    assert "Rollback status" in html
    assert "Durable mutation on failure" in html
    assert "Possible errors" in html
    assert "Recovery commands" in html
    assert "Follow-up commands" in html
    assert "Transaction status" in html
    assert "Recovery path" in html
    assert "async function previewBlockedRoute(path, targetId = 'action-preview-response')" in html
    assert "async function copyCommand(command, targetId = 'action-preview-response')" in html
    assert "async function submitReviewAction(path, action, recordId, targetId = 'action-preview-response', fieldPrefix = 'reviewer', successDetail = '')" in html
    assert "data-submit-review-action" in html
    assert "data-copy-command" in html
    assert "t('button.copy_recovery_cli')" in html
    assert "Review Action Result" in html
    assert "uiLabel('POST enabled')" in html
    assert "reviewer-label" in html
    assert "reviewer-kind" in html
    assert "reviewer-session-label" in html
    assert "uiLabel('Reviewer')" in html
    assert "uiLabel('Kind')" in html
    assert "uiLabel('Session')" in html
    assert "uiLabel('Note')" in html
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
        assert "Declared identity only" in html
        assert "Session label required" in html
        assert "Declared Identity Only" in html

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

        status, body = _http_post(
            host,
            port,
            f"/api/review-actions/{ids['runtime_summary_event_id']}/approve",
        )
        assert status == 403
        payload = json.loads(body)
        assert payload["ok"] is False
        assert payload["status"] == "blocked"
        assert payload["event_id"] == ids["runtime_summary_event_id"]
        assert payload["action"] == "approve"
        assert payload["error_code"] == "mutation_disabled"
        assert payload["mutation_enabled"] is False
        assert payload["failure_contract"]["rollback_status"] == "fail_closed"
        assert payload["failure_contract"]["durable_mutation_reported_on_failure"] is False
        assert payload["failure_contract"]["recovery_commands"] == [
            f"chronicle review approve --event {ids['runtime_summary_event_id']}"
        ]
        assert payload["cli_equivalent"] == (
            f"chronicle review approve --event {ids['runtime_summary_event_id']}"
        )

        status, body = _http_post(
            host,
            port,
            f"/api/review-actions/{ids['runtime_summary_event_id']}/request-changes",
        )
        assert status == 403
        payload = json.loads(body)
        assert payload["action"] == "request-changes"
        assert payload["failure_contract"]["rollback_status"] == "fail_closed"
        assert payload["failure_contract"]["recovery_commands"] == [
            f"chronicle review request-changes --event {ids['runtime_summary_event_id']}"
        ]
        assert payload["cli_equivalent"] == (
            f"chronicle review request-changes --event {ids['runtime_summary_event_id']}"
        )

        status, review_console = _http_get(host, port, "/review-console")
        assert status == 200
        assert "Chronicle Stack Review Console" in review_console
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_http_review_action_enabled_route_applies_decision(tmp_path):
    ids = _populate(tmp_path)
    try:
        server = make_server(
            host="127.0.0.1",
            port=0,
            root=tmp_path,
            mutation_capability_flag=True,
            enable_ui_mutation=True,
            auth_mode=UIAuthMode.LOOPBACK_LOCAL,
            authorization_mode=UIAuthorizationMode.REVIEWER_DECLARED,
        )
    except PermissionError as exc:
        pytest.skip(f"local socket bind unavailable in this environment: {exc}")
    host, port = server.server_address
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        status, body = _http_post(
            host,
            port,
            f"/api/review-actions/{ids['runtime_summary_event_id']}/approve",
            {
                "reviewer_label": "alice",
                "reviewer_kind": "local_operator",
                "session_label": "ui-http-test",
                "ui_intent": "approve",
                "note": "approved from ui",
            },
        )
        assert status == 200
        payload = json.loads(body)
        assert payload["ok"] is True
        assert payload["status"] == "applied"
        assert payload["mutation_enabled"] is True
        assert payload["action"] == "approve"
        assert payload["audit_id"].startswith("aud_")
        assert payload["decision_event_id"].startswith("evt_")
        assert payload["success_contract"]["transaction_status"] == "decision_and_audit_persisted"
        assert payload["success_contract"]["rollback_status"] == "not_required"
        assert payload["success_contract"]["follow_up_commands"][0] == "chronicle review queue --include-resolved --json"

        history = ReviewService(tmp_path).history(event_id=ids["runtime_summary_event_id"])
        assert history[0].disposition.value == "approve"
        assert history[0].reviewer_identity.kind.value == "local_operator"
        assert history[0].reviewer_identity.session_label == "ui-http-test"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_http_review_action_enabled_route_handles_audit_failure(tmp_path, monkeypatch):
    ids = _populate(tmp_path)

    def _broken_audit_record(self, *args, **kwargs):
        raise RuntimeError("audit insert boom")

    monkeypatch.setattr(AuditService, "record", _broken_audit_record)
    try:
        server = make_server(
            host="127.0.0.1",
            port=0,
            root=tmp_path,
            mutation_capability_flag=True,
            enable_ui_mutation=True,
            auth_mode=UIAuthMode.LOOPBACK_LOCAL,
            authorization_mode=UIAuthorizationMode.REVIEWER_DECLARED,
        )
    except PermissionError as exc:
        pytest.skip(f"local socket bind unavailable in this environment: {exc}")
    host, port = server.server_address
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        status, body = _http_post(
            host,
            port,
            f"/api/review-actions/{ids['runtime_summary_event_id']}/approve",
            {
                "reviewer_label": "alice",
                "reviewer_kind": "local_operator",
                "session_label": "ui-http-test",
                "ui_intent": "approve",
                "note": "approved from ui",
            },
        )
        assert status == 500
        payload = json.loads(body)
        assert payload["error_code"] == "audit_insertion_failed"
        assert "Audit insertion failed before the review decision could be reported as applied." in payload["message"]
        assert payload["failure_summary"] == "audit_insertion_failed; inspect local audit surface before retry"
        assert payload["failure_contract"]["rollback_status"] == "fail_closed"
        assert payload["failure_contract"]["durable_mutation_reported_on_failure"] is False
        assert payload["failure_contract"]["recovery_commands"] == [
            f"chronicle review approve --event {ids['runtime_summary_event_id']}",
            "chronicle audit list --json",
        ]
        assert ReviewService(tmp_path).history(event_id=ids["runtime_summary_event_id"]) == []
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_review_action_failure_summary_uses_human_warning_text(tmp_path):
    ids = _populate(tmp_path)
    service = ChronicleUIDataService(
        tmp_path,
        mutation_capability_flag=True,
        enable_ui_mutation=True,
        auth_mode=UIAuthMode.LOOPBACK_LOCAL,
        authorization_mode=UIAuthorizationMode.REVIEWER_DECLARED,
    )

    status, payload = service.review_action_response(
        f"/api/review-actions/{ids['runtime_summary_event_id']}/approve",
        {
            "reviewer_label": "alice",
            "reviewer_kind": "user_declared",
            "session_label": "ui-test-session",
            "ui_intent": "approve",
        },
    )

    assert status == 403
    assert payload["error_code"] == "authorization_failed"
    assert payload["identity_assurance_status"] == "boundary_aligned"
    assert payload["identity_assurance_message"] == "Reviewer identity metadata is aligned with the current UI auth boundary."
    assert payload["warning_details"] == [
        {
            "code": "reviewer_identity_declared_only",
            "message": "Reviewer identity is self-declared and has not been strengthened by a local auth boundary.",
        }
    ]
    assert "Reviewer identity is self-declared" in payload["failure_summary"]
    assert "reviewer_identity_declared_only" not in payload["failure_summary"]


def test_review_action_applies_when_session_gated_inputs_are_complete(tmp_path):
    ids = _populate(tmp_path)
    service = ChronicleUIDataService(
        tmp_path,
        mutation_capability_flag=True,
        enable_ui_mutation=True,
        auth_mode=UIAuthMode.LOOPBACK_LOCAL,
        authorization_mode=UIAuthorizationMode.REVIEWER_DECLARED,
    )

    status, payload = service.review_action_response(
        f"/api/review-actions/{ids['runtime_summary_event_id']}/approve",
        {
            "reviewer_label": "alice",
            "reviewer_kind": "local_operator",
            "session_label": "ui-test-session",
            "ui_intent": "approve",
        },
    )

    assert status == 200
    assert payload["ok"] is True
    assert payload["status"] == "applied"
    assert payload["reviewer_identity"]["session_label"] == "ui-test-session"


def test_review_action_requires_session_label_before_authorization_check(tmp_path):
    ids = _populate(tmp_path)
    service = ChronicleUIDataService(
        tmp_path,
        mutation_capability_flag=True,
        enable_ui_mutation=True,
        auth_mode=UIAuthMode.LOOPBACK_LOCAL,
        authorization_mode=UIAuthorizationMode.REVIEWER_DECLARED,
    )

    status, payload = service.review_action_response(
        f"/api/review-actions/{ids['runtime_summary_event_id']}/approve",
        {
            "reviewer_label": "alice",
            "reviewer_kind": "local_operator",
            "ui_intent": "approve",
        },
    )

    assert status == 400
    assert payload["error_code"] == "session_label_required"
    assert payload["failure_contract"]["possible_error_codes"][1:4] == [
        "reviewer_label_required",
        "invalid_reviewer_label",
        "session_label_required",
    ]


def test_review_action_rejects_invalid_reviewer_label_format(tmp_path):
    ids = _populate(tmp_path)
    service = ChronicleUIDataService(
        tmp_path,
        mutation_capability_flag=True,
        enable_ui_mutation=True,
        auth_mode=UIAuthMode.LOOPBACK_LOCAL,
        authorization_mode=UIAuthorizationMode.REVIEWER_DECLARED,
    )

    status, payload = service.review_action_response(
        f"/api/review-actions/{ids['runtime_summary_event_id']}/approve",
        {
            "reviewer_label": "Alice Smith",
            "reviewer_kind": "local_operator",
            "session_label": "ui-test-session",
            "ui_intent": "approve",
        },
    )

    assert status == 400
    assert payload["error_code"] == "invalid_reviewer_label"
    assert "lowercase letter or digit" in payload["message"]
    assert payload["reviewer_context_requirements"]["reviewer_label_pattern"] == (
        "^[a-z0-9][a-z0-9._-]{1,63}$"
    )
    assert payload["reviewer_context_requirements"]["effective_required_fields"] == [
        "reviewer_label",
        "reviewer_kind",
        "ui_intent",
        "session_label",
    ]


def test_review_action_rejects_invalid_session_label_format(tmp_path):
    ids = _populate(tmp_path)
    service = ChronicleUIDataService(
        tmp_path,
        mutation_capability_flag=True,
        enable_ui_mutation=True,
        auth_mode=UIAuthMode.LOOPBACK_LOCAL,
        authorization_mode=UIAuthorizationMode.REVIEWER_DECLARED,
    )

    status, payload = service.review_action_response(
        f"/api/review-actions/{ids['runtime_summary_event_id']}/approve",
        {
            "reviewer_label": "alice",
            "reviewer_kind": "local_operator",
            "session_label": "UI Session",
            "ui_intent": "approve",
        },
    )

    assert status == 400
    assert payload["error_code"] == "invalid_session_label"
    assert "lowercase letter or digit" in payload["message"]


def test_review_queue_auth_boundary_notice_exposes_human_blocker_details(tmp_path):
    _populate(tmp_path)
    service = ChronicleUIDataService(
        tmp_path,
        mutation_capability_flag=True,
        enable_ui_mutation=True,
        auth_mode=UIAuthMode.LOOPBACK_LOCAL,
        authorization_mode=UIAuthorizationMode.REVIEWER_DECLARED,
    )

    row = service.review_queue()["review_queue"][0]
    notice = row["auth_boundary_notice"]

    assert notice["status"] == "advisory_only"
    assert notice["blockers"] == ["reviewer_identity_missing"]
    assert notice["blocker_details"] == [
        {
            "code": "reviewer_identity_missing",
            "message": "Record reviewer identity metadata before relying on GUI review signals.",
        }
    ]


def test_http_review_action_enabled_route_handles_decision_persistence_failure(tmp_path, monkeypatch):
    ids = _populate(tmp_path)

    def _broken_append_event(self, event):
        raise RuntimeError("append boom")

    monkeypatch.setattr(ChronicleService, "append_event", _broken_append_event)
    try:
        server = make_server(
            host="127.0.0.1",
            port=0,
            root=tmp_path,
            mutation_capability_flag=True,
            enable_ui_mutation=True,
            auth_mode=UIAuthMode.LOOPBACK_LOCAL,
            authorization_mode=UIAuthorizationMode.REVIEWER_DECLARED,
        )
    except PermissionError as exc:
        pytest.skip(f"local socket bind unavailable in this environment: {exc}")
    host, port = server.server_address
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        status, body = _http_post(
            host,
            port,
            f"/api/review-actions/{ids['runtime_summary_event_id']}/approve",
            {
                "reviewer_label": "alice",
                "reviewer_kind": "local_operator",
                "session_label": "ui-http-test",
                "ui_intent": "approve",
                "note": "approved from ui",
            },
        )
        assert status == 500
        payload = json.loads(body)
        assert payload["error_code"] == "decision_persistence_failed"
        assert "Chronicle primary-record append failed" in payload["message"]
        assert payload["failure_summary"] == "decision_persistence_failed; inspect audit trail and primary record state"
        assert payload["audit_id"].startswith("aud_")
        assert payload["failure_contract"]["rollback_status"] == "fail_closed"
        assert payload["failure_contract"]["recovery_commands"][0] == "chronicle review queue --include-resolved --json"
        assert payload["failure_contract"]["recovery_commands"][1] == f"chronicle audit show --id {payload['audit_id']} --json"
        assert len(AuditService(tmp_path).list_events()) == 2
        assert ReviewService(tmp_path).history(event_id=ids["runtime_summary_event_id"]) == []
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_chronicle_ui_help():
    runner = CliRunner()
    result = runner.invoke(app, ["ui", "--help"])
    assert result.exit_code == 0
    for option in ("host", "port", "open", "root", "json", "enable-ui-mutation"):
        assert option in result.stdout.lower()
