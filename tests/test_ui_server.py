"""Tests for explicit local Chronicle UI server."""

import http.client
import json
import os
import re
import threading
from pathlib import Path

import pytest
from typer.testing import CliRunner

from chronicle.cli import app
from chronicle.models.artifact import ArtifactType
from chronicle.models.audit import AuditOperation, AuditSeverity, AuditTargetEnvironment
from chronicle.models.boundary import BoundaryConditionField, BoundaryOperator, BoundaryRuleType
from chronicle.models.decision import DecisionType
from chronicle.models.event import Actor, Confidence, EventType, ReviewStatus
from chronicle.models.lifecycle import LifecycleAction, LifecycleReasonClass
from chronicle.models.source import SourceProvenance
from chronicle.models.visibility import VisibilityHint
from chronicle.services.artifact_service import ArtifactService
from chronicle.services.audit_service import AuditService
from chronicle.services.boundary_service import BoundaryService
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.chronicle_object_service import ChronicleObjectService
from chronicle.services.context_service import ContextService
from chronicle.services.decision_service import DecisionService
from chronicle.services.federation_package_service import FederationPackageService
from chronicle.services.federation_message_service import FederationMessageService
from chronicle.services.graph_index_service import GraphIndexService
from chronicle.services.lifecycle_service import LifecycleService
from chronicle.services.proposal_service import ProposalService
from chronicle.services.rde_service import RdeService
from chronicle.services.review_service import ReviewService
from chronicle.services.runtime_config_service import RuntimeConfigService
from chronicle.services.runtime_service import RuntimeService
from chronicle.services.summary_job_service import SummaryJobService
from chronicle.services.trust_service import TrustService
from chronicle.services.vector_index_service import VectorIndexService
from chronicle.models.review import ReviewerIdentityKind
from chronicle.ui_server import (
    ChronicleUIDataService,
    UIAuthMode,
    UIAuthorizationMode,
    build_startup_metadata,
    make_server,
)


ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*m")


def _plain(text: str) -> str:
    return ANSI_ESCAPE_RE.sub("", text)


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


def _http_post(
    host: str,
    port: int,
    path: str,
    body: dict | None = None,
    *,
    headers: dict[str, str] | None = None,
) -> tuple[int, str]:
    connection = http.client.HTTPConnection(host, port, timeout=5)
    try:
        payload = json.dumps(body or {}).encode("utf-8")
        request_headers = {"Content-Type": "application/json", "Content-Length": str(len(payload))}
        if headers:
            request_headers.update(headers)
        connection.request(
            "POST",
            path,
            body=payload,
            headers=request_headers,
        )
        response = connection.getresponse()
        return response.status, response.read().decode("utf-8")
    finally:
        connection.close()


def _http_post_raw(
    host: str,
    port: int,
    path: str,
    body: str,
    *,
    headers: dict[str, str] | None = None,
) -> tuple[int, str]:
    connection = http.client.HTTPConnection(host, port, timeout=5)
    try:
        payload = body.encode("utf-8")
        request_headers = {"Content-Type": "application/json", "Content-Length": str(len(payload))}
        if headers:
            request_headers.update(headers)
        connection.request(
            "POST",
            path,
            body=payload,
            headers=request_headers,
        )
        response = connection.getresponse()
        return response.status, response.read().decode("utf-8")
    finally:
        connection.close()


def _http_mutation_token(host: str, port: int) -> str:
    status, html = _http_get(host, port, "/")
    assert status == 200
    match = re.search(r'window\.__chronicleMutationToken = "([^"]+)";', html)
    assert match is not None
    return match.group(1)


def _http_mutation_session_id(host: str, port: int) -> str:
    status, html = _http_get(host, port, "/")
    assert status == 200
    match = re.search(r'window\.__chronicleMutationSessionId = "([^"]+)";', html)
    assert match is not None
    return match.group(1)


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
    question_object = ChronicleObjectService(root).record(
        object_type="question",
        summary="Why does this UI boundary exist?",
        created_by="tester",
        context_id=context.context_id,
    )
    trust_node = TrustService(root).add_node_profile(
        node_id="node:partner:beta",
        subject_id="subject:beta",
        display_name="Partner Beta",
    )
    trust_relation = TrustService(root).assert_relation(
        target_node="node:partner:beta",
        target_subject_id="subject:beta",
        domain="technical_review",
        purpose="ui inspect",
        level="trusted",
        capabilities=["review", "reference"],
    )
    inbox_message = FederationMessageService(root).create_message(
        message_type="request_context",
        source_node="node:local:alpha",
        target_node="node:partner:beta",
        purpose="ui inspect",
        object_refs=[question_object.object_id],
        box="inbox",
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
        "question_object_id": question_object.object_id,
        "federation_inbox_message_id": inbox_message.envelope.message_id,
        "trust_node_id": trust_node.node_id,
        "trust_relation_id": trust_relation.relation_id,
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
    assert payload["ui_boundary"]["mutation_enabled_summary_key"] == "ui.boolean.false"
    assert payload["ui_boundary"]["mutation_capability_flag_summary_key"] == "ui.boolean.false"
    assert payload["ui_boundary"]["session_gating_summary_key"] == "ui.boolean.false"
    assert payload["ui_boundary"]["mutation_readiness_status"] == "preview_only"
    assert "write_routes_disabled" in payload["ui_boundary"]["mutation_blockers"]
    assert payload["ui_boundary"]["mutation_blocker_details"][0]["code"] == "write_routes_disabled"
    assert (
        payload["ui_boundary"]["mutation_blocker_details"][0]["message_key"]
        == "ui.mutation_blocker.write_routes_disabled"
    )
    auth_boundary_summary = payload["ui_boundary"]["auth_boundary_summary"]
    assert auth_boundary_summary["message_key"] == "ui.auth_boundary_summary.message.auth_not_enabled"
    assert auth_boundary_summary["scope_note_key"] == "ui.auth_readiness.scope.auth_not_enabled"
    assert auth_boundary_summary["session_gating_summary_key"] == "ui.boolean.false"
    assert auth_boundary_summary["shared_machine_safe_summary_key"] == "ui.boolean.false"
    assert auth_boundary_summary["blocker_details"][0]["message_key"] == "ui.auth_boundary_blocker.auth_not_enabled"
    assert auth_boundary_summary["blocker_summaries"][0]["summary_key"] == "ui.template.auth_boundary_blocker_summary"
    assert auth_boundary_summary["blocker_summaries"][0]["summary_params"]["message"]
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
    assert payload["ui_boundary"]["reviewer_context_requirements"]["mutation_session_id_pattern"] == (
        "^[a-z0-9][a-z0-9._:-]{7,127}$"
    )
    assert payload["ui_boundary"]["reviewer_context_requirements"]["mutation_request_id_pattern"] == (
        "^[a-z0-9][a-z0-9._:-]{7,127}$"
    )
    assert payload["ui_boundary"]["reviewer_context_requirements"]["required_reviewer_kinds_for_mutation"] == [
        "local_operator"
    ]
    assert payload["ui_boundary"]["reviewer_context_requirements"]["session_boundary_status"] == "optional"
    assert payload["ui_boundary"]["reviewer_context_requirements"]["session_boundary_status_summary_key"] == (
        "ui.reviewer_context.session_boundary_status.optional"
    )
    assert payload["ui_boundary"]["reviewer_context_requirements"]["ui_intent_required"] is True
    assert payload["ui_boundary"]["reviewer_context_requirements"]["ui_intent_required_summary_key"] == (
        "ui.reviewer_context.ui_intent_required.true"
    )
    assert payload["ui_boundary"]["reviewer_context_requirements"]["expectation_summary"].startswith(
        "Preview/read-only review context currently expects local_operator reviewer metadata"
    )
    assert payload["ui_boundary"]["reviewer_enforcement_summary"]["status"] == "descriptive_only"
    assert payload["ui_boundary"]["reviewer_enforcement_summary"]["enforced_request_fields"] == [
        "reviewer_label",
        "reviewer_kind",
        "ui_intent",
    ]
    assert payload["ui_boundary"]["reviewer_validation_gate_summary"]["status"] == "read_only_preview"
    assert payload["ui_boundary"]["reviewer_validation_gate_summary"]["validation_error_codes"][:7] == [
        "invalid_mutation_token",
        "invalid_mutation_session",
        "mutation_request_id_required",
        "invalid_mutation_request_id",
        "reviewer_label_required",
        "invalid_reviewer_label",
        "session_label_required",
    ]
    assert payload["ui_boundary"]["reviewer_enforcement_summary"]["route_enforcement_scope"] == (
        "browser-triggered review write route only"
    )
    assert payload["ui_boundary"]["write_route_contract"]["route_template"] == "/api/review-actions/<event_id>/<action>"
    assert payload["ui_boundary"]["write_route_contract"]["actions"] == [
        "approve",
        "reject",
        "request-changes",
    ]
    assert payload["ui_boundary"]["write_route_contract"]["action_routes"] == [
        {
            "action": "approve",
            "path_template": "/api/review-actions/<event_id>/approve",
            "cli_equivalent_template": "chronicle review approve --event <event_id>",
            "path_summary_key": "ui.template.review_write_route.action_route",
            "path_summary_params": {"action": "approve", "path_template": "/api/review-actions/<event_id>/approve"},
            "path_summary": "approve: /api/review-actions/<event_id>/approve",
            "cli_summary_key": "ui.template.review_write_route.cli_equivalent",
            "cli_summary_params": {"action": "approve", "cli_equivalent_template": "chronicle review approve --event <event_id>"},
            "cli_summary": "approve: chronicle review approve --event <event_id>",
        },
        {
            "action": "reject",
            "path_template": "/api/review-actions/<event_id>/reject",
            "cli_equivalent_template": "chronicle review reject --event <event_id>",
            "path_summary_key": "ui.template.review_write_route.action_route",
            "path_summary_params": {"action": "reject", "path_template": "/api/review-actions/<event_id>/reject"},
            "path_summary": "reject: /api/review-actions/<event_id>/reject",
            "cli_summary_key": "ui.template.review_write_route.cli_equivalent",
            "cli_summary_params": {"action": "reject", "cli_equivalent_template": "chronicle review reject --event <event_id>"},
            "cli_summary": "reject: chronicle review reject --event <event_id>",
        },
        {
            "action": "request-changes",
            "path_template": "/api/review-actions/<event_id>/request-changes",
            "cli_equivalent_template": "chronicle review request-changes --event <event_id>",
            "path_summary_key": "ui.template.review_write_route.action_route",
            "path_summary_params": {"action": "request-changes", "path_template": "/api/review-actions/<event_id>/request-changes"},
            "path_summary": "request-changes: /api/review-actions/<event_id>/request-changes",
            "cli_summary_key": "ui.template.review_write_route.cli_equivalent",
            "cli_summary_params": {"action": "request-changes", "cli_equivalent_template": "chronicle review request-changes --event <event_id>"},
            "cli_summary": "request-changes: chronicle review request-changes --event <event_id>",
        },
    ]
    assert payload["ui_boundary"]["write_route_contract"]["status_code_contract"] == [
        {
            "status_code": 200,
            "family": "success",
            "when": "review decision persistence and audit insertion both succeed",
            "when_key": "ui.review_write_route_status_code.when.success",
            "when_params": {},
            "summary": "200: success; review decision persistence and audit insertion both succeed",
            "summary_key": "ui.review_write_route_status_code.summary.success",
            "summary_params": {},
        },
        {
            "status_code": 400,
            "family": "pre_mutation_or_gate",
            "when": "reviewer-context or ui_intent validation fails before authorization",
            "when_key": "ui.review_write_route_status_code.when.validation_failed",
            "when_params": {},
            "summary": "400: pre_mutation_or_gate; reviewer-context or ui_intent validation fails before authorization",
            "summary_key": "ui.review_write_route_status_code.summary.validation_failed",
            "summary_params": {},
        },
        {
            "status_code": 403,
            "family": "pre_mutation_or_gate",
            "when": "mutation gate or authorization boundary blocks the write route",
            "when_key": "ui.review_write_route_status_code.when.authorization_blocked",
            "when_params": {},
            "summary": "403: pre_mutation_or_gate; mutation gate or authorization boundary blocks the write route",
            "summary_key": "ui.review_write_route_status_code.summary.authorization_blocked",
            "summary_params": {},
        },
        {
            "status_code": 404,
            "family": "pre_mutation_or_gate",
            "when": "the requested review target cannot be found in current Chronicle state",
            "when_key": "ui.review_write_route_status_code.when.target_missing",
            "when_params": {},
            "summary": "404: pre_mutation_or_gate; the requested review target cannot be found in current Chronicle state",
            "summary_key": "ui.review_write_route_status_code.summary.target_missing",
            "summary_params": {},
        },
        {
            "status_code": 409,
            "family": "pre_mutation_or_gate",
            "when": "the target is no longer pending for the requested action",
            "when_key": "ui.review_write_route_status_code.when.target_not_pending",
            "when_params": {},
            "summary": "409: pre_mutation_or_gate; the target is no longer pending for the requested action",
            "summary_key": "ui.review_write_route_status_code.summary.target_not_pending",
            "summary_params": {},
        },
        {
            "status_code": 500,
            "family": "durable_write_path",
            "when": "a durable write-path side effect fails and the route stays fail-closed",
            "when_key": "ui.review_write_route_status_code.when.durable_write_failed",
            "when_params": {},
            "summary": "500: durable_write_path; a durable write-path side effect fails and the route stays fail-closed",
            "summary_key": "ui.review_write_route_status_code.summary.durable_write_failed",
            "summary_params": {},
        },
    ]
    assert payload["ui_boundary"]["write_route_contract"]["blocked_status_code"] == 403
    assert payload["ui_boundary"]["write_route_contract"]["durable_success_requirements"] == [
        "route_gating_passed",
        "reviewer_context_validated",
        "decision_persisted",
        "audit_persisted",
    ]
    assert payload["ui_boundary"]["write_route_contract"]["transaction_order"] == [
        "validate route + reviewer context",
        "perform review decision persistence attempt",
        "perform audit insertion attempt",
        "report success only if both durable side effects succeeded",
    ]
    assert payload["ui_boundary"]["write_route_contract"]["failure_families"][0]["family"] == "pre_mutation_or_gate"
    assert payload["ui_boundary"]["write_route_contract"]["failure_families"][0]["summary_key"] == (
        "ui.review_write_route_failure_family.pre_mutation_or_gate"
    )
    assert payload["ui_boundary"]["write_route_contract"]["failure_families"][1]["family"] == "durable_write_path"
    assert payload["ui_boundary"]["write_route_contract"]["failure_families"][1]["summary_key"] == (
        "ui.review_write_route_failure_family.durable_write_path"
    )
    assert payload["ui_boundary"]["write_route_contract"]["status_code_contract"][0]["summary_key"] == (
        "ui.review_write_route_status_code.summary.success"
    )
    assert payload["ui_boundary"]["write_route_contract"]["status_code_contract"][5]["summary_key"] == (
        "ui.review_write_route_status_code.summary.durable_write_failed"
    )
    assert payload["ui_boundary"]["write_route_contract"]["expected_request_field_details"][0]["summary_key"] == (
        "ui.write_request_field.reviewer_label"
    )
    assert payload["ui_boundary"]["write_route_contract"]["transaction_order_details"][0]["summary_key"] == (
        "ui.review_write_route.transaction_order.step_1"
    )
    assert payload["ui_boundary"]["write_route_contract"]["success_status_summary_key"] == (
        "ui.review_write_route_status_code.summary.success"
    )
    assert payload["ui_boundary"]["write_route_contract"]["blocked_status_summary_key"] == (
        "ui.review_write_route_status_code.summary.authorization_blocked"
    )
    assert payload["ui_boundary"]["write_route_contract"]["authorization_contract"]["authorization_status"] == "advisory_only"
    assert payload["ui_boundary"]["write_route_contract"]["authorization_contract"]["authorization_status_summary_key"] == (
        "ui.review_authorization_contract.status.advisory_only"
    )
    assert payload["ui_boundary"]["write_route_contract"]["authorization_contract"]["required_identity_assurance_status"] == "boundary_aligned"
    assert payload["ui_boundary"]["write_route_contract"]["authorization_contract"]["required_identity_assurance_status_summary_key"] == (
        "ui.review_authorization_contract.required_identity_assurance_status.boundary_aligned"
    )
    assert payload["ui_boundary"]["write_route_contract"]["authorization_contract"]["target_pending_required"] is True
    assert payload["ui_boundary"]["write_route_contract"]["authorization_contract"]["server_side_checks"] == [
        "mutation_enabled",
        "reviewer_identity_assurance_boundary_aligned",
        "review_capability_ready",
        "pending_target_state",
    ]
    assert payload["ui_boundary"]["write_route_contract"]["authorization_contract"]["server_side_check_details"][0]["summary_key"] == (
        "ui.review_authorization_contract.server_side_check.mutation_enabled"
    )
    assert payload["ui_boundary"]["write_route_contract"]["authorization_contract"]["action_authorization_matrix"][0]["summary_key"] == (
        "ui.review_authorization_contract.action_matrix.approve"
    )
    assert payload["ui_boundary"]["write_route_contract"]["target_state_contract"]["required_current_review_status"] == "needs_review"
    assert payload["ui_boundary"]["write_route_contract"]["target_state_contract"]["required_current_review_status_summary_key"] == (
        "ui.review_target_state_contract.required_current_review_status.needs_review"
    )
    assert payload["ui_boundary"]["write_route_contract"]["target_state_contract"]["resolved_status_code"] == 409
    assert payload["ui_boundary"]["write_route_contract"]["target_state_contract"]["scope_note_key"] == (
        "ui.review_target_state_contract.note.scope"
    )
    assert payload["ui_boundary"]["write_route_contract"]["target_state_contract"]["action_target_matrix"][2]["resulting_queue_state"] == "remains_pending"
    assert payload["ui_boundary"]["write_route_contract"]["target_state_contract"]["action_target_matrix"][0]["summary_key"] == (
        "ui.review_target_state_contract.action_target_matrix.approve"
    )
    assert payload["ui_boundary"]["write_route_contract"]["target_state_contract"]["target_state_check_details"][0]["summary_key"] == (
        "ui.review_target_state_contract.check.target_exists_in_chronicle_state"
    )
    assert payload["ui_boundary"]["write_route_contract"]["target_state_contract"]["resolved_behavior_note_key"] == (
        "ui.review_target_state_contract.note.resolved_behavior"
    )
    assert payload["ui_boundary"]["write_route_contract"]["identity_proof_contract"]["proof_status"] == "local_operator_advisory"
    assert payload["ui_boundary"]["write_route_contract"]["identity_proof_contract"]["required_reviewer_kinds_for_mutation"] == [
        "local_operator"
    ]
    assert payload["ui_boundary"]["auth_boundary_summary"]["status"] == "auth_not_enabled"
    assert "auth_not_enabled" in payload["ui_boundary"]["auth_boundary_summary"]["blockers"]
    assert payload["ui_boundary"]["auth_boundary_summary"]["blocker_details"] == [
        {
            "code": "auth_not_enabled",
            "message_key": "ui.auth_boundary_blocker.auth_not_enabled",
            "message": "Define explicit local auth boundary.",
        },
        {
            "code": "authorization_not_enabled",
            "message_key": "ui.auth_boundary_blocker.authorization_not_enabled",
            "message": "Define authorization semantics for reviewer actions.",
        },
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
    assert payload["ui_boundary"]["reviewer_context_requirements"]["accepted_reviewer_kind_details"][0][
        "summary_key"
    ] == "ui.reviewer_kind.local_operator"
    assert payload["ui_boundary"]["reviewer_context_requirements"]["session_boundary_status"] == "required"
    assert payload["ui_boundary"]["reviewer_context_requirements"]["session_boundary_status_summary_key"] == (
        "ui.reviewer_context.session_boundary_status.required"
    )
    assert payload["ui_boundary"]["reviewer_context_requirements"]["expectation_summary"].startswith(
        "Explicit local GUI mutation currently expects local_operator reviewer metadata"
    )
    assert payload["ui_boundary"]["reviewer_enforcement_summary"]["status"] == "preview_contract_only"
    assert payload["ui_boundary"]["reviewer_enforcement_summary"]["session_gated"] is True
    assert payload["ui_boundary"]["reviewer_validation_gate_summary"]["status"] == "preview_route_contract"
    assert payload["ui_boundary"]["write_route_contract"]["identity_proof_contract"]["proof_status"] == "session_gated_local_operator"
    assert payload["ui_boundary"]["write_route_contract"]["authorization_contract"]["authorization_status"] == "explicit_local_reviewer_declared"
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
    assert "session enablement" in payload["ui_boundary"]["mutation_readiness_message"]


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
    assert payload["ui_boundary"]["reviewer_enforcement_summary"]["status"] == "enforced_local_session"
    assert payload["ui_boundary"]["reviewer_validation_gate_summary"]["status"] == "local_route_enforced"
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
    assert readiness["enablement_ready_summary_key"] == "ui.boolean.true"
    assert readiness["enablement_satisfied_count"] == readiness["enablement_required_count"] == 6
    assert all(check["satisfied"] is True for check in readiness["enablement_checks"])
    assert readiness["operational_readiness"]["status"] == "ready"
    assert readiness["operational_readiness"]["remaining_count"] == 0


def test_ui_overview_data(tmp_path):
    ids = _populate(tmp_path)
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
    assert overview["counts"]["audit_events"] == 2
    assert overview["counts"]["lifecycle_markers"] == 1
    assert overview["counts"]["summary_jobs"] == 1
    assert overview["runtime_boundary"]["read_only"] is True
    assert overview["runtime_boundary"]["daemon"] is False
    assert overview["runtime_boundary"]["external_model_api"] is False
    assert overview["runtime_boundary"]["graphrag_runtime"] is False
    assert overview["runtime_boundary"]["vector_db"] is False
    assert overview["runtime_boundary"]["graph_db"] is False
    assert overview["runtime_boundary"]["read_only_summary_key"] == "ui.boolean.true"
    assert overview["runtime_boundary"]["external_model_api_summary_key"] == "ui.boolean.false"
    assert overview["runtime_config"]["config"]["provider_kind"] == "http"
    assert overview["runtime_config"]["source_summary_key"] == "ui.runtime_config.source.stored"
    assert overview["runtime_config"]["config"]["provider_kind_summary_key"] == (
        "ui.runtime_config.provider_kind.http"
    )
    assert overview["runtime_config"]["config"]["model_name"] == "manual-http-model"
    assert overview["runtime_config"]["config"]["allow_network"] is True
    assert overview["runtime_config"]["config"]["allow_network_summary_key"] == "ui.boolean.true"
    assert overview["federation_overlap_summary"]["status"] == "no_overlaps"
    assert overview["federation_overlap_summary"]["message_key"] == (
        "ui.federation_overlap.message.no_overlaps"
    )
    assert overview["federation_overlap_summary"]["counts_summary_key"] == (
        "ui.template.federation_overlap.counts"
    )
    assert overview["federation_overlap_summary"]["runtime_overlap_count"] == 0
    assert overview["federation_overlap_summary"]["review_overlap_count"] == 0
    assert overview["federation_overlap_summary"]["consent_audit_count"] == 0
    assert overview["federation_overlap_summary"]["boundary_note_key"] == (
        "ui.federation_overlap.note.read_only_derived"
    )
    assert overview["federation_preflight_summary"]["suggested_boundary_check_cli"].startswith(
        "chronicle federation boundary check --purpose"
    )
    assert overview["federation_preflight_summary"]["suggested_package_preview_cli"].startswith(
        "chronicle federation package preview --package-dir"
    )
    assert overview["federation_preflight_summary"]["suggested_package_inspect_cli"].startswith(
        "chronicle federation package inspect --package-dir"
    )
    assert overview["federation_preflight_summary"]["suggested_package_verify_cli"].startswith(
        "chronicle federation package verify --package-dir"
    )
    assert overview["federation_preflight_summary"]["suggested_import_preview_cli"].startswith(
        "chronicle federation package import-preview --package-dir"
    )
    assert overview["ui_boundary"]["mutation_enabled"] is False
    assert overview["ui_boundary"]["mutation_capability_flag"] is False
    assert overview["ui_boundary"]["auth_mode"] == "not_enabled"
    assert overview["auth_boundary_summary"]["status"] == "auth_not_enabled"
    assert overview["auth_boundary_summary"]["scope_note"].startswith(
        "UI review remains advisory-only until an explicit local auth boundary"
    )
    assert "Define explicit local auth boundary." in overview["auth_boundary_summary"]["next_steps"]
    assert overview["auth_boundary_summary"]["blocker_details"][0]["code"] == "auth_not_enabled"
    assert (
        overview["auth_boundary_summary"]["blocker_details"][0]["message_key"]
        == "ui.auth_boundary_blocker.auth_not_enabled"
    )
    assert (
        overview["auth_boundary_summary"]["blocker_details"][0]["message"]
        == "Define explicit local auth boundary."
    )
    assert overview["auth_boundary_summary"]["blocker_summaries"][0]["summary"].startswith(
        "Auth boundary: "
    )
    assert overview["auth_boundary_overview"]["auth_warning_count"] == 3
    assert overview["auth_boundary_overview"]["authorization_warning_count"] == 3
    assert overview["auth_boundary_overview"]["missing_identity_count"] == 3
    assert overview["auth_boundary_overview"]["review_capability_counts"]["advisory_only"] == 3
    assert overview["auth_boundary_overview"]["provider_response_present_count"] == 0
    assert overview["auth_boundary_overview"]["latest_provider_response_detail_path"] is None
    assert overview["identity_boundary_summary"]["status"] == "identity_unavailable"
    assert overview["identity_boundary_summary"]["message_key"] == "ui.identity_boundary.message.identity_unavailable"
    assert overview["identity_boundary_summary"]["missing_identity_count"] == 3
    assert overview["reviewer_boundary_overview"]["enforcement_status"] == "descriptive_only"
    assert overview["reviewer_boundary_overview"]["validation_gate_status"] == "read_only_preview"
    assert overview["reviewer_boundary_overview"]["runtime_record_enforcement_counts"] == {
        "descriptive_only": 2
    }
    assert overview["reviewer_boundary_overview"]["review_queue_validation_gate_counts"] == {
        "read_only_preview": 3
    }
    assert overview["reviewer_boundary_overview"]["summary_job_enforcement_counts"] == {
        "descriptive_only": 1
    }
    assert overview["reviewer_boundary_overview"]["drilldown_summaries"][0]["dataset_key"] == "runtime_records"
    assert overview["reviewer_boundary_overview"]["drilldown_summaries"][0]["list_path"] == "/api/runtime-records"
    assert overview["reviewer_boundary_overview"]["drilldown_summaries"][1]["dataset_key"] == "review_queue"
    assert overview["reviewer_boundary_overview"]["drilldown_summaries"][2]["dataset_key"] == "summary_jobs"
    assert overview["mutation_readiness"]["status"] == "preview_only"
    assert overview["mutation_readiness"]["scope_note"].startswith("The UI remains preview-only")
    assert "Define explicit local auth boundary." in overview["mutation_readiness"]["next_steps"]
    assert overview["mutation_readiness"]["blocker_details"][0]["code"] == "write_routes_disabled"
    assert overview["mutation_readiness"]["blocker_summaries"][0]["source_label"] == "Boundary prerequisites"
    assert overview["mutation_readiness"]["blocker_summaries"][0]["summary"].startswith("Boundary prerequisites: ")
    assert overview["mutation_readiness"]["pending_boundary_warning_counts"]["reviewer_identity_missing"] == 3
    assert overview["mutation_readiness"]["enablement_ready"] is False
    assert overview["mutation_readiness"]["enablement_ready_summary_key"] == "ui.boolean.false"
    assert overview["mutation_readiness"]["enablement_satisfied_count"] == 1
    assert overview["mutation_readiness"]["enablement_required_count"] == 6
    assert overview["mutation_readiness"]["operational_readiness"]["status"] == "blocked"
    assert overview["mutation_readiness"]["operational_readiness"]["remaining_count"] == 5
    assert overview["mutation_readiness"]["enablement_checks"][0]["code"] == "mutation_capability_flag"
    assert (
        overview["mutation_readiness"]["enablement_checks"][0]["label_key"]
        == "ui.mutation_enablement_check.mutation_capability_flag.label"
    )
    assert (
        overview["mutation_readiness"]["enablement_checks"][0]["detail_key"]
        == "ui.mutation_enablement_check.mutation_capability_flag.detail"
    )
    assert overview["mutation_readiness"]["enablement_checks"][0]["satisfied"] is False
    assert overview["mutation_readiness"]["reviewer_context_requirements"]["required_fields"] == [
        "reviewer_label",
        "reviewer_kind",
        "ui_intent",
    ]
    assert overview["mutation_readiness"]["reviewer_context_requirements"]["required_reviewer_kinds_for_mutation"] == [
        "local_operator"
    ]
    assert overview["mutation_readiness"]["reviewer_context_requirements"]["expectation_summary"].startswith(
        "Preview/read-only review context currently expects local_operator reviewer metadata"
    )
    assert (
        overview["mutation_readiness"]["reviewer_context_requirements"]["expectation_summary_key"]
        == "ui.reviewer_context.expectation.optional"
    )
    assert (
        overview["mutation_readiness"]["reviewer_context_requirements"]["authority_note_key"]
        == "ui.reviewer_context.note.authority"
    )
    assert overview["mutation_readiness"]["reviewer_enforcement_summary"]["status"] == "descriptive_only"
    assert (
        overview["mutation_readiness"]["reviewer_enforcement_summary"]["message_key"]
        == "ui.reviewer_enforcement.message.descriptive_only"
    )
    assert overview["mutation_readiness"]["reviewer_enforcement_summary"]["descriptive_only_reviewer_kinds"] == [
        "user_declared"
    ]
    assert overview["mutation_readiness"]["reviewer_validation_gate_summary"]["status"] == "read_only_preview"
    assert (
        overview["mutation_readiness"]["reviewer_validation_gate_summary"]["message_key"]
        == "ui.reviewer_validation_gate.message.read_only_preview"
    )
    assert overview["mutation_readiness"]["reviewer_validation_gate_summary"]["fail_closed"] is True
    assert overview["mutation_readiness"]["identity_proof_contract"]["required_reviewer_kinds_for_mutation"] == [
        "local_operator"
    ]
    assert overview["mutation_readiness"]["operational_readiness"]["blocking_codes"] == [
        "mutation_capability_flag",
        "ui_mutation_enable_flag",
        "auth_boundary",
        "authorization_boundary",
        "reviewer_identity",
    ]
    assert overview["mutation_readiness"]["operational_readiness"]["blocking_summaries"][0].startswith(
        "Capability flag enabled: "
    )
    assert (
        overview["mutation_readiness"]["operational_readiness"]["unsatisfied_checks"][0]["summary_key"]
        == "ui.template.mutation_enablement_check_summary"
    )
    assert (
        overview["mutation_readiness"]["operational_readiness"]["unsatisfied_checks"][0]["label_key"]
        == "ui.mutation_enablement_check.mutation_capability_flag.label"
    )
    assert overview["runtime_records_summary"]["kind_counts"]["summary"] == 1
    assert overview["runtime_records_summary"]["kind_counts"]["retrieval_plan"] == 1
    assert overview["runtime_records_summary"]["auth_readiness_counts"]["advisory_only"] == 2
    assert overview["runtime_records_summary"]["mutation_readiness_counts"]["preview_only"] == 2
    assert overview["runtime_records_summary"]["mutation_operational_counts"]["blocked"] == 2
    assert overview["runtime_records_summary"]["provider_response_present_count"] == 0
    assert overview["runtime_records_summary"]["provider_response_absent_count"] == 2
    assert overview["runtime_records_summary"]["latest_provider_response_detail_path"] is None
    assert overview["runtime_records_summary"]["query_engine_trial_summary"]["total_count"] == 0
    assert overview["runtime_records_summary"]["query_engine_trial_summary"]["insufficient_count"] == 0
    assert overview["runtime_records_summary"]["query_engine_trial_escalation_summary"]["status"] == (
        "no_trial_records"
    )
    assert overview["runtime_records_summary"]["query_engine_trial_escalation_summary"]["active_count"] == 0
    assert overview["runtime_records_summary"]["query_engine_trial_escalation_drilldown_summary"][
        "dataset_key"
    ] == "runtime_records"
    assert (
        overview["runtime_records_summary"]["query_engine_trial_escalation_drilldown_summary"][
            "issue_template_title"
        ]
        == "Downstream query-engine trial summary"
    )
    assert overview["summary_jobs_summary"]["status_counts"]["pending_review"] == 1
    assert overview["summary_jobs_summary"]["review_capability_counts"]["advisory_only"] == 1
    assert overview["summary_jobs_summary"]["auth_readiness_counts"]["advisory_only"] == 1
    assert overview["summary_jobs_summary"]["package_readiness_counts"]["no_context_records"] == 1
    assert overview["summary_jobs_summary"]["mutation_readiness_counts"]["preview_only"] == 1
    assert overview["summary_jobs_summary"]["mutation_operational_counts"]["blocked"] == 1
    assert overview["summary_jobs_summary"]["provider_response_present_count"] == 0
    assert overview["summary_jobs_summary"]["latest_provider_response_detail_path"] is None
    assert overview["summary_jobs_summary"]["identity_assurance_counts"]["unknown"] == 1
    assert overview["summary_jobs_summary"]["reviewer_kind_counts"]["unknown"] == 1
    assert overview["summary_jobs_summary"]["runtime_provider_counts"]["disabled"] == 1
    assert overview["summary_jobs_summary"]["summary_source_total"] == 0
    assert overview["current_work_summary"]["question_count"] == 1
    assert overview["current_work_summary"]["objection_count"] == 0
    assert overview["current_work_summary"]["pending_proposal_count"] == 0
    assert overview["current_work_summary"]["current_question"]["summary"] == "Why does this UI boundary exist?"
    assert overview["current_work_summary"]["current_question"]["detail_path"] == (
        f"/api/chronicle-objects/{ids['question_object_id']}"
    )
    assert overview["current_work_summary"]["current_artifact_candidate"]["detail_path"].startswith(
        "/api/artifacts/"
    )
    assert overview["current_work_summary"]["boundary_note_key"] == (
        "ui.current_work_summary.note.read_only_derived"
    )
    assert overview["overview_evidence_summary"]["boundary_rule_count"] == 1
    assert overview["overview_evidence_summary"]["audit_event_count"] == 2
    assert overview["overview_evidence_summary"]["lifecycle_event_count"] == 1
    assert overview["overview_evidence_summary"]["trust_node_count"] == 1
    assert overview["overview_evidence_summary"]["trust_relation_count"] == 1
    assert overview["overview_evidence_summary"]["auth_blocker_count"] >= 1
    assert overview["overview_evidence_summary"]["consent_record_count"] == 0
    assert overview["overview_evidence_summary"]["federation_overlap_count"] == 0
    assert overview["overview_evidence_summary"]["latest_boundary_rule"]["reason"] == "UI boundary"
    assert overview["overview_evidence_summary"]["latest_boundary_rule"]["detail_path"] == (
        f"/api/boundary/{ids['rule_id']}"
    )
    assert overview["overview_evidence_summary"]["latest_audit_event"]["summary"].startswith(
        "Trust relation asserted: "
    )
    assert overview["overview_evidence_summary"]["latest_audit_event"]["detail_path"].startswith(
        "/api/audit/"
    )
    assert overview["overview_evidence_summary"]["latest_lifecycle_event"]["reason"] == (
        "UI lifecycle marker"
    )
    assert overview["overview_evidence_summary"]["latest_lifecycle_event"]["detail_path"] == (
        f"/api/lifecycle/{ids['lifecycle_id']}"
    )
    assert overview["overview_evidence_summary"]["boundary_note_key"] == (
        "ui.overview_evidence_summary.note.read_only_derived"
    )
    assert overview["triage"]["needs_attention_reviews"] == 3
    assert overview["triage"]["runtime_record_kinds"]["summary"] == 1
    assert overview["triage"]["runtime_record_kinds"]["retrieval_plan"] == 1
    assert overview["triage"]["review_capability_counts"]["advisory_only"] == 3
    assert overview["triage"]["package_readiness_counts"]["package_context_available"] >= 1
    assert overview["triage"]["provider_response_present_reviews"] == 0


def test_ui_data_service_read_endpoints(tmp_path):
    ids = _populate(tmp_path)
    RuntimeConfigService(tmp_path).set_local(model_name="ui-local-model", provider_name="ui-local")
    ProposalService(tmp_path).propose_context_update(
        context_id=ids["context_id"],
        summary="UI context proposal",
        proposed_summary="UI context proposal body",
    )
    ProposalService(tmp_path).propose_artifact_update(
        artifact_id=ids["artifact_id"],
        summary="UI artifact proposal",
        content="UI artifact proposal body",
    )
    approved_context_proposal = ProposalService(tmp_path).propose_context_update(
        context_id=ids["context_id"],
        summary="Approved UI context proposal",
        proposed_summary="Approved body",
    )
    ReviewService(tmp_path).approve(event_id=approved_context_proposal.event_id, reviewer="alice")
    service = ChronicleUIDataService(tmp_path)

    assert service.contexts()["contexts"][0]["title"] == "UI Context"
    assert service.contexts()["contexts"][0]["proposal_count"] == 2
    assert service.artifacts()["artifacts"][0]["title"] == "UI Artifact"
    assert service.artifacts()["artifacts"][0]["proposal_count"] == 1
    assert len(service.proposal_records()["proposals"]) == 3
    assert any(
        proposal["apply_ready"] is True
        and proposal["cli_apply_hint"].startswith("chronicle context apply-proposal --event evt_")
        for proposal in service.proposal_records()["proposals"]
        if proposal["event_id"] == approved_context_proposal.event_id
    )
    assert service.decisions()["decisions"][0]["reason"] == "UI decision"
    assert service.boundary_rules()["boundary_rules"][0]["reason"] == "UI boundary"
    assert any(
        event["summary"] == "UI audit event"
        for event in service.audit_events()["audit_events"]
    )
    consent_payload = FederationPackageService(tmp_path).record_consent(
        target_node="node:partner:beta",
        purpose="ui consent review",
        scope="partner-review",
        granted_by="review-owner",
        third_party_sharing_allowed=False,
        context_ids=[ids["context_id"]],
    )
    audit_payload = service.audit_events()
    assert audit_payload["federation_preflight_summary"]["message_key"] == (
        "ui.federation_preflight.message.consent_recorded"
    )
    assert audit_payload["federation_preflight_summary"]["boundary_check_message_key"] == (
        "ui.federation_preflight.boundary_check.cli_only_preview"
    )
    assert audit_payload["federation_preflight_summary"]["counts_summary_key"] == (
        "ui.template.federation_preflight.counts"
    )
    consent_row = next(
        event
        for event in audit_payload["audit_events"]
        if event["audit_id"] == consent_payload["audit_id"]
    )
    assert audit_payload["governance_summary"]["audit_event_count"] == len(
        audit_payload["audit_events"]
    )
    assert audit_payload["governance_summary"]["linked_boundary_count"] >= 1
    assert audit_payload["governance_summary"]["linked_lifecycle_count"] >= 1
    assert audit_payload["governance_summary"]["consent_record_count"] == 1
    assert audit_payload["governance_summary"]["boundary_note_key"] == (
        "ui.audit_governance_summary.note.read_only_derived"
    )
    assert consent_row["federation_consent_summary"]["message_key"] == (
        "ui.federation_consent_audit.message.recorded"
    )
    assert consent_row["federation_consent_summary"]["target_node"] == "node:partner:beta"
    assert consent_row["federation_consent_summary"]["scope"] == "partner-review"
    assert consent_row["federation_consent_summary"]["boundary_note_key"] == (
        "ui.federation_consent_audit.note.read_only_derived"
    )
    assert consent_row["operational_implication"]["boundary_note_key"] == (
        "ui.audit_operational_implication.note.read_only_derived"
    )
    assert service.lifecycle_markers()["lifecycle_markers"][0]["reason"] == "UI lifecycle marker"
    assert len(service.runtime_records()["runtime_records"]) == 2
    assert service.runtime_records()["runtime_records"][0]["runtime_record_preview"]["title"]
    assert service.runtime_records()["runtime_records"][0]["runtime_record_preview"]["title_key"]
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
    assert runtime_summary_row["runtime_record_preview"]["title_key"] == "ui.runtime_preview.title.summary"
    assert runtime_summary_row["posture_role"]["status"] == "local_summary_review"
    assert runtime_summary_row["posture_role"]["boundary_note_key"] == (
        "ui.runtime_posture_role.note.read_only_derived"
    )
    assert runtime_summary_row["downstream_boundary_note"]["status"] == "local_runtime_boundary"
    assert runtime_summary_row["downstream_boundary_note"]["boundary_note_key"] == (
        "ui.runtime_downstream_boundary.note.read_only_derived"
    )
    assert runtime_summary_row["trial_sufficiency_summary"]["status"] == "no_trial_context"
    assert runtime_summary_row["handoff_summary"]["status"] == "no_handoff_contract"
    assert runtime_summary_row["mutation_enablement_summary"]["status"] == "preview_only"
    assert "explicit local write enablement still requires" in runtime_summary_row["mutation_enablement_summary"]["message"]
    assert runtime_summary_row["mutation_enablement_summary"]["message_key"] == (
        "ui.mutation_readiness.message.preview_requirements_pending"
    )
    assert runtime_summary_row["mutation_enablement_summary"]["scope_note"].startswith(
        "The UI remains preview-only"
    )
    assert runtime_summary_row["mutation_enablement_summary"]["scope_note_key"] == (
        "ui.mutation_readiness.note.preview_only_requirements_pending"
    )
    assert runtime_summary_row["mutation_enablement_summary"]["blocked_status_code"] == 403
    assert runtime_summary_row["mutation_enablement_summary"]["blocked_status_summary_key"] == (
        "ui.review_write_route_status_code.summary.authorization_blocked"
    )
    assert runtime_summary_row["mutation_enablement_summary"]["identity_proof_status"] == "local_operator_advisory"
    assert runtime_summary_row["mutation_enablement_summary"]["remaining_summary"].startswith(
        "Capability flag enabled: "
    )
    assert runtime_summary_row["mutation_enablement_summary"]["remaining_summary_key"] == (
        "ui.template.mutation_enablement_check_summary"
    )
    assert runtime_summary_row["reviewer_enforcement_status"] == "descriptive_only"
    assert runtime_summary_row["reviewer_validation_gate_status"] == "read_only_preview"
    assert runtime_summary_row["reviewer_boundary_drilldown_summary"]["dataset_key"] == "runtime_records"
    assert runtime_summary_row["reviewer_boundary_drilldown_summary"]["summary_variant"] == "row_detail"
    assert runtime_summary_row["reviewer_boundary_drilldown_summary"]["detail_path"] == (
        f"/api/runtime-records/{ids['runtime_summary_event_id']}"
    )
    assert runtime_summary_row["reviewer_boundary_drilldown_summary"]["message_key"] == (
        "ui.message.reviewer_boundary_drilldown"
    )
    assert runtime_summary_row["reviewer_boundary_drilldown_summary"]["message_template_key"] == (
        "ui.template.reviewer_boundary_drilldown_message"
    )
    assert runtime_summary_row["reviewer_boundary_drilldown_summary"]["message_params"] == {
        "dataset_key": "runtime_records",
    }
    assert runtime_summary_row["reviewer_boundary_drilldown_summary"]["fact_line_template_key"] == (
        "ui.template.reviewer_boundary_fact_line"
    )
    assert runtime_summary_row["reviewer_boundary_drilldown_summary"]["fact_line_params"] == {
        "dataset_key": "runtime_records",
        "enforcement_status": "descriptive_only",
        "validation_gate_status": "read_only_preview",
    }
    assert "This read-only drilldown row appears in runtime records because reviewer enforcement is descriptive only" in (
        runtime_summary_row["reviewer_boundary_drilldown_summary"]["fact_line"]
    )
    review_queue = service.review_queue()["review_queue"]
    assert len(review_queue) == 5
    assert {"artifact_update", "context_update"} <= {
        row["review_kind"] for row in review_queue
    }
    assert len(service.summary_jobs_list()["summary_jobs"]) == 1
    assert service.summary_jobs_list()["summary_jobs"][0]["summary_job_id"].startswith("sum_")
    assert service.summary_jobs_list()["summary_jobs"][0]["review_target_event_id"].startswith("evt_")
    assert service.summary_jobs_list()["summary_jobs"][0]["review_capability_status"] == "advisory_only"
    assert service.summary_jobs_list()["summary_jobs"][0]["auth_readiness_status"] == "advisory_only"
    assert service.summary_jobs_list()["summary_jobs"][0]["package_readiness_summary"]["status"] == (
        "no_context_records"
    )
    assert service.summary_jobs_list()["summary_jobs"][0]["package_readiness_status"] == "no_context_records"
    assert service.summary_jobs_list()["summary_jobs"][0]["auth_advisory_summary"]["status"] == (
        "advisory_only"
    )
    assert service.summary_jobs_list()["summary_jobs"][0]["auth_advisory_summary"][
        "boundary_note_key"
    ] == "ui.summary_job_auth_advisory.note.read_only_derived"
    assert service.summary_jobs_list()["summary_jobs"][0]["identity_assurance_summary"]["status"] == (
        "unknown"
    )
    assert service.summary_jobs_list()["summary_jobs"][0]["identity_assurance_summary"][
        "boundary_note_key"
    ] == "ui.summary_job_identity_assurance.note.read_only_derived"
    assert service.summary_jobs_list()["summary_jobs"][0]["cli_parity_status"] == "aligned"
    assert service.summary_jobs_list()["summary_jobs"][0]["action_preview_summary"]["status"] == "preview_only"
    assert (
        service.summary_jobs_list()["summary_jobs"][0]["action_preview_summary"]["message_key"]
        == "ui.action_preview.message.preview_only_blocked"
    )
    assert (
        service.summary_jobs_list()["summary_jobs"][0]["action_preview_summary"]["cli_equivalent_summary_key"]
        == "ui.template.review_action_preview.cli_equivalent_summary"
    )
    assert service.summary_jobs_list()["summary_jobs"][0]["action_preview_summary"]["cli_equivalent"].startswith(
        "chronicle review approve --event evt_"
    )
    assert (
        service.summary_jobs_list()["summary_jobs"][0]["action_preview_summary"]["recovery_summary_key"]
        == "ui.template.review_action_preview.recovery_summary"
    )
    assert service.summary_jobs_list()["summary_jobs"][0]["action_preview_summary"]["recovery_summary"].startswith(
        "chronicle review approve --event evt_"
    )
    assert (
        service.summary_jobs_list()["summary_jobs"][0]["action_preview_summary"]["follow_up_summary_key"]
        == "ui.template.review_action_preview.follow_up_summary"
    )
    assert service.summary_jobs_list()["summary_jobs"][0]["action_preview_summary"]["success_contract"]["follow_up_commands"][0] == "chronicle review queue --include-resolved --json"
    assert service.summary_jobs_list()["summary_jobs"][0]["action_preview_summary"]["write_route_contract"]["route_template"] == "/api/review-actions/<event_id>/<action>"
    assert service.summary_jobs_list()["summary_jobs"][0]["identity_assurance_status"] == "unknown"
    assert service.summary_jobs_list()["summary_jobs"][0]["mutation_enablement_summary"]["status"] == "preview_only"
    assert service.summary_jobs_list()["summary_jobs"][0]["mutation_enablement_summary"]["message_key"] == (
        "ui.mutation_readiness.message.preview_requirements_pending"
    )
    assert service.summary_jobs_list()["summary_jobs"][0]["mutation_enablement_summary"]["scope_note"].startswith(
        "The UI remains preview-only"
    )
    assert service.summary_jobs_list()["summary_jobs"][0]["mutation_enablement_summary"]["scope_note_key"] == (
        "ui.mutation_readiness.note.preview_only_requirements_pending"
    )
    assert service.summary_jobs_list()["summary_jobs"][0]["mutation_enablement_summary"]["remaining_count"] >= 1
    assert service.summary_jobs_list()["summary_jobs"][0]["reviewer_enforcement_status"] == "descriptive_only"
    assert service.summary_jobs_list()["summary_jobs"][0]["reviewer_validation_gate_status"] == "read_only_preview"
    assert service.summary_jobs_list()["summary_jobs"][0]["reviewer_boundary_drilldown_summary"]["dataset_key"] == (
        "summary_jobs"
    )
    assert service.runtime_config_state()["runtime_config"]["config"]["provider_name"] == "ui-local"
    assert service.runtime_config_state()["runtime_config"]["source_summary_key"] == (
        "ui.runtime_config.source.stored"
    )
    assert service.runtime_config_state()["runtime_config"]["config"]["provider_kind_summary_key"] == (
        "ui.runtime_config.provider_kind.local"
    )
    assert review_queue[0]["review_preview_only"] is True
    assert review_queue[0]["target_event_id"].startswith("evt_")
    assert review_queue[0]["review_capability"]["status"] == "advisory_only"
    assert review_queue[0]["auth_boundary_notice"]["status"] == "advisory_only"
    assert review_queue[0]["reviewer_enforcement_status"] == "descriptive_only"
    assert review_queue[0]["reviewer_validation_gate_status"] == "read_only_preview"
    assert review_queue[0]["reviewer_boundary_drilldown_summary"]["dataset_key"] == (
        "review_queue"
    )
    assert review_queue[0]["response_metadata_summary"]["message_key"] == (
        "ui.provider_response.message.unavailable"
    )
    assert review_queue[0]["package_readiness_summary"]["label"].startswith("package:")
    assert review_queue[0]["package_readiness_summary"]["label_key"] == (
        "ui.package_readiness.summary.label.advisory"
    )
    assert review_queue[0]["package_readiness_summary"]["message"]
    assert (
        review_queue[0]["package_readiness_summary"]["message_key"]
        == "ui.package_readiness.message.no_context_records"
    )
    assert review_queue[0]["package_readiness_summary"]["message_template_key"] == (
        "ui.package_readiness.summary.message.advisory"
    )
    assert service.review_queue()["review_queue"][0]["action_preview_summary"]["status"] == "preview_only"
    assert (
        service.review_queue()["review_queue"][0]["action_preview_summary"]["message_key"]
        == "ui.action_preview.message.preview_only_blocked"
    )
    assert (
        service.review_queue()["review_queue"][0]["action_preview_summary"]["recovery_summary_key"]
        == "ui.template.review_action_preview.recovery_summary"
    )
    assert service.review_queue()["review_queue"][0]["action_preview_summary"]["follow_up_summary"] == (
        "chronicle review queue --include-resolved --json"
    )
    assert (
        service.review_queue()["review_queue"][0]["action_preview_summary"]["follow_up_summary_key"]
        == "ui.template.review_action_preview.follow_up_summary"
    )
    assert service.review_queue()["review_queue"][0]["action_preview_summary"]["success_contract"]["transaction_status"] == "decision_and_audit_persisted"
    assert service.review_queue()["review_queue"][0]["action_preview_summary"]["write_route_contract"]["transaction_order"] == [
        "validate route + reviewer context",
        "perform review decision persistence attempt",
        "perform audit insertion attempt",
        "report success only if both durable side effects succeeded",
    ]
    assert service.review_queue()["review_queue"][0]["action_preview_summary"]["write_route_contract"]["expected_request_fields"] == [
        "reviewer_label",
        "reviewer_kind",
        "ui_intent",
    ]
    assert service.review_queue()["review_queue"][0]["action_preview_summary"]["write_route_contract"]["authorization_contract"]["action_authorization_matrix"][0]["action"] == "approve"
    assert service.review_queue()["review_queue"][0]["action_preview_summary"]["write_route_contract"]["target_state_contract"]["target_state_checks"][2] == "target_pending_for_requested_action"
    assert service.review_queue()["review_queue"][0]["action_preview_summary"]["actions"][0]["post_path"].startswith(
        "/api/review-actions/evt_"
    )
    assert service.review_queue()["review_queue"][0]["mutation_enablement_summary"]["operational_status"] == "blocked"
    assert service.review_queue()["review_queue"][0]["mutation_enablement_summary"]["remaining_summary"]
    assert service.review_queue()["review_queue"][0]["mutation_enablement_summary"]["message_key"] == (
        "ui.mutation_readiness.message.preview_requirements_pending"
    )
    assert service.review_queue()["review_queue"][0]["mutation_enablement_summary"]["scope_note_key"] == (
        "ui.mutation_readiness.note.preview_only_requirements_pending"
    )
    assert service.review_queue()["review_queue"][0]["mutation_enablement_summary"]["remaining_summary_key"] == (
        "ui.template.mutation_enablement_check_summary"
    )
    assert service.review_queue()["review_queue"][0]["mutation_enablement_summary"][
        "operational_message_key"
    ] == "ui.mutation_operational_readiness.message.blocked"
    assert service.review_queue()["review_queue"][0]["cli_parity_summary"]["status"] == "aligned"
    assert (
        service.review_queue()["review_queue"][0]["cli_parity_summary"]["message_key"]
        == "ui.cli_parity.message.aligned"
    )
    assert service.review_queue()["review_queue"][0]["cli_parity_summary"]["expected_actions"] == [
        "approve",
        "reject",
        "request_changes",
    ]
    overview = service.overview()
    assert overview["triage"]["cli_parity_aligned_reviews"] == 5
    assert overview["triage"]["cli_parity_drift_reviews"] == 0
    assert overview["triage"]["cli_parity_counts"]["aligned"] == 5
    assert overview["triage"]["identity_assurance_counts"]["unknown"] == 5
    assert overview["triage"]["reviewer_kind_counts"]["unknown"] == 5
    assert overview["triage"]["warning_counts"]["ui_auth_not_enabled"] == 5
    assert overview["triage"]["warning_counts"]["ui_authorization_not_enabled"] == 5
    assert overview["triage"]["warning_summaries"][0]["code"] == "ui_auth_not_enabled"
    assert overview["triage"]["warning_summaries"][1]["code"] == "ui_authorization_not_enabled"
    assert overview["triage"]["warning_summaries"][0]["label_key"] == "filter.review.ui_auth_not_enabled"
    assert overview["triage"]["warning_summaries"][0]["message_key"] == "ui.review_warning.ui_auth_not_enabled"
    assert overview["triage"]["warning_summaries"][0]["summary_key"] == "ui.template.review_warning.summary"
    assert overview["reviewer_boundary_overview"]["drilldown_summaries"][0]["message_key"] == (
        "ui.message.reviewer_boundary_drilldown"
    )
    assert overview["reviewer_boundary_overview"]["drilldown_summaries"][0]["summary_variant"] == (
        "overview_dominant"
    )
    assert overview["reviewer_boundary_overview"]["drilldown_summaries"][0]["message_template_key"] == (
        "ui.template.reviewer_boundary_overview_message"
    )
    assert overview["reviewer_boundary_overview"]["drilldown_summaries"][0]["message_params"] == {
        "dataset_key": "runtime_records",
    }
    assert overview["reviewer_boundary_overview"]["drilldown_summaries"][0]["fact_line_template_key"] == (
        "ui.template.reviewer_boundary_dominant_fact_line"
    )
    assert overview["reviewer_boundary_overview"]["drilldown_summaries"][0]["fact_line_params"] == {
        "dataset_key": "runtime_records",
        "enforcement_status": "descriptive_only",
        "validation_gate_status": "read_only_preview",
    }
    assert "ui_auth_not_enabled" in service.review_queue()["review_queue"][0]["review_capability"]["warnings"]
    assert service.review_queue()["review_queue"][0]["review_capability"]["warning_details"][0]["message"]
    assert service.review_queue()["review_queue"][0]["review_capability"]["warning_details"][0][
        "message_key"
    ] == "ui.review_warning.ui_auth_not_enabled"
    assert "latest_identity_assurance" not in service.review_queue()["review_queue"][0]
    review_detail = service.detail_payload(
        f"/api/review-queue/{service.review_queue()['review_queue'][0]['target_event_id']}"
    )
    assert review_detail is not None
    assert review_detail["record"]["related_links"][0]["label_key"] == (
        "ui.related_link.open_matching_runtime_record"
    )
    assert service.ui_boundary()["ui_boundary"]["loopback_only"] is True
    assert "events" in service.events()
    assert "rde_records" in service.rde_records()
    package_review = service.package_review_snapshot()
    assert package_review["status"] in {"pass", "warning", "blocked", "unavailable"}
    assert package_review["message_key"] in {
        "ui.package_review.message.pass",
        "ui.package_review.message.warning",
        "ui.package_review.message.blocked",
        "ui.package_review.message.unavailable",
    }
    assert package_review["counts_summary_key"] == "ui.template.package_review.counts"
    assert package_review["boundary_note_key"] == "ui.package_review.note.read_only_derived"
    assert package_review["counts_summary_params"]["record_count"] >= 0
    assert service.overview()["federation_preflight_summary"]["boundary_note_key"] == (
        "ui.federation_preflight.note.read_only_derived"
    )
    federation_preview = service.api_payload("/api/federation-package-preview")
    assert federation_preview is not None
    assert federation_preview["federation_package_preview"]["status"] == "parameter_required"
    assert (
        federation_preview["federation_package_preview"]["message_key"]
        == "ui.federation_package_preview.message.parameter_required"
    )
    assert (
        federation_preview["federation_package_preview"]["boundary_note_key"]
        == "ui.federation_package_preview.note.read_only_derived"
    )
    assert federation_preview["federation_package_preview"]["suggested_query"]
    assert service.graph_summary()["status"] == "available"
    assert service.graph_summary()["message_key"] == "ui.graph_summary.message.available"
    assert service.graph_summary()["counts_summary_key"] == "ui.template.graph_summary.counts"
    assert service.graph_summary()["boundary_note_key"] == "ui.graph_summary.note.read_only_derived"
    assert service.graph_summary()["contract_version"] == "1.0"
    assert service.graph_summary()["incremental_mode"] == "event-driven_rebuildable"
    assert service.graph_summary()["incremental_expectations"]
    assert service.overview()["graph_summary"]["message_key"] == "ui.graph_summary.message.available"
    retrieval_result = RuntimeService(tmp_path).retrieve_plan(query="UI Context")
    assert retrieval_result.graph_adapter is not None
    assert retrieval_result.graph_adapter.contract_version == "1.0"
    assert retrieval_result.graph_adapter.incremental_mode == "event-driven_rebuildable"
    assert service.ai_index_status()["ai_index_status"]["message_key"] == (
        "ui.ai_index_status.message.available"
    )
    assert service.ai_index_status()["ai_index_status"]["boundary_note_key"] == (
        "ui.ai_index_status.note.read_only_derived"
    )
    assert service.ai_index_status()["ai_index_status"]["vector"]["counts_summary_key"] == (
        "ui.template.ai_index_status.vector_counts"
    )
    assert service.ai_index_status()["ai_index_status"]["graph"]["counts_summary_key"] == (
        "ui.template.ai_index_status.graph_counts"
    )


def test_ui_data_service_federation_package_preview_query_surfaces(tmp_path):
    ids = _populate(tmp_path)
    package_dir = tmp_path / "federation-package-ui-preview"
    FederationPackageService(tmp_path).create_package(
        purpose="ui preview review",
        target_node="node:partner:beta",
        output_dir=package_dir,
    )
    service = ChronicleUIDataService(tmp_path)

    preview_payload = service.api_payload(
        "/api/federation-package-preview",
        {"package_dir": [str(package_dir)]},
    )
    assert preview_payload is not None
    preview = preview_payload["federation_package_preview"]
    assert preview["package_path"] == str(package_dir)
    assert preview["mode"] == "preview"
    assert preview["status"] in {"pass", "warning", "blocked"}
    assert preview["message_key"] in {
        "ui.federation_package_preview.message.pass",
        "ui.federation_package_preview.message.warning",
        "ui.federation_package_preview.message.blocked",
    }
    assert preview["boundary_note_key"] == "ui.federation_package_preview.note.read_only_derived"
    assert preview["manifest"]["target_node"] == "node:partner:beta"
    assert preview["verification"]["valid"] is True
    assert isinstance(preview["findings"], list)
    assert isinstance(preview["warnings"], list)
    assert preview["package_route_summary"]["target_node"] == "node:partner:beta"
    assert preview["package_route_summary"]["record_count"] == 1
    assert preview["package_route_summary"]["boundary_note_key"] == (
        "ui.federation_package_route.note.read_only_derived"
    )
    assert preview["trust_reference_summary"]["target_node"] == "node:partner:beta"
    assert preview["trust_reference_summary"]["active_relation_count"] == 1
    assert preview["trust_reference_summary"]["dominant_level"] == "trusted"
    assert preview["trust_reference_summary"]["detail_path"] == (
        f"/api/trust-nodes/{ids['trust_node_id']}"
    )
    assert preview["trust_reference_summary"]["boundary_note_key"] == (
        "ui.federation_package_trust.note.read_only_derived"
    )
    assert preview["consent_summary"]["status"] == "not_recorded"
    assert preview["consent_summary"]["latest_audit_id"] is None
    assert preview["consent_summary"]["boundary_note_key"] == (
        "ui.federation_package_consent.note.read_only_derived"
    )
    assert preview["import_implication_summary"]["mode"] == "preview"
    assert preview["import_implication_summary"]["import_candidate"] is True
    assert preview["import_implication_summary"]["boundary_note_key"] == (
        "ui.federation_package_import_implication.note.read_only_derived"
    )

    import_preview_payload = service.api_payload(
        "/api/federation-package-preview",
        {"package_dir": [str(package_dir)], "mode": ["import-preview"]},
    )
    assert import_preview_payload is not None
    import_preview = import_preview_payload["federation_package_preview"]
    assert import_preview["package_path"] == str(package_dir)
    assert import_preview["mode"] == "import-preview"
    assert import_preview["status"] in {"pass", "warning", "blocked"}
    assert import_preview["message_key"] in {
        "ui.federation_package_preview.message.pass",
        "ui.federation_package_preview.message.warning",
        "ui.federation_package_preview.message.blocked",
    }
    assert import_preview["boundary_note_key"] == "ui.federation_package_preview.note.read_only_derived"
    assert isinstance(import_preview["findings"], list)
    assert isinstance(import_preview["warnings"], list)
    assert import_preview["package_route_summary"]["mode"] == "import-preview"
    assert import_preview["consent_summary"]["status"] == "not_recorded"
    assert import_preview["import_implication_summary"]["mode"] == "import-preview"
    assert import_preview["import_implication_summary"]["import_candidate"] is True
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
        "message": "Provider response metadata is available for this local derived record.",
        "message_key": "ui.provider_response.message.present",
        "response_id": "resp_ui_metadata",
        "finish_reason": "stop",
        "finish_reason_summary_key": "ui.provider_response.finish_reason.stop",
        "finish_reason_summary": "stop",
        "provider_status": "ok",
        "provider_status_summary_key": "ui.provider_response.provider_status.ok",
        "provider_status_summary": "ok",
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
        "counts_summary_key": "ui.template.provider_response.counts",
        "counts_summary_params": {
            "metadata_count": 6,
            "response_key_count": 5,
        },
        "boundary_note": "Provider response metadata remains derived, read-only, and non-authoritative over primary Chronicle records.",
        "boundary_note_key": "ui.provider_response.note.read_only_derived",
    }

    summary_job_row = service.summary_jobs_list()["summary_jobs"][0]
    assert summary_job_row["response_metadata_summary"]["response_id"] == "resp_ui_metadata"
    assert summary_job_row["response_metadata_summary"]["usage_output_tokens"] == 7
    assert summary_job_row["response_metadata_summary"]["response_key_count"] == 5
    assert summary_job_row["response_metadata_summary"]["counts_summary_key"] == (
        "ui.template.provider_response.counts"
    )

    review_row = service.review_queue()["review_queue"][0]
    assert review_row["response_metadata_summary"]["response_id"] == "resp_ui_metadata"
    assert review_row["response_metadata_summary"]["finish_reason"] == "stop"
    assert review_row["response_metadata_summary"]["usage_total_tokens"] == 21
    assert review_row["response_metadata_summary"]["boundary_note_key"] == (
        "ui.provider_response.note.read_only_derived"
    )

    overview = service.overview()
    assert overview["runtime_records_summary"]["provider_response_present_count"] == 1
    assert overview["runtime_records_summary"]["provider_response_finish_reason_counts"]["stop"] == 1
    assert overview["runtime_records_summary"]["provider_response_status_counts"]["ok"] == 1
    assert overview["runtime_records_summary"]["mutation_readiness_counts"]["preview_only"] == 1
    assert overview["runtime_records_summary"]["latest_provider_response_detail_path"] == f"/api/runtime-records/{result.event_id}"
    assert overview["auth_boundary_overview"]["provider_response_present_count"] == 1
    assert overview["auth_boundary_overview"]["provider_response_finish_reason_counts"]["stop"] == 1
    assert overview["auth_boundary_overview"]["provider_response_status_counts"]["ok"] == 1
    assert overview["auth_boundary_overview"]["latest_provider_response_detail_path"] == f"/api/review-queue/{result.event_id}"
    assert overview["summary_jobs_summary"]["provider_response_present_count"] == 1
    assert overview["summary_jobs_summary"]["provider_response_finish_reason_counts"]["stop"] == 1
    assert overview["summary_jobs_summary"]["provider_response_status_counts"]["ok"] == 1
    assert overview["summary_jobs_summary"]["mutation_readiness_counts"]["preview_only"] == 1
    assert overview["summary_jobs_summary"]["latest_provider_response_detail_path"] == f"/api/summary-jobs/{summary_job_row['summary_job_id']}"
    assert overview["triage"]["provider_response_present_reviews"] == 1
    assert overview["triage"]["latest_provider_response_detail_path"] == f"/api/review-queue/{result.event_id}"

    runtime_detail = service.detail_payload(f"/api/runtime-records/{result.event_id}")
    assert runtime_detail is not None
    assert runtime_detail["record"]["response_metadata_summary"]["finish_reason"] == "stop"
    assert runtime_detail["record"]["runtime_record_preview"]["record_kind"] == "execution"
    assert runtime_detail["record"]["reviewer_boundary_drilldown_summary"]["dataset_key"] == "runtime_records"
    assert runtime_detail["record"]["reviewer_boundary_drilldown_summary"]["enforcement_filter_value"] == (
        "reviewer_enforcement:descriptive_only"
    )
    assert any(
        link["path"] == f"/api/summary-jobs/{summary_job_row['summary_job_id']}"
        for link in runtime_detail["record"]["related_links"]
    )

    summary_detail = service.detail_payload(f"/api/summary-jobs/{summary_job_row['summary_job_id']}")
    assert summary_detail is not None
    assert summary_detail["record"]["response_metadata_summary"]["usage_total_tokens"] == 21
    assert summary_detail["record"]["reviewer_boundary_drilldown_summary"]["dataset_key"] == "summary_jobs"

    review_detail = service.detail_payload(f"/api/review-queue/{result.event_id}")
    assert review_detail is not None
    assert review_detail["record"]["response_metadata_summary"]["provider_status"] == "ok"
    assert review_detail["record"]["reviewer_boundary_drilldown_summary"]["dataset_key"] == "review_queue"


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
    assert "overviewCountButton(label('overview.provider_response', 'Provider response')" in html
    assert "summaryJsonLine('Provider finish reasons', authBoundaryOverview.provider_response_finish_reason_counts)" in html
    assert "summaryJsonLine('Provider statuses', authBoundaryOverview.provider_response_status_counts)" in html
    assert "summaryJsonLine('Provider finish reasons', runtimeRecords.provider_response_finish_reason_counts)" in html
    assert "summaryJsonLine('Query-engine trial summary', runtimeRecords.query_engine_trial_summary)" in html
    assert "summaryJsonLine('Trial escalation', runtimeRecords.query_engine_trial_escalation_summary)" in html
    assert "renderQueryEngineTrialEscalationDrilldownSummary(runtimeRecords.query_engine_trial_escalation_drilldown_summary || {})" in html
    assert "label('ui.label.issue_template_title', 'Issue template title')" in html
    assert "summaryJsonLine('Provider statuses', summaryJobs.provider_response_status_counts)" in html
    assert "summaryJsonLine('Mutation readiness counts', runtimeRecords.mutation_readiness_counts)" in html
    assert "summaryJsonLine('Mutation operational counts', runtimeRecords.mutation_operational_counts)" in html
    assert "summaryJsonLine('Mutation readiness counts', summaryJobs.mutation_readiness_counts)" in html
    assert "summaryJsonLine('Mutation operational counts', summaryJobs.mutation_operational_counts)" in html
    assert "function renderPreviewContractSummary(preview, previewTarget = 'action-preview-response')" in html
    assert "function mutationEnablementBadge(summary)" in html
    assert "function renderMutationEnablementSummary(summary)" in html
    assert "message=" in html
    assert "scope=" in html
    assert "remaining-summary=" in html
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
    assert "transaction-order=" in html
    assert "authorization-checks=" in html
    assert "target-state-checks=" in html
    assert "success-status=" in html
    assert "blocked-status=" in html
    assert "proof-status=" in html
    assert "proof-fields=" in html
    assert "errors=" in html
    assert "const localizedRecoverySummary = preview && preview.recovery_summary_key" in html
    assert "const localizedPossibleErrors = (Array.isArray(failureContract.possible_error_details) ? failureContract.possible_error_details : []).map(item => (" in html
    assert "const localizedFollowUpCommands = (Array.isArray(successContract.follow_up_command_details) ? successContract.follow_up_command_details : []).map(item => (" in html
    assert "const localizedProofStatus = identityProofContract.proof_status_message_key" in html
    assert "const localizedProofFields = (Array.isArray(identityProofContract.required_identity_field_details) ? identityProofContract.required_identity_field_details : []).map(item => (" in html
    assert "const localizedRequestFields = (Array.isArray(writeRouteContract.expected_request_field_details) ? writeRouteContract.expected_request_field_details : []).map(item => (" in html
    assert "const localizedTransactionOrder = (Array.isArray(writeRouteContract.transaction_order_details) ? writeRouteContract.transaction_order_details : []).map(item => (" in html
    assert "const localizedAuthorizationChecks = (Array.isArray(authorizationContract.server_side_check_details) ? authorizationContract.server_side_check_details : []).map(item => (" in html
    assert "const localizedTargetStateChecks = (Array.isArray(targetStateContract.target_state_check_details) ? targetStateContract.target_state_check_details : []).map(item => (" in html
    assert "const localizedSuccessStatus = writeRouteContract.success_status_summary_key" in html
    assert "const localizedBlockedStatus = writeRouteContract.blocked_status_summary_key" in html
    assert "const localizedRollbackStatus = failureContract.rollback_status_summary_key" in html
    assert "const localizedTransactionStatus = successContract.transaction_status_summary_key" in html
    assert "const localizedDurableOnFailure = typeof failureContract.durable_mutation_reported_on_failure === 'boolean'" in html
    assert "follow-up=" in html
    assert "const localizedEnablementReady = mutationReadiness.enablement_ready_summary_key" in html
    assert "detailLine('Enablement ready', localizedEnablementReady)" in html
    assert "detailLine('Scope note', mutationReadiness.scope_note_key ? formatLabel(mutationReadiness.scope_note_key, mutationReadiness.scope_note_params || {}, mutationReadiness.scope_note || '') : (mutationReadiness.scope_note || ''))" in html
    assert html.count("const localizedActionTargetMatrix = (targetStateContract.action_target_matrix || []).map(item => (") >= 2
    assert html.count("const localizedFailureFamilies = (writeRouteContract.failure_families || []).map(item => {") >= 2
    assert "detailLine('Operational readiness', operationalReadiness.status || '')" in html
    assert "const localizedRemainingChecks = (Array.isArray(operationalReadiness.unsatisfied_checks) ? operationalReadiness.unsatisfied_checks : []).map(item => (" in html
    assert "detailListLine('Remaining checks', localizedRemainingChecks.length > 0 ? localizedRemainingChecks : (operationalReadiness.blocking_summaries || []), ' | ')" in html
    assert "const localizedOperationalMessage = operationalReadiness.message_key" in html
    assert "const localizedProofStatus = summary.identity_proof_status_message_key" in html
    assert "const localizedProofFields = (Array.isArray(summary.identity_proof_field_details) ? summary.identity_proof_field_details : []).map(item => (" in html
    assert "const localizedBlockedStatus = summary.blocked_status_summary_key" in html
    assert "mutationOperationalDetailLines(operationalReadiness, blockerSummaries, enablementChecks)" in html
    assert "function renderMutationEnablementNotice(record)" in html
    assert "label('notice.mutation_enablement', 'Mutation Enablement')" in html
    assert "item && item.summary_key" in html
    assert "formatLabel(item.summary_key, item.summary_params || {}, item.summary || item.code || 'blocker')" in html
    assert "detailLine('Reviewer label pattern', reviewerContext.reviewer_label_pattern || '')" in html
    assert "detailLine('Write route', writeRouteContract.route_template || '')" in html
    assert "const localizedActionRoutes = (writeRouteContract.action_routes || []).map(item => (" in html
    assert "const localizedCliRouteEquivalents = (writeRouteContract.action_routes || []).map(item => (" in html
    assert "detailListLine('Action routes', localizedActionRoutes, ' | ')" in html
    assert "detailListLine('CLI route equivalents', localizedCliRouteEquivalents, ' | ')" in html
    assert "const localizedStatusCodeContract = (writeRouteContract.status_code_contract || []).map(item => {" in html
    assert "detailListLine('Status-code contract', localizedStatusCodeContract, ' | ')" in html
    assert "const localizedPossibleErrors = (Array.isArray(failureContract.possible_error_details) ? failureContract.possible_error_details : []).map(item => (" in html
    assert "const localizedRecoveryCommands = (Array.isArray(failureContract.recovery_command_details) ? failureContract.recovery_command_details : []).map(item => (" in html
    assert "const localizedCliEquivalent = payload.cli_equivalent_detail && payload.cli_equivalent_detail.summary_key" in html
    assert "detailListLine('Write request fields', localizedWriteRequestFields.length > 0 ? localizedWriteRequestFields : writeRouteContract.expected_request_fields, ' | ')" in html
    assert "detailListLine('Effective reviewer fields', reviewerContextRequirements.effective_required_fields, ' | ')" in html
    assert "const localizedEffectiveFields = (Array.isArray(reviewerContext.effective_required_field_details) ? reviewerContext.effective_required_field_details : []).map(item => (" in html
    assert "const localizedAcceptedKinds = (Array.isArray(reviewerContext.accepted_reviewer_kind_details) ? reviewerContext.accepted_reviewer_kind_details : []).map(item => (" in html
    assert "const localizedAdvisoryKinds = (Array.isArray(reviewerContext.advisory_only_reviewer_kind_details) ? reviewerContext.advisory_only_reviewer_kind_details : []).map(item => (" in html
    assert "Review queue blocked-route preview stays read-only and returns the CLI fallback contract." in html
    assert "Runtime-record blocked-route preview stays read-only and returns the CLI fallback contract." in html
    assert "Local mutation is enabled for this runtime-record list view." in html
    assert "function renderOverviewCurrentWorkPanel(currentWork)" in html
    assert "sectionTitle(label('section.current_work', 'Current Work'))" in html
    assert "label('overview.current_questions', 'Current questions')" in html
    assert "label('overview.pending_proposals', 'Pending proposals')" in html
    assert "label('overview.apply_ready_proposals', 'Apply-ready proposals')" in html
    assert "label('overview.unresolved_objections', 'Unresolved objections')" in html
    assert "label('overview.active_hypotheses', 'Active hypotheses')" in html
    assert "detailLine('Artifact candidate', currentArtifact.title || '')" in html
    assert "detailLine('Latest pending proposal', latestProposal.summary || '')" in html
    assert "detailLine('Latest apply-ready proposal', latestApplyReady.summary || '')" in html
    assert "detailLine('Latest objection', latestObjection.summary || '')" in html
    assert "data => renderOverviewCurrentWorkPanel(data.currentWork)," in html
    assert "function renderOverviewEvidencePanel(evidence)" in html
    assert "sectionTitle(label('section.overview_evidence', 'Evidence Rail'))" in html
    assert "label('overview.boundary_rules', 'Boundary rules')" in html
    assert "label('overview.audit_events', 'Audit events')" in html
    assert "label('overview.lifecycle_events', 'Lifecycle events')" in html
    assert "label('overview.trust_nodes', 'Trust nodes')" in html
    assert "label('overview.trust_relations', 'Trust relations')" in html
    assert "label('overview.auth_blockers', 'Auth blockers')" in html
    assert "label('overview.consent_records', 'Consent records')" in html
    assert "label('overview.federation_overlaps', 'Federation overlaps')" in html
    assert "detailLine('Latest boundary rule', latestBoundary.reason || '')" in html
    assert "detailLine('Latest audit event', latestAudit.summary || '')" in html
    assert "detailLine('Latest lifecycle event', latestLifecycle.reason || '')" in html
    assert "data => renderOverviewEvidencePanel(data.overviewEvidence)," in html


def test_overview_current_work_summary_tracks_questions_proposals_and_objections(tmp_path):
    ids = _populate(tmp_path)
    objection = ChronicleObjectService(tmp_path).record(
        object_type="objection",
        summary="Need stronger provenance proof",
        created_by="tester",
        artifact_id=ids["artifact_id"],
        origin_question_id=ids["question_object_id"],
    )
    ChronicleObjectService(tmp_path).record(
        object_type="hypothesis",
        summary="Artifact proposal may resolve the concern",
        created_by="tester",
        artifact_id=ids["artifact_id"],
        origin_question_id=ids["question_object_id"],
    )
    pending_proposal = ProposalService(tmp_path).propose_artifact_update(
        artifact_id=ids["artifact_id"],
        summary="Pending UI artifact proposal",
        content="pending proposal body",
    )
    approved_proposal = ProposalService(tmp_path).propose_context_update(
        context_id=ids["context_id"],
        summary="Approved UI context proposal",
        proposed_summary="approved proposal body",
    )
    ReviewService(tmp_path).approve(event_id=approved_proposal.event_id, reviewer="alice")

    summary = ChronicleUIDataService(tmp_path).overview()["current_work_summary"]

    assert summary["question_count"] == 1
    assert summary["objection_count"] == 1
    assert summary["hypothesis_count"] == 1
    assert summary["pending_proposal_count"] == 1
    assert summary["apply_ready_proposal_count"] == 1
    assert summary["current_question"]["detail_path"] == f"/api/chronicle-objects/{ids['question_object_id']}"
    assert summary["latest_objection"]["object_id"] == objection.object_id
    assert summary["latest_objection"]["detail_path"] == f"/api/chronicle-objects/{objection.object_id}"
    assert summary["current_artifact_candidate"]["artifact_id"] == ids["artifact_id"]
    assert summary["current_artifact_candidate"]["detail_path"] == f"/api/artifacts/{ids['artifact_id']}"
    assert summary["latest_pending_proposal"]["event_id"] == pending_proposal.event_id
    assert summary["latest_pending_proposal"]["detail_path"] == f"/api/review-queue/{pending_proposal.event_id}"
    assert summary["latest_apply_ready_proposal"]["event_id"] == approved_proposal.event_id
    assert summary["latest_apply_ready_proposal"]["detail_path"] == (
        f"/api/review-queue/{approved_proposal.event_id}"
    )


def test_ui_data_service_detail_endpoints(tmp_path):
    ids = _populate(tmp_path)
    consent_payload = FederationPackageService(tmp_path).record_consent(
        target_node="node:partner:beta",
        purpose="ui consent detail review",
        scope="detail-review",
        granted_by="detail-owner",
        third_party_sharing_allowed=True,
        third_party_sharing_reason="approved research partner",
        context_ids=[ids["context_id"]],
    )
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
    object_detail = service.detail_payload(f"/api/chronicle-objects/{ids['question_object_id']}")["record"]
    assert object_detail["object_type"] == "question"
    assert f"/api/contexts/{ids['context_id']}" in object_detail["related_resource_paths"]
    federation_detail = service.detail_payload(
        f"/api/federation-inbox/{ids['federation_inbox_message_id']}"
    )["record"]
    assert federation_detail["message_type"] == "request_context"
    assert federation_detail["audit_recorded"] is False
    assert federation_detail["related_resource_paths"] == [f"/api/chronicle-objects/{ids['question_object_id']}"]
    trust_node_detail = service.detail_payload(f"/api/trust-nodes/{ids['trust_node_id']}")["record"]
    trust_relation_detail = service.detail_payload(
        f"/api/trust-relations/{ids['trust_relation_id']}"
    )["record"]
    assert trust_node_detail["subject_id"] == "subject:beta"
    assert trust_node_detail["relation_count"] == 1
    assert trust_node_detail["latest_activity_summary"]["status"] == "active_relation_present"
    assert trust_node_detail["latest_activity_summary"]["relation_id"] == ids["trust_relation_id"]
    assert trust_node_detail["latest_activity_summary"]["detail_path"] == (
        f"/api/trust-relations/{ids['trust_relation_id']}"
    )
    assert trust_node_detail["domain_coverage_summary"]["domains"] == ["technical_review"]
    assert trust_node_detail["domain_coverage_summary"]["active_relation_count"] == 1
    assert trust_node_detail["domain_coverage_summary"]["capability_counts"] == {
        "reference": 1,
        "review": 1,
    }
    assert trust_relation_detail["level"] == "trusted"
    assert trust_relation_detail["subject_summary"]["subject_id"] == "subject:beta"
    assert trust_relation_detail["subject_summary"]["detail_path"] == (
        f"/api/trust-nodes/{ids['trust_node_id']}"
    )
    assert trust_relation_detail["active_state"]["status"] == "active"
    assert trust_relation_detail["active_state"]["is_active"] is True
    assert trust_relation_detail["history_summary"]["history_event_count"] == 1
    assert trust_relation_detail["history_summary"]["transition_count"] == 1
    assert trust_relation_detail["history_summary"]["latest_detail_path"].startswith("/api/audit/")
    assert trust_relation_detail["federation_implication"]["status"] == (
        "advisory_capability_present"
    )
    assert trust_relation_detail["federation_implication"]["capabilities"] == [
        "review",
        "reference",
    ]
    artifact_detail = service.detail_payload(f"/api/artifacts/{ids['artifact_id']}")["record"]
    assert artifact_detail["title"] == "UI Artifact"
    assert artifact_detail["versions"]
    assert service.detail_payload(f"/api/decisions/{ids['decision_id']}")["record"]["reason"] == "UI decision"
    boundary_detail = service.detail_payload(f"/api/boundary/{ids['rule_id']}")["record"]
    assert boundary_detail["reason"] == "UI boundary"
    assert boundary_detail["detail_governance_summary"]["list_path"] == "/api/boundary"
    assert boundary_detail["detail_governance_summary"]["linked_audit_count"] >= 1
    audit_detail = service.detail_payload(f"/api/audit/{ids['audit_id']}")["record"]
    assert audit_detail["summary"] == "UI audit event"
    assert audit_detail["related_boundary_rule_ids"] == [ids["rule_id"]]
    assert audit_detail["related_lifecycle_ids"] == [ids["lifecycle_id"]]
    assert audit_detail["impacted_target_summary"]["record_count"] == 0
    assert audit_detail["operational_implication"]["status"] == "local_trace_available"
    consent_detail = service.detail_payload(f"/api/audit/{consent_payload['audit_id']}")["record"]
    assert consent_detail["federation_consent_summary"]["message_key"] == (
        "ui.federation_consent_audit.message.recorded"
    )
    assert consent_detail["federation_consent_summary"]["scope"] == "detail-review"
    assert consent_detail["federation_consent_summary"]["third_party_sharing_allowed"] is True
    assert consent_detail["federation_consent_summary"]["third_party_sharing_allowed_summary_key"] == (
        "ui.boolean.true"
    )
    assert consent_detail["impacted_target_summary"]["record_count"] == 1
    assert consent_detail["impacted_target_summary"]["primary_target_path"] == (
        f"/api/contexts/{ids['context_id']}"
    )
    lifecycle_detail = service.detail_payload(f"/api/lifecycle/{ids['lifecycle_id']}")["record"]
    assert lifecycle_detail["reason"] == "UI lifecycle marker"
    assert lifecycle_detail["detail_governance_summary"]["list_path"] == "/api/lifecycle"
    assert lifecycle_detail["detail_governance_summary"]["linked_audit_count"] >= 1
    summary_detail = service.detail_payload(f"/api/summary-jobs/{ids['summary_job_id']}")["record"]
    assert summary_detail["title"] == "UI Summary Draft"
    assert summary_detail["suggested_cli_family"] == "chronicle summary show --id"
    assert summary_detail["runtime_provider_kind"] == "disabled"
    assert summary_detail["review_target_event_id"].startswith("evt_")
    assert summary_detail["review_capability"]["status"] == "advisory_only"
    assert summary_detail["auth_boundary_notice"]["status"] == "advisory_only"
    assert summary_detail["auth_advisory_summary"]["status"] == "advisory_only"
    assert summary_detail["identity_assurance_summary"]["status"] == "unknown"
    assert "auth_not_enabled" in summary_detail["auth_boundary_notice"]["blockers"]
    assert summary_detail["package_readiness"]["status"] == "no_context_records"
    assert summary_detail["cli_parity"]["status"] == "aligned"
    assert summary_detail["action_preview"]["status"] == "preview_only"
    assert summary_detail["action_preview"]["success_contract"]["rollback_status"] == "not_required"
    assert summary_detail["action_preview"]["write_route_contract"]["blocked_status_code"] == 403
    assert summary_detail["action_preview"]["write_route_contract"]["failure_families"][1]["possible_error_codes"] == [
        "audit_insertion_failed",
        "decision_persistence_failed",
    ]
    assert summary_detail["action_preview"]["write_route_contract"]["authorization_contract"]["server_side_checks"][2] == "review_capability_ready"
    assert summary_detail["action_preview"]["write_route_contract"]["target_state_contract"]["action_target_matrix"][1]["resulting_disposition"] == "reject"
    assert summary_detail["action_preview"]["write_route_contract"]["identity_proof_contract"]["required_identity_fields"] == [
        "reviewer_label",
        "reviewer_kind",
        "ui_intent",
    ]
    assert summary_detail["mutation_enablement"]["enablement_ready"] is False
    assert summary_detail["mutation_enablement"]["scope_note"].startswith("The UI remains preview-only")
    assert summary_detail["mutation_enablement"]["operational_readiness"]["status"] == "blocked"
    assert summary_detail["reviewer_enforcement_summary"]["status"] == "descriptive_only"
    assert summary_detail["reviewer_validation_gate_summary"]["status"] == "read_only_preview"
    assert any(item["source"] == "boundary" for item in summary_detail["mutation_enablement"]["blocker_summaries"])
    assert summary_detail["mutation_enablement"]["write_route_contract"]["route_template"] == "/api/review-actions/<event_id>/<action>"
    assert any(link["path"] == f"/api/review-queue/{summary_detail['review_target_event_id']}" for link in summary_detail["related_links"])
    runtime_detail = service.detail_payload(f"/api/runtime-records/{ids['runtime_summary_event_id']}")["record"]
    assert "runtime_summary" in runtime_detail["payload"]
    assert runtime_detail["runtime_record_preview"]["record_kind"] == "summary"
    assert runtime_detail["posture_role"]["status"] == "local_summary_review"
    assert runtime_detail["downstream_boundary_note"]["status"] == "local_runtime_boundary"
    assert runtime_detail["trial_sufficiency_summary"]["status"] == "no_trial_context"
    assert runtime_detail["handoff_summary"]["status"] == "no_handoff_contract"
    assert runtime_detail["auth_boundary_notice"]["status"] == "advisory_only"
    assert runtime_detail["mutation_enablement"]["enablement_ready"] is False
    assert runtime_detail["mutation_enablement"]["operational_readiness"]["remaining_count"] >= 1
    assert any(
        item["summary"].startswith("Pending review queue")
        for item in runtime_detail["mutation_enablement"]["blocker_summaries"]
    )
    assert any(item["source"] == "review_queue" for item in runtime_detail["mutation_enablement"]["blocker_summaries"])
    assert runtime_detail["mutation_enablement"]["write_route_contract"]["success_status_code"] == 200
    assert runtime_detail["suggested_cli_family"] == "chronicle runtime summarize --record"
    assert runtime_detail["related_links"][0]["path"] == f"/api/review-queue/{ids['runtime_summary_event_id']}"
    assert runtime_detail["related_links"][0]["label"] == "Open matching review detail"


def test_trust_workspace_payloads_capture_withdrawal_history(tmp_path):
    ids = _populate(tmp_path)
    TrustService(tmp_path).withdraw_relation(
        relation_id=ids["trust_relation_id"],
        reason="review window expired",
    )

    service = ChronicleUIDataService(tmp_path)
    trust_relation = service.trust_relations()["trust_relations"][0]
    trust_node = service.trust_nodes()["trust_nodes"][0]

    assert trust_relation["active_state"]["status"] == "withdrawn"
    assert trust_relation["active_state"]["is_active"] is False
    assert trust_relation["history_summary"]["history_event_count"] == 2
    assert trust_relation["history_summary"]["transition_count"] == 2
    assert trust_relation["history_summary"]["withdrawal_reason"] == "review window expired"
    assert trust_relation["history_summary"]["withdrawn_at"] is not None
    assert trust_relation["federation_implication"]["status"] == "withdrawn_advisory"
    assert trust_node["latest_activity_summary"]["status"] == "withdrawn_relation_present"
    assert trust_node["domain_coverage_summary"]["active_relation_count"] == 0
    assert trust_node["domain_coverage_summary"]["withdrawn_relation_count"] == 1
    retrieval_detail = service.detail_payload(f"/api/runtime-records/{ids['runtime_plan_event_id']}")["record"]
    assert "runtime_retrieval_plan" in retrieval_detail["payload"]
    assert retrieval_detail["runtime_record_preview"]["record_kind"] == "retrieval_plan"
    assert retrieval_detail["posture_role"]["status"] == "retrieval_handoff_preview"
    assert retrieval_detail["downstream_boundary_note"]["status"] == "external_runtime_boundary"
    assert retrieval_detail["trial_sufficiency_summary"]["message"].startswith(
        "Retrieval handoff includes an import-readiness posture"
    )
    assert retrieval_detail["handoff_summary"]["status"] == "retrieval_handoff_available"
    assert retrieval_detail["handoff_summary"]["downstream_command_count"] >= 1
    assert retrieval_detail["retrieval_handoff"]["query"] == "UI Context"
    assert retrieval_detail["retrieval_handoff"]["package_review_required"] is True
    assert retrieval_detail["retrieval_handoff"]["downstream_commands"][0].startswith("chronicle package review")
    assert retrieval_detail["retrieval_handoff"]["composition"]["total_hit_count"] >= 1
    assert retrieval_detail["retrieval_handoff"]["composition"]["source_summaries"][0]["source"] == "vector_index"
    assert retrieval_detail["retrieval_handoff"]["downstream_command_details"][0]["summary_key"] == (
        "ui.template.retrieval_handoff.command.package_review"
    )
    assert retrieval_detail["query_engine_handoff_preview"]["status"] == "contract_available"
    assert retrieval_detail["query_engine_handoff_preview"]["counts_summary_key"] == (
        "ui.template.query_engine_handoff.counts"
    )
    assert retrieval_detail["query_engine_handoff_preview"]["suggested_command_details"][0]["summary_key"] == (
        "ui.template.query_engine_handoff.command.graph_summary"
    )
    assert retrieval_detail["query_engine_handoff_preview"]["boundary_note_key"] == (
        "ui.query_engine_handoff.note.read_only_derived"
    )
    assert retrieval_detail["query_engine_handoff_preview"]["import_validation"]["message_key"] == (
        "ui.query_engine_import_validation.message.contract_validated"
    )
    assert retrieval_detail["query_engine_handoff_preview"]["import_validation"]["counts_summary_key"] == (
        "ui.template.query_engine_import_validation.counts"
    )


def test_artifact_detail_exposes_workbench_summaries(tmp_path):
    ChronicleService(tmp_path).init("Artifact Workbench")
    context = ContextService(tmp_path).add_context(
        title="Workbench Context",
        visibility_hint=VisibilityHint.PUBLIC,
    )
    artifact, first_version = ArtifactService(tmp_path).create(
        title="Workbench Artifact",
        artifact_type=ArtifactType.DOCUMENT,
        content="first version",
        visibility_hint=VisibilityHint.PRIVATE,
        source=SourceProvenance(source_type="context", source_ref=context.context_id),
    )
    _updated_artifact, second_version = ArtifactService(tmp_path).update(
        artifact.artifact_id,
        content="second version",
        summary="Refined workbench narrative",
    )
    decision = DecisionService(tmp_path).record(
        decision_type=DecisionType.ACCEPTED,
        reason="Accept workbench direction",
        artifact_id=artifact.artifact_id,
    )
    rde_record = RdeService(tmp_path).record(
        artifact_id=artifact.artifact_id,
        from_version_id=first_version.version_id,
        to_version_id=second_version.version_id,
        summary="Tracked workbench change",
        unresolved=["Confirm audit linkage"],
        deviation_risks=["Semantic drift"],
    )
    audit_event = AuditService(tmp_path).record(
        operation=AuditOperation.CONTEXT_USE,
        actor="tester",
        purpose="artifact workbench audit",
        target_environment=AuditTargetEnvironment.LOCAL,
        referenced_records=[
            artifact.artifact_id,
            context.context_id,
            decision.decision_id,
            rde_record.rde_record_id,
        ],
        source_event_id=second_version.source_event_id,
        result=AuditSeverity.INFO,
        summary="Workbench artifact audit",
    )
    ChronicleService(tmp_path).rebuild_indexes()

    service = ChronicleUIDataService(tmp_path)
    detail = service.detail_payload(f"/api/artifacts/{artifact.artifact_id}")["record"]

    assert detail["linked_contexts"] == [
        {
            "context_id": context.context_id,
            "title": "Workbench Context",
            "scope": "project",
            "visibility_hint": "public",
            "detail_path": f"/api/contexts/{context.context_id}",
            "linked_via": ["artifact_source"],
        }
    ]
    assert detail["linked_decisions"][0]["decision_id"] == decision.decision_id
    assert detail["linked_decisions"][0]["detail_path"] == f"/api/decisions/{decision.decision_id}"
    assert detail["linked_rde_records"] == [
        {
            "rde_record_id": rde_record.rde_record_id,
            "summary": "Tracked workbench change",
            "created_at": rde_record.created_at.isoformat(),
            "from_version_id": first_version.version_id,
            "to_version_id": second_version.version_id,
            "unresolved_count": 1,
            "deviation_risk_count": 1,
            "detail_path": f"/api/rde/{rde_record.rde_record_id}",
        }
    ]
    assert detail["source_event_summary"]["status"] == "available"
    assert detail["source_event_summary"]["event_count"] == 2
    assert detail["source_event_summary"]["version_count"] == 2
    assert detail["source_event_summary"]["latest_event_id"] == second_version.source_event_id
    assert detail["boundary_summary"]["status"] == "advisory"
    assert detail["boundary_summary"]["visibility_hint"] == "private"
    assert detail["boundary_summary"]["source_type"] == "context"
    assert detail["boundary_summary"]["linked_context_count"] == 1
    assert detail["audit_summary"]["status"] == "related_audits_present"
    assert detail["audit_summary"]["audit_event_count"] == 1
    assert detail["audit_summary"]["latest_audit_id"] == audit_event.audit_id
    assert detail["audit_summary"]["latest_detail_path"] == f"/api/audit/{audit_event.audit_id}"
    assert detail["audit_summary"]["operation_counts"] == {"context_use": 1}
    assert detail["audit_summary"]["result_counts"] == {"info": 1}
    assert detail["audit_summary"]["audits"][0]["matched_record_ids"] == [
        artifact.artifact_id,
        context.context_id,
        decision.decision_id,
        rde_record.rde_record_id,
    ]
    assert detail["audit_summary"]["audits"][0]["source_event_matched"] is True


def test_ui_read_models_expose_matching_federation_consent_summary_on_overlap(tmp_path):
    ids = _populate(tmp_path)
    consent_payload = FederationPackageService(tmp_path).record_consent(
        target_node="node:partner:beta",
        purpose="overlap review",
        scope="overlap-scope",
        granted_by="overlap-owner",
        third_party_sharing_allowed=False,
        context_ids=[ids["context_id"]],
    )
    summary_result = RuntimeService(tmp_path).summarize(
        text="Linked runtime summary for consent overlap.",
        record=False,
    )
    event = ChronicleService(tmp_path).record_event(
        event_type=EventType.ASSISTANT_OUTPUT,
        actor=Actor.ASSISTANT,
        summary="Runtime summary generated: linked overlap summary",
        payload={
            "runtime_summary": summary_result.model_dump(mode="json"),
            "runtime_provider": summary_result.provider_kind.value,
        },
        context_ids=[ids["context_id"]],
        source=SourceProvenance(
            source_type="runtime",
            source_ref=ids["context_id"],
            source_tool="chronicle-runtime",
            source_model=summary_result.model_name,
        ),
        review_status=ReviewStatus.NEEDS_REVIEW,
        confidence=Confidence.LOW,
    )
    service = ChronicleUIDataService(tmp_path)

    runtime_row = next(
        row for row in service.runtime_records()["runtime_records"] if row["event_id"] == event.event_id
    )
    assert runtime_row["matching_federation_consent_summary"]["audit_id"] == consent_payload["audit_id"]
    assert runtime_row["matching_federation_consent_summary"]["message_key"] == (
        "ui.federation_consent_match.message.overlap_found"
    )
    assert runtime_row["matching_federation_consent_summary"]["counts_summary_key"] == (
        "ui.template.federation_consent_match.counts"
    )
    assert runtime_row["matching_federation_consent_summary"]["matched_record_ids"] == [ids["context_id"]]
    assert runtime_row["matching_federation_consent_summary"]["boundary_note_key"] == (
        "ui.federation_consent_match.note.read_only_derived"
    )

    review_row = next(
        row for row in service.review_queue()["review_queue"] if row["target_event_id"] == event.event_id
    )
    assert review_row["matching_federation_consent_summary"]["audit_id"] == consent_payload["audit_id"]
    assert review_row["matching_federation_consent_summary"]["matched_record_ids"] == [ids["context_id"]]

    runtime_detail = service.detail_payload(f"/api/runtime-records/{event.event_id}")["record"]
    assert runtime_detail["matching_federation_consent_summary"]["audit_id"] == consent_payload["audit_id"]

    review_detail = service.detail_payload(f"/api/review-queue/{event.event_id}")["record"]
    assert review_detail["matching_federation_consent_summary"]["audit_id"] == consent_payload["audit_id"]
    overview = service.overview()
    assert overview["federation_overlap_summary"]["status"] == "overlaps_present"
    assert overview["federation_overlap_summary"]["message_key"] == (
        "ui.federation_overlap.message.overlaps_present"
    )
    assert overview["federation_overlap_summary"]["counts_summary_key"] == (
        "ui.template.federation_overlap.counts"
    )
    assert overview["federation_overlap_summary"]["runtime_overlap_count"] >= 1
    assert overview["federation_overlap_summary"]["review_overlap_count"] >= 1
    assert overview["federation_overlap_summary"]["consent_audit_count"] == 1
    assert overview["federation_overlap_summary"]["latest_matching_audit_id"] == consent_payload["audit_id"]
    assert overview["federation_overlap_summary"]["latest_matching_detail_path"] == (
        f"/api/audit/{consent_payload['audit_id']}"
    )
    assert overview["federation_overlap_summary"]["latest_target_node"] == "node:partner:beta"
    assert overview["federation_overlap_summary"]["latest_scope"] == "overlap-scope"
    assert overview["federation_overlap_summary"]["boundary_note_key"] == (
        "ui.federation_overlap.note.read_only_derived"
    )


def test_runtime_records_include_query_engine_trial_rows(tmp_path):
    _populate(tmp_path)
    os.chdir(str(tmp_path))
    runner = CliRunner()
    output_dir = tmp_path / "handoff-bundle"
    result = runner.invoke(
        app,
        [
            "package",
            "query-engine-bundle",
            "--query",
            "UI Context",
            "--output-dir",
            str(output_dir),
        ],
    )
    assert result.exit_code == 0
    record_result = runner.invoke(
        app,
        [
            "package",
            "query-engine-trial-record",
            "--bundle-dir",
            str(output_dir),
            "--reviewer",
            "ui-reviewer",
            "--consumer",
            "ui-consumer",
            "--sufficient",
            "--json",
        ],
    )
    assert record_result.exit_code == 0
    event_id = json.loads(record_result.stdout)["event_id"]

    service = ChronicleUIDataService(tmp_path)
    rows = service.runtime_records()["runtime_records"]
    trial_row = next(row for row in rows if row["event_id"] == event_id)
    assert trial_row["runtime_record_kind"] == "query_engine_trial"
    assert trial_row["runtime_record_preview"]["title_key"] == "ui.template.runtime_preview.title.query_engine_trial"
    assert trial_row["query_engine_trial_preview"]["message_key"] == "ui.query_engine_trial.message.recorded"
    assert trial_row["query_engine_trial_preview"]["query"] == "UI Context"
    assert trial_row["query_engine_trial_preview"]["files_reviewed"][0] == "bundle_manifest.json"

    detail = service.detail_payload(f"/api/runtime-records/{event_id}")["record"]
    assert detail["runtime_record_kind"] == "query_engine_trial"
    assert detail["query_engine_trial_preview"]["query"] == "UI Context"
    assert detail["query_engine_trial_preview"]["bundle_dir"].endswith("handoff-bundle")
    assert detail["query_engine_trial_preview"]["bundle_manifest_path"].endswith(
        "handoff-bundle/bundle_manifest.json"
    )
    assert detail["query_engine_trial_preview"]["reviewer"] == "ui-reviewer"
    assert detail["query_engine_trial_preview"]["downstream_consumer"] == "ui-consumer"
    assert detail["query_engine_trial_preview"]["sufficient"] is True
    assert detail["query_engine_trial_preview"]["sufficient_summary_key"] == "ui.boolean.true"
    assert detail["query_engine_trial_preview"]["import_validation_status"] in {
        "contract_validated",
        "advisory_only",
    }
    assert isinstance(detail["query_engine_trial_preview"]["import_ready"], bool)
    assert detail["query_engine_trial_preview"]["import_ready_summary_key"] in {
        "ui.boolean.true",
        "ui.boolean.false",
    }
    assert "query_engine_handoff.json" in detail["query_engine_trial_preview"]["files_reviewed"]
    assert detail["query_engine_trial_preview"]["boundary_note_key"] == (
        "ui.query_engine_trial.note.read_only_derived"
    )
    assert detail["query_engine_trial_preview"]["message_key"] == "ui.query_engine_trial.message.recorded"


def test_runtime_records_include_ai_boundary_preview_rows(tmp_path):
    from datetime import datetime, timezone

    from chronicle.models.context import Context, ContextScope
    from chronicle.models.event import Actor, ChronicleEvent, EventType
    from chronicle.services.ai_boundary_service import AiBoundaryService

    ChronicleService(tmp_path).init("UI AI Boundary")
    metadata = ChronicleService(tmp_path).load_metadata()
    ChronicleService(tmp_path).append_event(
        ChronicleEvent(
            event_id="evt_ui_ai_boundary",
            chronicle_id=metadata.chronicle_id,
            timestamp=datetime(2026, 6, 28, tzinfo=timezone.utc),
            event_type=EventType.CONTEXT_ADDED,
            actor=Actor.USER,
            summary="Add UI AI Boundary Context",
            payload={
                "context": Context(
                    context_id="ctx_ui_ai_boundary",
                    title="UI AI Boundary Context",
                    summary="Context for AI boundary preview UI",
                    scope=ContextScope.TASK,
                    created_at=datetime(2026, 6, 28, tzinfo=timezone.utc),
                ).model_dump(mode="json")
            },
        )
    )
    ChronicleService(tmp_path).rebuild_indexes()
    preview = AiBoundaryService(tmp_path).preview(
        task="ui ai boundary review",
        model_id="external:test-model",
        context_ids=["ctx_ui_ai_boundary"],
        record=True,
    )

    service = ChronicleUIDataService(tmp_path)
    rows = service.runtime_records()["runtime_records"]
    row = next(item for item in rows if item["event_id"] == preview.event_id)
    assert row["runtime_record_kind"] == "ai_boundary_preview"
    assert row["runtime_record_preview"]["suggested_cli_family"] == "chronicle ai-boundary preview --record"

    detail = service.detail_payload(f"/api/runtime-records/{preview.event_id}")["record"]
    assert detail["runtime_record_preview"]["record_kind"] == "ai_boundary_preview"
    assert any(link["path"] == "/api/contexts/ctx_ui_ai_boundary" for link in detail["related_links"])


def test_context_sns_views_include_reactions_and_lineage(tmp_path):
    from chronicle.models.chronicle_object import ChronicleObjectType
    from chronicle.models.reaction import ChronicleReactionType
    from chronicle.services.chronicle_object_service import ChronicleObjectService
    from chronicle.services.reaction_service import ReactionService

    ids = _populate(tmp_path)
    objection = ChronicleObjectService(tmp_path).record(
        object_type=ChronicleObjectType.OBJECTION,
        summary="Need stronger evidence",
        created_by="reviewer",
        detail="Current claim lacks support.",
        artifact_id=ids["artifact_id"],
        decision_id=ids["decision_id"],
    )
    ReactionService(tmp_path).record(
        reaction_type=ChronicleReactionType.INSUFFICIENT_EVIDENCE,
        created_by="reviewer",
        target_object_id=objection.object_id,
        summary="Evidence is insufficient",
        detail="Requesting more support before adoption.",
        target_artifact_id=ids["artifact_id"],
        target_decision_id=ids["decision_id"],
    )

    service = ChronicleUIDataService(tmp_path)
    reactions = service.reaction_records()["reactions"]
    assert reactions[0]["reaction_type"] == "insufficient_evidence"
    assert reactions[0]["related_resource_paths"][0] == f"/api/chronicle-objects/{objection.object_id}"

    lineage_rows = service.lineage_view()["lineage_view"]
    lineage_row = next(row for row in lineage_rows if row["lineage_id"] == objection.object_id)
    assert lineage_row["reaction_count"] == 1

    objection_rows = service.objection_view()["objection_view"]
    assert any(row["object_id"] == objection.object_id for row in objection_rows)

    contract = service.context_sns_contract()["context_sns_contract"]
    assert contract["question_follow_design"]["status"] == "design_only"
    assert "reference" in contract["reaction_types"]


def test_overview_runtime_records_summarize_query_engine_trials(tmp_path):
    _populate(tmp_path)
    os.chdir(str(tmp_path))
    runner = CliRunner()
    first_output_dir = tmp_path / "handoff-bundle-a"
    second_output_dir = tmp_path / "handoff-bundle-b"
    first_bundle = runner.invoke(
        app,
        ["package", "query-engine-bundle", "--query", "UI Context", "--output-dir", str(first_output_dir)],
    )
    assert first_bundle.exit_code == 0
    second_bundle = runner.invoke(
        app,
        ["package", "query-engine-bundle", "--query", "Gap Context", "--output-dir", str(second_output_dir)],
    )
    assert second_bundle.exit_code == 0
    sufficient_record = runner.invoke(
        app,
        [
            "package",
            "query-engine-trial-record",
            "--bundle-dir",
            str(first_output_dir),
            "--reviewer",
            "ui-reviewer",
            "--consumer",
            "ui-consumer",
            "--sufficient",
            "--json",
        ],
    )
    assert sufficient_record.exit_code == 0
    insufficient_record = runner.invoke(
        app,
        [
            "package",
            "query-engine-trial-record",
            "--bundle-dir",
            str(second_output_dir),
            "--reviewer",
            "ui-reviewer",
            "--consumer",
            "ui-consumer-b",
            "--insufficient",
            "--missing-behavior",
            "needs hosted runtime",
            "--json",
        ],
    )
    assert insufficient_record.exit_code == 0
    insufficient_event_id = json.loads(insufficient_record.stdout)["event_id"]

    overview = ChronicleUIDataService(tmp_path).overview()
    summary = overview["runtime_records_summary"]["query_engine_trial_summary"]
    assert summary["total_count"] == 2
    assert summary["sufficient_count"] == 1
    assert summary["insufficient_count"] == 1
    assert summary["import_ready_count"] >= 1
    assert summary["consumer_counts"]["ui-consumer"] == 1
    assert summary["consumer_counts"]["ui-consumer-b"] == 1
    assert summary["latest_trial_detail_path"] == f"/api/runtime-records/{insufficient_event_id}"
    escalation = overview["runtime_records_summary"]["query_engine_trial_escalation_summary"]
    assert escalation["status"] == "watch"
    assert escalation["active_count"] == 1
    assert escalation["insufficient_trial_count"] == 1
    assert "single_insufficient_trial" in escalation["reasons"]
    assert "needs hosted runtime" in escalation["top_missing_behaviors"]
    assert overview["triage"]["query_engine_trial_escalation_summary"]["status"] == "watch"
    assert overview["triage"]["query_engine_trial_escalation_drilldown_summary"]["detail_path"] == (
        f"/api/runtime-records/{insufficient_event_id}"
    )
    assert (
        "Downstream Query-Engine Escalation Follow-up"
        in overview["triage"]["query_engine_trial_escalation_drilldown_summary"]["issue_template_body"]
    )


def test_overview_runtime_records_escalate_repeated_query_engine_trials(tmp_path):
    _populate(tmp_path)
    os.chdir(str(tmp_path))
    runner = CliRunner()
    first_output_dir = tmp_path / "handoff-bundle-a"
    second_output_dir = tmp_path / "handoff-bundle-b"
    assert runner.invoke(
        app,
        ["package", "query-engine-bundle", "--query", "Gap A", "--output-dir", str(first_output_dir)],
    ).exit_code == 0
    assert runner.invoke(
        app,
        ["package", "query-engine-bundle", "--query", "Gap B", "--output-dir", str(second_output_dir)],
    ).exit_code == 0
    assert runner.invoke(
        app,
        [
            "package",
            "query-engine-trial-record",
            "--bundle-dir",
            str(first_output_dir),
            "--reviewer",
            "ui-reviewer",
            "--consumer",
            "shared-consumer",
            "--insufficient",
            "--missing-behavior",
            "needs hosted runtime",
            "--json",
        ],
    ).exit_code == 0
    second_record = runner.invoke(
        app,
        [
            "package",
            "query-engine-trial-record",
            "--bundle-dir",
            str(second_output_dir),
            "--reviewer",
            "ui-reviewer",
            "--consumer",
            "shared-consumer",
            "--insufficient",
            "--missing-behavior",
            "needs hosted runtime",
            "--json",
        ],
    )
    assert second_record.exit_code == 0
    second_event_id = json.loads(second_record.stdout)["event_id"]

    overview = ChronicleUIDataService(tmp_path).overview()
    escalation = overview["runtime_records_summary"]["query_engine_trial_escalation_summary"]
    assert escalation["status"] == "escalate"
    assert escalation["active_count"] == 2
    assert escalation["insufficient_trial_count"] == 2
    assert escalation["repeated_insufficient_consumers"] == ["shared-consumer"]
    assert escalation["top_missing_behaviors"] == ["needs hosted runtime"]
    assert escalation["latest_trial_detail_path"] == f"/api/runtime-records/{second_event_id}"
    assert "repeated_insufficient_trials" in escalation["reasons"]
    assert "repeated_consumer_insufficient" in escalation["reasons"]
    triage_escalation = overview["triage"]["query_engine_trial_escalation_summary"]
    assert triage_escalation["status"] == "escalate"
    assert triage_escalation["active_count"] == 2
    drilldown = overview["runtime_records_summary"]["query_engine_trial_escalation_drilldown_summary"]
    assert drilldown["status"] == "escalate"
    assert drilldown["active_count"] == 2
    assert drilldown["detail_path"] == f"/api/runtime-records/{second_event_id}"
    assert drilldown["issue_template_title"] == "Downstream query-engine escalation follow-up"
    assert "repeated_insufficient_consumers: shared-consumer" in drilldown["issue_template_body"]


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
    assert detail["invocation_plan"]["message_key"] == "ui.invocation_plan.message.blocked"
    assert detail["invocation_plan"]["provider_summary_key"] == (
        "ui.template.invocation_plan.provider_summary"
    )
    assert detail["invocation_plan"]["invocation_ready_summary_key"] == "ui.boolean.false"
    assert detail["invocation_plan"]["would_use_network_summary_key"] == "ui.boolean.true"
    assert detail["invocation_plan"]["network_allowed_by_contract_summary_key"] == "ui.boolean.false"
    assert detail["invocation_plan"]["downstream_command_details"][0]["summary_key"] == (
        "ui.template.invocation_plan.command.runtime_config_show"
    )
    assert "network_not_allowed_by_contract" in detail["invocation_plan"]["blocking_reasons"]
    assert detail["invocation_plan"]["execution_request"]["prompt"] == "Invocation summary prompt."
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
    assert review_detail["review_capability"]["status_summary_key"] == "ui.review_capability.status.ready"
    assert review_detail["review_capability"]["can_review_now"] is True
    assert review_detail["review_capability"]["can_review_now_summary_key"] == "ui.boolean.true"
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
    assert review_detail["action_preview"]["failure_contract"]["possible_error_details"][0]["message_key"] == (
        "ui.review_action_failure.message.mutation_disabled"
    )
    assert review_detail["action_preview"]["cli_equivalent_detail"]["summary_key"] == (
        "ui.template.review_action_preview.cli_equivalent_summary"
    )
    assert review_detail["action_preview"]["failure_contract"]["recovery_command_details"][0]["summary_key"] == (
        "ui.template.review_action_preview.recovery_summary"
    )
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
    assert review_detail["auth_boundary_notice"]["capability_status_summary_key"] == (
        "ui.review_capability.status.ready"
    )
    assert review_detail["auth_boundary_notice"]["identity_assurance_status_summary_key"] == (
        "ui.identity_assurance.status.boundary_aligned"
    )
    assert review_detail["auth_boundary_notice"]["blockers"] == []
    assert review_detail["latest_identity_assurance"]["status"] == "boundary_aligned"
    assert review_detail["latest_identity_assurance"]["status_summary_key"] == (
        "ui.identity_assurance.status.boundary_aligned"
    )
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
    assert rows[0]["action_preview_summary"]["recovery_summary_key"] == (
        "ui.template.review_action_preview.recovery_summary"
    )
    assert rows[0]["action_preview_summary"]["follow_up_summary_key"] == (
        "ui.template.review_action_preview.follow_up_summary"
    )


def test_ui_shell_contains_interactive_local_ui(tmp_path):
    ChronicleService(tmp_path).init("UI Shell")

    html = ChronicleUIDataService(tmp_path).html_shell()

    assert "Chronicle Stack ローカルUI" in html
    assert "読み取り専用の前景ローカルUIです。" in html
    assert ".shell-grid {" in html
    assert "white-space: nowrap;" in html
    assert "#detail { position: sticky;" in html
    assert "@media (max-width: 980px)" in html
    assert "window.__chronicleMutationToken =" in html
    assert "window.__chronicleMutationSessionId =" in html
    assert "headers['X-Chronicle-UI-Mutation-Token'] = window.__chronicleMutationToken;" in html
    assert "mutation_request_id: 'mrq-' + sessionId" in html
    assert '<div class="shell-grid">' in html
    assert ".json-block {" in html
    assert ".fact-line {" in html
    assert ".fact-label {" in html
    assert ".fact-value {" in html
    assert ".notice-section {" in html
    assert ".fold-section {" in html
    assert ".cell-title {" in html
    assert ".cell-meta {" in html
    assert ".cell-stack {" in html
    assert "display: flex;" in html
    assert "min-width: 11rem;" in html
    assert ".cell-details {" in html
    assert ".cell-details-body > * + *" in html
    assert ".cell-actions {" in html
    assert "loadDetail" in html
    assert "label('notice.runtime_preview', 'Runtime Preview')" in html
    assert "label('notice.retrieval_handoff', 'Retrieval Handoff')" in html
    assert "label('notice.query_engine_handoff_preview', 'Query-Engine Handoff Preview')" in html
    assert "detailLine('Import validation', localizedImportValidation)" in html
    assert "detailListLine('Composed hits', composedHits)" in html
    assert "const localizedDownstreamCommands = (Array.isArray(handoff.downstream_command_details) ? handoff.downstream_command_details : []).map(item => (" in html
    assert "detailListLine('Downstream commands', localizedDownstreamCommands.length > 0 ? localizedDownstreamCommands : handoff.downstream_commands, ' | ')" in html
    assert "label('notice.invocation_plan', 'Invocation Plan')" in html
    assert "label('notice.package_handoff_preview', 'Package Handoff Preview')" in html
    assert "preview.counts_summary_key" in html
    assert "const localizedSuggestedCommands = (Array.isArray(preview.suggested_command_details) ? preview.suggested_command_details : []).map(item => (" in html
    assert "label('notice.review_package_readiness', 'Review Package Readiness')" in html
    assert "readiness.counts_summary_key" in html
    assert "const localizedSuggestedCommands = (Array.isArray(readiness.suggested_command_details) ? readiness.suggested_command_details : []).map(item => (" in html
    assert "label('notice.provider_response', 'Provider Response')" in html
    assert "summary.counts_summary_key" in html
    assert "label('notice.related_links', 'Related Links')" in html
    assert "readiness.label_key" in html
    assert "const localizedMessage = localizedPayloadText(handoff);" in html
    assert "handoff.hit_counts_summary_key" in html
    assert "plan.provider_summary_key" in html
    assert "detailNavButton(item.path || '', localizedLinkLabel(item))" in html
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
    assert "function localizedPayloadText(item, keyField = 'message_key', fallbackField = 'message', paramsField = 'message_params')" in html
    assert "item && item.message_key" in html
    assert "formatLabel(item.message_key, item.message_params || {}, item.message || '')" in html
    assert "return fallback.map(item => reviewWarningLabel(item)).join(' | ') || '';" in html
    assert "function contractDetailLines(successContract, failureContract, targetId)" in html
    assert "function renderReviewActionResultPanel(title, responseStatus, path, payload, targetId, options = {})" in html
    assert "function renderReviewMutationForm(title, prefix)" in html
    assert "function renderPreviewSummary(preview)" in html
    assert "cli=" in html
    assert "recovery=" in html
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
    assert "function renderRuntimeRecordsWorkspacePanel(summary)" in html
    assert "function renderReviewQueueWorkspacePanel(summary)" in html
    assert "function renderSummaryJobsWorkspacePanel(summary)" in html
    assert "function renderGenericTable(endpoint, rows)" in html
    assert "const endpointRenderers =" in html
    assert "reviewerIdentityBadge" in html
    assert "sortSelect" in html
    assert "sortRuntimeRows" in html
    assert "function mutationSummaryRank(summary)" in html
    assert "function authStatusRank(status)" in html
    assert "function attentionRankFromStatuses(reviewStatus, packageStatus, parityStatus)" in html
    assert "function compareRuntimeReadiness(left, right, primary = 'mutation')" in html
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
    assert "const localizedTitle = preview.title_key" in html
    assert "function packageContextDetailLines(packageReview, manifest, eligibleContextIds = [], extraLines = '')" in html
    assert "function packageContextNoticeBody(status, message, packageReview, manifest, eligibleContextIds = [], extraLines = '', buttons = [])" in html
    assert "function statusScopeNoticeBody(status, message, buttons = [], scopeNote = '')" in html
    assert "function blockerSummaryDetailLines(blockerDetails, blockers, blockerSummaries = [], nextSteps = [])" in html
    assert "function writeRouteDetailLines(writeRouteContract, identityProofContract, authorizationContract, targetStateContract, includeRequestFields = false)" in html
    assert "function mutationOperationalDetailLines(operationalReadiness, blockerSummaries, enablementChecks, checksLabel = 'Enablement checks')" in html
    assert "const localizedChecks = enablementChecks.map(check => {" in html
    assert "check && check.label_key" in html
    assert "formatLabel(check.label_key, check.label_params || {}, check.label || check.code || 'check')" in html
    assert "operationalReadiness.unsatisfied_checks" in html
    assert "item && item.summary_key" in html
    assert "formatLabel(item.summary_key, item.summary_params || {}, ((item.label || item.code || 'check') + ': ' + (item.detail || '')))" in html
    assert "function reviewerLabelDetailLines(reviewerContext)" in html
    assert "function recoveryContractDetailLines(failureContract, targetId = 'action-preview-response')" in html
    assert "function identityBoundaryDetailLines(identityBoundary)" in html
    assert "function renderAuthReadinessNotice(record)" in html
    assert "localizedPayloadText(notice)" in html
    assert "localizedPayloadText(capability)" in html
    assert "localizedPayloadText(assurance)" in html
    assert "label('section.operational_readiness', 'Operational Readiness')" in html
    assert "label('section.reviewer_context', 'Reviewer Context')" in html
    assert "label('section.write_route_contract', 'Write Route Contract')" in html
    assert "label('section.next_steps', 'Next Steps')" in html
    assert "function renderDetailActionPreviewControls(preview, actions, mutationTargetEventId)" in html
    assert "function renderDetailActionPreviewList(preview, actions)" in html
    assert "function renderDetailActionPreviewNotice(record)" in html
    assert "function noticeSectionGroup(sections)" in html
    assert "function sliceButtonRows(rows)" in html
    assert "async function responseJsonOrEmpty(response)" in html
    assert "async function postJson(path, body = undefined)" in html
    assert "function appendCommandFeedback(target, command, copied)" in html
    assert "async function tryCopyText(command)" in html
    assert "function reviewActionRequestBody(action, fieldPrefix = 'reviewer')" in html
    assert "function reloadCurrentEndpoint()" in html
    assert "function handleViewClick(event)" in html
    assert "function handleDetailClick(event)" in html
    assert "if (event.target.dataset.detailNav) loadDetail(event.target.dataset.detailNav);" in html
    assert "function handleViewInput(event)" in html
    assert "function handleViewChange(event)" in html
    assert "function renderPanel(body)" in html
    assert "function renderWorkspaceSummaryPanel(title, countLines, summaryPairs, latestResponsePath, latestResponseLabelKey, latestResponseFallback)" in html
    assert "function renderMultiPanelRoute(panels, payload = null, includeResponseJson = false)" in html
    assert "function renderMultiPanelDetail(panels, payload)" in html
    assert "function workspaceCountLine(labelText, value)" in html
    assert "function workspaceLatestResponseLine(path, labelKey, fallbackLabel)" in html
    assert "function workspaceSummaryLines(summaryPairs)" in html
    assert "function renderOverviewHeaderPanel(chronicle)" in html
    assert "function renderOverviewCountsPanel(counts)" in html
    assert "function renderOverviewRuntimeBoundaryPanel(runtime)" in html
    assert "function renderOverviewFederationPanel(federationSummary, federationPreflight, federationOverlap)" in html
    assert "function renderOverviewAuthBoundaryPanel(authBoundary, authBoundaryOverview)" in html
    assert "function renderOverviewIdentityBoundaryPanel(identityBoundary)" in html
    assert "localizedPayloadText(authBoundary)" in html
    assert "localizedPayloadText(identityBoundary)" in html
    assert "function renderOverviewReviewerBoundaryPanel(reviewerBoundary)" in html
    assert "function renderReviewerBoundaryDrilldownSummary(summary)" in html
    assert "function reviewerBoundaryDominantButtons(drilldownSummaries)" in html
    assert "function formatLabel(key, replacements = {}, fallback = '')" in html
    assert "function reviewerBoundaryDatasetLabel(datasetKey)" in html
    assert "function reviewerBoundaryStatusText(status)" in html
    assert "label('button.open_list', 'Open List')" in html
    assert "label('button.open_detail', 'Open Detail')" in html
    assert "label('ui.label.dataset', 'Dataset')" in html
    assert "Object.assign({}, summary.message_params || {}" in html
    assert "Object.assign({}, summary.fact_line_params || {}" in html
    assert "formatLabel(summary.message_template_key" in html
    assert "label(summary.message_key, summary.message || '')" in html
    assert "formatLabel(summary.fact_line_template_key" in html
    assert "item && item.summary_key" in html
    assert "formatLabel(item.summary_key, item.summary_params || {}, item.summary || item.code || 'blocker')" in html
    assert "function reviewerBoundaryFilterValue(kind, status)" in html
    assert "function reviewerBoundaryCountButtons(target, endpoint, enforcementCounts, gateCounts)" in html
    assert "function overviewRuntimeRecordCountButtons(counts, runtimeRecords)" in html
    assert "function renderOverviewRuntimeRecordsPanel(counts, runtimeRecords)" in html
    assert "function overviewSummaryJobCountButtons(counts, summaryJobs)" in html
    assert "function renderOverviewSummaryJobsPanel(counts, summaryJobs)" in html
    assert "renderWorkspaceSummaryPanel(" in html
    assert "label('section.runtime_records_workspace', 'Runtime Records Workspace')" in html
    assert "label('section.review_queue_workspace', 'Review Queue Workspace')" in html
    assert "label('section.summary_jobs_workspace', 'Summary Jobs Workspace')" in html
    assert "function overviewTriageCountRows(triage)" in html
    assert "function renderOverviewTriagePanel(triage, warningButtons, warningSummaries)" in html
    assert "function overviewWarningButtons(warningSummaries)" in html
    assert "function overviewWarningPriorityBadges(warningSummaries)" in html
    assert "function overviewTriageNavigationCluster(triage)" in html
    assert "function overviewTriageJumpButtons()" in html
    assert "const overviewPanelRenderers = [" in html
    assert "data => renderOverviewFederationPanel(data.federationSummary, data.federationPreflight, data.federationOverlap)," in html
    assert "label('overview.reviewer_runtime_enforcement_counts', 'Runtime enforcement counts')" in html
    assert "sectionTitle(label('section.federation', 'Federation'))" in html
    assert "detailJumpButton(federationOverlap.latest_matching_detail_path || '', label('button.open_detail', 'Open Detail'))" in html
    assert "detailLine('Boundary check CLI', federationPreflight.suggested_boundary_check_cli || '')" in html
    assert "const packageReviewCliCommands = [" in html
    assert "detailListLine('Package review CLIs', packageReviewCliCommands, ' | ')" in html
    assert "detailLine('Import review CLI', federationPreflight.suggested_import_preview_cli || '')" in html
    assert "openEndpointButton('/api/federation-inbox')" in html
    assert "openEndpointButton('/api/federation-outbox')" in html
    assert "openEndpointButton('/api/audit')" in html
    assert "label('ui.label.validation_gate_status', 'Validation gate status')" in html
    assert "label('ui.label.drilldown_datasets', 'Drilldown datasets')" in html
    assert "label('ui.label.drilldown_summary', 'Drilldown summary')" in html
    assert "label('ui.label.dominant_enforcement_status', 'Dominant enforcement status')" in html
    assert "label('ui.label.dominant_validation_gate_status', 'Dominant gate status')" in html
    assert "reviewerBoundaryDominantButtons(drilldownSummaries)" in html
    assert "reviewerBoundaryFilterValue('reviewer_enforcement', status)" in html
    assert "sliceButtonRows([" in html
    assert "reviewerBoundaryListButtons('runtimeRecords', '/api/runtime-records', sorted)" in html
    assert "reviewerBoundaryListButtons('reviewQueue', '/api/review-queue', sorted)" in html
    assert "reviewerBoundaryListButtons('summaryJobs', '/api/summary-jobs', sorted)" in html
    assert "function renderOverviewPanels(data)" in html
    assert "const detailPathResolvers =" in html
    assert "function endpointBody(endpoint, payload)" in html
    assert "function detailNavigationOptions(endpoint, record)" in html
    assert "const detailNoticeRenderers = [" in html
    assert "function renderFederationPackagePreview(payload)" in html
    assert "renderMultiPanelRoute([" in html
    assert "'button.open_latest_runtime_response'," in html
    assert "'button.open_latest_review_response'," in html
    assert "'button.open_latest_summary_response'," in html
    assert "sectionTitle(label('section.federation_package_preview', 'Federation Package Preview'))" in html
    assert "sectionTitle(label('section.package_route_summary', 'Package Route Summary'))" in html
    assert "sectionTitle(label('section.trust_reference_summary', 'Trust Reference Summary'))" in html
    assert "sectionTitle(label('section.consent_summary', 'Consent Summary'))" in html
    assert "sectionTitle(label('section.import_implication_summary', 'Import Implication Summary'))" in html
    assert "function renderAuditTable(endpoint, rows)" in html
    assert "function renderAuditGovernanceSummary(summary)" in html
    assert "function renderAuditTimelinePanel(endpoint, rows)" in html
    assert "function renderAuditInterpretationPanel(endpoint, rows)" in html
    assert "sectionTitle(label('section.audit_timeline', 'Audit Timeline'))" in html
    assert "sectionTitle(label('section.audit_interpretation', 'Audit Interpretation'))" in html
    assert "function renderBoundaryGovernanceSummary(rows)" in html
    assert "function renderBoundaryTable(endpoint, rows)" in html
    assert "function renderLifecycleGovernanceSummary(rows)" in html
    assert "function renderLifecycleTable(endpoint, rows)" in html
    assert "function renderBoundaryLifecycleGovernanceNotice(record)" in html
    assert "sectionTitle(label('section.boundary_governance', 'Boundary Governance'))" in html
    assert "sectionTitle(label('section.lifecycle_governance', 'Lifecycle Governance'))" in html
    assert "isBoundary ? 'notice.boundary_detail_governance' : 'notice.lifecycle_detail_governance'" in html
    assert "isBoundary ? 'Boundary Governance Link' : 'Lifecycle Governance Link'" in html
    assert "renderAuditGovernanceNotice," in html
    assert "renderBoundaryLifecycleGovernanceNotice," in html
    assert "renderRuntimeWorkspaceNotice," in html
    assert "renderSummaryJobWorkspaceNotice," in html
    assert "renderArtifactWorkbenchNotice," in html
    assert "'/api/audit': renderAuditTable," in html
    assert "'/api/boundary': renderBoundaryTable," in html
    assert "'/api/lifecycle': renderLifecycleTable," in html
    assert "if (endpoint === '/api/federation-package-preview') return renderFederationPackagePreview(payload);" in html
    assert "function renderDetailNoticePanels(record)" in html
    assert "function detailNoticeBody(endpoint, record)" in html
    assert "function renderReviewerBoundaryDrilldownNotice(record)" in html
    assert "label('notice.reviewer_boundary_drilldown', 'Reviewer Boundary Drilldown')" in html
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
    assert "function emptyFilterButtons(target)" in html
    assert "function emptyFilterState(query, rows, message, target)" in html
    assert "function listToolbar(endpoint, target, placeholder, sortOptions, filterChipHtml, query)" in html
    assert "function renderWorkspaceTableControls(toolbarHtml, buttonRows, query, rows, emptyMessage, target, mutationConfig, previewConfig)" in html
    assert "function responseMetadataQueryTokens(responseMetadata)" in html
    assert "function reviewerIdentityQueryTokens(row)" in html
    assert "function rowMatchesWorkspaceQuery(query, row, queryTokens)" in html
    assert "function actionPreviewStatus(targetId, mutationEnabled, enabledMessage, disabledMessage)" in html
    assert "function tableHtml(headers, body)" in html
    assert "function packageReviewButtons(record)" in html
    assert "function firstRelatedLink(record, prefix)" in html
    assert "function openEndpointButton(endpoint)" in html
    assert "function latestResponseButton(path, labelKey, fallbackLabel)" in html
    assert "function endpointLatestResponseCluster(endpoint, path, labelKey, fallbackLabel)" in html
    assert "function overviewCountButton(text, count, cls, endpoint, filterTarget, filterValue)" in html
    assert "function detailNavButton(path, labelText)" in html
    assert "function detailButton(path)" in html
    assert "function reviewDetailButton(eventId)" in html
    assert "function reviewQueueStatusButtons(status, prefix = '')" in html
    assert "function relatedDetailButton(record, prefix, fallbackLabel = '')" in html
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
    assert "function metricsSection(body)" in html
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
    assert "function detailJumpButton(path, labelText)" in html
    assert "function renderArtifactWorkbenchNotice(record)" in html
    assert "label('notice.artifact_workbench', 'Artifact Workbench')" in html
    assert "detailListLine('Linked contexts', contextSummaries, ' | ')" in html
    assert "detailListLine('Linked decisions', decisionSummaries, ' | ')" in html
    assert "detailListLine('Linked RDE records', rdeSummaries, ' | ')" in html
    assert "detailLine('Source-event scope note', localizedSourceBoundaryNote)" in html
    assert "detailLine('Boundary visibility', boundarySummary.visibility_hint || '')" in html
    assert "summaryJsonLine('Audit operations', auditSummary.operation_counts)" in html
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
    assert "summaryJsonLine('Trial escalation', triage.query_engine_trial_escalation_summary)" in html
    assert "renderQueryEngineTrialEscalationDrilldownSummary(triage.query_engine_trial_escalation_drilldown_summary || {})" in html
    assert "label('button.copy_issue_body', 'Copy issue body')" in html
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
    assert "function reviewerContextDetailLines(reviewerContext, identityProofContract = {})" in html
    assert "const expectationSummary = reviewerContext.expectation_summary_key" in html
    assert "detailLine('Reviewer expectation summary', expectationSummary)" in html
    assert "detailListLine('Advisory-only reviewer kinds', localizedAdvisoryKinds.length > 0 ? localizedAdvisoryKinds : advisoryKinds, ' | ')" in html
    assert "const localizedSessionBoundary = reviewerContext.session_boundary_status_summary_key" in html
    assert "const localizedUiIntentRequired = reviewerContext.ui_intent_required_summary_key" in html
    assert "detailLine('Session boundary', localizedSessionBoundary)" in html
    assert "detailLine('UI intent required', localizedUiIntentRequired)" in html
    assert "const authorityNote = reviewerContext.authority_note_key" in html
    assert "detailLine('Authority note', authorityNote)" in html
    assert "detailLine('Session label required', reviewerContextRequirements.session_label_required)" in html
    assert "detailListLine('Durable success requirements', writeRouteContract.durable_success_requirements, ' | ')" in html
    assert "detailListLine('Transaction order', writeRouteContract.transaction_order, ' | ')" in html
    assert "const localizedFailureFamilies = (writeRouteContract.failure_families || []).map(item => {" in html
    assert "const localizedAuthorizationStatus = authorizationContract.authorization_status_summary_key" in html
    assert "const localizedRequiredAssurance = authorizationContract.required_identity_assurance_status_summary_key" in html
    assert "detailListLine('Authorization checks', localizedAuthorizationChecks.length > 0 ? localizedAuthorizationChecks : authorizationContract.server_side_checks, ' | ')" in html
    assert html.count("const localizedActionAuthorizationMatrix = (authorizationContract.action_authorization_matrix || []).map(item => (") >= 2
    assert "detailListLine('Action authorization matrix', localizedActionAuthorizationMatrix, ' | ')" in html
    assert "const localizedRequiredReviewStatus = targetStateContract.required_current_review_status_summary_key" in html
    assert "detailListLine('Target-state checks', localizedTargetStateChecks.length > 0 ? localizedTargetStateChecks : targetStateContract.target_state_checks, ' | ')" in html
    assert "const localizedTargetStateScopeNote = targetStateContract.scope_note_key" in html
    assert "detailLine('Target-state scope note', localizedTargetStateScopeNote)" in html
    assert html.count("const localizedActionTargetMatrix = (targetStateContract.action_target_matrix || []).map(item => (") >= 2
    assert "item && item.summary_key" in html
    assert "detailListLine('Action target matrix', localizedActionTargetMatrix, ' | ')" in html
    assert "const localizedResolvedBehaviorNote = targetStateContract.resolved_behavior_note_key" in html
    assert "detailLine('Resolved behavior note', localizedResolvedBehaviorNote)" in html
    assert "detailListLine('Failure families', localizedFailureFamilies, ' | ')" in html
    assert "const localizedTargetStateStatus = targetStateRecovery.status_summary_key" in html
    assert "const localizedPendingQueueSufficient = typeof targetStateRecovery.pending_queue_sufficient === 'boolean'" in html
    assert "detailLine('Target-state recovery status', localizedTargetStateStatus)" in html
    assert "detailLine('Pending queue sufficient', localizedPendingQueueSufficient)" in html
    assert "const localizedTargetStateSummary = targetStateRecovery.summary_key" in html
    assert "detailLine('Target-state recovery summary', localizedTargetStateSummary)" in html
    assert "const localizedResolvedQueueReason = targetStateRecovery.resolved_queue_reason_key" in html
    assert "detailLine('Resolved queue reason', localizedResolvedQueueReason)" in html
    assert "const localizedFailureFamilies = failureFamilies.map(item => {" in html
    assert "const localizedRecoverySummary = preview.recovery_summary_key" in html
    assert "const localizedFollowUpSummary = preview.follow_up_summary_key" in html
    assert "detailLine('Resolved queue command', targetStateRecovery.resolved_queue_command || '')" in html
    assert "detailLine('Chronicle state command', targetStateRecovery.chronicle_state_command || '')" in html
    assert "function responseMetadataDetailLines(summary)" in html
    assert "function renderResponseMetadataNotice(record)" in html
    assert "function localizedLinkLabel(item)" in html
    assert "detailLine('Response ID', summary.response_id || '')" in html
    assert "const localizedFinishReason = summary.finish_reason_summary_key" in html
    assert "const localizedProviderStatus = summary.provider_status_summary_key" in html
    assert "const localizedCapabilityStatus = notice.capability_status_summary_key" in html
    assert "const localizedIdentityAssuranceStatus = notice.identity_assurance_status_summary_key" in html
    assert "const localizedCapabilityStatus = capability.status_summary_key" in html
    assert "const localizedCanReviewNow = capability.can_review_now_summary_key" in html
    assert "detailLine('Status', localizedCapabilityStatus)" in html
    assert "detailLine('Can review now', localizedCanReviewNow)" in html
    assert "detailLine('Usage total tokens', summary.usage_total_tokens ?? '')" in html
    assert "responseMetadataDetailLines(summary)" in html
    assert "messageParagraph(localizedPayloadText(summary))" in html
    assert "const localizedMessage = summary.message_key" in html
    assert "const localizedScopeNote = summary.scope_note_key" in html
    assert "const localizedRemainingSummary = summary.remaining_summary_key" in html
    assert "packageContextNoticeBody(" in html
    assert '"Action": "操作"' in html
    assert '"Rollback status": "ロールバック状態"' in html
    assert '"Response ID": "応答ID"' in html
    assert '"Read-only": "読み取り専用"' in html
    assert '"Source": "ソース"' in html
    assert '"Provider kind": "プロバイダ種別"' in html
    assert '"Runtime records": "ランタイム記録"' in html
    assert "label('overview.query_engine_trial_insufficient', 'Insufficient trials')" in html
    assert "label('overview.query_engine_trial_escalation', 'Trial escalation cues')" in html
    assert "function renderQueryEngineTrialEscalationDrilldownSummary(summary)" in html
    assert "copyCommandButton(String(summary.issue_template_body || ''), 'action-preview-response', label('button.copy_issue_body', 'Copy issue body'))" in html
    assert '"Audit ID": "監査ID"' in html
    assert "payload.failure_summary_key" in html
    assert "payload && payload.message_key" in html
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
    assert "sliceButtonRows([" in html
    assert "runtimeRecordsSliceButtons()," in html
    assert "summaryJobsSliceButtons()," in html
    assert "Review requested" in html
    assert "Review ready" in html
    assert "Review advisory" in html
    assert "CLI drift" in html
    assert "reviewQueueSliceButtons()," in html
    assert "badge('slice:' + filterLabel, cls)" in html
    assert "' <span class=\"id\">' + esc(value) + '</span>'" in html
    assert "label('overview.warning_priority', 'Warning priority')" in html
    assert "reviewWarningLabel('ui_authorization_not_enabled')" in html
    assert "reviewWarningLabel('reviewer_session_label_missing')" in html
    assert "filterValueLabel('runtimeRecords', 'retrieval_plan')" in html
    assert "filterValueLabel('runtimeRecords', 'query_engine_trial')" in html
    assert "label('notice.query_engine_trial_preview', 'Query-Engine Trial Preview')" in html
    assert "function renderRuntimeWorkspaceNotice(record)" in html
    assert "label('notice.runtime_workspace', 'Runtime Workspace')" in html
    assert "detailLine('Posture role', posture.status || '')" in html
    assert "detailLine('Handoff status', handoff.status || '')" in html
    assert "function renderSummaryJobWorkspaceNotice(record)" in html
    assert "label('notice.summary_job_workspace', 'Summary Job Workspace')" in html
    assert "detailLine('Auth advisory', authAdvisory.status || '')" in html
    assert "detailLine('Identity assurance', identity.status || '')" in html
    assert "function renderAuditGovernanceNotice(record)" in html
    assert "label('notice.audit_governance', 'Audit Governance')" in html
    assert "detailLine('Operational status', implication.status || '')" in html
    assert "detailLine('Bundle manifest', preview.bundle_manifest_path || '')" in html
    assert "filterValueLabel('reviewQueue', 'response_id')" in html
    assert "summaryJsonLine('Runtime kinds', triage.runtime_record_kinds)" in html
    assert "statusScopeNoticeBody(readiness.status, readiness.message, readinessButtons, readiness.scope_note)" in html
    assert "const localizedScopeNote = notice.scope_note_key" in html
    assert "statusScopeNoticeBody(notice.status, localizedMessage, noticeButtons, localizedScopeNote)" in html
    assert "statusMessageBody(assurance.status, localizedPayloadText(assurance), assuranceButtons)" in html
    assert "statusMessageBody(parity.status, localizedPayloadText(parity), parityButtons)" in html
    assert "statusMessageBody(capability.status, localizedPayloadText(capability))" in html
    assert "statusMessageBody(preview.status, localizedPreviewMessage, previewButtons)" in html
    assert "detailListLine('Expected actions', parity.expected_actions)" in html
    assert "label('button.open_review_queue', 'Open Review Queue')" in html
    assert "workspaceLatestResponseLine(authBoundaryOverview.latest_provider_response_detail_path, 'button.open_latest_review_response', 'Open Latest Review Response')" in html
    assert "label('button.open_runtime_records', 'Open Runtime Records')" in html
    assert "label('button.open_summary_jobs', 'Open Summary Jobs')" in html
    assert "endpointLatestResponseCluster('/api/runtime-records', runtimeRecords.latest_provider_response_detail_path, 'button.open_latest_runtime_response', 'Open Latest Runtime Response')" in html
    assert "endpointLatestResponseCluster('/api/summary-jobs', summaryJobs.latest_provider_response_detail_path, 'button.open_latest_summary_response', 'Open Latest Summary Response')" in html
    assert "overviewRuntimeRecordCountButtons(counts, runtimeRecords)" in html
    assert "overviewSummaryJobCountButtons(counts, summaryJobs)" in html
    assert "label('button.open_runtime_config', 'Open Runtime Config')" in html
    assert "label('button.open_package_review', 'Open Package Review')" in html
    assert "buttons.push(openEndpointButton('/api/review-queue'));" in html
    assert "latestResponseButton(triage.latest_provider_response_detail_path, 'button.open_latest_review_response', 'Open Latest Review Response')" in html
    assert "extraButtons: runtimeRowShortcutButtons" in html
    assert "extraButtons: reviewRowShortcutButtons" in html
    assert "extraButtons: summaryRowShortcutButtons" in html
    assert "Open matching runtime record" in html
    assert "reviewDetailButton(row.review_target_event_id || '')" in html
    assert "relatedDetailButton(row, '/api/runtime-records/', 'Open matching runtime record')" in html
    assert "const summaryLink = firstRelatedLink(record, '/api/summary-jobs/');" in html
    assert "const artifactLink = firstRelatedLink(record, '/api/artifacts/');" in html
    assert "const buttons = [openEndpointButton('/api/runtime-records')];" in html
    assert "buttons.push(listJumpButton(localizeTextValue(summaryLink.label || 'Open summary job'), summaryLink.path));" in html
    assert "buttons.push(listJumpButton(localizeTextValue(artifactLink.label || 'Open artifact'), artifactLink.path));" in html
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
    assert "renderWorkspaceTableControls(" in html
    assert "listToolbar(endpoint, 'summaryJobs', t('placeholder.summary_filter')" in html
    assert "{ value: 'mutation', label: t('sort.runtime.mutation') }" in html
    assert "{ value: 'auth', label: t('sort.runtime.auth') }" in html
    assert "runtimeRecordsSliceButtons()," in html
    assert "reviewQueueSliceButtons()," in html
    assert "summaryJobsSliceButtons()," in html
    assert "label('label.table_review_route', 'Review Route')" in html
    assert "Auth aligned" in html
    assert "Auth advisory" in html
    assert "label('button.open_review', 'Open review')" in html
    assert "package:no_context_records" in html
    assert 'data-reset-filters="all"' in html
    assert "listJumpButton(filterValueLabel('reviewQueue', 'advisory'), '/api/review-queue', 'reviewQueue', 'advisory')" in html
    assert "listJumpButton(filterValueLabel('reviewQueue', 'package:package_context_available'), '/api/review-queue', 'reviewQueue', 'package:package_context_available')" in html
    assert "listJumpButton(filterValueLabel('reviewQueue', 'aligned'), '/api/review-queue', 'reviewQueue', 'aligned')" in html
    assert "listJumpButton(filterValueLabel('reviewQueue', 'boundary_aligned'), '/api/review-queue', 'reviewQueue', 'boundary_aligned')" in html
    assert "listJumpButton(reviewWarningLabel('ui_auth_not_enabled'), '/api/review-queue', 'reviewQueue', 'ui_auth_not_enabled')" in html
    assert "listJumpButton(reviewWarningLabel('reviewer_identity_declared_only'), '/api/review-queue', 'reviewQueue', 'reviewer_identity_declared_only')" in html
    assert "listJumpButton(filterValueLabel('runtimeRecords', 'retrieval_plan'), '/api/runtime-records', 'runtimeRecords', 'retrieval_plan')" in html
    assert "overviewTriageCountRows(triage)" in html
    assert "overviewWarningPriorityBadges(warningSummaries)" in html
    assert "overviewTriageNavigationCluster(triage)" in html
    assert "overviewTriageJumpButtons()" in html
    assert "data-detail-nav" in html
    assert "'<td>' + button + (path ? detailButton(path) : '') + '</td>'" in html
    assert "data-detail-trail" in html
    assert "data-back-view" in html
    assert "uiLabel('No matching runtime records for current filter.')" in html
    assert "uiLabel('No matching review rows for current filter.')" in html
    assert "uiLabel('No matching summary jobs for current filter.')" in html
    assert "if (target === 'runtimeRecords')" in html
    assert "if (target === 'reviewQueue')" in html
    assert "if (target === 'summaryJobs')" in html
    assert "CLI aligned" in html
    assert "Open Runtime Records" in html
    assert "Open Review Queue" in html
    assert "Open Package Review" in html
    assert "Review advisory" in html
    assert "Auth Boundary Warnings" in html
    assert "warnings.slice(0, 2).forEach" in html
    assert "function buttonRow(buttons)" in html
    assert "function navigationCluster(buttons)" in html
    assert "function moreStatusButtons(status, endpoint, filterTarget, prefix = '')" in html
    assert "const previewButtons = [" in html
    assert "const parityButtons = reviewQueueStatusButtons(parity.status);" in html
    assert "const assuranceButtons = reviewQueueStatusButtons(assurance.status);" in html
    assert "const readinessButtons = reviewQueueStatusButtons(readiness.status, 'package:');" in html
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
    assert "statusScopeNoticeBody(notice.status, localizedMessage, noticeButtons, localizedScopeNote)" in html
    assert "blockerSummaryDetailLines(blockerDetails, notice.blockers, blockerSummaries, notice.next_steps)" in html
    assert "label('notice.review_capability', 'Review Capability')" in html
    assert "label('notice.action_preview', 'Action Preview')" in html
    assert "const localizedPreviewMessage = localizedPayloadText(preview)" in html
    assert "const localizedCliEquivalent = preview.cli_equivalent_summary_key" in html
    assert "summaryJsonLine('Execution request', executionRequest)" in html
    assert "const localizedDownstreamCommands = (Array.isArray(plan.downstream_command_details) ? plan.downstream_command_details : []).map(item => (" in html
    assert "detailListLine('Downstream commands', localizedDownstreamCommands.length > 0 ? localizedDownstreamCommands : plan.downstream_commands, ' | ')" in html
    assert "downstreamCommands.map(command => copyCommandButton(command, 'action-preview-response', t('button.copy_cli')))" in html
    assert "const localizedInvocationReady = plan.invocation_ready_summary_key" in html
    assert "const localizedWouldUseNetwork = plan.would_use_network_summary_key" in html
    assert "const localizedNetworkAllowed = plan.network_allowed_by_contract_summary_key" in html
    assert "ui.label.execution_request" in html
    assert "uiLabel('Approve')" in html
    assert "uiLabel('Reject')" in html
    assert "uiLabel('Request Changes')" in html
    assert "uiLabel('Preview blocked route')" in html
    assert "data-preview-post" in html
    assert "Blocked route preview stays read-only and returns the CLI fallback contract." in html
    assert "localizedPayloadText(readiness)" in html
    assert "localizedPayloadText(preview)" in html
    assert "localizedPayloadText(parity)" in html
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
    assert "const localizedReadOnly = runtime.read_only_summary_key" in html
    assert "const localizedSource = runtimeConfig.source_summary_key" in html
    assert "const localizedProviderKind = runtimeConfigContract.provider_kind_summary_key" in html
    assert "const localizedAllowNetwork = runtimeConfigContract.allow_network_summary_key" in html
    assert "const localizedAllowExternalContext = runtimeConfigContract.allow_external_context_summary_key" in html
    assert "const localizedMutationEnabled = uiBoundary.mutation_enabled_summary_key" in html
    assert "const localizedMutationCapabilityFlag = uiBoundary.mutation_capability_flag_summary_key" in html
    assert "const localizedSessionGating = uiBoundary.session_gating_summary_key" in html
    assert "authBoundary.session_gating_summary_key ? formatLabel(authBoundary.session_gating_summary_key" in html
    assert "authBoundary.shared_machine_safe_summary_key ? formatLabel(authBoundary.shared_machine_safe_summary_key" in html


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
            "/api/chronicle-objects": "chronicle_objects",
            "/api/federation-inbox": "federation_messages",
            "/api/federation-outbox": "federation_messages",
            "/api/trust-nodes": "trust_nodes",
            "/api/trust-relations": "trust_relations",
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
            "/api/federation-package-preview": "federation_package_preview",
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
            if endpoint == "/api/runtime-records":
                assert "runtime_records_summary" in payload
            if endpoint == "/api/review-queue":
                assert "review_queue_summary" in payload
            if endpoint == "/api/summary-jobs":
                assert "summary_jobs_summary" in payload

        package_dir = tmp_path / "http-federation-package-preview"
        FederationPackageService(tmp_path).create_package(
            purpose="http ui preview review",
            target_node="node:partner:beta",
            output_dir=package_dir,
        )
        status, body = _http_get(
            host,
            port,
            f"/api/federation-package-preview?package_dir={package_dir}",
        )
        assert status == 200
        payload = json.loads(body)
        assert payload["federation_package_preview"]["package_path"] == str(package_dir)
        assert payload["federation_package_preview"]["mode"] == "preview"

        detail_paths = [
            f"/api/events/{ids['event_id']}",
            f"/api/contexts/{ids['context_id']}",
            f"/api/chronicle-objects/{ids['question_object_id']}",
            f"/api/federation-inbox/{ids['federation_inbox_message_id']}",
            f"/api/trust-nodes/{ids['trust_node_id']}",
            f"/api/trust-relations/{ids['trust_relation_id']}",
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
        assert payload["success_contract"]["rollback_status"] == "not_required"
        assert payload["success_contract"]["durable_success_requirements"] == [
            "route_gating_passed",
            "reviewer_context_validated",
            "decision_persisted",
            "audit_persisted",
        ]
        assert payload["success_contract"]["follow_up_commands"] == [
            "chronicle review queue --include-resolved --json",
            f"chronicle review approve --event {ids['runtime_summary_event_id']}",
        ]
        assert payload["success_contract"]["rollback_status_summary_key"] == "ui.review_contract.rollback_status.not_required"
        assert payload["success_contract"]["transaction_status_summary_key"] == (
            "ui.review_success_contract.transaction_status.decision_and_audit_persisted"
        )
        assert payload["failure_contract"]["rollback_status"] == "fail_closed"
        assert payload["failure_contract"]["durable_mutation_reported_on_failure"] is False
        assert payload["failure_contract"]["rollback_status_summary_key"] == "ui.review_contract.rollback_status.fail_closed"
        assert payload["failure_contract"]["durable_mutation_reported_on_failure_summary_key"] == (
            "ui.review_failure_contract.durable_mutation_reported_on_failure.false"
        )
        assert payload["failure_contract"]["failure_families"][0]["family"] == "pre_mutation_or_gate"
        assert payload["failure_contract"]["recovery_commands"] == [
            f"chronicle review approve --event {ids['runtime_summary_event_id']}"
        ]
        assert payload["cli_equivalent_detail"]["summary_key"] == (
            "ui.template.review_action_preview.cli_equivalent_summary"
        )
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
        assert payload["success_contract"]["follow_up_commands"] == [
            "chronicle review queue --include-resolved --json",
            f"chronicle review request-changes --event {ids['runtime_summary_event_id']}",
        ]
        assert payload["failure_contract"]["rollback_status"] == "fail_closed"
        assert payload["failure_contract"]["recovery_commands"] == [
            f"chronicle review request-changes --event {ids['runtime_summary_event_id']}"
        ]
        assert payload["cli_equivalent_detail"]["summary_key"] == (
            "ui.template.review_action_preview.cli_equivalent_summary"
        )
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
        token = _http_mutation_token(host, port)
        mutation_session_id = _http_mutation_session_id(host, port)
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
                "mutation_session_id": mutation_session_id,
                "mutation_request_id": "mrq-ui-http-test-approve-1",
            },
            headers={"X-Chronicle-UI-Mutation-Token": token},
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
        assert payload["success_contract"]["durable_success_requirements"] == [
            "route_gating_passed",
            "reviewer_context_validated",
            "decision_persisted",
            "audit_persisted",
        ]
        assert payload["success_contract"]["follow_up_commands"][0] == "chronicle review queue --include-resolved --json"

        history = ReviewService(tmp_path).history(event_id=ids["runtime_summary_event_id"])
        assert history[0].disposition.value == "approve"
        assert history[0].reviewer_identity.kind.value == "local_operator"
        assert history[0].reviewer_identity.session_label == "ui-http-test"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_http_review_action_enabled_route_rejects_missing_mutation_token(tmp_path):
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
                "mutation_session_id": "msn-missing",
                "mutation_request_id": "mrq-ui-http-test-approve-missing-token",
            },
        )
        assert status == 403
        payload = json.loads(body)
        assert payload["error_code"] == "invalid_mutation_token"
        assert payload["message_key"] == "ui.review_action_failure.message.invalid_mutation_token"
        assert payload["write_route_contract"]["mutation_token_required"] is True
        assert payload["write_route_contract"]["mutation_token_header"] == (
            "X-Chronicle-UI-Mutation-Token"
        )
        assert payload["reviewer_validation_gate_summary"]["validation_error_codes"][0] == (
            "invalid_mutation_token"
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_http_review_action_enabled_route_rejects_invalid_mutation_session(tmp_path):
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
        token = _http_mutation_token(host, port)
        status, body = _http_post(
            host,
            port,
            f"/api/review-actions/{ids['runtime_summary_event_id']}/approve",
            {
                "reviewer_label": "alice",
                "reviewer_kind": "local_operator",
                "session_label": "ui-http-test",
                "ui_intent": "approve",
                "mutation_session_id": "msn-wrong-session",
                "mutation_request_id": "mrq-ui-http-test-approve-invalid-session",
            },
            headers={"X-Chronicle-UI-Mutation-Token": token},
        )
        assert status == 403
        payload = json.loads(body)
        assert payload["error_code"] == "invalid_mutation_session"
        assert payload["message_key"] == "ui.review_action_failure.message.invalid_mutation_session"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_http_review_action_enabled_route_rejects_missing_or_duplicate_request_id(tmp_path):
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
        token = _http_mutation_token(host, port)
        mutation_session_id = _http_mutation_session_id(host, port)
        status, body = _http_post(
            host,
            port,
            f"/api/review-actions/{ids['runtime_summary_event_id']}/approve",
            {
                "reviewer_label": "alice",
                "reviewer_kind": "local_operator",
                "session_label": "ui-http-test",
                "ui_intent": "approve",
                "mutation_session_id": mutation_session_id,
            },
            headers={"X-Chronicle-UI-Mutation-Token": token},
        )
        assert status == 400
        payload = json.loads(body)
        assert payload["error_code"] == "mutation_request_id_required"
        assert payload["message_key"] == "ui.review_action_failure.message.mutation_request_id_required"

        request_id = "mrq-ui-http-test-approve-duplicate"
        status, body = _http_post(
            host,
            port,
            f"/api/review-actions/{ids['runtime_summary_event_id']}/approve",
            {
                "reviewer_label": "alice",
                "reviewer_kind": "local_operator",
                "session_label": "ui-http-test",
                "ui_intent": "approve",
                "mutation_session_id": mutation_session_id,
                "mutation_request_id": request_id,
            },
            headers={"X-Chronicle-UI-Mutation-Token": token},
        )
        assert status == 200

        status, body = _http_post(
            host,
            port,
            f"/api/review-actions/{ids['runtime_summary_event_id']}/approve",
            {
                "reviewer_label": "alice",
                "reviewer_kind": "local_operator",
                "session_label": "ui-http-test",
                "ui_intent": "approve",
                "mutation_session_id": mutation_session_id,
                "mutation_request_id": request_id,
            },
            headers={"X-Chronicle-UI-Mutation-Token": token},
        )
        assert status == 409
        payload = json.loads(body)
        assert payload["error_code"] == "duplicate_mutation_request"
        assert payload["message_key"] == "ui.review_action_failure.message.duplicate_mutation_request"
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
        token = _http_mutation_token(host, port)
        mutation_session_id = _http_mutation_session_id(host, port)
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
                "mutation_session_id": mutation_session_id,
                "mutation_request_id": "mrq-ui-http-test-approve-audit-failure",
            },
            headers={"X-Chronicle-UI-Mutation-Token": token},
        )
        assert status == 500
        payload = json.loads(body)
        assert payload["error_code"] == "audit_insertion_failed"
        assert "Audit insertion failed before the review decision could be reported as applied." in payload["message"]
        assert payload["message_key"] == "ui.review_action_failure.message.audit_insertion_failed"
        assert payload["failure_summary"] == "audit_insertion_failed; inspect local audit surface before retry"
        assert payload["failure_summary_key"] == "ui.review_action_failure.summary.audit_insertion_failed"
        assert payload["failure_contract"]["rollback_status"] == "fail_closed"
        assert payload["failure_contract"]["durable_mutation_reported_on_failure"] is False
        assert payload["failure_contract"]["failure_families"][1]["family"] == "durable_write_path"
        assert payload["failure_contract"]["failure_families"][1]["summary_key"] == (
            "ui.review_write_route_failure_family.durable_write_path"
        )
        assert payload["failure_contract"]["recovery_commands"] == [
            f"chronicle review approve --event {ids['runtime_summary_event_id']}",
            "chronicle audit list --json",
        ]
        assert ReviewService(tmp_path).history(event_id=ids["runtime_summary_event_id"]) == []
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_http_review_action_rejects_invalid_json_and_non_object_body(tmp_path):
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
        token = _http_mutation_token(host, port)
        _http_mutation_session_id(host, port)
        status, body = _http_post_raw(
            host,
            port,
            f"/api/review-actions/{ids['runtime_summary_event_id']}/approve",
            "{",
            headers={"X-Chronicle-UI-Mutation-Token": token},
        )
        assert status == 400
        payload = json.loads(body)
        assert payload["error_code"] == "invalid_json"
        assert payload["message_key"] == "ui.review_action_failure.message.invalid_json"

        status, body = _http_post_raw(
            host,
            port,
            f"/api/review-actions/{ids['runtime_summary_event_id']}/approve",
            "[]",
            headers={"X-Chronicle-UI-Mutation-Token": token},
        )
        assert status == 400
        payload = json.loads(body)
        assert payload["error_code"] == "invalid_request_body"
        assert payload["message_key"] == "ui.review_action_failure.message.invalid_request_body"
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
    assert payload["write_route_contract"]["route_template"] == "/api/review-actions/<event_id>/<action>"
    assert payload["reviewer_context_requirements"]["required_reviewer_kinds_for_mutation"] == [
        "local_operator"
    ]
    assert payload["reviewer_enforcement_summary"]["status"] == "enforced_local_session"
    assert payload["reviewer_enforcement_summary"]["enforced_reviewer_kinds_for_mutation"] == [
        "local_operator"
    ]
    assert payload["reviewer_validation_gate_summary"]["status"] == "local_route_enforced"
    assert payload["reviewer_validation_gate_summary"]["authorization_error_codes"] == [
        "authorization_failed"
    ]
    assert payload["message_key"] == "ui.review_action_failure.message.authorization_failed"
    assert payload["reviewer_context_requirements"]["expectation_summary"].startswith(
        "Explicit local GUI mutation currently expects local_operator reviewer metadata"
    )
    assert payload["warning_details"] == [
        {
            "code": "reviewer_identity_declared_only",
            "label_key": "filter.review.reviewer_identity_declared_only",
            "label": "Declared identity only",
            "message_key": "ui.review_warning.reviewer_identity_declared_only",
            "message": "Reviewer identity is self-declared and has not been strengthened by a local auth boundary.",
        }
    ]
    assert payload["success_contract"]["follow_up_commands"] == [
        "chronicle review queue --include-resolved --json",
        f"chronicle review approve --event {ids['runtime_summary_event_id']}",
    ]
    assert "Reviewer identity is self-declared" in payload["failure_summary"]
    assert payload["failure_summary_key"] == "ui.review_action_failure.summary.authorization_failed"
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
    assert payload["write_route_contract"]["route_template"] == "/api/review-actions/<event_id>/<action>"
    assert payload["reviewer_context_requirements"]["session_boundary_status"] == "required"
    assert payload["reviewer_enforcement_summary"]["status"] == "enforced_local_session"
    assert payload["reviewer_validation_gate_summary"]["status"] == "local_route_enforced"
    assert payload["reviewer_context_requirements"]["session_note"] == (
        "Session label is required because the current local mutation boundary is session-gated."
    )


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
    assert payload["write_route_contract"]["blocked_status_code"] == 403
    assert payload["reviewer_enforcement_summary"]["session_gated"] is True
    assert payload["reviewer_validation_gate_summary"]["session_gated"] is True
    assert payload["reviewer_context_requirements"]["ui_intent_note"] == (
        "ui_intent must match the requested action so preview and apply paths stay fail-closed."
    )
    assert payload["success_contract"]["follow_up_commands"] == [
        "chronicle review queue --include-resolved --json",
        f"chronicle review approve --event {ids['runtime_summary_event_id']}",
    ]
    assert payload["failure_contract"]["possible_error_codes"][:7] == [
        "mutation_disabled",
        "invalid_mutation_token",
        "invalid_mutation_session",
        "mutation_request_id_required",
        "invalid_mutation_request_id",
        "duplicate_mutation_request",
        "reviewer_label_required",
    ]
    assert payload["failure_contract"]["failure_families"][0]["possible_error_codes"][:7] == [
        "mutation_disabled",
        "invalid_mutation_token",
        "invalid_mutation_session",
        "mutation_request_id_required",
        "invalid_mutation_request_id",
        "duplicate_mutation_request",
        "reviewer_label_required",
    ]


def test_review_action_reports_resolved_queue_recovery_when_target_not_pending(tmp_path):
    ids = _populate(tmp_path)
    review_service = ReviewService(tmp_path)
    review_service.approve(
        event_id=ids["runtime_summary_event_id"],
        reviewer="alice",
        reviewer_kind=ReviewerIdentityKind.LOCAL_OPERATOR,
        session_label="ui-test-session",
        note="resolve before browser retry",
    )
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

    assert status == 409
    assert payload["error_code"] == "review_not_pending"
    assert payload["failure_summary"] == "review_not_pending; inspect resolved queue state before retry"
    assert payload["message_key"] == "ui.review_action_failure.message.review_not_pending"
    assert payload["failure_summary_key"] == "ui.review_action_failure.summary.review_not_pending"
    assert payload["failure_contract"]["target_state_recovery"]["status"] == "resolved_queue_check_required"
    assert payload["failure_contract"]["target_state_recovery"]["status_summary_key"] == (
        "ui.review_action_target_state_recovery.status.resolved_queue_check_required"
    )
    assert payload["failure_contract"]["target_state_recovery"]["summary_key"] == (
        "ui.review_action_target_state_recovery.summary.review_not_pending"
    )
    assert payload["failure_contract"]["target_state_recovery"]["pending_queue_sufficient"] is False
    assert payload["failure_contract"]["target_state_recovery"]["pending_queue_sufficient_summary_key"] == (
        "ui.boolean.false"
    )
    assert payload["failure_contract"]["target_state_recovery"]["resolved_queue_reason_key"] == (
        "ui.review_action_target_state_recovery.reason.review_not_pending"
    )
    assert "later review decision" in payload["failure_contract"]["target_state_recovery"]["resolved_queue_reason"]
    assert payload["failure_contract"]["target_state_recovery"]["resolved_queue_command"] == (
        "chronicle review queue --include-resolved --json"
    )
    assert "resolved queue" in payload["failure_contract"]["target_state_recovery"]["summary"]
    assert payload["failure_contract"]["recovery_commands"][0] == (
        "chronicle review queue --include-resolved --json"
    )


def test_review_action_reports_chronicle_state_recheck_when_target_missing(tmp_path):
    _populate(tmp_path)
    service = ChronicleUIDataService(
        tmp_path,
        mutation_capability_flag=True,
        enable_ui_mutation=True,
        auth_mode=UIAuthMode.LOOPBACK_LOCAL,
        authorization_mode=UIAuthorizationMode.REVIEWER_DECLARED,
    )

    status, payload = service.review_action_response(
        "/api/review-actions/evt_missing/approve",
        {
            "reviewer_label": "alice",
            "reviewer_kind": "local_operator",
            "session_label": "ui-test-session",
            "ui_intent": "approve",
        },
    )

    assert status == 404
    assert payload["error_code"] == "review_target_not_found"
    assert payload["failure_contract"]["target_state_recovery"]["status"] == "chronicle_state_recheck_required"
    assert payload["failure_contract"]["target_state_recovery"]["status_summary_key"] == (
        "ui.review_action_target_state_recovery.status.chronicle_state_recheck_required"
    )
    assert payload["failure_contract"]["target_state_recovery"]["summary_key"] == (
        "ui.review_action_target_state_recovery.summary.review_target_not_found"
    )
    assert payload["failure_contract"]["target_state_recovery"]["pending_queue_sufficient"] is False
    assert payload["failure_contract"]["target_state_recovery"]["pending_queue_sufficient_summary_key"] == (
        "ui.boolean.false"
    )
    assert payload["failure_contract"]["target_state_recovery"]["resolved_queue_reason_key"] == (
        "ui.review_action_target_state_recovery.reason.review_target_not_found"
    )
    assert payload["failure_contract"]["target_state_recovery"]["resolved_queue_command"] == (
        "chronicle review queue --include-resolved --json"
    )
    assert payload["failure_contract"]["target_state_recovery"]["chronicle_state_command"] == (
        "chronicle show --json"
    )
    assert "current Chronicle state" in payload["failure_contract"]["target_state_recovery"]["summary"]


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
    assert payload["message_key"] == "ui.review_action_failure.message.invalid_reviewer_label"
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
    assert payload["reviewer_context_requirements"]["reviewer_label_note"].startswith(
        "Reviewer label must identify the local operator"
    )


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
    assert notice["scope_note"].startswith(
        "Loopback-local reviewer metadata is session-gated"
    )
    assert notice["blocker_details"] == [
        {
            "code": "reviewer_identity_missing",
            "message_key": "ui.auth_boundary_blocker.reviewer_identity_missing",
            "message": "Record reviewer identity metadata before relying on GUI review signals.",
        }
    ]
    assert notice["blocker_summaries"] == [
        {
            "code": "reviewer_identity_missing",
            "message_key": "ui.auth_boundary_blocker.reviewer_identity_missing",
            "summary_key": "ui.template.auth_boundary_blocker_summary",
            "summary_params": {
                "message": "Record reviewer identity metadata before relying on GUI review signals.",
            },
            "summary": "Auth boundary: Record reviewer identity metadata before relying on GUI review signals.",
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
        token = _http_mutation_token(host, port)
        mutation_session_id = _http_mutation_session_id(host, port)
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
                "mutation_session_id": mutation_session_id,
                "mutation_request_id": "mrq-ui-http-test-approve-persist-failure",
            },
            headers={"X-Chronicle-UI-Mutation-Token": token},
        )
        assert status == 500
        payload = json.loads(body)
        assert payload["error_code"] == "decision_persistence_failed"
        assert "Chronicle primary-record append failed" in payload["message"]
        assert payload["message_key"] == "ui.review_action_failure.message.decision_persistence_failed"
        assert payload["failure_summary"] == "decision_persistence_failed; inspect audit trail and primary record state"
        assert payload["failure_summary_key"] == "ui.review_action_failure.summary.decision_persistence_failed"
        assert payload["audit_id"].startswith("aud_")
        assert payload["failure_contract"]["rollback_status"] == "fail_closed"
        assert payload["failure_contract"]["failure_families"][0]["summary_key"] == (
            "ui.review_write_route_failure_family.pre_mutation_or_gate"
        )
        assert payload["failure_contract"]["recovery_commands"][0] == "chronicle review queue --include-resolved --json"
        assert payload["failure_contract"]["recovery_commands"][1] == f"chronicle audit show --id {payload['audit_id']} --json"
        assert len(AuditService(tmp_path).list_events()) == 3
        assert ReviewService(tmp_path).history(event_id=ids["runtime_summary_event_id"]) == []
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_chronicle_ui_help():
    runner = CliRunner()
    result = runner.invoke(app, ["ui", "--help"])
    assert result.exit_code == 0
    plain = _plain(result.stdout).lower()
    for option in ("host", "port", "open", "root", "json", "enable-ui-mutation"):
        assert option in plain
