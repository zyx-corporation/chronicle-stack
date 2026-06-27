"""Explicit foreground local web UI for Chronicle Stack.

This module intentionally uses Python stdlib only. It serves read-only views over
local Chronicle files and must not be confused with a daemon, hosted service,
model runtime, GraphRAG engine, vector DB, or graph DB.
"""

from __future__ import annotations

import html
import ipaddress
import json
import re
import secrets
import webbrowser
from dataclasses import asdict, dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote, urlparse

from chronicle.errors import ChronicleError, UIHostNotLoopbackError
from chronicle.exporters.html_exporter import HtmlDashboardExporter
from chronicle.models.runtime import RuntimeExecutionResult, RuntimeInvocationPlan, RuntimeRetrievalPlan
from chronicle.models.review import ReviewerIdentity, ReviewerIdentityKind
from chronicle.services.audit_service import AuditService
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.graph_index_service import GraphIndexService
from chronicle.services.graph_export_service import GraphExportService
from chronicle.services.integration_package_service import IntegrationPackageService
from chronicle.services.lifecycle_service import LifecycleService
from chronicle.services.package_review_service import PackageReviewService
from chronicle.services.proposal_service import ProposalService
from chronicle.services.review_service import (
    ReviewAuditInsertionError,
    ReviewDecisionPersistenceError,
    ReviewService,
    review_action_commands,
)
from chronicle.services.runtime_config_service import RuntimeConfigService
from chronicle.services.runtime_service import RuntimeService
from chronicle.services.summary_job_service import SummaryJobService
from chronicle.ui_i18n import (
    AUTH_BOUNDARY_BLOCKER_TEXT,
    AUTH_BOUNDARY_WARNING_TO_BLOCKER,
    DEFAULT_UI_LOCALE,
    FALLBACK_UI_LOCALE,
    MUTATION_BLOCKER_TEXT,
    REVIEW_WARNING_LABELS,
    REVIEW_WARNING_PRIORITY,
    REVIEW_WARNING_TEXT,
    SUPPORTED_UI_LOCALES,
    UI_I18N_CATALOG,
)
from chronicle.services.vector_index_service import VectorIndexService

DEFAULT_UI_HOST = "127.0.0.1"
DEFAULT_UI_PORT = 8765
REVIEWER_LABEL_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{1,63}$")
SESSION_LABEL_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{1,63}$")
MUTATION_TOKEN_HEADER = "X-Chronicle-UI-Mutation-Token"
MUTATION_REQUEST_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._:-]{7,127}$")
MUTATION_SESSION_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._:-]{7,127}$")


class UIAuthMode:
    NOT_ENABLED = "not_enabled"
    LOOPBACK_LOCAL = "loopback_local"


class UIAuthorizationMode:
    NOT_ENABLED = "not_enabled"
    REVIEWER_DECLARED = "reviewer_declared"


@dataclass(frozen=True)
class UIBoundaryMetadata:
    """Read-only UI boundary configuration."""

    bind_scope: str
    loopback_only: bool = True
    read_only: bool = True
    mutation_enabled: bool = False
    mutation_capability_flag: bool = False
    auth_mode: str = UIAuthMode.NOT_ENABLED
    authorization_mode: str = UIAuthorizationMode.NOT_ENABLED
    session_gating: bool = False
    shared_machine_safe: bool = False
    review_queue_preview_only: bool = True
    future_write_requires_auth: bool = True
    primary_record_authoritative: bool = True
    mutation_readiness_status: str = "preview_only"
    mutation_readiness_message: str = "GUI mutation remains disabled; read-only preview only."
    mutation_token_required: bool = False
    mutation_token_transport: str = "header"
    mutation_token_header: str = MUTATION_TOKEN_HEADER
    mutation_enabled_summary_key: str = "ui.boolean.false"
    mutation_enabled_summary: str = "false"
    mutation_capability_flag_summary_key: str = "ui.boolean.false"
    mutation_capability_flag_summary: str = "false"
    session_gating_summary_key: str = "ui.boolean.false"
    session_gating_summary: str = "false"
    mutation_blockers: tuple[str, ...] = (
        "write_routes_disabled",
        "auth_not_enabled",
        "authorization_not_enabled",
        "audit_insertion_cli_only",
    )
    mutation_blocker_details: list[dict[str, str]] | None = None
    reviewer_context_requirements: dict[str, Any] | None = None
    reviewer_enforcement_summary: dict[str, Any] | None = None
    reviewer_validation_gate_summary: dict[str, Any] | None = None
    auth_boundary_summary: dict[str, Any] | None = None
    write_route_contract: dict[str, Any] | None = None


def _auth_boundary_summary(metadata: UIBoundaryMetadata) -> dict[str, Any]:
    blockers: list[str] = []
    next_steps: list[str] = []

    if metadata.auth_mode == UIAuthMode.NOT_ENABLED:
        _append_auth_boundary_blocker(blockers, next_steps, "auth_not_enabled")
    if metadata.authorization_mode == UIAuthorizationMode.NOT_ENABLED:
        _append_auth_boundary_blocker(blockers, next_steps, "authorization_not_enabled")
    if metadata.session_gating and not metadata.shared_machine_safe:
        _append_auth_boundary_blocker(blockers, next_steps, "shared_machine_session_unhardened")

    if metadata.auth_mode == UIAuthMode.NOT_ENABLED:
        status = "auth_not_enabled"
        message = "UI auth boundary is not enabled; reviewer identity remains advisory only."
    elif metadata.authorization_mode == UIAuthorizationMode.NOT_ENABLED:
        status = "authorization_not_enabled"
        message = "UI auth boundary is loopback-local, but reviewer authorization remains advisory only."
    else:
        status = "reviewer_declared_preview"
        message = "UI auth/authz metadata is configured for preview, but GUI mutation remains disabled."

    pre_gate_summary_key, pre_gate_summary_params, pre_gate_summary = (
        _review_failure_family_summary_contract("pre_mutation_or_gate")
    )
    durable_summary_key, durable_summary_params, durable_summary = (
        _review_failure_family_summary_contract("durable_write_path")
    )
    return {
        "status": status,
        "message": message,
        "message_key": f"ui.auth_boundary_summary.message.{status}",
        "scope_note": _auth_readiness_scope_note(
            auth_mode=metadata.auth_mode,
            authorization_mode=metadata.authorization_mode,
            session_gating=metadata.session_gating,
        ),
        "scope_note_key": (
            "ui.auth_readiness.scope.auth_not_enabled"
            if metadata.auth_mode == UIAuthMode.NOT_ENABLED
            else (
                "ui.auth_readiness.scope.authorization_not_enabled"
                if metadata.authorization_mode == UIAuthorizationMode.NOT_ENABLED
                else (
                    "ui.auth_readiness.scope.session_gated"
                    if metadata.session_gating
                    else "ui.auth_readiness.scope.descriptive_preview"
                )
            )
        ),
        "blockers": blockers,
        "blocker_details": _serialize_auth_boundary_blocker_details(blockers),
        "blocker_summaries": _auth_blocker_summaries(blockers),
        "next_steps": next_steps,
        "shared_machine_safe": metadata.shared_machine_safe,
        "session_gating": metadata.session_gating,
        "shared_machine_safe_summary_key": _boolean_summary_payload(bool(metadata.shared_machine_safe))[0],
        "shared_machine_safe_summary": _boolean_summary_payload(bool(metadata.shared_machine_safe))[1],
        "session_gating_summary_key": _boolean_summary_payload(bool(metadata.session_gating))[0],
        "session_gating_summary": _boolean_summary_payload(bool(metadata.session_gating))[1],
    }


def _append_auth_boundary_blocker(
    blockers: list[str],
    next_steps: list[str],
    blocker_code: str,
) -> None:
    blockers.append(blocker_code)
    next_steps.append(AUTH_BOUNDARY_BLOCKER_TEXT.get(blocker_code, blocker_code.replace("_", " ")))


def _serialize_auth_boundary_blocker_details(blockers: list[str]) -> list[dict[str, str]]:
    return [
        {
            "code": blocker,
            "message_key": f"ui.auth_boundary_blocker.{blocker}",
            "message": AUTH_BOUNDARY_BLOCKER_TEXT.get(blocker, blocker.replace("_", " ")),
        }
        for blocker in blockers
    ]


def _auth_blocker_summaries(blockers: list[str]) -> list[dict[str, Any]]:
    return [
        {
            "code": blocker,
            "message_key": f"ui.auth_boundary_blocker.{blocker}",
            "summary_key": "ui.template.auth_boundary_blocker_summary",
            "summary_params": {
                "message": AUTH_BOUNDARY_BLOCKER_TEXT.get(blocker, blocker.replace("_", " ")),
            },
            "summary": f"Auth boundary: {AUTH_BOUNDARY_BLOCKER_TEXT.get(blocker, blocker.replace('_', ' '))}",
        }
        for blocker in blockers
    ]


def _auth_readiness_scope_note(
    *,
    auth_mode: str,
    authorization_mode: str,
    session_gating: bool,
) -> str:
    if auth_mode == UIAuthMode.NOT_ENABLED:
        return "UI review remains advisory-only until an explicit local auth boundary is configured."
    if authorization_mode == UIAuthorizationMode.NOT_ENABLED:
        return "Loopback-local auth metadata is present, but reviewer authorization still remains advisory-only."
    if session_gating:
        return "Loopback-local reviewer metadata is session-gated, but this surface still reports preview readiness rather than granting write authority."
    return "Auth readiness remains a descriptive preview surface; it does not grant write authority on its own."


def _serialize_review_warning_details(warnings: list[str]) -> list[dict[str, str]]:
    return [
        {
            "code": warning,
            "label_key": f"filter.review.{warning}",
            "label": REVIEW_WARNING_LABELS.get(warning, warning.replace("_", " ")),
            "message_key": f"ui.review_warning.{warning}",
            "message": REVIEW_WARNING_TEXT.get(warning, warning.replace("_", " ")),
        }
        for warning in warnings
    ]


def _review_action_failure_message_key(error_code: str) -> str:
    return f"ui.review_action_failure.message.{error_code}"


def _review_possible_error_detail(error_code: str) -> dict[str, Any]:
    return {
        "code": error_code,
        "message_key": _review_action_failure_message_key(error_code),
        "message": ChronicleUIDataService._review_action_failure_message(error_code),
        "message_params": {},
    }


def _review_command_detail(command: str, *, kind: str) -> dict[str, Any]:
    template_key = (
        "ui.template.review_action_preview.recovery_summary"
        if kind == "recovery"
        else "ui.template.review_action_preview.follow_up_summary"
    )
    return {
        "command": command,
        "summary_key": template_key,
        "summary_params": {"command": command},
        "summary": command,
    }


def _review_cli_equivalent_detail(command: str) -> dict[str, Any]:
    return {
        "command": command,
        "summary_key": "ui.template.review_action_preview.cli_equivalent_summary",
        "summary_params": {"command": command},
        "summary": command,
    }


def _invocation_plan_command_detail(command: str) -> dict[str, Any]:
    if command.startswith("chronicle runtime config show --json"):
        template_key = "ui.template.invocation_plan.command.runtime_config_show"
    elif command.startswith("chronicle review queue --json"):
        template_key = "ui.template.invocation_plan.command.review_queue"
    elif command.startswith("chronicle runtime execute-plan --event "):
        template_key = "ui.template.invocation_plan.command.execute_plan"
    elif command.startswith("chronicle runtime summarize --text "):
        template_key = "ui.template.invocation_plan.command.runtime_operation_execute"
    else:
        template_key = "ui.template.invocation_plan.command.generic"
    return {
        "command": command,
        "summary_key": template_key,
        "summary_params": {"command": command},
        "summary": command,
    }


def _retrieval_handoff_command_detail(command: str) -> dict[str, Any]:
    if command.startswith('chronicle package review --purpose "runtime retrieval handoff"'):
        template_key = "ui.template.retrieval_handoff.command.package_review"
    elif command.startswith('chronicle package context --purpose "runtime retrieval handoff" --persist'):
        template_key = "ui.template.retrieval_handoff.command.package_context_persist"
    elif command.startswith("chronicle review queue --json"):
        template_key = "ui.template.retrieval_handoff.command.review_queue"
    else:
        template_key = "ui.template.retrieval_handoff.command.generic"
    return {
        "command": command,
        "summary_key": template_key,
        "summary_params": {"command": command},
        "summary": command,
    }


def _package_readiness_command_detail(command: str) -> dict[str, Any]:
    if command.startswith('chronicle package review --purpose "runtime retrieval handoff"'):
        template_key = "ui.template.package_readiness.command.package_review_runtime_handoff"
    elif command.startswith('chronicle package context --purpose "runtime retrieval handoff" --persist'):
        template_key = "ui.template.package_readiness.command.package_context_runtime_handoff"
    elif command.startswith('chronicle package review --purpose "review target handoff"'):
        template_key = "ui.template.package_readiness.command.package_review_target_handoff"
    elif command.startswith('chronicle package context --purpose "review target handoff" --persist'):
        template_key = "ui.template.package_readiness.command.package_context_target_handoff"
    elif command.startswith("chronicle show --json"):
        template_key = "ui.template.package_readiness.command.chronicle_show"
    elif command.startswith("chronicle review queue --json"):
        template_key = "ui.template.package_readiness.command.review_queue"
    else:
        template_key = "ui.template.package_readiness.command.generic"
    return {
        "command": command,
        "summary_key": template_key,
        "summary_params": {"command": command},
        "summary": command,
    }


def _package_handoff_command_detail(command: str) -> dict[str, Any]:
    if command.startswith('chronicle package review --purpose "runtime retrieval handoff"'):
        template_key = "ui.template.package_handoff.command.package_review"
    elif command.startswith('chronicle package context --purpose "runtime retrieval handoff" --persist'):
        template_key = "ui.template.package_handoff.command.package_context_persist"
    elif command.startswith("chronicle review queue --json"):
        template_key = "ui.template.package_handoff.command.review_queue"
    else:
        template_key = "ui.template.package_handoff.command.generic"
    return {
        "command": command,
        "summary_key": template_key,
        "summary_params": {"command": command},
        "summary": command,
    }


def _review_action_failure_summary_contract(
    *,
    error_code: str,
    warning_codes: list[str] | None = None,
    identity_assurance_status: str | None = None,
) -> tuple[str, dict[str, Any], str]:
    if error_code == "authorization_failed":
        warning_text = " | ".join(
            ChronicleUIDataService._warning_message(code)
            for code in (warning_codes or [])
            if code
        )
        if warning_text and identity_assurance_status:
            summary = f"authorization_failed; identity={identity_assurance_status}; warnings={warning_text}"
        elif identity_assurance_status:
            summary = f"authorization_failed; identity={identity_assurance_status}"
        elif warning_text:
            summary = f"authorization_failed; warnings={warning_text}"
        else:
            summary = "authorization_failed"
        return (
            "ui.review_action_failure.summary.authorization_failed",
            {
                "identity_assurance_status": identity_assurance_status or "",
                "warning_text": warning_text,
            },
            summary,
        )
    if error_code == "review_not_pending":
        return (
            "ui.review_action_failure.summary.review_not_pending",
            {},
            "review_not_pending; inspect resolved queue state before retry",
        )
    if error_code == "audit_insertion_failed":
        return (
            "ui.review_action_failure.summary.audit_insertion_failed",
            {},
            "audit_insertion_failed; inspect local audit surface before retry",
        )
    if error_code == "decision_persistence_failed":
        return (
            "ui.review_action_failure.summary.decision_persistence_failed",
            {},
            "decision_persistence_failed; inspect audit trail and primary record state",
        )
    return ("", {}, error_code)


def _identity_boundary_summary_message(status: str) -> str:
    messages = {
        "boundary_aligned": "Recorded reviewer identity metadata is aligned with the current preview auth boundary.",
        "partially_aligned": "Some reviewer identity metadata is present, but boundary alignment remains incomplete.",
        "identity_unavailable": "Reviewer identity assurance is not yet available in the current derived queue view.",
    }
    return messages.get(status, status.replace("_", " "))


def _identity_boundary_summary_message_key(status: str) -> str:
    return f"ui.identity_boundary.message.{status}"


def _auth_readiness_message(
    *,
    capability_status: str,
    assurance_status: str,
    has_blockers: bool,
) -> str:
    if capability_status == "ready" and assurance_status == "boundary_aligned" and not has_blockers:
        return "Current review metadata is aligned with the preview auth boundary, while GUI mutation remains disabled."
    if has_blockers:
        return "Current review metadata remains advisory only until auth, authorization, and reviewer identity boundaries are explicit."
    if assurance_status != "unknown":
        return "Some reviewer identity metadata is present, but auth-boundary alignment remains incomplete."
    return "Auth-boundary readiness is not yet available in the current derived detail view."


def _auth_readiness_message_key(
    *,
    capability_status: str,
    assurance_status: str,
    has_blockers: bool,
) -> str:
    if capability_status == "ready" and assurance_status == "boundary_aligned" and not has_blockers:
        return "ui.auth_readiness.message.boundary_aligned"
    if has_blockers:
        return "ui.auth_readiness.message.advisory_only"
    if assurance_status != "unknown":
        return "ui.auth_readiness.message.partially_aligned"
    return "ui.auth_readiness.message.unavailable"


def _identity_assurance_message(
    *,
    reviewer_auth_mode: str,
    boundary_auth_mode: str,
) -> str:
    if reviewer_auth_mode == "none":
        return "Reviewer identity is self-declared only; UI auth is not enforcing reviewer identity."
    if boundary_auth_mode == "not_enabled":
        return "Reviewer identity carries local session metadata, but UI auth/authz is not enabled."
    return "Reviewer identity metadata is aligned with the current UI auth boundary."


def _identity_assurance_message_key(
    *,
    reviewer_auth_mode: str,
    boundary_auth_mode: str,
) -> str:
    if reviewer_auth_mode == "none":
        return "ui.identity_assurance.message.declared_only"
    if boundary_auth_mode == "not_enabled":
        return "ui.identity_assurance.message.local_session_unverified"
    return "ui.identity_assurance.message.boundary_aligned"


def _review_capability_message(can_review_now: bool) -> str:
    return (
        "Boundary and reviewer identity conditions are aligned for future mutation-capable review."
        if can_review_now
        else "Review remains CLI-led and read-only in UI; see warnings for unmet boundary conditions."
    )


def _review_capability_message_key(can_review_now: bool) -> str:
    return (
        "ui.review_capability.message.ready"
        if can_review_now
        else "ui.review_capability.message.advisory_only"
    )


def _package_readiness_message_key(status: str) -> str:
    if status == "package_context_available":
        return "ui.package_readiness.message.package_context_available"
    if status == "no_context_records":
        return "ui.package_readiness.message.no_context_records"
    return "ui.package_readiness.message.unavailable"


def _package_readiness_summary_label_key(*, status: str, review_status: str) -> str:
    if status == "package_context_available":
        pre_gate_summary_key, pre_gate_summary_params, pre_gate_summary = (
            _review_failure_family_summary_contract("pre_mutation_or_gate")
        )
        durable_summary_key, durable_summary_params, durable_summary = (
            _review_failure_family_summary_contract("durable_write_path")
        )
        return {
            "pass": "ui.package_readiness.summary.label.pass",
            "warning": "ui.package_readiness.summary.label.warning",
            "blocked": "ui.package_readiness.summary.label.blocked",
        }.get(review_status, "ui.package_readiness.summary.label.available")
    if status == "no_context_records":
        return "ui.package_readiness.summary.label.advisory"
    return "ui.package_readiness.summary.label.unavailable"


def _package_readiness_summary_message_template_key(status: str) -> str:
    if status == "package_context_available":
        return "ui.template.package_readiness.summary.available"
    if status == "no_context_records":
        return "ui.package_readiness.summary.message.advisory"
    return "ui.package_readiness.summary.message.unavailable"


def _package_handoff_message_key(status: str) -> str:
    if status == "package_context_available":
        return "ui.package_handoff.message.package_context_available"
    if status == "no_context_records":
        return "ui.package_handoff.message.no_context_records"
    return "ui.package_handoff.message.unavailable"


def _package_handoff_counts_contract(
    *, eligible_context_count: int, skipped_record_count: int
) -> tuple[str, dict[str, Any]]:
    return "ui.template.package_handoff.counts", {
        "eligible_context_count": eligible_context_count,
        "skipped_record_count": skipped_record_count,
    }


def _package_readiness_counts_contract(
    *, eligible_context_count: int, skipped_record_count: int
) -> tuple[str, dict[str, Any]]:
    return "ui.template.package_readiness.counts", {
        "eligible_context_count": eligible_context_count,
        "skipped_record_count": skipped_record_count,
    }


def _response_metadata_counts_contract(
    *, metadata_count: int, response_key_count: int
) -> tuple[str, dict[str, Any]]:
    return "ui.template.provider_response.counts", {
        "metadata_count": metadata_count,
        "response_key_count": response_key_count,
    }


def _review_action_preview_message_key(mutation_enabled: bool, can_review_now: bool) -> str:
    if mutation_enabled and can_review_now:
        return "ui.action_preview.message.enabled_ready"
    if mutation_enabled and not can_review_now:
        return "ui.action_preview.message.enabled_blocked"
    if not mutation_enabled and can_review_now:
        return "ui.action_preview.message.preview_only_ready"
    return "ui.action_preview.message.preview_only_blocked"


def _cli_parity_message_key(aligned: bool) -> str:
    return "ui.cli_parity.message.aligned" if aligned else "ui.cli_parity.message.drift_detected"


def _review_action_preview_summary_contract(kind: str, command: str) -> tuple[str, dict[str, Any], str]:
    if not command:
        return ("", {}, "")
    if kind == "cli_equivalent":
        return (
            "ui.template.review_action_preview.cli_equivalent_summary",
            {"command": command},
            command,
        )
    if kind == "recovery":
        return ("ui.template.review_action_preview.recovery_summary", {"command": command}, command)
    if kind == "follow_up":
        return ("ui.template.review_action_preview.follow_up_summary", {"command": command}, command)
    return ("", {}, command)


def _review_failure_family_summary_contract(family: str) -> tuple[str, dict[str, Any], str]:
    if family == "pre_mutation_or_gate":
        summary = (
            "Gate, validation, authorization, or target-state checks failed before durable success could be reported."
        )
        return ("ui.review_write_route_failure_family.pre_mutation_or_gate", {}, summary)
    if family == "durable_write_path":
        summary = (
            "A durable write-path side effect failed, so the route stays fail-closed and must not report applied success."
        )
        return ("ui.review_write_route_failure_family.durable_write_path", {}, summary)
    return ("", {}, family.replace("_", " "))


def _review_status_code_when_contract(
    status_code: int, family: str
) -> tuple[str, dict[str, Any], str]:
    mapping = {
        (200, "success"): (
            "ui.review_write_route_status_code.when.success",
            "review decision persistence and audit insertion both succeed",
        ),
        (400, "pre_mutation_or_gate"): (
            "ui.review_write_route_status_code.when.validation_failed",
            "reviewer-context or ui_intent validation fails before authorization",
        ),
        (403, "pre_mutation_or_gate"): (
            "ui.review_write_route_status_code.when.authorization_blocked",
            "mutation gate or authorization boundary blocks the write route",
        ),
        (404, "pre_mutation_or_gate"): (
            "ui.review_write_route_status_code.when.target_missing",
            "the requested review target cannot be found in current Chronicle state",
        ),
        (409, "pre_mutation_or_gate"): (
            "ui.review_write_route_status_code.when.target_not_pending",
            "the target is no longer pending for the requested action",
        ),
        (500, "durable_write_path"): (
            "ui.review_write_route_status_code.when.durable_write_failed",
            "a durable write-path side effect fails and the route stays fail-closed",
        ),
    }
    key, text = mapping.get((status_code, family), ("", family.replace("_", " ")))
    return key, {}, text


def _review_status_code_summary_contract(
    status_code: int, family: str
) -> tuple[str, dict[str, Any], str]:
    mapping = {
        (200, "success"): (
            "ui.review_write_route_status_code.summary.success",
            "200: success; review decision persistence and audit insertion both succeed",
        ),
        (400, "pre_mutation_or_gate"): (
            "ui.review_write_route_status_code.summary.validation_failed",
            "400: pre_mutation_or_gate; reviewer-context or ui_intent validation fails before authorization",
        ),
        (403, "pre_mutation_or_gate"): (
            "ui.review_write_route_status_code.summary.authorization_blocked",
            "403: pre_mutation_or_gate; mutation gate or authorization boundary blocks the write route",
        ),
        (404, "pre_mutation_or_gate"): (
            "ui.review_write_route_status_code.summary.target_missing",
            "404: pre_mutation_or_gate; the requested review target cannot be found in current Chronicle state",
        ),
        (409, "pre_mutation_or_gate"): (
            "ui.review_write_route_status_code.summary.target_not_pending",
            "409: pre_mutation_or_gate; the target is no longer pending for the requested action",
        ),
        (500, "durable_write_path"): (
            "ui.review_write_route_status_code.summary.durable_write_failed",
            "500: durable_write_path; a durable write-path side effect fails and the route stays fail-closed",
        ),
    }
    key, text = mapping.get((status_code, family), ("", f"{status_code}: {family}"))
    return key, {}, text


def _review_target_state_note_contract(kind: str) -> tuple[str, dict[str, Any], str]:
    if kind == "scope":
        note = (
            "Current browser-triggered review routes operate only on Chronicle targets that are still pending within the local single-operator review boundary."
        )
        return ("ui.review_target_state_contract.note.scope", {}, note)
    if kind == "resolved_behavior":
        note = (
            "Approve/reject targets are hidden from the default pending queue after success, while request-changes remains pending until a later resolving review decision."
        )
        return ("ui.review_target_state_contract.note.resolved_behavior", {}, note)
    return ("", {}, "")


def _review_target_state_action_matrix() -> list[dict[str, Any]]:
    return [
        {
            "action": "approve",
            "requires_pending": True,
            "resulting_queue_state": "resolved_hidden_by_default",
            "resulting_disposition": "approve",
            "summary_key": "ui.review_target_state_contract.action_target_matrix.approve",
            "summary_params": {},
            "summary": (
                "approve requires a pending target, resolves the review, and hides it from the "
                "default pending queue after success."
            ),
        },
        {
            "action": "reject",
            "requires_pending": True,
            "resulting_queue_state": "resolved_hidden_by_default",
            "resulting_disposition": "reject",
            "summary_key": "ui.review_target_state_contract.action_target_matrix.reject",
            "summary_params": {},
            "summary": (
                "reject requires a pending target, resolves the review, and hides it from the "
                "default pending queue after success."
            ),
        },
        {
            "action": "request-changes",
            "requires_pending": True,
            "resulting_queue_state": "remains_pending",
            "resulting_disposition": "request_changes",
            "summary_key": "ui.review_target_state_contract.action_target_matrix.request_changes",
            "summary_params": {},
            "summary": (
                "request-changes requires a pending target and keeps the review in the pending "
                "queue until a later resolving decision."
            ),
        },
    ]


def _review_action_authorization_matrix() -> list[dict[str, Any]]:
    return [
        {
            "action": "approve",
            "ui_intent": "approve",
            "pending_required": True,
            "note_status": "optional",
            "authorized_reviewer_kinds": [ReviewerIdentityKind.LOCAL_OPERATOR.value],
            "summary_key": "ui.review_authorization_contract.action_matrix.approve",
            "summary_params": {},
            "summary": (
                "approve expects matching ui_intent, a pending target, and local_operator reviewer "
                "metadata inside the local single-operator boundary."
            ),
        },
        {
            "action": "reject",
            "ui_intent": "reject",
            "pending_required": True,
            "note_status": "optional",
            "authorized_reviewer_kinds": [ReviewerIdentityKind.LOCAL_OPERATOR.value],
            "summary_key": "ui.review_authorization_contract.action_matrix.reject",
            "summary_params": {},
            "summary": (
                "reject expects matching ui_intent, a pending target, and local_operator reviewer "
                "metadata inside the local single-operator boundary."
            ),
        },
        {
            "action": "request-changes",
            "ui_intent": "request-changes",
            "pending_required": True,
            "note_status": "optional",
            "authorized_reviewer_kinds": [ReviewerIdentityKind.LOCAL_OPERATOR.value],
            "summary_key": "ui.review_authorization_contract.action_matrix.request_changes",
            "summary_params": {},
            "summary": (
                "request-changes expects matching ui_intent, a pending target, and local_operator "
                "reviewer metadata inside the local single-operator boundary."
            ),
        },
    ]


def _runtime_preview_title_contract(preview: dict[str, Any]) -> tuple[str | None, dict[str, Any]]:
    record_kind = str(preview.get("record_kind", ""))
    title = str(preview.get("title", ""))
    if record_kind == "summary":
        return "ui.runtime_preview.title.summary", {}
    if record_kind == "execution":
        return "ui.template.runtime_preview.title.execution", {
            "operation": title.split(": ", 1)[1] if ": " in title else "",
        }
    if record_kind == "retrieval_plan":
        return "ui.template.runtime_preview.title.retrieval_plan", {
            "query": title.split(": ", 1)[1] if ": " in title else "",
        }
    if record_kind == "invocation_plan":
        suffix = title.split(": ", 1)[1] if ": " in title else ""
        return "ui.template.runtime_preview.title.invocation_plan", {
            "descriptor": suffix,
        }
    if record_kind == "unknown":
        return "ui.runtime_preview.title.unknown", {}
    return None, {}


def _provider_response_message_key(summary: dict[str, Any]) -> str:
    return (
        "ui.provider_response.message.present"
        if bool(summary.get("present"))
        else "ui.provider_response.message.unavailable"
    )


def _retrieval_handoff_message_key(handoff: dict[str, Any]) -> str:
    return (
        "ui.retrieval_handoff.message.records_available"
        if bool(handoff.get("referenced_record_ids"))
        else "ui.retrieval_handoff.message.no_records"
    )


def _retrieval_handoff_counts_contract(handoff: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    return "ui.template.retrieval_handoff.hit_counts", {
        "vector_hit_count": int(handoff.get("vector_hit_count", 0) or 0),
        "graph_hit_count": int(handoff.get("graph_hit_count", 0) or 0),
        "chronicle_hit_count": int(handoff.get("chronicle_hit_count", 0) or 0),
    }


def _invocation_plan_message_key(plan: dict[str, Any]) -> str:
    return (
        "ui.invocation_plan.message.ready"
        if bool(plan.get("invocation_ready"))
        else "ui.invocation_plan.message.blocked"
    )


def _invocation_plan_provider_summary_contract(plan: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    return "ui.template.invocation_plan.provider_summary", {
        "provider_kind": str(plan.get("provider_kind", "")),
        "provider_name": str(plan.get("provider_name", "")),
    }


def _graph_summary_message_key(status: str) -> str:
    return (
        "ui.graph_summary.message.available"
        if status == "available"
        else "ui.graph_summary.message.unavailable"
    )


def _status_summary_payload(prefix: str, value: str | None) -> tuple[str | None, str]:
    normalized = str(value or "").strip()
    if not normalized:
        return None, ""
    return f"{prefix}.{normalized}", normalized.replace("_", " ")


def _boolean_summary_payload(value: bool) -> tuple[str, str]:
    normalized = str(bool(value)).lower()
    return f"ui.boolean.{normalized}", normalized


def _graph_summary_counts_contract(node_count: int, edge_count: int) -> tuple[str, dict[str, Any]]:
    return "ui.template.graph_summary.counts", {
        "node_count": node_count,
        "edge_count": edge_count,
    }


def _ai_index_status_message_key(status: str) -> str:
    return (
        "ui.ai_index_status.message.available"
        if status == "available"
        else "ui.ai_index_status.message.unavailable"
    )


def _ai_index_vector_counts_contract(entry_count: int) -> tuple[str, dict[str, Any]]:
    return "ui.template.ai_index_status.vector_counts", {
        "entry_count": entry_count,
    }


def _ai_index_graph_counts_contract(node_count: int, edge_count: int) -> tuple[str, dict[str, Any]]:
    return "ui.template.ai_index_status.graph_counts", {
        "node_count": node_count,
        "edge_count": edge_count,
    }


def _ai_index_vector_detail_message_key(entry: dict[str, Any]) -> str:
    return (
        "ui.ai_index_vector_detail.message.metadata_present"
        if bool(entry.get("metadata"))
        else "ui.ai_index_vector_detail.message.metadata_empty"
    )


def _ai_index_vector_detail_counts_contract(text_length: int, metadata_count: int) -> tuple[str, dict[str, Any]]:
    return "ui.template.ai_index_vector_detail.counts", {
        "text_length": text_length,
        "metadata_count": metadata_count,
    }


def _ai_index_graph_node_detail_message_key(payload: dict[str, Any]) -> str:
    neighbor_total = int(payload.get("outgoing_neighbor_count", 0) or 0) + int(
        payload.get("incoming_neighbor_count", 0) or 0
    )
    return (
        "ui.ai_index_graph_node_detail.message.neighbors_present"
        if neighbor_total > 0
        else "ui.ai_index_graph_node_detail.message.no_neighbors"
    )


def _ai_index_graph_node_detail_counts_contract(
    *, label_count: int, property_count: int, outgoing_neighbor_count: int, incoming_neighbor_count: int
) -> tuple[str, dict[str, Any]]:
    return "ui.template.ai_index_graph_node_detail.counts", {
        "label_count": label_count,
        "property_count": property_count,
        "outgoing_neighbor_count": outgoing_neighbor_count,
        "incoming_neighbor_count": incoming_neighbor_count,
    }


def _package_review_message_key(status: str) -> str:
    return {
        "pass": "ui.package_review.message.pass",
        "warning": "ui.package_review.message.warning",
        "blocked": "ui.package_review.message.blocked",
    }.get(status, "ui.package_review.message.unavailable")


def _package_review_counts_contract(
    *, record_count: int, warning_count: int, finding_count: int
) -> tuple[str, dict[str, Any]]:
    return "ui.template.package_review.counts", {
        "record_count": record_count,
        "warning_count": warning_count,
        "finding_count": finding_count,
    }


def _decorate_package_review_payload(payload: dict[str, Any]) -> dict[str, Any]:
    status = str(payload.get("status", ""))
    payload["message"] = {
        "pass": "Package review passed for the current local context package snapshot.",
        "warning": "Package review reported warnings for the current local context package snapshot.",
        "blocked": "Package review reported blocked findings for the current local context package snapshot.",
    }.get(status, "Package review snapshot is unavailable.")
    payload["message_key"] = _package_review_message_key(status)
    counts_key, counts_params = _package_review_counts_contract(
        record_count=int(payload.get("record_count", 0) or 0),
        warning_count=len(payload.get("package_warnings", [])),
        finding_count=len(payload.get("findings", [])),
    )
    payload["counts_summary_key"] = counts_key
    payload["counts_summary_params"] = counts_params
    payload["boundary_note"] = (
        "Package review snapshot remains derived, read-only, and non-authoritative over primary Chronicle records."
    )
    payload["boundary_note_key"] = "ui.package_review.note.read_only_derived"
    return payload


def _append_mutation_blocker(
    blockers: list[str],
    next_steps: list[str],
    blocker_code: str,
) -> None:
    if blocker_code not in blockers:
        blockers.append(blocker_code)
    message = MUTATION_BLOCKER_TEXT.get(blocker_code, blocker_code.replace("_", " "))
    if message not in next_steps:
        next_steps.append(message)


def _serialize_mutation_blocker_details(blockers: list[str]) -> list[dict[str, str]]:
    return [
        {
            "code": blocker,
            "message_key": f"ui.mutation_blocker.{blocker}",
            "message": MUTATION_BLOCKER_TEXT.get(blocker, blocker.replace("_", " ")),
        }
        for blocker in blockers
    ]


def _mutation_blocker_source_label(source: str) -> str:
    return {
        "boundary": "Boundary prerequisites",
        "review_queue": "Pending review queue",
    }.get(source, source.replace("_", " "))


def _dominant_status(counts: dict[str, int]) -> str:
    if not counts:
        return "unknown"
    return max(sorted(counts), key=lambda key: counts.get(key, 0))


def _reviewer_boundary_dataset_fallback_label(dataset_key: str) -> str:
    return {
        "runtime_records": "runtime records",
        "review_queue": "review queue",
        "summary_jobs": "summary jobs",
    }.get(dataset_key, dataset_key.replace("_", " "))


def _reviewer_boundary_status_fallback_label(status: str) -> str:
    return status.replace("_", " ")


def _reviewer_boundary_fallback_message(*, dataset_key: str, overview: bool) -> str:
    dataset_label = _reviewer_boundary_dataset_fallback_label(dataset_key)
    if overview:
        return (
            f"{dataset_label.capitalize()} reviewer-boundary summary is a read-only drilldown for moving "
            "from overview counts to list rows and detail explanation."
        )
    return (
        f"{dataset_label.capitalize()} reviewer-boundary summary is a read-only drilldown for moving "
        "from overview counts to list rows and detail explanation."
    )


def _reviewer_boundary_fallback_fact_line(
    *,
    dataset_key: str,
    enforcement_status: str,
    gate_status: str,
    dominant: bool,
) -> str:
    dataset_label = _reviewer_boundary_dataset_fallback_label(dataset_key)
    enforcement_label = _reviewer_boundary_status_fallback_label(enforcement_status)
    gate_label = _reviewer_boundary_status_fallback_label(gate_status)
    if dominant:
        return (
            f"This read-only drilldown summary highlights {dataset_label} because dominant reviewer "
            f"enforcement is {enforcement_label} and dominant reviewer gate status is {gate_label} "
            "for the current local boundary."
        )
    return (
        f"This read-only drilldown row appears in {dataset_label} because reviewer enforcement is "
        f"{enforcement_label} and reviewer gate status is {gate_label} for the current local boundary."
    )


def _reviewer_boundary_drilldown_summary(
    *,
    dataset_key: str,
    list_path: str,
    detail_path: str | None,
    enforcement_status: str,
    gate_status: str,
) -> dict[str, Any]:
    return {
        "summary_variant": "row_detail",
        "dataset_key": dataset_key,
        "overview_path": "/api/overview",
        "list_path": list_path,
        "detail_path": detail_path,
        "message_template_key": "ui.template.reviewer_boundary_drilldown_message",
        "message_params": {
            "dataset_key": dataset_key,
        },
        "message_key": "ui.message.reviewer_boundary_drilldown",
        "enforcement_status": enforcement_status,
        "validation_gate_status": gate_status,
        "enforcement_filter_value": f"reviewer_enforcement:{enforcement_status}",
        "validation_gate_filter_value": f"reviewer_gate:{gate_status}",
        "fact_line_template_key": "ui.template.reviewer_boundary_fact_line",
        "fact_line_params": {
            "dataset_key": dataset_key,
            "enforcement_status": enforcement_status,
            "validation_gate_status": gate_status,
        },
        "summary_level": "read_only_reviewer_boundary_drilldown",
        "message": _reviewer_boundary_fallback_message(dataset_key=dataset_key, overview=False),
        "fact_line": _reviewer_boundary_fallback_fact_line(
            dataset_key=dataset_key,
            enforcement_status=enforcement_status,
            gate_status=gate_status,
            dominant=False,
        ),
    }


def _mutation_scope_note(boundary: dict[str, Any]) -> str:
    if boundary.get("mutation_enabled", False):
        return "Browser apply is available only inside the explicit loopback-local session boundary."
    if boundary.get("mutation_capability_flag", False):
        return "Capability intent is recorded, but the UI remains preview-only until local session enablement, auth, authorization, reviewer identity, and session proof align."
    return "The UI remains preview-only until explicit local write capability, session enablement, auth, authorization, reviewer identity, and session proof are configured."


def _mutation_scope_note_key(boundary: dict[str, Any]) -> str:
    if boundary.get("mutation_enabled", False):
        return "ui.mutation_readiness.note.loopback_local_boundary"
    if boundary.get("mutation_capability_flag", False):
        return "ui.mutation_readiness.note.capability_intent_recorded"
    return "ui.mutation_readiness.note.preview_only_requirements_pending"


def _mutation_readiness_message_key(boundary: dict[str, Any]) -> str:
    if boundary.get("mutation_enabled", False):
        return "ui.mutation_readiness.message.enabled"
    if boundary.get("mutation_capability_flag", False):
        return "ui.mutation_readiness.message.preview_capability_intent"
    return "ui.mutation_readiness.message.preview_requirements_pending"


def _mutation_operational_message_key(has_unsatisfied_checks: bool) -> str:
    if has_unsatisfied_checks:
        return "ui.mutation_operational_readiness.message.blocked"
    return "ui.mutation_operational_readiness.message.ready"


def _mutation_blocker_summaries(
    *,
    boundary_blockers: list[str],
    pending_boundary_warning_counts: dict[str, int],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for blocker_code in boundary_blockers:
        key = ("boundary", blocker_code)
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            {
                "code": blocker_code,
                "message_key": f"ui.mutation_blocker.{blocker_code}",
                "message": MUTATION_BLOCKER_TEXT.get(blocker_code, blocker_code.replace("_", " ")),
                "source": "boundary",
                "source_label_key": "ui.mutation_blocker_source.boundary",
                "source_label": _mutation_blocker_source_label("boundary"),
                "affected_count": 1,
                "summary_key": "ui.template.mutation_blocker_summary_boundary",
                "summary_params": {
                    "source_label": _mutation_blocker_source_label("boundary"),
                    "message": MUTATION_BLOCKER_TEXT.get(
                        blocker_code, blocker_code.replace("_", " ")
                    ),
                },
                "summary": (
                    "Boundary prerequisites: "
                    + MUTATION_BLOCKER_TEXT.get(blocker_code, blocker_code.replace("_", " "))
                ),
            }
        )
    for blocker_code, count in sorted(pending_boundary_warning_counts.items()):
        key = ("review_queue", blocker_code)
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            {
                "code": blocker_code,
                "message_key": f"ui.mutation_blocker.{blocker_code}",
                "message": MUTATION_BLOCKER_TEXT.get(blocker_code, blocker_code.replace("_", " ")),
                "source": "review_queue",
                "source_label_key": "ui.mutation_blocker_source.review_queue",
                "source_label": _mutation_blocker_source_label("review_queue"),
                "affected_count": count,
                "summary_key": "ui.template.mutation_blocker_summary_review_queue",
                "summary_params": {
                    "source_label": _mutation_blocker_source_label("review_queue"),
                    "affected_count": count,
                    "message": MUTATION_BLOCKER_TEXT.get(
                        blocker_code, blocker_code.replace("_", " ")
                    ),
                },
                "summary": (
                    f"Pending review queue ({count}): "
                    + MUTATION_BLOCKER_TEXT.get(blocker_code, blocker_code.replace("_", " "))
                ),
            }
        )
    return rows


def _mutation_enablement_checks(
    *,
    boundary: dict[str, Any],
    pending_boundary_warning_counts: dict[str, int],
) -> list[dict[str, Any]]:
    blocker_set = {str(item) for item in boundary.get("mutation_blockers", [])}
    checks = [
        {
            "code": "mutation_capability_flag",
            "label": "Capability flag enabled",
            "label_key": "ui.mutation_enablement_check.mutation_capability_flag.label",
            "satisfied": "mutation_capability_flag_disabled" not in blocker_set,
            "detail_key": "ui.mutation_enablement_check.mutation_capability_flag.detail",
            "detail": MUTATION_BLOCKER_TEXT["mutation_capability_flag_disabled"],
        },
        {
            "code": "ui_mutation_enable_flag",
            "label": "Session enable flag enabled",
            "label_key": "ui.mutation_enablement_check.ui_mutation_enable_flag.label",
            "satisfied": "ui_mutation_enable_flag_disabled" not in blocker_set,
            "detail_key": "ui.mutation_enablement_check.ui_mutation_enable_flag.detail",
            "detail": MUTATION_BLOCKER_TEXT["ui_mutation_enable_flag_disabled"],
        },
        {
            "code": "auth_boundary",
            "label": "Auth boundary configured",
            "label_key": "ui.mutation_enablement_check.auth_boundary.label",
            "satisfied": "auth_not_enabled" not in blocker_set,
            "detail_key": "ui.mutation_enablement_check.auth_boundary.detail",
            "detail": MUTATION_BLOCKER_TEXT["auth_not_enabled"],
        },
        {
            "code": "authorization_boundary",
            "label": "Authorization boundary configured",
            "label_key": "ui.mutation_enablement_check.authorization_boundary.label",
            "satisfied": "authorization_not_enabled" not in blocker_set,
            "detail_key": "ui.mutation_enablement_check.authorization_boundary.detail",
            "detail": MUTATION_BLOCKER_TEXT["authorization_not_enabled"],
        },
        {
            "code": "reviewer_identity",
            "label": "Reviewer identity recorded",
            "label_key": "ui.mutation_enablement_check.reviewer_identity.label",
            "satisfied": pending_boundary_warning_counts.get("reviewer_identity_missing", 0) == 0,
            "detail_key": "ui.mutation_enablement_check.reviewer_identity.detail",
            "detail": MUTATION_BLOCKER_TEXT["reviewer_identity_missing"],
        },
        {
            "code": "session_labels",
            "label": "Session labels recorded",
            "label_key": "ui.mutation_enablement_check.session_labels.label",
            "satisfied": pending_boundary_warning_counts.get("reviewer_session_label_missing", 0) == 0,
            "detail_key": "ui.mutation_enablement_check.session_labels.detail",
            "detail": MUTATION_BLOCKER_TEXT["reviewer_session_label_missing"],
        },
    ]
    return checks


def _mutation_operational_readiness(
    *,
    enablement_checks: list[dict[str, Any]],
) -> dict[str, Any]:
    unsatisfied = [
        {
            "code": str(check.get("code", "")),
            "label": str(check.get("label", check.get("code", ""))),
            "label_key": str(check.get("label_key", "")),
            "detail_key": str(check.get("detail_key", "")),
            "detail": str(check.get("detail", "")),
            "summary_key": "ui.template.mutation_enablement_check_summary",
            "summary_params": {
                "label": str(check.get("label", check.get("code", ""))),
                "detail": str(check.get("detail", "")),
            },
        }
        for check in enablement_checks
        if check.get("satisfied") is not True
    ]
    satisfied_count = len(enablement_checks) - len(unsatisfied)
    required_count = len(enablement_checks)
    return {
        "status": "ready" if not unsatisfied else "blocked",
        "satisfied_count": satisfied_count,
        "required_count": required_count,
        "remaining_count": len(unsatisfied),
        "blocking_codes": [str(item.get("code", "")) for item in unsatisfied],
        "blocking_labels": [str(item.get("label", item.get("code", ""))) for item in unsatisfied],
        "blocking_summaries": [
            f"{str(item.get('label', item.get('code', 'check')))}: {str(item.get('detail', ''))}"
            for item in unsatisfied
        ],
        "unsatisfied_checks": unsatisfied,
        "message": (
            "All explicit local mutation prerequisites are currently satisfied."
            if not unsatisfied
            else "Explicit local mutation prerequisites remain unsatisfied."
        ),
        "message_key": _mutation_operational_message_key(bool(unsatisfied)),
    }


def _reviewer_context_requirements(metadata: UIBoundaryMetadata) -> dict[str, Any]:
    effective_required_fields = ["reviewer_label", "reviewer_kind", "ui_intent"]
    if metadata.session_gating:
        effective_required_fields.append("session_label")
    accepted_reviewer_kinds = [ReviewerIdentityKind.LOCAL_OPERATOR.value]
    advisory_only_reviewer_kinds = [ReviewerIdentityKind.USER_DECLARED.value]
    session_boundary_status = "required" if metadata.session_gating else "optional"
    expectation_summary = (
        "Explicit local GUI mutation currently expects local_operator reviewer metadata, matching ui_intent, and a session label inside the session-gated loopback-local boundary."
        if metadata.session_gating
        else "Preview/read-only review context currently expects local_operator reviewer metadata and matching ui_intent; session labels remain optional until session-gated local mutation is enabled."
    )
    return {
        "required_fields": ["reviewer_label", "reviewer_kind", "ui_intent"],
        "effective_required_fields": effective_required_fields,
        "effective_required_field_details": [
            {
                "field": str(field),
                "summary_key": f"ui.write_request_field.{field}",
                "summary": str(field).replace("_", " "),
            }
            for field in effective_required_fields
        ],
        "reviewer_label_pattern": REVIEWER_LABEL_PATTERN.pattern,
        "reviewer_label_examples": ["alice", "desk-operator.01"],
        "session_label_required": bool(metadata.session_gating),
        "session_label_pattern": SESSION_LABEL_PATTERN.pattern,
        "session_label_examples": ["desk-session-1", "review.local-01"],
        "mutation_session_id_pattern": MUTATION_SESSION_ID_PATTERN.pattern,
        "mutation_request_id_pattern": MUTATION_REQUEST_ID_PATTERN.pattern,
        "accepted_reviewer_kinds": accepted_reviewer_kinds,
        "accepted_reviewer_kind_details": [
            {
                "kind": str(kind),
                "summary_key": f"ui.reviewer_kind.{kind}",
                "summary": str(kind).replace("_", " "),
            }
            for kind in accepted_reviewer_kinds
        ],
        "required_reviewer_kinds_for_mutation": [ReviewerIdentityKind.LOCAL_OPERATOR.value],
        "advisory_only_reviewer_kinds": advisory_only_reviewer_kinds,
        "advisory_only_reviewer_kind_details": [
            {
                "kind": str(kind),
                "summary_key": f"ui.reviewer_kind.{kind}",
                "summary": str(kind).replace("_", " "),
            }
            for kind in advisory_only_reviewer_kinds
        ],
        "session_boundary_status": session_boundary_status,
        "session_boundary_status_summary_key": f"ui.reviewer_context.session_boundary_status.{session_boundary_status}",
        "session_boundary_status_summary": session_boundary_status.replace("_", " "),
        "ui_intent_required": True,
        "ui_intent_required_summary_key": "ui.reviewer_context.ui_intent_required.true",
        "ui_intent_required_summary": "true",
        "expectation_summary": expectation_summary,
        "expectation_summary_key": (
            "ui.reviewer_context.expectation.required"
            if metadata.session_gating
            else "ui.reviewer_context.expectation.optional"
        ),
        "authority_note": "Request reviewer metadata is required local context, but it is not sufficient proof of authority on its own.",
        "authority_note_key": "ui.reviewer_context.note.authority",
        "reviewer_label_note": "Reviewer label must identify the local operator consistently enough for audit and review history drilldown.",
        "reviewer_label_note_key": "ui.reviewer_context.note.reviewer_label",
        "reviewer_kind_note": "Only local_operator is currently eligible for explicit local GUI mutation; user_declared remains advisory-only metadata.",
        "reviewer_kind_note_key": "ui.reviewer_context.note.reviewer_kind",
        "session_note": (
            "Session label is required because the current local mutation boundary is session-gated."
            if metadata.session_gating
            else "Session label is optional while session-gated review is disabled."
        ),
        "session_note_key": (
            "ui.reviewer_context.note.session_required"
            if metadata.session_gating
            else "ui.reviewer_context.note.session_optional"
        ),
        "ui_intent_note": "ui_intent must match the requested action so preview and apply paths stay fail-closed.",
        "ui_intent_note_key": "ui.reviewer_context.note.ui_intent",
        "mutation_token_required": bool(metadata.mutation_enabled),
        "mutation_token_transport": metadata.mutation_token_transport,
        "mutation_token_header": metadata.mutation_token_header,
        "mutation_token_note": (
            "A per-session local mutation token is required on browser-triggered write routes."
            if metadata.mutation_enabled
            else "Per-session local mutation tokens are only required after GUI mutation is explicitly enabled."
        ),
        "mutation_session_note": (
            "Browser-triggered review apply requests must stay within the current local mutation session."
        ),
        "mutation_request_id_note": (
            "Each browser-triggered review apply request must carry a unique local mutation request identifier."
        ),
    }


def _reviewer_enforcement_summary(metadata: UIBoundaryMetadata) -> dict[str, Any]:
    reviewer_context = _reviewer_context_requirements(metadata)
    if metadata.mutation_enabled:
        status = "enforced_local_session"
        message = (
            "Local reviewer/session enforcement is active only for the explicit loopback-local mutation route."
        )
    elif (
        metadata.auth_mode == UIAuthMode.LOOPBACK_LOCAL
        and metadata.authorization_mode == UIAuthorizationMode.REVIEWER_DECLARED
    ):
        status = "preview_contract_only"
        message = (
            "Reviewer/session enforcement requirements are defined for the local route contract, but read-only surfaces remain descriptive until GUI mutation is explicitly enabled."
        )
    else:
        status = "descriptive_only"
        message = (
            "Reviewer/session fields remain descriptive local metadata until explicit route enforcement is enabled."
        )
    return {
        "status": status,
        "message": message,
        "message_key": f"ui.reviewer_enforcement.message.{status}",
        "enforced_request_fields": reviewer_context.get("effective_required_fields", []),
        "enforced_reviewer_kinds_for_mutation": reviewer_context.get(
            "required_reviewer_kinds_for_mutation", []
        ),
        "descriptive_only_reviewer_kinds": reviewer_context.get("advisory_only_reviewer_kinds", []),
        "session_gated": bool(metadata.session_gating),
        "route_enforcement_scope": "browser-triggered review write route only",
        "read_only_scope_note": (
            "Read-only UI surfaces expose current local enforcement expectations, but they do not grant or prove authority on their own."
        ),
        "read_only_scope_note_key": "ui.reviewer_enforcement.note.read_only_scope",
        "descriptive_note": (
            "Recorded reviewer/session metadata supports local auditability and boundary inspection, but it does not imply hosted authentication, multi-user-safe authority, or default-on GUI mutation."
        ),
        "descriptive_note_key": "ui.reviewer_enforcement.note.descriptive",
    }


def _reviewer_validation_gate_summary(metadata: UIBoundaryMetadata) -> dict[str, Any]:
    reviewer_context = _reviewer_context_requirements(metadata)
    validation_error_codes = [
        "invalid_mutation_token",
        "invalid_mutation_session",
        "mutation_request_id_required",
        "invalid_mutation_request_id",
        "reviewer_label_required",
        "invalid_reviewer_label",
        "session_label_required",
        "invalid_session_label",
        "ui_intent_mismatch",
        "invalid_reviewer_kind",
    ]
    if metadata.mutation_enabled:
        status = "local_route_enforced"
        message = (
            "Reviewer/session validation and gate checks are actively enforced on the local browser-triggered write route."
        )
    elif metadata.auth_mode == UIAuthMode.LOOPBACK_LOCAL:
        status = "preview_route_contract"
        message = (
            "Reviewer/session validation and gate checks are defined for the local route contract, but the current UI surface remains preview-only."
        )
    else:
        status = "read_only_preview"
        message = (
            "Reviewer/session validation and gate checks are exposed for inspection, while read-only UI surfaces remain non-authoritative previews."
        )
    return {
        "status": status,
        "message": message,
        "message_key": f"ui.reviewer_validation_gate.message.{status}",
        "required_request_fields": reviewer_context.get("effective_required_fields", []),
        "validation_error_codes": validation_error_codes,
        "authorization_error_codes": ["authorization_failed"],
        "target_state_error_codes": ["review_target_not_found", "review_not_pending"],
        "durable_write_error_codes": ["audit_insertion_failed", "decision_persistence_failed"],
        "route_gate_error_code": "mutation_disabled",
        "mutation_token_header": metadata.mutation_token_header,
        "mutation_session_id_pattern": MUTATION_SESSION_ID_PATTERN.pattern,
        "mutation_request_id_pattern": MUTATION_REQUEST_ID_PATTERN.pattern,
        "session_gated": bool(metadata.session_gating),
        "pending_target_required": True,
        "ui_intent_required": True,
        "fail_closed": True,
        "scope_note": (
            "The same reviewer/session validation families should stay aligned across readiness, preview, apply, and recovery-facing surfaces."
        ),
        "scope_note_key": "ui.reviewer_validation_gate.note.scope_alignment",
    }


def _reviewer_identity_proof_contract(metadata: UIBoundaryMetadata) -> dict[str, Any]:
    reviewer_context = _reviewer_context_requirements(metadata)
    proof_status = (
        "session_gated_local_operator"
        if metadata.session_gating
        else "local_operator_advisory"
    )
    required_identity_fields = reviewer_context.get("effective_required_fields", [])
    return {
        "proof_status": proof_status,
        "proof_status_message_key": f"ui.identity_proof.status.{proof_status}",
        "proof_status_message": proof_status.replace("_", " "),
        "accepted_auth_modes": [UIAuthMode.LOOPBACK_LOCAL],
        "required_identity_fields": required_identity_fields,
        "required_identity_field_details": [
            {
                "field": str(field),
                "summary_key": f"ui.identity_proof.field.{field}",
                "summary": str(field).replace("_", " "),
            }
            for field in required_identity_fields
        ],
        "session_label_required": bool(metadata.session_gating),
        "session_label_pattern": reviewer_context.get("session_label_pattern", ""),
        "required_reviewer_kinds_for_mutation": reviewer_context.get(
            "required_reviewer_kinds_for_mutation", []
        ),
        "accepted_reviewer_kinds": reviewer_context.get("accepted_reviewer_kinds", []),
        "advisory_only_reviewer_kinds": reviewer_context.get("advisory_only_reviewer_kinds", []),
        "proof_note": (
            "Local reviewer identity proof currently means loopback-local operator context plus reviewer/session metadata."
        ),
        "insufficient_without": [
            "explicit authorization boundary",
            "fail-closed audit insertion",
        ],
    }


def _ui_authorization_contract(metadata: UIBoundaryMetadata) -> dict[str, Any]:
    server_side_checks = [
        "mutation_enabled",
        "reviewer_identity_assurance_boundary_aligned",
        "review_capability_ready",
        "pending_target_state",
    ]
    return {
        "authorization_status": (
            "explicit_local_reviewer_declared"
            if metadata.authorization_mode == UIAuthorizationMode.REVIEWER_DECLARED
            else "advisory_only"
        ),
        "authorization_status_summary_key": (
            "ui.review_authorization_contract.status.explicit_local_reviewer_declared"
            if metadata.authorization_mode == UIAuthorizationMode.REVIEWER_DECLARED
            else "ui.review_authorization_contract.status.advisory_only"
        ),
        "authorization_status_summary": (
            "explicit local reviewer declared"
            if metadata.authorization_mode == UIAuthorizationMode.REVIEWER_DECLARED
            else "advisory only"
        ),
        "required_authorization_mode": UIAuthorizationMode.REVIEWER_DECLARED,
        "required_identity_assurance_status": "boundary_aligned",
        "required_identity_assurance_status_summary_key": (
            "ui.review_authorization_contract.required_identity_assurance_status.boundary_aligned"
        ),
        "required_identity_assurance_status_summary": "boundary aligned",
        "required_review_capability_status": "ready",
        "target_pending_required": True,
        "server_side_checks": server_side_checks,
        "server_side_check_details": [
            {
                "code": code,
                "summary_key": f"ui.review_authorization_contract.server_side_check.{code}",
                "summary": code.replace("_", " "),
            }
            for code in server_side_checks
        ],
        "scope_note": (
            "Current browser-triggered authorization is a local single-operator boundary only; it does not claim hosted or multi-user-safe authority semantics."
        ),
        "action_authorization_matrix": _review_action_authorization_matrix(),
    }


def _ui_target_state_contract() -> dict[str, Any]:
    scope_note_key, scope_note_params, scope_note = _review_target_state_note_contract("scope")
    resolved_behavior_note_key, resolved_behavior_note_params, resolved_behavior_note = (
        _review_target_state_note_contract("resolved_behavior")
    )
    target_state_checks = [
        "target_exists_in_chronicle_state",
        "target_review_status_needs_review",
        "target_pending_for_requested_action",
    ]
    return {
        "required_current_review_status": "needs_review",
        "required_current_review_status_summary_key": (
            "ui.review_target_state_contract.required_current_review_status.needs_review"
        ),
        "required_current_review_status_summary": "needs review",
        "pending_target_required": True,
        "resolved_status_code": HTTPStatus.CONFLICT.value,
        "not_found_status_code": HTTPStatus.NOT_FOUND.value,
        "target_state_checks": target_state_checks,
        "target_state_check_details": [
            {
                "code": code,
                "summary_key": f"ui.review_target_state_contract.check.{code}",
                "summary": code.replace("_", " "),
            }
            for code in target_state_checks
        ],
        "scope_note": scope_note,
        "scope_note_key": scope_note_key,
        "scope_note_params": scope_note_params,
        "action_target_matrix": _review_target_state_action_matrix(),
        "resolved_behavior_note": resolved_behavior_note,
        "resolved_behavior_note_key": resolved_behavior_note_key,
        "resolved_behavior_note_params": resolved_behavior_note_params,
    }


def _ui_write_route_contract(metadata: UIBoundaryMetadata) -> dict[str, Any]:
    reviewer_context = _reviewer_context_requirements(metadata)
    identity_proof = _reviewer_identity_proof_contract(metadata)
    authorization_contract = _ui_authorization_contract(metadata)
    target_state_contract = _ui_target_state_contract()
    mutation_enabled = bool(metadata.mutation_enabled)
    actions = ["approve", "reject", "request-changes"]
    pre_mutation_or_gate_errors = [
        "mutation_disabled",
        "invalid_mutation_token",
        "invalid_mutation_session",
        "mutation_request_id_required",
        "invalid_mutation_request_id",
        "duplicate_mutation_request",
        "reviewer_label_required",
        "invalid_reviewer_label",
        "session_label_required",
        "invalid_session_label",
        "ui_intent_mismatch",
        "invalid_reviewer_kind",
        "authorization_failed",
        "review_target_not_found",
        "review_not_pending",
        "invalid_json",
    ]
    durable_write_path_errors = [
        "audit_insertion_failed",
        "decision_persistence_failed",
    ]
    action_routes = [
        {
            "action": action,
            "path_template": f"/api/review-actions/<event_id>/{action}",
            "cli_equivalent_template": f"chronicle review {action} --event <event_id>",
            "path_summary_key": "ui.template.review_write_route.action_route",
            "path_summary_params": {
                "action": action,
                "path_template": f"/api/review-actions/<event_id>/{action}",
            },
            "path_summary": f"{action}: /api/review-actions/<event_id>/{action}",
            "cli_summary_key": "ui.template.review_write_route.cli_equivalent",
            "cli_summary_params": {
                "action": action,
                "cli_equivalent_template": f"chronicle review {action} --event <event_id>",
            },
            "cli_summary": f"{action}: chronicle review {action} --event <event_id>",
        }
        for action in actions
    ]
    status_code_contract = []
    for status_code, family in [
        (HTTPStatus.OK.value, "success"),
        (HTTPStatus.BAD_REQUEST.value, "pre_mutation_or_gate"),
        (HTTPStatus.FORBIDDEN.value, "pre_mutation_or_gate"),
        (HTTPStatus.NOT_FOUND.value, "pre_mutation_or_gate"),
        (HTTPStatus.CONFLICT.value, "pre_mutation_or_gate"),
        (HTTPStatus.INTERNAL_SERVER_ERROR.value, "durable_write_path"),
    ]:
        when_key, when_params, when = _review_status_code_when_contract(status_code, family)
        summary_key, summary_params, summary = _review_status_code_summary_contract(status_code, family)
        status_code_contract.append(
            {
                "status_code": status_code,
                "family": family,
                "when": when,
                "when_key": when_key,
                "when_params": when_params,
                "summary": summary,
                "summary_key": summary_key,
                "summary_params": summary_params,
            }
        )
    pre_gate_summary_key, pre_gate_summary_params, pre_gate_summary = (
        _review_failure_family_summary_contract("pre_mutation_or_gate")
    )
    durable_summary_key, durable_summary_params, durable_summary = (
        _review_failure_family_summary_contract("durable_write_path")
    )
    expected_request_fields = reviewer_context.get("effective_required_fields", [])
    transaction_order = [
        "validate route + reviewer context",
        "perform review decision persistence attempt",
        "perform audit insertion attempt",
        "report success only if both durable side effects succeeded",
    ]
    return {
        "route_template": "/api/review-actions/<event_id>/<action>",
        "actions": actions,
        "action_routes": action_routes,
        "status_code_contract": status_code_contract,
        "expected_request_fields": expected_request_fields,
        "mutation_token_required": bool(metadata.mutation_enabled),
        "mutation_token_transport": metadata.mutation_token_transport,
        "mutation_token_header": metadata.mutation_token_header,
        "mutation_session_id_pattern": MUTATION_SESSION_ID_PATTERN.pattern,
        "mutation_request_id_pattern": MUTATION_REQUEST_ID_PATTERN.pattern,
        "expected_request_field_details": [
            {
                "field": str(field),
                "summary_key": f"ui.write_request_field.{field}",
                "summary": str(field).replace("_", " "),
            }
            for field in expected_request_fields
        ],
        "optional_request_fields": ["note"],
        "accepted_reviewer_kinds": reviewer_context.get("accepted_reviewer_kinds", []),
        "advisory_only_reviewer_kinds": reviewer_context.get("advisory_only_reviewer_kinds", []),
        "session_gated": bool(metadata.session_gating),
        "mutation_enabled": mutation_enabled,
        "success_status_code": HTTPStatus.OK.value,
        "success_status_summary": status_code_contract[0]["summary"],
        "success_status_summary_key": status_code_contract[0]["summary_key"],
        "success_status_summary_params": status_code_contract[0]["summary_params"],
        "blocked_status_code": HTTPStatus.FORBIDDEN.value,
        "blocked_status_summary": status_code_contract[2]["summary"],
        "blocked_status_summary_key": status_code_contract[2]["summary_key"],
        "blocked_status_summary_params": status_code_contract[2]["summary_params"],
        "validation_status_code": HTTPStatus.BAD_REQUEST.value,
        "resolved_status_code": HTTPStatus.CONFLICT.value,
        "missing_target_status_code": HTTPStatus.NOT_FOUND.value,
        "server_error_status_code": HTTPStatus.INTERNAL_SERVER_ERROR.value,
        "durable_success_requirements": [
            "route_gating_passed",
            "reviewer_context_validated",
            "decision_persisted",
            "audit_persisted",
        ],
        "transaction_order": transaction_order,
        "transaction_order_details": [
            {
                "step": step,
                "summary_key": f"ui.review_write_route.transaction_order.step_{index + 1}",
                "summary": step,
            }
            for index, step in enumerate(transaction_order)
        ],
        "transaction_rule": (
            "No durable GUI review result is reported as applied unless both review decision persistence and audit insertion succeed."
        ),
        "failure_families": [
            {
                "family": "pre_mutation_or_gate",
                "summary": pre_gate_summary,
                "summary_key": pre_gate_summary_key,
                "summary_params": pre_gate_summary_params,
                "possible_error_codes": pre_mutation_or_gate_errors,
            },
            {
                "family": "durable_write_path",
                "summary": durable_summary,
                "summary_key": durable_summary_key,
                "summary_params": durable_summary_params,
                "possible_error_codes": durable_write_path_errors,
            },
        ],
        "identity_proof_contract": identity_proof,
        "authorization_contract": authorization_contract,
        "target_state_contract": target_state_contract,
        "success_contract": {
            "transaction_status": "decision_and_audit_persisted",
            "transaction_status_summary_key": "ui.review_success_contract.transaction_status.decision_and_audit_persisted",
            "transaction_status_summary": "decision and audit persisted",
            "rollback_status": "not_required",
            "rollback_status_summary_key": "ui.review_contract.rollback_status.not_required",
            "rollback_status_summary": "not required",
            "durable_mutation_reported": True,
            "durable_success_requirements": [
                "route_gating_passed",
                "reviewer_context_validated",
                "decision_persisted",
                "audit_persisted",
            ],
        },
        "failure_contract": {
            "rollback_status": "fail_closed",
            "rollback_status_summary_key": "ui.review_contract.rollback_status.fail_closed",
            "rollback_status_summary": "fail closed",
            "durable_mutation_reported_on_failure": False,
            "durable_mutation_reported_on_failure_summary_key": (
                "ui.review_failure_contract.durable_mutation_reported_on_failure.false"
            ),
            "durable_mutation_reported_on_failure_summary": "false",
            "possible_error_codes": pre_mutation_or_gate_errors + durable_write_path_errors,
            "failure_families": [
                {
                    "family": "pre_mutation_or_gate",
                    "summary": pre_gate_summary,
                    "summary_key": pre_gate_summary_key,
                    "summary_params": pre_gate_summary_params,
                    "possible_error_codes": pre_mutation_or_gate_errors,
                },
                {
                    "family": "durable_write_path",
                    "summary": durable_summary,
                    "summary_key": durable_summary_key,
                    "summary_params": durable_summary_params,
                    "possible_error_codes": durable_write_path_errors,
                },
            ],
        },
    }


@dataclass(frozen=True)
class UIStartupMetadata:
    """Startup metadata printed by `chronicle ui --json`."""

    host: str
    port: int
    url: str
    root: str
    bind_scope: str
    read_only: bool = True
    runtime: str = "foreground-local-ui"
    external_runtime: bool = False
    mutation_enabled: bool = False
    mutation_capability_flag: bool = False
    auth_mode: str = UIAuthMode.NOT_ENABLED
    authorization_mode: str = UIAuthorizationMode.NOT_ENABLED
    ui_boundary: UIBoundaryMetadata | None = None

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)


def build_startup_metadata(
    *,
    host: str,
    port: int,
    root: Path,
    mutation_capability_flag: bool = False,
    enable_ui_mutation: bool = False,
    auth_mode: str = UIAuthMode.NOT_ENABLED,
    authorization_mode: str = UIAuthorizationMode.NOT_ENABLED,
) -> UIStartupMetadata:
    """Build local UI startup metadata without starting the server."""
    ui_boundary = build_ui_boundary_metadata(
        host=host,
        mutation_capability_flag=mutation_capability_flag,
        enable_ui_mutation=enable_ui_mutation,
        auth_mode=auth_mode,
        authorization_mode=authorization_mode,
    )
    return UIStartupMetadata(
        host=host,
        port=port,
        url=f"http://{host}:{port}",
        root=str(root.resolve()),
        bind_scope=ui_boundary.bind_scope,
        mutation_enabled=ui_boundary.mutation_enabled,
        mutation_capability_flag=ui_boundary.mutation_capability_flag,
        auth_mode=ui_boundary.auth_mode,
        authorization_mode=ui_boundary.authorization_mode,
        ui_boundary=ui_boundary,
    )


def build_ui_boundary_metadata(
    *,
    host: str = DEFAULT_UI_HOST,
    mutation_capability_flag: bool = False,
    enable_ui_mutation: bool = False,
    auth_mode: str = UIAuthMode.NOT_ENABLED,
    authorization_mode: str = UIAuthorizationMode.NOT_ENABLED,
) -> UIBoundaryMetadata:
    """Build explicit UI boundary metadata."""
    mutation_enabled = (
        enable_ui_mutation
        and mutation_capability_flag
        and auth_mode == UIAuthMode.LOOPBACK_LOCAL
        and authorization_mode == UIAuthorizationMode.REVIEWER_DECLARED
    )
    blockers = []
    if not mutation_enabled:
        blockers.append("write_routes_disabled")
    if auth_mode == UIAuthMode.NOT_ENABLED:
        blockers.append("auth_not_enabled")
    if authorization_mode == UIAuthorizationMode.NOT_ENABLED:
        blockers.append("authorization_not_enabled")
    if not mutation_capability_flag:
        blockers.append("mutation_capability_flag_disabled")
    if not enable_ui_mutation:
        blockers.append("ui_mutation_enable_flag_disabled")
    metadata = UIBoundaryMetadata(
        bind_scope=_bind_scope(host),
        read_only=not mutation_enabled,
        mutation_enabled=mutation_enabled,
        mutation_capability_flag=mutation_capability_flag,
        mutation_enabled_summary_key=_boolean_summary_payload(bool(mutation_enabled))[0],
        mutation_enabled_summary=_boolean_summary_payload(bool(mutation_enabled))[1],
        mutation_capability_flag_summary_key=_boolean_summary_payload(bool(mutation_capability_flag))[0],
        mutation_capability_flag_summary=_boolean_summary_payload(bool(mutation_capability_flag))[1],
        auth_mode=auth_mode,
        authorization_mode=authorization_mode,
        session_gating=auth_mode == UIAuthMode.LOOPBACK_LOCAL,
        session_gating_summary_key=_boolean_summary_payload(bool(auth_mode == UIAuthMode.LOOPBACK_LOCAL))[0],
        session_gating_summary=_boolean_summary_payload(bool(auth_mode == UIAuthMode.LOOPBACK_LOCAL))[1],
        shared_machine_safe=mutation_enabled,
        mutation_blockers=tuple(blockers),
        mutation_readiness_status="enabled" if mutation_enabled else "preview_only",
        mutation_readiness_message=(
            "GUI mutation is explicitly enabled for loopback-local reviewer-declared actions."
            if mutation_enabled
            else (
                "GUI mutation remains disabled; capability flag records preview intent only until session enablement, auth, authorization, reviewer identity, and session proof all align."
                if mutation_capability_flag
                else "GUI mutation remains disabled; explicit local write enablement still requires capability intent, session enablement, auth, authorization, reviewer identity, and session proof."
            )
        ),
    )
    return UIBoundaryMetadata(
        **{
            **asdict(metadata),
            "mutation_blocker_details": _serialize_mutation_blocker_details(list(metadata.mutation_blockers)),
            "reviewer_context_requirements": _reviewer_context_requirements(metadata),
            "reviewer_enforcement_summary": _reviewer_enforcement_summary(metadata),
            "reviewer_validation_gate_summary": _reviewer_validation_gate_summary(metadata),
            "auth_boundary_summary": _auth_boundary_summary(metadata),
            "write_route_contract": _ui_write_route_contract(metadata),
        }
    )


def _dump_model(model: object) -> dict[str, Any]:
    return model.model_dump(mode="json")  # type: ignore[attr-defined]


def _find_by_attr(items: list[object], attr: str, value: str) -> dict[str, Any] | None:
    for item in items:
        if getattr(item, attr, None) == value:
            return _dump_model(item)
    return None


def _unique_list(plan: RuntimeRetrievalPlan) -> list[str]:
    seen: set[str] = set()
    values: list[str] = []
    for hit in [*plan.vector_hits, *plan.graph_hits, *plan.chronicle_hits]:
        if hit.identifier and hit.identifier not in seen:
            values.append(hit.identifier)
            seen.add(hit.identifier)
    return values


def _related_link(
    path: str,
    label: str,
    *,
    label_key: str | None = None,
    label_params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"path": path, "label": label}
    if label_key:
        payload["label_key"] = label_key
    if label_params:
        payload["label_params"] = label_params
    return payload


def _open_detail_label(resource: str, record_id: str) -> str:
    labels = {
        "contexts": "Open context",
        "events": "Open event",
    }
    prefix = labels.get(resource, f"Open {resource.rstrip('s')}")
    return f"{prefix} {record_id}".strip()


def _open_detail_label_key(resource: str) -> str:
    labels = {
        "contexts": "ui.template.related_link.open_context",
        "events": "ui.template.related_link.open_event",
    }
    return labels.get(resource, "ui.template.related_link.open_detail")


def _open_matching_detail_label(resource: str) -> str:
    labels = {
        "review-queue": "Open matching review detail",
        "runtime-records": "Open matching runtime record",
    }
    return labels.get(resource, f"Open matching {resource.rstrip('s')} detail")


def _open_matching_detail_label_key(resource: str) -> str:
    labels = {
        "review-queue": "ui.related_link.open_matching_review_detail",
        "runtime-records": "ui.related_link.open_matching_runtime_record",
    }
    return labels.get(resource, "ui.template.related_link.open_matching_detail")


class ChronicleUIDataService:
    """Read-only data provider for the local UI."""

    def __init__(
        self,
        root: Path | None = None,
        *,
        host: str = DEFAULT_UI_HOST,
        mutation_capability_flag: bool = False,
        enable_ui_mutation: bool = False,
        auth_mode: str = UIAuthMode.NOT_ENABLED,
        authorization_mode: str = UIAuthorizationMode.NOT_ENABLED,
        mutation_session_token: str = "",
        mutation_session_id: str = "",
    ) -> None:
        self.root = root or Path.cwd()
        self.host = host
        self.mutation_capability_flag = mutation_capability_flag
        self.enable_ui_mutation = enable_ui_mutation
        self.auth_mode = auth_mode
        self.authorization_mode = authorization_mode
        self.mutation_session_token = mutation_session_token
        self.mutation_session_id = mutation_session_id
        self.chronicle = ChronicleService(self.root)
        self.audit = AuditService(self.root)
        self.lifecycle = LifecycleService(self.root)
        self.packages = IntegrationPackageService(self.root)
        self.package_review = PackageReviewService(self.root)
        self.review = ReviewService(self.root)
        self.proposals = ProposalService(self.root)
        self.runtime = RuntimeService(self.root)
        self.runtime_config = RuntimeConfigService(self.root)
        self.summary_jobs = SummaryJobService(self.root)
        self.vector_index = VectorIndexService(self.root)
        self.graph_index = GraphIndexService(self.root)

    def overview(self) -> dict[str, Any]:
        metadata = self.chronicle.require_initialized()
        events = self.chronicle.jsonl.read_all()
        artifacts, _ = self.chronicle.index.load_artifacts()
        contexts = self.chronicle.index.load_contexts()
        decisions = self.chronicle.index.load_decisions()
        rde_records = self.chronicle.index.load_rde_records()
        boundary_rules = self.chronicle.index.load_boundary_rules()
        audit_events = self.audit.list_events()
        lifecycle_events = self.lifecycle.list_events()
        runtime_records = self.runtime_records()["runtime_records"]
        review_queue = self.review_queue()["review_queue"]
        summary_jobs = self.summary_jobs_list()["summary_jobs"]
        ai_index_status = self.ai_index_status()["ai_index_status"]
        runtime_config = self.runtime_config_state()["runtime_config"]
        triage = self.overview_triage(runtime_records, review_queue)
        identity_boundary_summary = self.identity_boundary_summary(review_queue)
        summary_jobs_summary = self.summary_jobs_overview(summary_jobs)
        auth_boundary_overview = self.auth_boundary_overview(review_queue)
        runtime_records_summary = self.runtime_records_overview(runtime_records)
        reviewer_boundary_overview = self.reviewer_boundary_overview(
            runtime_records,
            review_queue,
            summary_jobs,
        )
        return {
            "chronicle": {
                "id": metadata.chronicle_id,
                "title": metadata.title,
                "schema_version": metadata.schema_version,
                "root": str(self.root.resolve()),
            },
            "counts": {
                "events": len(events),
                "contexts": len(contexts),
                "artifacts": len(artifacts),
                "decisions": len(decisions),
                "rde_records": len(rde_records),
                "boundary_rules": len(boundary_rules),
                "audit_events": len(audit_events),
                "lifecycle_markers": len(lifecycle_events),
                "runtime_records": len(runtime_records),
                "review_queue": len(review_queue),
                "summary_jobs": len(summary_jobs),
                "vector_index_entries": ai_index_status["vector"]["entry_count"],
                "graph_index_nodes": ai_index_status["graph"]["node_count"],
                "graph_index_edges": ai_index_status["graph"]["edge_count"],
            },
            "package_review": self.package_review_snapshot(),
            "graph_summary": self.graph_summary(),
            "ai_index": ai_index_status,
            "runtime_config": runtime_config,
            "triage": triage,
            "runtime_boundary": self.runtime_boundary(),
            "ui_boundary": self.ui_boundary()["ui_boundary"],
            "auth_boundary_summary": self.ui_boundary()["ui_boundary"]["auth_boundary_summary"],
            "auth_boundary_overview": auth_boundary_overview,
            "identity_boundary_summary": identity_boundary_summary,
            "reviewer_boundary_overview": reviewer_boundary_overview,
            "runtime_records_summary": runtime_records_summary,
            "summary_jobs_summary": summary_jobs_summary,
            "mutation_readiness": self.mutation_readiness_summary(review_queue),
        }

    def runtime_records_overview(self, runtime_records: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        rows = runtime_records if runtime_records is not None else self.runtime_records()["runtime_records"]
        kind_counts: dict[str, int] = {}
        auth_counts: dict[str, int] = {}
        mutation_counts: dict[str, int] = {}
        mutation_operational_counts: dict[str, int] = {}
        finish_reason_counts: dict[str, int] = {}
        provider_status_counts: dict[str, int] = {}
        response_present_count = 0
        latest_provider_response_detail_path: str | None = None
        for row in rows:
            kind = str(row.get("runtime_record_kind", "unknown"))
            auth_status = str(row.get("auth_readiness_status", "unknown"))
            mutation_summary = row.get("mutation_enablement_summary", {})
            mutation_status = str(mutation_summary.get("status", "unknown"))
            mutation_operational_status = str(
                mutation_summary.get("operational_status", "unknown")
            )
            response_summary = row.get("response_metadata_summary", {})
            kind_counts[kind] = kind_counts.get(kind, 0) + 1
            auth_counts[auth_status] = auth_counts.get(auth_status, 0) + 1
            mutation_counts[mutation_status] = mutation_counts.get(mutation_status, 0) + 1
            mutation_operational_counts[mutation_operational_status] = (
                mutation_operational_counts.get(mutation_operational_status, 0) + 1
            )
            if isinstance(response_summary, dict) and response_summary.get("present") is True:
                response_present_count += 1
                if latest_provider_response_detail_path is None:
                    event_id = str(row.get("event_id", ""))
                    if event_id.startswith("evt_"):
                        latest_provider_response_detail_path = f"/api/runtime-records/{event_id}"
                finish_reason = str(response_summary.get("finish_reason") or "unknown")
                provider_status = str(response_summary.get("provider_status") or "unknown")
                finish_reason_counts[finish_reason] = finish_reason_counts.get(finish_reason, 0) + 1
                provider_status_counts[provider_status] = provider_status_counts.get(provider_status, 0) + 1
        return {
            "kind_counts": kind_counts,
            "auth_readiness_counts": auth_counts,
            "mutation_readiness_counts": mutation_counts,
            "mutation_operational_counts": mutation_operational_counts,
            "provider_response_present_count": response_present_count,
            "provider_response_absent_count": len(rows) - response_present_count,
            "provider_response_finish_reason_counts": finish_reason_counts,
            "provider_response_status_counts": provider_status_counts,
            "latest_provider_response_detail_path": latest_provider_response_detail_path,
        }

    def auth_boundary_overview(self, review_queue: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        queue = review_queue if review_queue is not None else self.review_queue()["review_queue"]
        auth_warning_count = 0
        authorization_warning_count = 0
        missing_identity_count = 0
        declared_identity_count = 0
        session_label_missing_count = 0
        review_capability_counts: dict[str, int] = {}
        assurance_counts: dict[str, int] = {}
        provider_finish_reason_counts: dict[str, int] = {}
        provider_status_counts: dict[str, int] = {}
        provider_response_present_count = 0
        latest_provider_response_detail_path: str | None = None

        for row in queue:
            capability = row.get("review_capability", {})
            capability_status = str(capability.get("status", "unknown"))
            review_capability_counts[capability_status] = review_capability_counts.get(capability_status, 0) + 1
            warnings = capability.get("warnings", [])
            if "ui_auth_not_enabled" in warnings:
                auth_warning_count += 1
            if "ui_authorization_not_enabled" in warnings:
                authorization_warning_count += 1
            if "no_reviewer_identity_recorded" in warnings:
                missing_identity_count += 1
            if "reviewer_identity_declared_only" in warnings:
                declared_identity_count += 1
            if "reviewer_session_label_missing" in warnings:
                session_label_missing_count += 1
            assurance = row.get("latest_identity_assurance")
            if isinstance(assurance, dict) and assurance.get("status"):
                assurance_status = str(assurance.get("status", "unknown"))
                assurance_counts[assurance_status] = assurance_counts.get(assurance_status, 0) + 1
            response_summary = row.get("response_metadata_summary", {})
            if isinstance(response_summary, dict) and response_summary.get("present") is True:
                provider_response_present_count += 1
                if latest_provider_response_detail_path is None:
                    target_event_id = str(row.get("target_event_id", ""))
                    if target_event_id.startswith("evt_"):
                        latest_provider_response_detail_path = f"/api/review-queue/{target_event_id}"
                finish_reason = str(response_summary.get("finish_reason") or "unknown")
                provider_status = str(response_summary.get("provider_status") or "unknown")
                provider_finish_reason_counts[finish_reason] = (
                    provider_finish_reason_counts.get(finish_reason, 0) + 1
                )
                provider_status_counts[provider_status] = (
                    provider_status_counts.get(provider_status, 0) + 1
                )

        return {
            "auth_warning_count": auth_warning_count,
            "authorization_warning_count": authorization_warning_count,
            "missing_identity_count": missing_identity_count,
            "declared_identity_count": declared_identity_count,
            "session_label_missing_count": session_label_missing_count,
            "review_capability_counts": review_capability_counts,
            "identity_assurance_counts": assurance_counts,
            "provider_response_present_count": provider_response_present_count,
            "provider_response_absent_count": len(queue) - provider_response_present_count,
            "provider_response_finish_reason_counts": provider_finish_reason_counts,
            "provider_response_status_counts": provider_status_counts,
            "latest_provider_response_detail_path": latest_provider_response_detail_path,
        }

    def summary_jobs_overview(self, summary_jobs: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        rows = summary_jobs if summary_jobs is not None else self.summary_jobs_list()["summary_jobs"]
        status_counts: dict[str, int] = {}
        review_counts: dict[str, int] = {}
        auth_counts: dict[str, int] = {}
        package_counts: dict[str, int] = {}
        mutation_counts: dict[str, int] = {}
        mutation_operational_counts: dict[str, int] = {}
        provider_counts: dict[str, int] = {}
        assurance_counts: dict[str, int] = {}
        reviewer_kind_counts: dict[str, int] = {}
        finish_reason_counts: dict[str, int] = {}
        provider_status_counts: dict[str, int] = {}
        response_present_count = 0
        source_count_total = 0
        latest_provider_response_detail_path: str | None = None
        for row in rows:
            status = str(row.get("status", "unknown"))
            review_status = str(row.get("review_capability_status", "unknown"))
            auth_status = str(row.get("auth_readiness_status", "unknown"))
            package_status = str(row.get("package_readiness_status", "unknown"))
            mutation_summary = row.get("mutation_enablement_summary", {})
            mutation_status = str(mutation_summary.get("status", "unknown"))
            mutation_operational_status = str(
                mutation_summary.get("operational_status", "unknown")
            )
            provider_kind = str(row.get("runtime_provider_kind", "unknown"))
            assurance_status = str(row.get("identity_assurance_status", "unknown"))
            reviewer_kind = str((row.get("latest_reviewer_identity") or {}).get("kind", "unknown"))
            status_counts[status] = status_counts.get(status, 0) + 1
            review_counts[review_status] = review_counts.get(review_status, 0) + 1
            auth_counts[auth_status] = auth_counts.get(auth_status, 0) + 1
            package_counts[package_status] = package_counts.get(package_status, 0) + 1
            mutation_counts[mutation_status] = mutation_counts.get(mutation_status, 0) + 1
            mutation_operational_counts[mutation_operational_status] = (
                mutation_operational_counts.get(mutation_operational_status, 0) + 1
            )
            provider_counts[provider_kind] = provider_counts.get(provider_kind, 0) + 1
            assurance_counts[assurance_status] = assurance_counts.get(assurance_status, 0) + 1
            reviewer_kind_counts[reviewer_kind] = reviewer_kind_counts.get(reviewer_kind, 0) + 1
            response_summary = row.get("response_metadata_summary", {})
            if isinstance(response_summary, dict) and response_summary.get("present") is True:
                response_present_count += 1
                if latest_provider_response_detail_path is None:
                    summary_job_id = str(row.get("summary_job_id", ""))
                    if summary_job_id.startswith("sum_"):
                        latest_provider_response_detail_path = f"/api/summary-jobs/{summary_job_id}"
                finish_reason = str(response_summary.get("finish_reason") or "unknown")
                provider_status = str(response_summary.get("provider_status") or "unknown")
                finish_reason_counts[finish_reason] = finish_reason_counts.get(finish_reason, 0) + 1
                provider_status_counts[provider_status] = provider_status_counts.get(provider_status, 0) + 1
            source_count_total += int(row.get("summary_source_count", 0) or 0)
        return {
            "status_counts": status_counts,
            "review_capability_counts": review_counts,
            "auth_readiness_counts": auth_counts,
            "package_readiness_counts": package_counts,
            "mutation_readiness_counts": mutation_counts,
            "mutation_operational_counts": mutation_operational_counts,
            "runtime_provider_counts": provider_counts,
            "provider_response_present_count": response_present_count,
            "provider_response_absent_count": len(rows) - response_present_count,
            "provider_response_finish_reason_counts": finish_reason_counts,
            "provider_response_status_counts": provider_status_counts,
            "latest_provider_response_detail_path": latest_provider_response_detail_path,
            "identity_assurance_counts": assurance_counts,
            "reviewer_kind_counts": reviewer_kind_counts,
            "summary_source_total": source_count_total,
        }

    def identity_boundary_summary(self, review_queue: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        queue = review_queue if review_queue is not None else self.review_queue()["review_queue"]
        assurance_counts: dict[str, int] = {}
        missing_identity_count = 0
        declared_identity_count = 0
        session_label_missing_count = 0

        for row in queue:
            assurance = row.get("latest_identity_assurance")
            if isinstance(assurance, dict) and assurance.get("status"):
                status = str(assurance["status"])
                assurance_counts[status] = assurance_counts.get(status, 0) + 1
            else:
                missing_identity_count += 1

            warnings = row.get("review_capability", {}).get("warnings", [])
            if "reviewer_identity_declared_only" in warnings:
                declared_identity_count += 1
            if "reviewer_session_label_missing" in warnings:
                session_label_missing_count += 1

        blockers: list[str] = []
        next_steps: list[str] = []
        if missing_identity_count > 0:
            blockers.append("reviewer_identity_missing")
            next_steps.append("Record reviewer identity metadata before relying on GUI review signals.")
        if declared_identity_count > 0:
            blockers.append("reviewer_identity_declared_only")
            next_steps.append("Strengthen reviewer identity beyond self-declared metadata.")
        if session_label_missing_count > 0:
            blockers.append("reviewer_session_label_missing")
            next_steps.append("Require session labels when session-gated review is expected.")

        if assurance_counts.get("boundary_aligned", 0) > 0 and not blockers:
            status = "boundary_aligned"
        elif assurance_counts:
            status = "partially_aligned"
        else:
            status = "identity_unavailable"
        message = _identity_boundary_summary_message(status)

        return {
            "status": status,
            "message": message,
            "message_key": _identity_boundary_summary_message_key(status),
            "assurance_counts": assurance_counts,
            "missing_identity_count": missing_identity_count,
            "declared_identity_count": declared_identity_count,
            "session_label_missing_count": session_label_missing_count,
            "blockers": blockers,
            "next_steps": next_steps,
        }

    def reviewer_boundary_overview(
        self,
        runtime_records: list[dict[str, Any]] | None = None,
        review_queue: list[dict[str, Any]] | None = None,
        summary_jobs: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        runtime_rows = runtime_records if runtime_records is not None else self.runtime_records()["runtime_records"]
        review_rows = review_queue if review_queue is not None else self.review_queue()["review_queue"]
        summary_rows = summary_jobs if summary_jobs is not None else self.summary_jobs_list()["summary_jobs"]

        runtime_enforcement_counts: dict[str, int] = {}
        runtime_gate_counts: dict[str, int] = {}
        review_enforcement_counts: dict[str, int] = {}
        review_gate_counts: dict[str, int] = {}
        summary_enforcement_counts: dict[str, int] = {}
        summary_gate_counts: dict[str, int] = {}

        for row in runtime_rows:
            enforcement_status = str(row.get("reviewer_enforcement_status", "unknown"))
            gate_status = str(row.get("reviewer_validation_gate_status", "unknown"))
            runtime_enforcement_counts[enforcement_status] = (
                runtime_enforcement_counts.get(enforcement_status, 0) + 1
            )
            runtime_gate_counts[gate_status] = runtime_gate_counts.get(gate_status, 0) + 1

        for row in review_rows:
            enforcement_status = str(row.get("reviewer_enforcement_status", "unknown"))
            gate_status = str(row.get("reviewer_validation_gate_status", "unknown"))
            review_enforcement_counts[enforcement_status] = (
                review_enforcement_counts.get(enforcement_status, 0) + 1
            )
            review_gate_counts[gate_status] = review_gate_counts.get(gate_status, 0) + 1

        for row in summary_rows:
            enforcement_status = str(row.get("reviewer_enforcement_status", "unknown"))
            gate_status = str(row.get("reviewer_validation_gate_status", "unknown"))
            summary_enforcement_counts[enforcement_status] = (
                summary_enforcement_counts.get(enforcement_status, 0) + 1
            )
            summary_gate_counts[gate_status] = summary_gate_counts.get(gate_status, 0) + 1

        boundary = self.ui_boundary()["ui_boundary"]
        enforcement_summary = boundary.get("reviewer_enforcement_summary", {})
        gate_summary = boundary.get("reviewer_validation_gate_summary", {})

        return {
            "enforcement_status": str(enforcement_summary.get("status", "")),
            "validation_gate_status": str(gate_summary.get("status", "")),
            "session_gated": bool(
                enforcement_summary.get("session_gated") or gate_summary.get("session_gated")
            ),
            "route_enforced": bool(gate_summary.get("fail_closed", False)),
            "runtime_record_enforcement_counts": runtime_enforcement_counts,
            "runtime_record_validation_gate_counts": runtime_gate_counts,
            "review_queue_enforcement_counts": review_enforcement_counts,
            "review_queue_validation_gate_counts": review_gate_counts,
            "summary_job_enforcement_counts": summary_enforcement_counts,
            "summary_job_validation_gate_counts": summary_gate_counts,
            "drilldown_summaries": [
                {
                    "summary_variant": "overview_dominant",
                    "dataset_key": "runtime_records",
                    "list_path": "/api/runtime-records",
                    "detail_path_template": "/api/runtime-records/<event_id>",
                    "dominant_enforcement_status": _dominant_status(runtime_enforcement_counts),
                    "dominant_validation_gate_status": _dominant_status(runtime_gate_counts),
                    "message_template_key": "ui.template.reviewer_boundary_overview_message",
                    "message_params": {
                        "dataset_key": "runtime_records",
                    },
                    "message_key": "ui.message.reviewer_boundary_drilldown",
                    "message": _reviewer_boundary_fallback_message(
                        dataset_key="runtime_records",
                        overview=True,
                    ),
                    "fact_line_template_key": "ui.template.reviewer_boundary_dominant_fact_line",
                    "fact_line_params": {
                        "dataset_key": "runtime_records",
                        "enforcement_status": _dominant_status(runtime_enforcement_counts),
                        "validation_gate_status": _dominant_status(runtime_gate_counts),
                    },
                    "fact_line": _reviewer_boundary_fallback_fact_line(
                        dataset_key="runtime_records",
                        enforcement_status=_dominant_status(runtime_enforcement_counts),
                        gate_status=_dominant_status(runtime_gate_counts),
                        dominant=True,
                    ),
                },
                {
                    "summary_variant": "overview_dominant",
                    "dataset_key": "review_queue",
                    "list_path": "/api/review-queue",
                    "detail_path_template": "/api/review-queue/<target_event_id>",
                    "dominant_enforcement_status": _dominant_status(review_enforcement_counts),
                    "dominant_validation_gate_status": _dominant_status(review_gate_counts),
                    "message_template_key": "ui.template.reviewer_boundary_overview_message",
                    "message_params": {
                        "dataset_key": "review_queue",
                    },
                    "message_key": "ui.message.reviewer_boundary_drilldown",
                    "message": _reviewer_boundary_fallback_message(
                        dataset_key="review_queue",
                        overview=True,
                    ),
                    "fact_line_template_key": "ui.template.reviewer_boundary_dominant_fact_line",
                    "fact_line_params": {
                        "dataset_key": "review_queue",
                        "enforcement_status": _dominant_status(review_enforcement_counts),
                        "validation_gate_status": _dominant_status(review_gate_counts),
                    },
                    "fact_line": _reviewer_boundary_fallback_fact_line(
                        dataset_key="review_queue",
                        enforcement_status=_dominant_status(review_enforcement_counts),
                        gate_status=_dominant_status(review_gate_counts),
                        dominant=True,
                    ),
                },
                {
                    "summary_variant": "overview_dominant",
                    "dataset_key": "summary_jobs",
                    "list_path": "/api/summary-jobs",
                    "detail_path_template": "/api/summary-jobs/<summary_job_id>",
                    "dominant_enforcement_status": _dominant_status(summary_enforcement_counts),
                    "dominant_validation_gate_status": _dominant_status(summary_gate_counts),
                    "message_template_key": "ui.template.reviewer_boundary_overview_message",
                    "message_params": {
                        "dataset_key": "summary_jobs",
                    },
                    "message_key": "ui.message.reviewer_boundary_drilldown",
                    "message": _reviewer_boundary_fallback_message(
                        dataset_key="summary_jobs",
                        overview=True,
                    ),
                    "fact_line_template_key": "ui.template.reviewer_boundary_dominant_fact_line",
                    "fact_line_params": {
                        "dataset_key": "summary_jobs",
                        "enforcement_status": _dominant_status(summary_enforcement_counts),
                        "validation_gate_status": _dominant_status(summary_gate_counts),
                    },
                    "fact_line": _reviewer_boundary_fallback_fact_line(
                        dataset_key="summary_jobs",
                        enforcement_status=_dominant_status(summary_enforcement_counts),
                        gate_status=_dominant_status(summary_gate_counts),
                        dominant=True,
                    ),
                },
            ],
        }

    def overview_triage(
        self,
        runtime_records: list[dict[str, Any]],
        review_queue: list[dict[str, Any]],
    ) -> dict[str, Any]:
        runtime_by_kind: dict[str, int] = {}
        for row in runtime_records:
            kind = str(row.get("runtime_record_kind", "unknown"))
            runtime_by_kind[kind] = runtime_by_kind.get(kind, 0) + 1

        review_capability_counts: dict[str, int] = {}
        readiness_counts: dict[str, int] = {}
        cli_parity_counts: dict[str, int] = {}
        warning_counts: dict[str, int] = {}
        identity_assurance_counts: dict[str, int] = {}
        reviewer_kind_counts: dict[str, int] = {}
        provider_response_present_reviews = 0
        latest_provider_response_detail_path: str | None = None
        ready_now = 0
        advisory_only = 0
        package_ready = 0
        parity_aligned = 0
        parity_drift = 0
        identity_boundary_aligned = 0
        identity_declared_only = 0

        for row in review_queue:
            capability_status = str(row.get("review_capability", {}).get("status", "unknown"))
            review_capability_counts[capability_status] = review_capability_counts.get(capability_status, 0) + 1
            if capability_status == "ready":
                ready_now += 1
            elif capability_status == "advisory_only":
                advisory_only += 1

            readiness_status = str(row.get("package_readiness_summary", {}).get("status", "unknown"))
            readiness_counts[readiness_status] = readiness_counts.get(readiness_status, 0) + 1
            if readiness_status == "package_context_available":
                package_ready += 1

            parity_status = str(row.get("cli_parity_summary", {}).get("status", "unknown"))
            cli_parity_counts[parity_status] = cli_parity_counts.get(parity_status, 0) + 1
            if parity_status == "aligned":
                parity_aligned += 1
            elif parity_status == "drift_detected":
                parity_drift += 1

            for warning_code in row.get("review_capability", {}).get("warnings", []):
                code = str(warning_code)
                warning_counts[code] = warning_counts.get(code, 0) + 1
                if code == "reviewer_identity_declared_only":
                    identity_declared_only += 1

            assurance = row.get("latest_identity_assurance") or {}
            assurance_status = str(assurance.get("status", "unknown"))
            identity_assurance_counts[assurance_status] = identity_assurance_counts.get(assurance_status, 0) + 1
            if assurance_status == "boundary_aligned":
                identity_boundary_aligned += 1

            latest_identity = row.get("latest_reviewer_identity") or {}
            reviewer_kind = str(latest_identity.get("kind", "unknown"))
            reviewer_kind_counts[reviewer_kind] = reviewer_kind_counts.get(reviewer_kind, 0) + 1
            response_summary = row.get("response_metadata_summary", {})
            if isinstance(response_summary, dict) and response_summary.get("present") is True:
                provider_response_present_reviews += 1
                if latest_provider_response_detail_path is None:
                    target_event_id = str(row.get("target_event_id", ""))
                    if target_event_id.startswith("evt_"):
                        latest_provider_response_detail_path = f"/api/review-queue/{target_event_id}"

        return {
            "runtime_record_kinds": runtime_by_kind,
            "review_capability_counts": review_capability_counts,
            "package_readiness_counts": readiness_counts,
            "cli_parity_counts": cli_parity_counts,
            "warning_counts": warning_counts,
            "identity_assurance_counts": identity_assurance_counts,
            "reviewer_kind_counts": reviewer_kind_counts,
            "warning_summaries": self._warning_summaries(warning_counts),
            "ready_now_reviews": ready_now,
            "advisory_only_reviews": advisory_only,
            "package_ready_reviews": package_ready,
            "cli_parity_aligned_reviews": parity_aligned,
            "cli_parity_drift_reviews": parity_drift,
            "identity_boundary_aligned_reviews": identity_boundary_aligned,
            "identity_declared_only_reviews": identity_declared_only,
            "provider_response_present_reviews": provider_response_present_reviews,
            "latest_provider_response_detail_path": latest_provider_response_detail_path,
            "needs_attention_reviews": len(review_queue),
        }

    def _warning_summaries(self, warning_counts: dict[str, int]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for code, count in warning_counts.items():
            rows.append(
                {
                    "code": code,
                    "count": count,
                    "priority": REVIEW_WARNING_PRIORITY.get(code, 99),
                    "label_key": f"filter.review.{code}",
                    "label": REVIEW_WARNING_LABELS.get(code, code.replace("_", " ")),
                    "message_key": f"ui.review_warning.{code}",
                    "message": self._warning_message(code),
                    "summary_key": "ui.template.review_warning.summary",
                    "summary_params": {
                        "label": REVIEW_WARNING_LABELS.get(code, code.replace("_", " ")),
                        "count": count,
                    },
                }
            )
        return sorted(rows, key=lambda item: (item["priority"], -item["count"], item["code"]))

    def events(self, *, limit: int = 100) -> dict[str, Any]:
        self.chronicle.require_initialized()
        events = self.chronicle.jsonl.read_all()
        return {"events": [_dump_model(event) for event in reversed(events[-limit:])]}

    def contexts(self) -> dict[str, Any]:
        self.chronicle.require_initialized()
        contexts = sorted(self.chronicle.index.load_contexts().values(), key=lambda ctx: ctx.created_at)
        rows = []
        for context in contexts:
            data = _dump_model(context)
            proposals = self.proposals.proposals_for_target(target_kind="context", target_id=context.context_id)
            data["proposal_count"] = len(proposals)
            data["pending_proposal_count"] = sum(
                1 for proposal in proposals if proposal.get("review_status") == "needs_review"
            )
            data["latest_proposal_event_id"] = proposals[-1]["event_id"] if proposals else None
            rows.append(data)
        return {"contexts": rows}

    def artifacts(self) -> dict[str, Any]:
        self.chronicle.require_initialized()
        artifacts, versions = self.chronicle.index.load_artifacts()
        rows = []
        for artifact in sorted(artifacts.values(), key=lambda item: item.created_at):
            data = _dump_model(artifact)
            data["version_count"] = len(versions.get(artifact.artifact_id, []))
            proposals = self.proposals.proposals_for_target(
                target_kind="artifact", target_id=artifact.artifact_id
            )
            data["proposal_count"] = len(proposals)
            data["pending_proposal_count"] = sum(
                1 for proposal in proposals if proposal.get("review_status") == "needs_review"
            )
            data["latest_proposal_event_id"] = proposals[-1]["event_id"] if proposals else None
            rows.append(data)
        return {"artifacts": rows}

    def proposal_records(self) -> dict[str, Any]:
        self.chronicle.require_initialized()
        rows = self.proposals.list_proposals()
        for row in rows:
            proposal = row.get("proposal", {})
            target_kind = str(proposal.get("target_kind", ""))
            event_id = str(row.get("event_id", ""))
            if row.get("apply_ready") is True:
                if target_kind == "artifact":
                    row["cli_apply_hint"] = f"chronicle artifact apply-proposal --event {event_id}"
                elif target_kind == "context":
                    row["cli_apply_hint"] = f"chronicle context apply-proposal --event {event_id}"
        return {"proposals": rows}

    def decisions(self) -> dict[str, Any]:
        self.chronicle.require_initialized()
        decisions = sorted(self.chronicle.index.load_decisions().values(), key=lambda item: item.decided_at)
        return {"decisions": [_dump_model(decision) for decision in decisions]}

    def rde_records(self) -> dict[str, Any]:
        self.chronicle.require_initialized()
        records = sorted(self.chronicle.index.load_rde_records().values(), key=lambda item: item.created_at)
        return {"rde_records": [_dump_model(record) for record in records]}

    def boundary_rules(self) -> dict[str, Any]:
        self.chronicle.require_initialized()
        rules = sorted(self.chronicle.index.load_boundary_rules().values(), key=lambda item: item.created_at)
        return {"boundary_rules": [_dump_model(rule) for rule in rules]}

    def audit_events(self, *, limit: int = 100) -> dict[str, Any]:
        events = self.audit.list_events()
        return {"audit_events": [_dump_model(event) for event in reversed(events[-limit:])]}

    def lifecycle_markers(self, *, limit: int = 100) -> dict[str, Any]:
        events = self.lifecycle.list_events()
        return {"lifecycle_markers": [_dump_model(event) for event in reversed(events[-limit:])]}

    def runtime_records(self, *, limit: int = 100) -> dict[str, Any]:
        self.chronicle.require_initialized()
        events = [
            event
            for event in self.chronicle.jsonl.read_all()
            if event.event_type.value == "assistant_output"
            and (
                "runtime_summary" in event.payload
                or "runtime_execution" in event.payload
                or "runtime_retrieval_plan" in event.payload
                or "runtime_invocation_plan" in event.payload
            )
        ]
        rows: list[dict[str, Any]] = []
        for event in reversed(events[-limit:]):
            data = _dump_model(event)
            preview = self.runtime.record_preview(event)
            preview_payload = preview.model_dump(mode="json")
            title_key, title_params = _runtime_preview_title_contract(preview_payload)
            if title_key:
                preview_payload["title_key"] = title_key
            if title_params:
                preview_payload["title_params"] = title_params
            data["runtime_record_kind"] = preview.record_kind
            data["runtime_record_preview"] = preview_payload
            review_row = self._review_queue_row(event.event_id)
            if review_row is not None:
                mutation_enablement = self.mutation_readiness_summary()
                boundary = self.ui_boundary()["ui_boundary"]
                data["review_target_event_id"] = event.event_id
                data["review_capability_status"] = str(
                    review_row.get("review_capability", {}).get("status", "")
                )
                data["auth_readiness_status"] = str(
                    review_row.get("auth_boundary_notice", {}).get("status", "")
                )
                data["action_preview_summary"] = review_row.get("action_preview_summary", {})
                data["identity_assurance_status"] = str(
                    review_row.get("latest_identity_assurance", {}).get("status", "unknown")
                )
                data["mutation_enablement_summary"] = self._mutation_enablement_list_summary(
                    mutation_enablement
                )
                data["reviewer_enforcement_status"] = str(
                    boundary.get("reviewer_enforcement_summary", {}).get("status", "")
                )
                data["reviewer_validation_gate_status"] = str(
                    boundary.get("reviewer_validation_gate_summary", {}).get("status", "")
                )
                data["reviewer_boundary_drilldown_summary"] = _reviewer_boundary_drilldown_summary(
                    dataset_key="runtime_records",
                    list_path="/api/runtime-records",
                    detail_path=f"/api/runtime-records/{event.event_id}",
                    enforcement_status=data["reviewer_enforcement_status"],
                    gate_status=data["reviewer_validation_gate_status"],
                )
                data["ui_mutation_enabled"] = bool(mutation_enablement.get("enablement_ready")) and bool(
                    review_row.get("ui_mutation_enabled", False)
                )
                data["review_preview_only"] = not bool(data["ui_mutation_enabled"])
            data["response_metadata_summary"] = self._runtime_response_metadata_summary(payload=data["payload"])
            rows.append(data)
        return {"runtime_records": rows}

    def review_queue(self, *, limit: int = 100) -> dict[str, Any]:
        self.chronicle.require_initialized()
        boundary = self.ui_boundary()["ui_boundary"]
        rows: list[dict[str, Any]] = []
        for entry in self.review.queue()[:limit]:
            data = entry.model_dump(mode="json")
            data["suggested_cli_family"] = self._suggested_cli_family_from_kind(entry.review_kind)
            data["response_metadata_summary"] = self._review_target_response_metadata_summary(
                entry.target_event_id
            )
            data["review_capability"] = self._review_capability(
                pending=bool(data.get("pending")),
                boundary=boundary,
                identity=(
                    ReviewerIdentity.model_validate(data["latest_reviewer_identity"])
                    if data.get("latest_reviewer_identity") is not None
                    else None
                ),
            )
            if data.get("latest_reviewer_identity") is not None:
                data["latest_identity_assurance"] = self._identity_assurance(
                    ReviewerIdentity.model_validate(data["latest_reviewer_identity"]),
                    boundary,
                )
            data["auth_boundary_notice"] = self._auth_boundary_notice(
                boundary,
                data.get("review_capability"),
                data.get("latest_identity_assurance"),
            )
            readiness = self.review_package_readiness(entry.target_event_id)
            data["package_readiness_summary"] = self._package_readiness_summary(readiness)
            data["action_preview_summary"] = self._review_action_preview(
                entry.target_event_id,
                data.get("review_capability", {}),
                mutation_enabled=bool(boundary.get("mutation_enabled", False)),
                write_route_contract=boundary.get("write_route_contract", {}),
            )
            data["cli_parity_summary"] = self._review_cli_parity_summary(
                entry.target_event_id,
                data.get("available_actions", []),
                data["action_preview_summary"],
            )
            data["reviewer_enforcement_status"] = str(
                boundary.get("reviewer_enforcement_summary", {}).get("status", "")
            )
            data["reviewer_validation_gate_status"] = str(
                boundary.get("reviewer_validation_gate_summary", {}).get("status", "")
            )
            data["reviewer_boundary_drilldown_summary"] = _reviewer_boundary_drilldown_summary(
                dataset_key="review_queue",
                list_path="/api/review-queue",
                detail_path=f"/api/review-queue/{entry.target_event_id}",
                enforcement_status=data["reviewer_enforcement_status"],
                gate_status=data["reviewer_validation_gate_status"],
            )
            data["ui_mutation_enabled"] = bool(boundary.get("mutation_enabled", False))
            data["review_preview_only"] = not bool(boundary.get("mutation_enabled", False))
            rows.append(data)
        mutation_enablement = self._mutation_enablement_list_summary(
            self.mutation_readiness_summary(rows)
        )
        for row in rows:
            row["mutation_enablement_summary"] = mutation_enablement
        return {"review_queue": rows}

    def summary_jobs_list(self, *, limit: int = 100) -> dict[str, Any]:
        rows: list[dict[str, Any]] = []
        for job in reversed(self.summary_jobs.list_jobs()[:limit]):
            data = job.model_dump(mode="json")
            data["summary_source_count"] = len(job.source_refs)
            data["runtime_provider_kind"] = job.provenance.runtime.provider_kind.value
            data["response_metadata_summary"] = self._response_metadata_summary(
                response_metadata=job.provenance.response_metadata,
                response_keys=job.provenance.response_keys,
            )
            data["suggested_cli_family"] = "chronicle summary show --id"
            data["identity_assurance_status"] = "unknown"
            review_target_event_id = str(data.get("event_id", ""))
            if review_target_event_id.startswith("evt_"):
                review_row = self._review_queue_row(review_target_event_id)
                if review_row is not None:
                    boundary = self.ui_boundary()["ui_boundary"]
                    data["review_target_event_id"] = review_target_event_id
                    data["review_capability_status"] = str(
                        review_row.get("review_capability", {}).get("status", "")
                    )
                    data["auth_readiness_status"] = str(
                        review_row.get("auth_boundary_notice", {}).get("status", "")
                    )
                    data["package_readiness_status"] = str(
                        review_row.get("package_readiness_summary", {}).get("status", "")
                    )
                    data["cli_parity_status"] = str(
                        review_row.get("cli_parity_summary", {}).get("status", "")
                    )
                    data["action_preview_summary"] = review_row.get("action_preview_summary", {})
                    data["mutation_enablement_summary"] = self._mutation_enablement_list_summary(
                        self.mutation_readiness_summary()
                    )
                    data["reviewer_enforcement_status"] = str(
                        boundary.get("reviewer_enforcement_summary", {}).get("status", "")
                    )
                    data["reviewer_validation_gate_status"] = str(
                        boundary.get("reviewer_validation_gate_summary", {}).get("status", "")
                    )
                    data["reviewer_boundary_drilldown_summary"] = _reviewer_boundary_drilldown_summary(
                        dataset_key="summary_jobs",
                        list_path="/api/summary-jobs",
                        detail_path=f"/api/summary-jobs/{job.summary_job_id}",
                        enforcement_status=data["reviewer_enforcement_status"],
                        gate_status=data["reviewer_validation_gate_status"],
                    )
                    data["ui_mutation_enabled"] = bool(boundary.get("mutation_enabled", False))
                    data["review_preview_only"] = not bool(boundary.get("mutation_enabled", False))
                    if review_row.get("latest_reviewer_identity") is not None:
                        data["latest_reviewer_identity"] = review_row.get("latest_reviewer_identity")
                    if review_row.get("latest_identity_assurance") is not None:
                        data["latest_identity_assurance"] = review_row.get("latest_identity_assurance")
                        data["identity_assurance_status"] = str(
                            review_row.get("latest_identity_assurance", {}).get("status", "")
                        )
            rows.append(data)
        return {"summary_jobs": rows}

    def mutation_readiness_summary(self, review_queue: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        boundary = self.ui_boundary()["ui_boundary"]
        queue = review_queue if review_queue is not None else self.review_queue()["review_queue"]
        ready_rows = sum(1 for row in queue if row.get("review_capability", {}).get("can_review_now") is True)
        advisory_rows = sum(1 for row in queue if row.get("review_capability", {}).get("can_review_now") is not True)
        blockers: list[str] = []
        next_steps: list[str] = []
        boundary_blockers = [str(blocker) for blocker in boundary.get("mutation_blockers", [])]
        for blocker in boundary_blockers:
            _append_mutation_blocker(blockers, next_steps, str(blocker))
        pending_boundary_warning_counts: dict[str, int] = {}
        for row in queue:
            for warning in row.get("review_capability", {}).get("warnings", []):
                blocker_code = AUTH_BOUNDARY_WARNING_TO_BLOCKER.get(str(warning))
                if blocker_code is None:
                    continue
                pending_boundary_warning_counts[blocker_code] = (
                    pending_boundary_warning_counts.get(blocker_code, 0) + 1
                )
        for blocker_code in pending_boundary_warning_counts:
            _append_mutation_blocker(blockers, next_steps, blocker_code)
        enablement_checks = _mutation_enablement_checks(
            boundary=boundary,
            pending_boundary_warning_counts=pending_boundary_warning_counts,
        )
        blocker_summaries = _mutation_blocker_summaries(
            boundary_blockers=boundary_blockers,
            pending_boundary_warning_counts=pending_boundary_warning_counts,
        )
        operational_readiness = _mutation_operational_readiness(
            enablement_checks=enablement_checks,
        )
        satisfied_checks = sum(1 for check in enablement_checks if check.get("satisfied") is True)
        if ready_rows > 0:
            next_steps.append(
                "Preserve review-ready signals as preview-only until browser-triggered write ADR and audit semantics are explicit."
            )
        return {
            "status": boundary.get("mutation_readiness_status", "preview_only"),
            "message": boundary.get("mutation_readiness_message", "GUI mutation remains disabled."),
            "message_key": _mutation_readiness_message_key(boundary),
            "scope_note": _mutation_scope_note(boundary),
            "scope_note_key": _mutation_scope_note_key(boundary),
            "ready_row_count": ready_rows,
            "advisory_row_count": advisory_rows,
            "blockers": blockers,
            "blocker_details": _serialize_mutation_blocker_details(blockers),
            "blocker_summaries": blocker_summaries,
            "pending_boundary_warning_counts": pending_boundary_warning_counts,
            "enablement_checks": enablement_checks,
            "enablement_ready": satisfied_checks == len(enablement_checks),
            "enablement_ready_summary_key": _boolean_summary_payload(
                satisfied_checks == len(enablement_checks)
            )[0],
            "enablement_ready_summary": _boolean_summary_payload(
                satisfied_checks == len(enablement_checks)
            )[1],
            "enablement_satisfied_count": satisfied_checks,
            "enablement_required_count": len(enablement_checks),
            "operational_readiness": operational_readiness,
            "reviewer_context_requirements": boundary.get("reviewer_context_requirements", {}),
            "reviewer_enforcement_summary": boundary.get("reviewer_enforcement_summary", {}),
            "reviewer_validation_gate_summary": boundary.get("reviewer_validation_gate_summary", {}),
            "write_route_contract": boundary.get("write_route_contract", {}),
            "identity_proof_contract": boundary.get("write_route_contract", {}).get(
                "identity_proof_contract", {}
            ),
            "next_steps": next_steps,
        }

    @staticmethod
    def _mutation_enablement_list_summary(mutation_readiness: dict[str, Any]) -> dict[str, Any]:
        operational_readiness = mutation_readiness.get("operational_readiness", {})
        write_route_contract = mutation_readiness.get("write_route_contract", {})
        identity_proof_contract = write_route_contract.get("identity_proof_contract", {})
        unsatisfied_checks = [
            item
            for item in operational_readiness.get("unsatisfied_checks", [])
            if isinstance(item, dict)
        ]
        blocking_summaries = [
            str(item)
            for item in operational_readiness.get("blocking_summaries", [])
            if str(item)
        ]
        first_unsatisfied = unsatisfied_checks[0] if unsatisfied_checks else {}
        return {
            "status": str(mutation_readiness.get("status", "")),
            "message": str(mutation_readiness.get("message", "")),
            "message_key": str(mutation_readiness.get("message_key", "")),
            "scope_note": str(mutation_readiness.get("scope_note", "")),
            "scope_note_key": str(mutation_readiness.get("scope_note_key", "")),
            "enablement_ready": bool(mutation_readiness.get("enablement_ready", False)),
            "operational_status": str(operational_readiness.get("status", "")),
            "operational_message": str(operational_readiness.get("message", "")),
            "operational_message_key": str(operational_readiness.get("message_key", "")),
            "remaining_count": int(operational_readiness.get("remaining_count", 0) or 0),
            "remaining_summary": blocking_summaries[0] if blocking_summaries else "",
            "remaining_summary_key": str(first_unsatisfied.get("summary_key", "")),
            "remaining_summary_params": dict(first_unsatisfied.get("summary_params", {}))
            if isinstance(first_unsatisfied.get("summary_params", {}), dict)
            else {},
            "blocked_status_code": write_route_contract.get("blocked_status_code"),
            "blocked_status_summary": str(write_route_contract.get("blocked_status_summary", "")),
            "blocked_status_summary_key": str(
                write_route_contract.get("blocked_status_summary_key", "")
            ),
            "blocked_status_summary_params": dict(
                write_route_contract.get("blocked_status_summary_params", {})
            )
            if isinstance(write_route_contract.get("blocked_status_summary_params", {}), dict)
            else {},
            "success_status_code": write_route_contract.get("success_status_code"),
            "identity_proof_status": str(identity_proof_contract.get("proof_status", "")),
            "identity_proof_status_message": str(
                identity_proof_contract.get("proof_status_message", "")
            ),
            "identity_proof_status_message_key": str(
                identity_proof_contract.get("proof_status_message_key", "")
            ),
            "identity_proof_fields": [
                str(item)
                for item in identity_proof_contract.get("required_identity_fields", [])
            ],
            "identity_proof_field_details": [
                item
                for item in identity_proof_contract.get("required_identity_field_details", [])
                if isinstance(item, dict)
            ],
        }

    def ai_index_status(self) -> dict[str, Any]:
        vector_status = self.vector_index.status()
        graph_snapshot = self.graph_index.snapshot()
        vector_counts_key, vector_counts_params = _ai_index_vector_counts_contract(
            int(vector_status.entry_count)
        )
        graph_counts_key, graph_counts_params = _ai_index_graph_counts_contract(
            len(graph_snapshot.nodes),
            len(graph_snapshot.edges),
        )
        return {
            "ai_index_status": {
                "status": "available",
                "message": "AI index status is available as a local derived read model.",
                "message_key": _ai_index_status_message_key("available"),
                "boundary_note": "AI index status remains derived, read-only, and non-authoritative over primary Chronicle records.",
                "boundary_note_key": "ui.ai_index_status.note.read_only_derived",
                "vector": {
                    **vector_status.model_dump(mode="json"),
                    "counts_summary_key": vector_counts_key,
                    "counts_summary_params": vector_counts_params,
                },
                "graph": {
                    "path": str(self.graph_index.paths.graph_index_file),
                    "node_count": len(graph_snapshot.nodes),
                    "edge_count": len(graph_snapshot.edges),
                    "external_call_made": False,
                    "counts_summary_key": graph_counts_key,
                    "counts_summary_params": graph_counts_params,
                },
                "derived_surface": True,
                "primary_record_authoritative": True,
                "external_services": False,
                "graphrag_runtime": False,
                "correctness_proof": False,
            }
        }

    def ai_index_vector_entries(self) -> dict[str, Any]:
        snapshot = self.vector_index.snapshot()
        return {"vector_entries": [_dump_model(entry) for entry in snapshot.entries]}

    def ai_index_graph_nodes(self) -> dict[str, Any]:
        snapshot = self.graph_index.snapshot()
        return {"graph_nodes": [_dump_model(node) for node in snapshot.nodes]}

    def ai_index_graph_edges(self) -> dict[str, Any]:
        snapshot = self.graph_index.snapshot()
        return {"graph_edges": [_dump_model(edge) for edge in snapshot.edges]}

    def runtime_config_state(self) -> dict[str, Any]:
        state = self.runtime_config.show()
        payload = state.model_dump(mode="json")
        source_key, source_summary = _status_summary_payload(
            "ui.runtime_config.source",
            payload.get("source"),
        )
        payload["source_summary_key"] = source_key
        payload["source_summary"] = source_summary
        config = payload.get("config", {})
        if isinstance(config, dict):
            provider_kind_key, provider_kind_summary = _status_summary_payload(
                "ui.runtime_config.provider_kind",
                config.get("provider_kind"),
            )
            config["provider_kind_summary_key"] = provider_kind_key
            config["provider_kind_summary"] = provider_kind_summary
            allow_network_key, allow_network_summary = _boolean_summary_payload(
                bool(config.get("allow_network"))
            )
            config["allow_network_summary_key"] = allow_network_key
            config["allow_network_summary"] = allow_network_summary
            allow_external_context_key, allow_external_context_summary = _boolean_summary_payload(
                bool(config.get("allow_external_context"))
            )
            config["allow_external_context_summary_key"] = allow_external_context_key
            config["allow_external_context_summary"] = allow_external_context_summary
        return {"runtime_config": payload}

    def package_review_snapshot(self) -> dict[str, Any]:
        try:
            report = self.package_review.review_context_package(purpose="chronicle ui overview")
            return _decorate_package_review_payload(report.model_dump(mode="json"))
        except Exception as exc:  # pragma: no cover - defensive UI degradation
            return _decorate_package_review_payload(
                {
                "status": "unavailable",
                "error": str(exc),
                }
            )

    def graph_summary(self) -> dict[str, Any]:
        try:
            graph = GraphExportService(self.root).export_graph()
            node_count = len(graph.nodes)
            edge_count = len(graph.edges)
            counts_key, counts_params = _graph_summary_counts_contract(node_count, edge_count)
            return {
                "status": "available",
                "nodes": node_count,
                "edges": edge_count,
                "message": "Graph summary is available as a local derived read model.",
                "message_key": _graph_summary_message_key("available"),
                "counts_summary_key": counts_key,
                "counts_summary_params": counts_params,
                "boundary_note": "Graph summary remains derived, read-only, and non-authoritative over primary Chronicle records.",
                "boundary_note_key": "ui.graph_summary.note.read_only_derived",
                "derived_surface": True,
                "primary_record_authoritative": True,
                "external_services": False,
                "graphrag_runtime": False,
                "correctness_proof": False,
            }
        except Exception as exc:  # pragma: no cover - defensive UI degradation
            counts_key, counts_params = _graph_summary_counts_contract(0, 0)
            return {
                "status": "unavailable",
                "nodes": 0,
                "edges": 0,
                "error": str(exc),
                "message": "Graph summary is unavailable; keep using primary Chronicle records for authority.",
                "message_key": _graph_summary_message_key("unavailable"),
                "counts_summary_key": counts_key,
                "counts_summary_params": counts_params,
                "boundary_note": "Graph summary remains derived, read-only, and non-authoritative over primary Chronicle records.",
                "boundary_note_key": "ui.graph_summary.note.read_only_derived",
                "derived_surface": True,
                "primary_record_authoritative": True,
                "external_services": False,
                "graphrag_runtime": False,
                "correctness_proof": False,
            }

    def runtime_package_handoff(self, plan: RuntimeRetrievalPlan) -> dict[str, Any]:
        context_ids = [record_id for record_id in _unique_list(plan) if record_id.startswith("ctx_")]
        skipped_ids = [record_id for record_id in _unique_list(plan) if not record_id.startswith("ctx_")]
        payload: dict[str, Any] = {
            "status": "package_context_available" if context_ids else "no_context_records",
            "eligible_context_ids": context_ids,
            "skipped_record_ids": skipped_ids,
            "purpose": f"runtime retrieval handoff: {plan.query}",
            "target_environment": "local",
            "package_review_required": True,
        }
        counts_key, counts_params = _package_handoff_counts_contract(
            eligible_context_count=len(context_ids),
            skipped_record_count=len(skipped_ids),
        )
        payload["counts_summary_key"] = counts_key
        payload["counts_summary_params"] = counts_params
        payload["boundary_note"] = (
            "Package handoff preview remains derived, read-only, and non-authoritative over primary Chronicle records."
        )
        payload["boundary_note_key"] = "ui.package_handoff.note.read_only_derived"
        payload["suggested_commands"] = [
            'chronicle package review --purpose "runtime retrieval handoff"',
            'chronicle package context --purpose "runtime retrieval handoff" --persist',
            "chronicle review queue --json",
        ]
        payload["suggested_command_details"] = [
            _package_handoff_command_detail(command)
            for command in payload["suggested_commands"]
        ]
        if not context_ids:
            payload["message"] = "No context records were selected by the retrieval dry-run, so package preview is advisory only."
            payload["message_key"] = _package_handoff_message_key(str(payload["status"]))
            return payload
        package = self.packages.build_context_package(
            purpose=payload["purpose"],
            context_ids=context_ids,
        )
        review = self.package_review.review_package(package)
        payload["package_manifest_preview"] = package.manifest.model_dump(mode="json")
        payload["package_review"] = _decorate_package_review_payload(review.model_dump(mode="json"))
        payload["message"] = "Read-only package preview derived from retrieval-plan context hits."
        payload["message_key"] = _package_handoff_message_key(str(payload["status"]))
        return payload

    def runtime_related_links(self, event_id: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
        links = [
            _related_link(
                f"/api/review-queue/{event_id}",
                _open_matching_detail_label("review-queue"),
                label_key=_open_matching_detail_label_key("review-queue"),
            )
        ]
        if "runtime_invocation_plan" in payload:
            request_preview = payload["runtime_invocation_plan"].get("request_preview", {})
            summary_job_id = request_preview.get("summary_job_id")
            if isinstance(summary_job_id, str) and summary_job_id.startswith("sum_"):
                links.append(
                    _related_link(
                        f"/api/summary-jobs/{summary_job_id}",
                        f"Open summary job {summary_job_id}",
                        label_key="ui.template.related_link.open_summary_job",
                        label_params={"summary_job_id": summary_job_id},
                    )
                )
        if "runtime_execution" in payload:
            execution = RuntimeExecutionResult.model_validate(payload["runtime_execution"])
            if execution.draft_summary_job_id:
                links.append(
                    _related_link(
                        f"/api/summary-jobs/{execution.draft_summary_job_id}",
                        f"Open summary job {execution.draft_summary_job_id}",
                        label_key="ui.template.related_link.open_summary_job",
                        label_params={"summary_job_id": execution.draft_summary_job_id},
                    )
                )
            if execution.artifact_id:
                links.append(
                    _related_link(
                        f"/api/artifacts/{execution.artifact_id}",
                        f"Open artifact {execution.artifact_id}",
                        label_key="ui.template.related_link.open_artifact",
                        label_params={"artifact_id": execution.artifact_id},
                    )
                )
        if "runtime_retrieval_plan" in payload:
            plan = RuntimeRetrievalPlan.model_validate(payload["runtime_retrieval_plan"])
            for record_id in _unique_list(plan):
                if record_id.startswith("ctx_"):
                    links.append(
                        _related_link(
                            f"/api/contexts/{record_id}",
                            _open_detail_label("contexts", record_id),
                            label_key=_open_detail_label_key("contexts"),
                            label_params={"record_id": record_id},
                        )
                    )
                elif record_id.startswith("evt_"):
                    links.append(
                        _related_link(
                            f"/api/events/{record_id}",
                            _open_detail_label("events", record_id),
                            label_key=_open_detail_label_key("events"),
                            label_params={"record_id": record_id},
                        )
                    )
        return links

    def review_package_readiness(self, target_event_id: str) -> dict[str, Any]:
        self.chronicle.require_initialized()
        event = next(
            (item for item in self.chronicle.jsonl.read_all() if item.event_id == target_event_id),
            None,
        )
        if event is None:
            return {
                "status": "missing_target",
                "message": "Target event is not available for package readiness derivation.",
                "message_key": "ui.package_readiness.message.unavailable",
                "counts_summary_key": "ui.template.package_readiness.counts",
                "counts_summary_params": {
                    "eligible_context_count": 0,
                    "skipped_record_count": 0,
                },
                "boundary_note": "Package readiness remains derived, read-only, and non-authoritative over primary Chronicle records.",
                "boundary_note_key": "ui.package_readiness.note.read_only_derived",
                "message_params": {
                    "eligible_context_count": 0,
                    "review_status": "not_available",
                },
                "suggested_commands": [],
                "suggested_command_details": [],
            }

        payload = getattr(event, "payload", {})
        if "runtime_retrieval_plan" in payload:
            plan = RuntimeRetrievalPlan.model_validate(payload["runtime_retrieval_plan"])
            handoff = self.runtime_package_handoff(plan)
            handoff["suggested_commands"] = [
                'chronicle package review --purpose "runtime retrieval handoff"',
                'chronicle package context --purpose "runtime retrieval handoff" --persist',
            ]
            handoff["suggested_command_details"] = [
                _package_readiness_command_detail(command)
                for command in handoff["suggested_commands"]
            ]
            return handoff

        context_ids = [context_id for context_id in getattr(event, "context_ids", []) if context_id.startswith("ctx_")]
        source_ref = getattr(getattr(event, "source", None), "source_ref", "") or ""
        if source_ref.startswith("ctx_") and source_ref not in context_ids:
            context_ids.append(source_ref)

        if not context_ids:
            return {
                "status": "no_context_records",
                "eligible_context_ids": [],
                "skipped_record_ids": [],
                "message": "No context-linked records are available for package/export preview from this review target.",
                "message_key": "ui.package_readiness.message.no_context_records",
                "counts_summary_key": "ui.template.package_readiness.counts",
                "counts_summary_params": {
                    "eligible_context_count": 0,
                    "skipped_record_count": 0,
                },
                "boundary_note": "Package readiness remains derived, read-only, and non-authoritative over primary Chronicle records.",
                "boundary_note_key": "ui.package_readiness.note.read_only_derived",
                "message_params": {
                    "eligible_context_count": 0,
                    "review_status": "not_available",
                },
                "suggested_commands": ["chronicle show --json", "chronicle review queue --json"],
                "suggested_command_details": [
                    _package_readiness_command_detail("chronicle show --json"),
                    _package_readiness_command_detail("chronicle review queue --json"),
                ],
                "package_review_required": True,
            }

        package = self.packages.build_context_package(
            purpose=f"review target handoff: {target_event_id}",
            context_ids=context_ids,
        )
        review = self.package_review.review_package(package)
        counts_key, counts_params = _package_readiness_counts_contract(
            eligible_context_count=len(context_ids),
            skipped_record_count=0,
        )
        return {
            "status": "package_context_available",
            "eligible_context_ids": context_ids,
            "skipped_record_ids": [],
            "message": "Read-only package readiness derived from context-linked review target records.",
            "message_key": "ui.package_readiness.message.package_context_available",
            "counts_summary_key": counts_key,
            "counts_summary_params": counts_params,
            "boundary_note": "Package readiness remains derived, read-only, and non-authoritative over primary Chronicle records.",
            "boundary_note_key": "ui.package_readiness.note.read_only_derived",
            "message_params": {
                "eligible_context_count": len(context_ids),
                "review_status": str(review.status.value),
            },
            "suggested_commands": [
                'chronicle package review --purpose "review target handoff"',
                'chronicle package context --purpose "review target handoff" --persist',
            ],
            "suggested_command_details": [
                _package_readiness_command_detail('chronicle package review --purpose "review target handoff"'),
                _package_readiness_command_detail(
                    'chronicle package context --purpose "review target handoff" --persist'
                ),
            ],
            "package_review_required": True,
            "package_manifest_preview": package.manifest.model_dump(mode="json"),
            "package_review": _decorate_package_review_payload(review.model_dump(mode="json")),
        }

    def review_related_links(self, target_event_id: str) -> list[dict[str, Any]]:
        links = [
            _related_link(
                f"/api/runtime-records/{target_event_id}",
                _open_matching_detail_label("runtime-records"),
                label_key=_open_matching_detail_label_key("runtime-records"),
            )
        ]
        readiness = self.review_package_readiness(target_event_id)
        for context_id in readiness.get("eligible_context_ids", []):
            if isinstance(context_id, str) and context_id.startswith("ctx_"):
                links.append(
                    _related_link(
                        f"/api/contexts/{context_id}",
                        _open_detail_label("contexts", context_id),
                        label_key=_open_detail_label_key("contexts"),
                        label_params={"record_id": context_id},
                    )
                )
        return links

    def summary_job_related_links(self, summary_job_id: str, job: dict[str, Any]) -> list[dict[str, Any]]:
        links: list[dict[str, Any]] = []
        event_id = str(job.get("event_id", ""))
        if event_id.startswith("evt_"):
            links.append(
                _related_link(
                    f"/api/review-queue/{event_id}",
                    f"Open review target {event_id}",
                    label_key="ui.template.related_link.open_review_target",
                    label_params={"event_id": event_id},
                )
            )
        for ref in job.get("source_refs", []):
            record_type = str(ref.get("record_type", "event"))
            record_id = str(ref.get("record_id", ""))
            if record_type == "event" and record_id.startswith("evt_"):
                links.append(
                    _related_link(
                        f"/api/events/{record_id}",
                        f"Open event {record_id}",
                        label_key=_open_detail_label_key("events"),
                        label_params={"record_id": record_id},
                    )
                )
            elif record_id.startswith("ctx_"):
                links.append(
                    _related_link(
                        f"/api/contexts/{record_id}",
                        f"Open context {record_id}",
                        label_key=_open_detail_label_key("contexts"),
                        label_params={"record_id": record_id},
                    )
                )
        artifact_id = str(job.get("artifact_id", ""))
        if artifact_id.startswith("art_"):
            links.append(
                _related_link(
                    f"/api/artifacts/{artifact_id}",
                    f"Open artifact {artifact_id}",
                    label_key="ui.template.related_link.open_artifact",
                    label_params={"artifact_id": artifact_id},
                )
            )
        return links

    def runtime_boundary(self) -> dict[str, Any]:
        read_only_key, read_only_summary = _boolean_summary_payload(True)
        external_model_api_key, external_model_api_summary = _boolean_summary_payload(False)
        graphrag_runtime_key, graphrag_runtime_summary = _boolean_summary_payload(False)
        vector_db_key, vector_db_summary = _boolean_summary_payload(False)
        graph_db_key, graph_db_summary = _boolean_summary_payload(False)
        return {
            "read_only": True,
            "read_only_summary_key": read_only_key,
            "read_only_summary": read_only_summary,
            "foreground_process": True,
            "daemon": False,
            "server_default_host": DEFAULT_UI_HOST,
            "external_model_api": False,
            "external_model_api_summary_key": external_model_api_key,
            "external_model_api_summary": external_model_api_summary,
            "graphrag_runtime": False,
            "graphrag_runtime_summary_key": graphrag_runtime_key,
            "graphrag_runtime_summary": graphrag_runtime_summary,
            "vector_db": False,
            "vector_db_summary_key": vector_db_key,
            "vector_db_summary": vector_db_summary,
            "graph_db": False,
            "graph_db_summary_key": graph_db_key,
            "graph_db_summary": graph_db_summary,
            "correctness_proof": False,
        }

    @staticmethod
    def _response_metadata_summary(
        *,
        response_metadata: dict[str, Any] | None,
        response_keys: list[str] | None,
    ) -> dict[str, Any]:
        metadata = response_metadata or {}
        keys = [str(item) for item in (response_keys or [])]
        counts_key, counts_params = _response_metadata_counts_contract(
            metadata_count=len(metadata),
            response_key_count=len(keys),
        )
        finish_reason_key, finish_reason_summary = _status_summary_payload(
            "ui.provider_response.finish_reason",
            metadata.get("finish_reason"),
        )
        provider_status_key, provider_status_summary = _status_summary_payload(
            "ui.provider_response.provider_status",
            metadata.get("provider_status"),
        )
        return {
            "present": bool(metadata or keys),
            "message": (
                "Provider response metadata is available for this local derived record."
                if (metadata or keys)
                else "Provider response metadata is not available for this local derived record."
            ),
            "message_key": (
                "ui.provider_response.message.present"
                if (metadata or keys)
                else "ui.provider_response.message.unavailable"
            ),
            "response_id": metadata.get("response_id"),
            "finish_reason": metadata.get("finish_reason"),
            "finish_reason_summary_key": finish_reason_key,
            "finish_reason_summary": finish_reason_summary,
            "provider_status": metadata.get("provider_status"),
            "provider_status_summary_key": provider_status_key,
            "provider_status_summary": provider_status_summary,
            "usage_input_tokens": metadata.get("usage_input_tokens"),
            "usage_output_tokens": metadata.get("usage_output_tokens"),
            "usage_total_tokens": metadata.get("usage_total_tokens"),
            "metadata_count": len(metadata),
            "response_key_count": len(keys),
            "response_keys": keys,
            "counts_summary_key": counts_key,
            "counts_summary_params": counts_params,
            "boundary_note": "Provider response metadata remains derived, read-only, and non-authoritative over primary Chronicle records.",
            "boundary_note_key": "ui.provider_response.note.read_only_derived",
        }

    def _runtime_response_metadata_summary(self, *, payload: dict[str, Any]) -> dict[str, Any]:
        if "runtime_execution" in payload:
            execution = RuntimeExecutionResult.model_validate(payload["runtime_execution"])
            return self._response_metadata_summary(
                response_metadata=execution.response_metadata,
                response_keys=execution.response_keys,
            )
        if "runtime_summary" in payload:
            summary = payload["runtime_summary"]
            return self._response_metadata_summary(
                response_metadata=summary.get("response_metadata", {}),
                response_keys=summary.get("response_keys", []),
            )
        return self._response_metadata_summary(response_metadata={}, response_keys=[])

    def _review_target_response_metadata_summary(self, target_event_id: str) -> dict[str, Any]:
        event = next(
            (item for item in self.chronicle.jsonl.read_all() if item.event_id == target_event_id),
            None,
        )
        if event is None:
            return self._response_metadata_summary(response_metadata={}, response_keys=[])
        payload = getattr(event, "payload", {})
        if not isinstance(payload, dict):
            return self._response_metadata_summary(response_metadata={}, response_keys=[])
        return self._runtime_response_metadata_summary(payload=payload)

    def ui_boundary(self) -> dict[str, Any]:
        metadata = build_ui_boundary_metadata(
            host=self.host,
            mutation_capability_flag=self.mutation_capability_flag,
            enable_ui_mutation=self.enable_ui_mutation,
            auth_mode=self.auth_mode,
            authorization_mode=self.authorization_mode,
        )
        return {"ui_boundary": asdict(metadata)}

    @staticmethod
    def _auth_boundary_notice(
        boundary: dict[str, Any],
        capability: dict[str, Any] | None,
        assurance: dict[str, Any] | None,
    ) -> dict[str, Any]:
        capability = capability or {}
        assurance = assurance or {}
        warnings = [str(item) for item in capability.get("warnings", [])]
        blockers: list[str] = []
        next_steps: list[str] = []

        for warning in warnings:
            blocker_code = AUTH_BOUNDARY_WARNING_TO_BLOCKER.get(warning)
            if blocker_code is None:
                continue
            _append_auth_boundary_blocker(blockers, next_steps, blocker_code)

        assurance_status = str(assurance.get("status", "unknown"))
        capability_status = str(capability.get("status", "unknown"))
        if capability_status == "ready" and assurance_status == "boundary_aligned" and not blockers:
            status = "boundary_aligned"
        elif blockers:
            status = "advisory_only"
        elif assurance_status != "unknown":
            status = assurance_status
        else:
            status = capability_status
        message = _auth_readiness_message(
            capability_status=capability_status,
            assurance_status=assurance_status,
            has_blockers=bool(blockers),
        )

        return {
            "status": status,
            "capability_status_summary_key": f"ui.review_capability.status.{capability_status}",
            "capability_status_summary": capability_status.replace("_", " "),
            "identity_assurance_status_summary_key": f"ui.identity_assurance.status.{assurance_status}",
            "identity_assurance_status_summary": assurance_status.replace("_", " "),
            "message": message,
            "message_key": _auth_readiness_message_key(
                capability_status=capability_status,
                assurance_status=assurance_status,
                has_blockers=bool(blockers),
            ),
            "scope_note": _auth_readiness_scope_note(
                auth_mode=str(boundary.get("auth_mode", UIAuthMode.NOT_ENABLED)),
                authorization_mode=str(
                    boundary.get("authorization_mode", UIAuthorizationMode.NOT_ENABLED)
                ),
                session_gating=bool(boundary.get("session_gating", False)),
            ),
            "scope_note_key": (
                "ui.auth_readiness.scope.auth_not_enabled"
                if str(boundary.get("auth_mode", UIAuthMode.NOT_ENABLED)) == UIAuthMode.NOT_ENABLED
                else (
                    "ui.auth_readiness.scope.authorization_not_enabled"
                    if str(boundary.get("authorization_mode", UIAuthorizationMode.NOT_ENABLED))
                    == UIAuthorizationMode.NOT_ENABLED
                    else (
                        "ui.auth_readiness.scope.session_gated"
                        if bool(boundary.get("session_gating", False))
                        else "ui.auth_readiness.scope.descriptive_preview"
                    )
                )
            ),
            "blockers": blockers,
            "blocker_details": _serialize_auth_boundary_blocker_details(blockers),
            "blocker_summaries": _auth_blocker_summaries(blockers),
            "next_steps": next_steps,
            "capability_status": capability_status,
            "identity_assurance_status": assurance_status,
            "reviewer_enforcement_summary": boundary.get("reviewer_enforcement_summary", {}),
            "reviewer_validation_gate_summary": boundary.get("reviewer_validation_gate_summary", {}),
        }

    def _review_queue_row(self, target_event_id: str) -> dict[str, Any] | None:
        for row in self.review_queue()["review_queue"]:
            if row.get("target_event_id") == target_event_id:
                return row
        return None

    def _review_queue_row_including_resolved(self, target_event_id: str) -> dict[str, Any] | None:
        boundary = self.ui_boundary()["ui_boundary"]
        for entry in self.review.queue(include_resolved=True):
            if entry.target_event_id != target_event_id:
                continue
            data = entry.model_dump(mode="json")
            data["review_capability"] = self._review_capability(
                pending=bool(data.get("pending")),
                boundary=boundary,
                identity=(
                    ReviewerIdentity.model_validate(data["latest_reviewer_identity"])
                    if data.get("latest_reviewer_identity") is not None
                    else None
                ),
            )
            return data
        return None

    @staticmethod
    def _review_kind(payload: dict[str, Any]) -> str:
        if "runtime_summary" in payload:
            return "runtime_summary"
        if "runtime_retrieval_plan" in payload:
            return "runtime_retrieval_plan"
        if "runtime_invocation_plan" in payload:
            return "runtime_invocation_plan"
        return "assistant_output"

    @staticmethod
    def _suggested_cli_family(payload: dict[str, Any]) -> str:
        if "runtime_summary" in payload:
            return "chronicle runtime summarize --record"
        if "runtime_retrieval_plan" in payload:
            return "chronicle runtime retrieve-plan --record"
        if "runtime_invocation_plan" in payload:
            return "chronicle runtime invoke-plan --record"
        return "chronicle show --json"

    @staticmethod
    def _suggested_cli_family_from_kind(review_kind: str) -> str:
        if review_kind == "artifact_update":
            return "chronicle artifact propose-update"
        if review_kind == "context_update":
            return "chronicle context propose-update"
        if review_kind == "runtime_summary":
            return "chronicle runtime summarize --record"
        if review_kind == "runtime_retrieval_plan":
            return "chronicle runtime retrieve-plan --record"
        if review_kind == "runtime_invocation_plan":
            return "chronicle runtime invoke-plan --record"
        return "chronicle show --json"

    @staticmethod
    def _identity_assurance(identity: ReviewerIdentity, boundary: dict[str, Any]) -> dict[str, Any]:
        boundary_auth_mode = boundary.get("auth_mode", "not_enabled")
        session_gating = bool(boundary.get("session_gating", False))
        if identity.auth_mode.value == "none":
            status = "declared_only"
        elif boundary_auth_mode == "not_enabled":
            status = "local_session_unverified"
        else:
            status = "boundary_aligned"
        message = _identity_assurance_message(
            reviewer_auth_mode=identity.auth_mode.value,
            boundary_auth_mode=str(boundary_auth_mode),
        )
        return {
            "status": status,
            "status_summary_key": f"ui.identity_assurance.status.{status}",
            "status_summary": status.replace("_", " "),
            "reviewer_auth_mode": identity.auth_mode.value,
            "boundary_auth_mode": boundary_auth_mode,
            "session_gating": session_gating,
            "message": message,
            "message_key": _identity_assurance_message_key(
                reviewer_auth_mode=identity.auth_mode.value,
                boundary_auth_mode=str(boundary_auth_mode),
            ),
        }

    def _review_capability(
        self,
        *,
        pending: bool,
        boundary: dict[str, Any],
        identity: ReviewerIdentity | None,
    ) -> dict[str, Any]:
        if not pending:
            return {
                "status": "resolved",
                "status_summary_key": "ui.review_capability.status.resolved",
                "status_summary": "resolved",
                "can_review_now": False,
                "can_review_now_summary_key": _boolean_summary_payload(False)[0],
                "can_review_now_summary": _boolean_summary_payload(False)[1],
                "warnings": [],
                "message": "Review target is already resolved in the current derived queue view.",
                "message_key": "ui.review_capability.message.resolved",
            }

        warnings: list[str] = []
        auth_mode = boundary.get("auth_mode", UIAuthMode.NOT_ENABLED)
        authorization_mode = boundary.get("authorization_mode", UIAuthorizationMode.NOT_ENABLED)
        session_gating = bool(boundary.get("session_gating", False))

        if auth_mode == UIAuthMode.NOT_ENABLED:
            warnings.append("ui_auth_not_enabled")
        if authorization_mode == UIAuthorizationMode.NOT_ENABLED:
            warnings.append("ui_authorization_not_enabled")
        if identity is None:
            warnings.append("no_reviewer_identity_recorded")
        elif identity.kind.value == "user_declared":
            warnings.append("reviewer_identity_declared_only")
        elif session_gating and identity.session_label is None:
            warnings.append("reviewer_session_label_missing")

        can_review_now = len(warnings) == 0
        message = _review_capability_message(can_review_now)
        return {
            "status": "ready" if can_review_now else "advisory_only",
            "status_summary_key": f"ui.review_capability.status.{'ready' if can_review_now else 'advisory_only'}",
            "status_summary": ("ready" if can_review_now else "advisory only"),
            "can_review_now": can_review_now,
            "can_review_now_summary_key": _boolean_summary_payload(bool(can_review_now))[0],
            "can_review_now_summary": _boolean_summary_payload(bool(can_review_now))[1],
            "warnings": warnings,
            "warning_details": _serialize_review_warning_details(warnings),
            "message": message,
            "message_key": _review_capability_message_key(can_review_now),
        }

    def _history_row(self, item: Any, boundary: dict[str, Any]) -> dict[str, Any]:
        data = item.model_dump(mode="json")
        data["identity_assurance"] = self._identity_assurance(item.reviewer_identity, boundary)
        return data

    @staticmethod
    def _package_readiness_summary(readiness: dict[str, Any]) -> dict[str, Any]:
        package_review = readiness.get("package_review", {})
        status = str(readiness.get("status", "unknown"))
        review_status = str(package_review.get("status", "not_available"))
        eligible_context_ids = readiness.get("eligible_context_ids", [])
        warnings = package_review.get("package_warnings", [])

        if status == "package_context_available":
            label = f"package:{review_status}"
            message = (
                f"Package preview available for {len(eligible_context_ids)} context record(s); "
                f"review status is {review_status}."
            )
        elif status == "no_context_records":
            label = "package:advisory"
            message = "No context-linked records available for package/export preview."
        else:
            label = f"package:{status}"
            message = str(readiness.get("message", "Package readiness unavailable."))

        return {
            "status": status,
            "review_status": review_status,
            "eligible_context_count": len(eligible_context_ids) if isinstance(eligible_context_ids, list) else 0,
            "warning_count": len(warnings) if isinstance(warnings, list) else 0,
            "label": label,
            "label_key": _package_readiness_summary_label_key(
                status=status,
                review_status=review_status,
            ),
            "message": message,
            "message_key": _package_readiness_message_key(status),
            "message_template_key": _package_readiness_summary_message_template_key(status),
            "message_params": {
                "eligible_context_count": len(eligible_context_ids)
                if isinstance(eligible_context_ids, list)
                else 0,
                "review_status": review_status,
            },
        }

    @staticmethod
    def _review_recovery_commands(
        *,
        event_id: str | None = None,
        action: str | None = None,
        error_code: str | None = None,
        audit_id: str | None = None,
    ) -> list[str]:
        cli_equivalent = (
            f"chronicle review {action} --event {event_id}"
            if event_id and action
            else ""
        )
        commands: list[str] = []
        if error_code == "review_not_pending":
            commands.extend([
                "chronicle review queue --include-resolved --json",
                cli_equivalent,
            ])
        elif error_code == "review_target_not_found":
            commands.extend([
                "chronicle review queue --include-resolved --json",
                cli_equivalent,
            ])
        elif error_code == "authorization_failed":
            commands.extend([
                "chronicle review queue --json",
                cli_equivalent,
            ])
        elif error_code == "audit_insertion_failed":
            commands.extend([
                cli_equivalent,
                "chronicle audit list --json",
            ])
        elif error_code == "decision_persistence_failed":
            commands.extend([
                "chronicle review queue --include-resolved --json",
                f"chronicle audit show --id {audit_id} --json" if audit_id else "",
                "chronicle audit list --json",
                cli_equivalent,
            ])
        else:
            commands.append(cli_equivalent)
        return [command for index, command in enumerate(commands) if command and command not in commands[:index]]

    @staticmethod
    def _review_action_target_state_recovery(error_code: str | None) -> dict[str, Any]:
        if error_code == "review_not_pending":
            return {
                "status": "resolved_queue_check_required",
                "status_summary_key": "ui.review_action_target_state_recovery.status.resolved_queue_check_required",
                "status_summary": "resolved queue check required",
                "summary_key": "ui.review_action_target_state_recovery.summary.review_not_pending",
                "summary": "The target is no longer pending in the default queue view; inspect the resolved queue before retrying any follow-up action.",
                "pending_queue_sufficient": False,
                "pending_queue_sufficient_summary_key": _boolean_summary_payload(False)[0],
                "pending_queue_sufficient_summary": _boolean_summary_payload(False)[1],
                "resolved_queue_reason_key": "ui.review_action_target_state_recovery.reason.review_not_pending",
                "resolved_queue_reason": "A later review decision already resolved the pending target in the current derived queue view.",
                "resolved_queue_command": "chronicle review queue --include-resolved --json",
            }
        if error_code == "review_target_not_found":
            return {
                "status": "chronicle_state_recheck_required",
                "status_summary_key": "ui.review_action_target_state_recovery.status.chronicle_state_recheck_required",
                "status_summary": "chronicle state recheck required",
                "summary_key": "ui.review_action_target_state_recovery.summary.review_target_not_found",
                "summary": "The target is missing from the current Chronicle state; inspect the resolved queue and current derived state before retrying.",
                "pending_queue_sufficient": False,
                "pending_queue_sufficient_summary_key": _boolean_summary_payload(False)[0],
                "pending_queue_sufficient_summary": _boolean_summary_payload(False)[1],
                "resolved_queue_reason_key": "ui.review_action_target_state_recovery.reason.review_target_not_found",
                "resolved_queue_reason": "The review queue alone may be stale relative to the operator's expectation for this target.",
                "resolved_queue_command": "chronicle review queue --include-resolved --json",
                "chronicle_state_command": "chronicle show --json",
            }
        return {}

    @staticmethod
    def _warning_message(code: str) -> str:
        return REVIEW_WARNING_TEXT.get(code, code.replace("_", " "))

    @staticmethod
    def _warning_label(code: str) -> str:
        return REVIEW_WARNING_LABELS.get(code, code.replace("_", " "))

    @staticmethod
    def _review_action_failure_contract(
        *,
        mutation_enabled: bool,
        cli_equivalent: str | None = None,
        event_id: str | None = None,
        action: str | None = None,
        error_code: str | None = None,
        audit_id: str | None = None,
    ) -> dict[str, Any]:
        pre_mutation_or_gate_errors = [
            "mutation_disabled",
            "invalid_mutation_token",
            "invalid_mutation_session",
            "mutation_request_id_required",
            "invalid_mutation_request_id",
            "duplicate_mutation_request",
            "reviewer_label_required",
            "invalid_reviewer_label",
            "session_label_required",
            "invalid_session_label",
            "ui_intent_mismatch",
            "invalid_reviewer_kind",
            "authorization_failed",
            "review_target_not_found",
            "review_not_pending",
            "invalid_json",
        ]
        durable_write_path_errors = [
            "audit_insertion_failed",
            "decision_persistence_failed",
        ]
        possible_error_codes = pre_mutation_or_gate_errors + durable_write_path_errors
        possible_error_details = [_review_possible_error_detail(code) for code in possible_error_codes]
        recovery_commands = ChronicleUIDataService._review_recovery_commands(
            event_id=event_id,
            action=action,
            error_code=error_code,
            audit_id=audit_id,
        )
        recovery_command_details = [
            _review_command_detail(command, kind="recovery") for command in recovery_commands
        ]
        target_state_recovery = ChronicleUIDataService._review_action_target_state_recovery(error_code)
        pre_gate_summary_key, pre_gate_summary_params, pre_gate_summary = (
            _review_failure_family_summary_contract("pre_mutation_or_gate")
        )
        durable_summary_key, durable_summary_params, durable_summary = (
            _review_failure_family_summary_contract("durable_write_path")
        )
        return {
            "transaction_rule": (
                "No durable GUI review result is reported as applied unless both review decision persistence and audit insertion succeed."
            ),
            "rollback_status": "fail_closed",
            "rollback_status_summary_key": "ui.review_contract.rollback_status.fail_closed",
            "rollback_status_summary": "fail closed",
            "durable_mutation_reported_on_failure": False,
            "durable_mutation_reported_on_failure_summary_key": (
                "ui.review_failure_contract.durable_mutation_reported_on_failure.false"
            ),
            "durable_mutation_reported_on_failure_summary": "false",
            "partial_failure_visible": True,
            "possible_error_codes": possible_error_codes,
            "possible_error_details": possible_error_details,
            "failure_families": [
                {
                    "family": "pre_mutation_or_gate",
                    "summary": pre_gate_summary,
                    "summary_key": pre_gate_summary_key,
                    "summary_params": pre_gate_summary_params,
                    "possible_error_codes": pre_mutation_or_gate_errors,
                },
                {
                    "family": "durable_write_path",
                    "summary": durable_summary,
                    "summary_key": durable_summary_key,
                    "summary_params": durable_summary_params,
                    "possible_error_codes": durable_write_path_errors,
                },
            ],
            "recovery_path": (
                recovery_commands[0]
                if recovery_commands
                else cli_equivalent or "Use the equivalent chronicle review CLI command for recovery or inspection."
            ),
            "recovery_commands": recovery_commands,
            "recovery_command_details": recovery_command_details,
            "target_state_recovery": target_state_recovery,
        }

    @staticmethod
    def _review_action_failure_message(error_code: str) -> str:
        messages = {
            "mutation_disabled": "GUI mutation remains disabled for this session; use the CLI review path instead.",
            "invalid_mutation_token": "The local mutation token is missing or invalid for this browser session.",
            "invalid_mutation_session": "The local mutation session is missing or no longer aligned with this browser session.",
            "mutation_request_id_required": "A unique local mutation request identifier is required for browser-triggered write routes.",
            "invalid_mutation_request_id": "The local mutation request identifier format is invalid for this browser session.",
            "duplicate_mutation_request": "This local mutation request identifier was already used in the current browser session.",
            "reviewer_label_required": "Reviewer label is missing, so the UI cannot attribute the review action.",
            "invalid_reviewer_label": "Reviewer label must start with a lowercase letter or digit and use only lowercase letters, digits, dot, underscore, or hyphen.",
            "session_label_required": "Session label is required for the current session-gated local mutation boundary.",
            "invalid_session_label": "Session label must start with a lowercase letter or digit and use only lowercase letters, digits, dot, underscore, or hyphen.",
            "ui_intent_mismatch": "Requested route and submitted UI intent differ, so the action was rejected before mutation.",
            "invalid_reviewer_kind": "Reviewer kind is not one of the supported local reviewer identity kinds.",
            "authorization_failed": "Reviewer identity or session boundary is not aligned, so the action stays blocked.",
            "review_target_not_found": "The target review event is no longer available from the current Chronicle state.",
            "review_not_pending": "The review target is no longer pending; inspect the resolved queue before retrying.",
            "invalid_json": "The request body could not be parsed as JSON, so no mutation path was attempted.",
            "invalid_request_body": "Request body must be a JSON object.",
            "audit_insertion_failed": "Audit insertion failed before the review decision could be reported as applied.",
            "decision_persistence_failed": "Audit insertion succeeded, but the Chronicle primary-record append failed, so treat the route as fail-closed.",
        }
        return messages.get(error_code, error_code.replace("_", " "))

    @staticmethod
    def _review_action_failure_summary(
        *,
        error_code: str,
        warning_codes: list[str] | None = None,
        identity_assurance_status: str | None = None,
    ) -> str:
        return _review_action_failure_summary_contract(
            error_code=error_code,
            warning_codes=warning_codes,
            identity_assurance_status=identity_assurance_status,
        )[2]

    def _review_action_failure_payload(
        self,
        *,
        error_code: str,
        mutation_enabled: bool,
        event_id: str | None = None,
        action: str | None = None,
        cli_equivalent: str | None = None,
        reviewer_context_requirements: dict[str, Any] | None = None,
        reviewer_enforcement_summary: dict[str, Any] | None = None,
        reviewer_validation_gate_summary: dict[str, Any] | None = None,
        write_route_contract: dict[str, Any] | None = None,
        success_contract: dict[str, Any] | None = None,
        failure_contract: dict[str, Any] | None = None,
        warning_codes: list[str] | None = None,
        warning_details: list[dict[str, Any]] | None = None,
        identity_assurance_status: str | None = None,
        identity_assurance_message: str | None = None,
        detail: str | None = None,
        audit_id: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "ok": False,
            "status": "blocked",
            "error_code": error_code,
            "message": self._review_action_failure_message(error_code),
            "message_key": _review_action_failure_message_key(error_code),
            "mutation_enabled": mutation_enabled,
        }
        if event_id is not None:
            payload["event_id"] = event_id
        if action is not None:
            payload["action"] = action
        if cli_equivalent is not None:
            payload["cli_equivalent"] = cli_equivalent
            payload["cli_equivalent_detail"] = _review_cli_equivalent_detail(cli_equivalent)
        if reviewer_context_requirements is not None:
            payload["reviewer_context_requirements"] = reviewer_context_requirements
        if reviewer_enforcement_summary is not None:
            payload["reviewer_enforcement_summary"] = reviewer_enforcement_summary
        if reviewer_validation_gate_summary is not None:
            payload["reviewer_validation_gate_summary"] = reviewer_validation_gate_summary
        if write_route_contract is not None:
            payload["write_route_contract"] = write_route_contract
        if success_contract is not None:
            payload["success_contract"] = success_contract
        if failure_contract is not None:
            payload["failure_contract"] = failure_contract
        if warning_codes is not None:
            payload["warning_codes"] = warning_codes
        if warning_details is not None:
            payload["warning_details"] = warning_details
        if identity_assurance_status is not None:
            payload["identity_assurance_status"] = identity_assurance_status
        if identity_assurance_message is not None:
            payload["identity_assurance_message"] = identity_assurance_message
        if detail is not None:
            payload["detail"] = detail
        if audit_id is not None:
            payload["audit_id"] = audit_id

        summary_key, summary_params, summary = _review_action_failure_summary_contract(
            error_code=error_code,
            warning_codes=warning_codes,
            identity_assurance_status=identity_assurance_status,
        )
        if summary_key:
            payload["failure_summary"] = summary
            payload["failure_summary_key"] = summary_key
            payload["failure_summary_params"] = summary_params
        if extra:
            payload.update(extra)
        return payload

    @staticmethod
    def _review_action_success_contract(
        *,
        cli_equivalent: str | None = None,
        event_id: str | None = None,
        audit_id: str | None = None,
    ) -> dict[str, Any]:
        follow_up_commands = [
            command
            for command in [
                "chronicle review queue --include-resolved --json" if event_id else "",
                f"chronicle audit show --id {audit_id} --json" if audit_id else "",
                cli_equivalent or "",
            ]
            if command
        ]
        follow_up_command_details = [
            _review_command_detail(command, kind="follow_up") for command in follow_up_commands
        ]
        return {
            "transaction_status": "decision_and_audit_persisted",
            "transaction_status_summary_key": "ui.review_success_contract.transaction_status.decision_and_audit_persisted",
            "transaction_status_summary": "decision and audit persisted",
            "rollback_status": "not_required",
            "rollback_status_summary_key": "ui.review_contract.rollback_status.not_required",
            "rollback_status_summary": "not required",
            "durable_mutation_reported": True,
            "audit_insertion_required": True,
            "durable_success_requirements": [
                "route_gating_passed",
                "reviewer_context_validated",
                "decision_persisted",
                "audit_persisted",
            ],
            "recovery_path": follow_up_commands[0] if follow_up_commands else cli_equivalent or "Use the equivalent chronicle review CLI command for follow-up inspection.",
            "follow_up_commands": follow_up_commands,
            "follow_up_command_details": follow_up_command_details,
        }

    @staticmethod
    def _review_action_preview(
        target_event_id: str,
        capability: dict[str, Any],
        *,
        mutation_enabled: bool = False,
        write_route_contract: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        can_review_now = bool(capability.get("can_review_now", False))
        cli_equivalent = f"chronicle review approve --event {target_event_id}"
        actions = []
        for item in review_action_commands(target_event_id):
            route_action = str(item.get("action", "")).replace("_", "-")
            actions.append(
                {
                    **item,
                    "post_path": (
                        f"/api/review-actions/{quote(target_event_id, safe='')}/{quote(route_action, safe='')}"
                    ),
                    "post_expected_status": (
                        HTTPStatus.OK.value if mutation_enabled else HTTPStatus.FORBIDDEN.value
                    ),
                    "post_expected_error_code": (None if mutation_enabled else "mutation_disabled"),
                }
            )
        failure_contract = ChronicleUIDataService._review_action_failure_contract(
            mutation_enabled=mutation_enabled,
            cli_equivalent=cli_equivalent,
            event_id=target_event_id,
            action="approve",
            error_code="mutation_disabled",
        )
        success_contract = ChronicleUIDataService._review_action_success_contract(
            cli_equivalent=cli_equivalent,
            event_id=target_event_id,
            audit_id=None,
        )
        cli_equivalent_summary_key, cli_equivalent_summary_params, cli_equivalent_summary = (
            _review_action_preview_summary_contract(
                "cli_equivalent",
                cli_equivalent,
            )
        )
        recovery_summary_key, recovery_summary_params, recovery_summary = (
            _review_action_preview_summary_contract(
                "recovery",
                str(failure_contract.get("recovery_path", "")),
            )
        )
        follow_up_summary_key, follow_up_summary_params, follow_up_summary = (
            _review_action_preview_summary_contract(
                "follow_up",
                str((success_contract.get("follow_up_commands") or [""])[0]),
            )
        )
        return {
            "status": "enabled" if mutation_enabled else "preview_only",
            "ui_mutation_enabled": mutation_enabled,
            "can_review_now": can_review_now,
            "message": (
                (
                    "UI mutation is enabled for this local session; review actions still require explicit reviewer context."
                    if can_review_now
                    else "UI mutation is enabled, but boundary warnings still block review until reviewer context aligns."
                )
                if mutation_enabled
                else (
                    "UI mutation is not enabled; use the equivalent CLI command."
                    if can_review_now
                    else "UI mutation is not enabled; boundary warnings still require CLI-led review."
                )
            ),
            "message_key": _review_action_preview_message_key(mutation_enabled, can_review_now),
            "cli_equivalent": cli_equivalent,
            "cli_equivalent_summary": cli_equivalent_summary,
            "cli_equivalent_summary_key": cli_equivalent_summary_key,
            "cli_equivalent_summary_params": cli_equivalent_summary_params,
            "cli_equivalent_detail": _review_cli_equivalent_detail(cli_equivalent),
            "recovery_summary": recovery_summary,
            "recovery_summary_key": recovery_summary_key,
            "recovery_summary_params": recovery_summary_params,
            "follow_up_summary": follow_up_summary,
            "follow_up_summary_key": follow_up_summary_key,
            "follow_up_summary_params": follow_up_summary_params,
            "failure_contract": failure_contract,
            "success_contract": success_contract,
            "write_route_contract": write_route_contract or {},
            "actions": actions,
        }

    @staticmethod
    def _review_cli_parity_summary(
        target_event_id: str,
        available_actions: list[str],
        action_preview: dict[str, Any],
    ) -> dict[str, Any]:
        preview_actions = action_preview.get("actions", [])
        preview_commands = [
            str(item.get("command", ""))
            for item in preview_actions
            if isinstance(item, dict) and item.get("command")
        ]
        canonical_actions = review_action_commands(target_event_id)
        expected_commands = [item["command"] for item in canonical_actions]
        expected_action_ids = [item["action"] for item in canonical_actions]
        queue_commands = [command for command in available_actions if isinstance(command, str)]
        missing_preview_commands = [
            command for command in expected_commands if command not in preview_commands
        ]
        missing_queue_commands = [
            command for command in expected_commands if command not in queue_commands
        ]
        extra_preview_commands = [
            command for command in preview_commands if command not in expected_commands
        ]
        extra_queue_commands = [command for command in queue_commands if command not in expected_commands]
        aligned = (
            not missing_preview_commands
            and not missing_queue_commands
            and not extra_preview_commands
            and not extra_queue_commands
        )
        return {
            "status": "aligned" if aligned else "drift_detected",
            "preview_only": True,
            "expected_actions": expected_action_ids,
            "expected_commands": expected_commands,
            "preview_command_count": len(preview_commands),
            "queue_command_count": len(queue_commands),
            "missing_preview_commands": missing_preview_commands,
            "missing_queue_commands": missing_queue_commands,
            "extra_preview_commands": extra_preview_commands,
            "extra_queue_commands": extra_queue_commands,
            "message": (
                "UI preview commands match the current append-only review CLI contract."
                if aligned
                else "UI preview commands drifted from the append-only review CLI contract."
            ),
            "message_key": _cli_parity_message_key(aligned),
        }

    def detail_payload(self, path: str) -> dict[str, Any] | None:
        parts = [unquote(part) for part in path.strip("/").split("/")]
        if len(parts) == 4 and parts[0] == "api" and parts[1] == "ai-index":
            resource, record_id = parts[2], parts[3]
            if resource == "vector":
                entry = self.vector_index.get_entry(record_id)
                if entry is None:
                    return None
                payload = _dump_model(entry)
                payload["message"] = (
                    "Vector entry retains indexed metadata for this local derived record."
                    if payload.get("metadata")
                    else "Vector entry has no indexed metadata; treat it as a local derived text-only index row."
                )
                payload["message_key"] = _ai_index_vector_detail_message_key(payload)
                counts_key, counts_params = _ai_index_vector_detail_counts_contract(
                    text_length=len(str(payload.get("text", ""))),
                    metadata_count=len(payload.get("metadata", {})),
                )
                payload["counts_summary_key"] = counts_key
                payload["counts_summary_params"] = counts_params
                payload["boundary_note"] = (
                    "Vector entry remains derived, read-only, and non-authoritative over primary Chronicle records."
                )
                payload["boundary_note_key"] = "ui.ai_index_vector_detail.note.read_only_derived"
                return {"record": payload}
            if resource == "graph-nodes":
                node = self.graph_index.get_node(record_id)
                if node is None:
                    return None
                payload = _dump_model(node)
                neighbors = self.graph_index.neighbors(node_id=record_id)
                payload["neighbors"] = neighbors.model_dump(mode="json")
                payload["outgoing_neighbor_count"] = len(neighbors.outgoing)
                payload["incoming_neighbor_count"] = len(neighbors.incoming)
                payload["message"] = (
                    "Graph node detail includes local derived neighbor relationships for inspection."
                    if payload["outgoing_neighbor_count"] + payload["incoming_neighbor_count"] > 0
                    else "Graph node detail has no derived neighbor relationships yet."
                )
                payload["message_key"] = _ai_index_graph_node_detail_message_key(payload)
                counts_key, counts_params = _ai_index_graph_node_detail_counts_contract(
                    label_count=len(payload.get("labels", [])),
                    property_count=len(payload.get("properties", {})),
                    outgoing_neighbor_count=payload["outgoing_neighbor_count"],
                    incoming_neighbor_count=payload["incoming_neighbor_count"],
                )
                payload["counts_summary_key"] = counts_key
                payload["counts_summary_params"] = counts_params
                payload["boundary_note"] = (
                    "Graph node detail remains derived, read-only, and non-authoritative over primary Chronicle records."
                )
                payload["boundary_note_key"] = "ui.ai_index_graph_node_detail.note.read_only_derived"
                return {"record": payload}
            return None

        if len(parts) == 3 and parts[0] == "api" and parts[1] == "runtime-records":
            self.chronicle.require_initialized()
            event = next(
                (item for item in self.chronicle.jsonl.read_all() if item.event_id == parts[2]),
                None,
            )
            if event is None:
                return None
            record = _dump_model(event)
            payload = record["payload"]
            if (
                "runtime_summary" not in payload
                and "runtime_execution" not in payload
                and "runtime_retrieval_plan" not in payload
                and "runtime_invocation_plan" not in payload
            ):
                return None
            preview = self.runtime.record_preview(event)
            preview_payload = preview.model_dump(mode="json")
            title_key, title_params = _runtime_preview_title_contract(preview_payload)
            if title_key:
                preview_payload["title_key"] = title_key
            if title_params:
                preview_payload["title_params"] = title_params
            record["runtime_record_kind"] = preview.record_kind
            record["runtime_record_preview"] = preview_payload
            record["suggested_cli_family"] = preview.suggested_cli_family
            record["related_links"] = self.runtime_related_links(parts[2], payload)
            record["response_metadata_summary"] = self._runtime_response_metadata_summary(payload=payload)
            review_row = self._review_queue_row(parts[2])
            if review_row is not None:
                boundary = self.ui_boundary()["ui_boundary"]
                record["auth_boundary_notice"] = review_row.get("auth_boundary_notice")
                record["mutation_enablement"] = self.mutation_readiness_summary()
                record["reviewer_enforcement_summary"] = boundary.get("reviewer_enforcement_summary", {})
                record["reviewer_validation_gate_summary"] = boundary.get(
                    "reviewer_validation_gate_summary", {}
                )
                record["auth_readiness_status"] = str(
                    review_row.get("auth_boundary_notice", {}).get("status", "")
                )
                record["reviewer_boundary_drilldown_summary"] = _reviewer_boundary_drilldown_summary(
                    dataset_key="runtime_records",
                    list_path="/api/runtime-records",
                    detail_path=f"/api/runtime-records/{parts[2]}",
                    enforcement_status=str(
                        boundary.get("reviewer_enforcement_summary", {}).get("status", "")
                    ),
                    gate_status=str(
                        boundary.get("reviewer_validation_gate_summary", {}).get("status", "")
                    ),
                )
            if "runtime_retrieval_plan" in payload:
                plan = RuntimeRetrievalPlan.model_validate(payload["runtime_retrieval_plan"])
                handoff_payload = self.runtime.retrieval_handoff(plan).model_dump(mode="json")
                handoff_payload["message"] = (
                    "Retrieval handoff summarizes dry-run record hits for downstream local package review."
                    if handoff_payload.get("referenced_record_ids")
                    else "Retrieval handoff has no referenced records; downstream package review remains advisory."
                )
                handoff_payload["message_key"] = _retrieval_handoff_message_key(handoff_payload)
                counts_key, counts_params = _retrieval_handoff_counts_contract(handoff_payload)
                handoff_payload["hit_counts_summary_key"] = counts_key
                handoff_payload["hit_counts_summary_params"] = counts_params
                handoff_payload["downstream_command_details"] = [
                    _retrieval_handoff_command_detail(command)
                    for command in handoff_payload.get("downstream_commands", [])
                    if isinstance(command, str) and command
                ]
                record["retrieval_handoff"] = handoff_payload
                record["package_handoff_preview"] = self.runtime_package_handoff(plan)
            if "runtime_invocation_plan" in payload:
                plan = RuntimeInvocationPlan.model_validate(payload["runtime_invocation_plan"])
                plan_payload = plan.model_dump(mode="json")
                plan_payload["message"] = (
                    "Invocation plan is ready for explicit local execution."
                    if plan_payload.get("invocation_ready")
                    else "Invocation plan remains blocked until local runtime boundary requirements align."
                )
                plan_payload["message_key"] = _invocation_plan_message_key(plan_payload)
                provider_summary_key, provider_summary_params = (
                    _invocation_plan_provider_summary_contract(plan_payload)
                )
                plan_payload["provider_summary_key"] = provider_summary_key
                plan_payload["provider_summary_params"] = provider_summary_params
                plan_payload["invocation_ready_summary_key"] = _boolean_summary_payload(
                    bool(plan_payload.get("invocation_ready"))
                )[0]
                plan_payload["invocation_ready_summary"] = _boolean_summary_payload(
                    bool(plan_payload.get("invocation_ready"))
                )[1]
                plan_payload["would_use_network_summary_key"] = _boolean_summary_payload(
                    bool(plan_payload.get("would_use_network"))
                )[0]
                plan_payload["would_use_network_summary"] = _boolean_summary_payload(
                    bool(plan_payload.get("would_use_network"))
                )[1]
                plan_payload["network_allowed_by_contract_summary_key"] = _boolean_summary_payload(
                    bool(plan_payload.get("network_allowed_by_contract"))
                )[0]
                plan_payload["network_allowed_by_contract_summary"] = _boolean_summary_payload(
                    bool(plan_payload.get("network_allowed_by_contract"))
                )[1]
                plan_payload["downstream_command_details"] = [
                    _invocation_plan_command_detail(command)
                    for command in plan_payload.get("downstream_commands", [])
                    if isinstance(command, str) and command
                ]
                record["invocation_plan"] = plan_payload
            return {"record": record}

        if len(parts) == 3 and parts[0] == "api" and parts[1] == "review-queue":
            boundary = self.ui_boundary()["ui_boundary"]
            for row in self.review_queue()["review_queue"]:
                if row.get("target_event_id") == parts[2]:
                    row["history"] = [
                        self._history_row(item, boundary)
                        for item in self.review.history(event_id=parts[2])
                    ]
                    row["package_readiness"] = self.review_package_readiness(parts[2])
                    row["related_links"] = self.review_related_links(parts[2])
                    row["action_preview"] = self._review_action_preview(
                        parts[2],
                        row.get("review_capability", {}),
                        mutation_enabled=bool(boundary.get("mutation_enabled", False)),
                        write_route_contract=boundary.get("write_route_contract", {}),
                    )
                    row["cli_parity"] = self._review_cli_parity_summary(
                        parts[2],
                        row.get("available_actions", []),
                        row["action_preview"],
                    )
                    row["auth_boundary_notice"] = self._auth_boundary_notice(
                        boundary,
                        row.get("review_capability"),
                        row.get("latest_identity_assurance"),
                    )
                    row["mutation_enablement"] = self.mutation_readiness_summary()
                    row["reviewer_enforcement_summary"] = boundary.get("reviewer_enforcement_summary", {})
                    row["reviewer_validation_gate_summary"] = boundary.get(
                        "reviewer_validation_gate_summary", {}
                    )
                    row["reviewer_boundary_drilldown_summary"] = _reviewer_boundary_drilldown_summary(
                        dataset_key="review_queue",
                        list_path="/api/review-queue",
                        detail_path=f"/api/review-queue/{parts[2]}",
                        enforcement_status=str(
                            boundary.get("reviewer_enforcement_summary", {}).get("status", "")
                        ),
                        gate_status=str(
                            boundary.get("reviewer_validation_gate_summary", {}).get("status", "")
                        ),
                    )
                    row["ui_mutation_enabled"] = bool(boundary.get("mutation_enabled", False))
                    row["review_preview_only"] = not bool(boundary.get("mutation_enabled", False))
                    return {"record": row}
            return None

        if len(parts) == 3 and parts[0] == "api" and parts[1] == "summary-jobs":
            job = self.summary_jobs.get(parts[2]).model_dump(mode="json")
            job["summary_source_count"] = len(job.get("source_refs", []))
            job["runtime_provider_kind"] = str(job.get("provenance", {}).get("runtime", {}).get("provider_kind", ""))
            job["response_metadata_summary"] = self._response_metadata_summary(
                response_metadata=job.get("provenance", {}).get("response_metadata", {}),
                response_keys=job.get("provenance", {}).get("response_keys", []),
            )
            job["suggested_cli_family"] = "chronicle summary show --id"
            job["identity_assurance_status"] = "unknown"
            event_id = str(job.get("event_id", ""))
            if event_id.startswith("evt_"):
                review_row = self._review_queue_row(event_id)
                if review_row is not None:
                    boundary = self.ui_boundary()["ui_boundary"]
                    job["review_target_event_id"] = event_id
                    job["review_kind"] = review_row.get("review_kind")
                    job["review_capability"] = review_row.get("review_capability")
                    if review_row.get("latest_identity_assurance") is not None:
                        job["latest_identity_assurance"] = review_row.get("latest_identity_assurance")
                        job["identity_assurance_status"] = str(
                            review_row.get("latest_identity_assurance", {}).get("status", "")
                        )
                    if review_row.get("latest_reviewer_identity") is not None:
                        job["latest_reviewer_identity"] = review_row.get("latest_reviewer_identity")
                    job["package_readiness_summary"] = review_row.get("package_readiness_summary")
                    job["package_readiness"] = self.review_package_readiness(event_id)
                    job["action_preview"] = self._review_action_preview(
                        event_id,
                        job["review_capability"],
                        mutation_enabled=bool(boundary.get("mutation_enabled", False)),
                        write_route_contract=boundary.get("write_route_contract", {}),
                    )
                    job["cli_parity"] = self._review_cli_parity_summary(
                        event_id,
                        review_row.get("available_actions", []),
                        job["action_preview"],
                    )
                    job["auth_boundary_notice"] = self._auth_boundary_notice(
                        boundary,
                        job.get("review_capability"),
                        job.get("latest_identity_assurance"),
                    )
                    job["mutation_enablement"] = self.mutation_readiness_summary()
                    job["reviewer_enforcement_summary"] = boundary.get("reviewer_enforcement_summary", {})
                    job["reviewer_validation_gate_summary"] = boundary.get(
                        "reviewer_validation_gate_summary", {}
                    )
                    job["reviewer_boundary_drilldown_summary"] = _reviewer_boundary_drilldown_summary(
                        dataset_key="summary_jobs",
                        list_path="/api/summary-jobs",
                        detail_path=f"/api/summary-jobs/{parts[2]}",
                        enforcement_status=str(
                            boundary.get("reviewer_enforcement_summary", {}).get("status", "")
                        ),
                        gate_status=str(
                            boundary.get("reviewer_validation_gate_summary", {}).get("status", "")
                        ),
                    )
                    job["history"] = [
                        self._history_row(item, boundary)
                        for item in self.review.history(event_id=event_id)
                    ]
                    job["ui_mutation_enabled"] = bool(boundary.get("mutation_enabled", False))
                    job["review_preview_only"] = not bool(boundary.get("mutation_enabled", False))
            job["related_links"] = self.summary_job_related_links(parts[2], job)
            return {"record": job}

        if len(parts) != 3 or parts[0] != "api":
            return None
        resource, record_id = parts[1], parts[2]
        self.chronicle.require_initialized()
        if resource == "events":
            record = _find_by_attr(self.chronicle.jsonl.read_all(), "event_id", record_id)
        elif resource == "contexts":
            contexts = self.chronicle.index.load_contexts()
            record = _dump_model(contexts[record_id]) if record_id in contexts else None
            if record is not None:
                proposals = self.proposals.proposals_for_target(target_kind="context", target_id=record_id)
                record["proposals"] = proposals
                record["proposal_summary"] = {
                    "count": len(proposals),
                    "pending_count": sum(
                        1 for proposal in proposals if proposal.get("review_status") == "needs_review"
                    ),
                    "boundary_note": "Proposal records are append-only and reviewable; direct in-place UI editing remains unavailable.",
                }
        elif resource == "artifacts":
            artifacts, versions = self.chronicle.index.load_artifacts()
            record = _dump_model(artifacts[record_id]) if record_id in artifacts else None
            if record is not None:
                record["versions"] = [_dump_model(version) for version in versions.get(record_id, [])]
                proposals = self.proposals.proposals_for_target(target_kind="artifact", target_id=record_id)
                record["proposals"] = proposals
                record["proposal_summary"] = {
                    "count": len(proposals),
                    "pending_count": sum(
                        1 for proposal in proposals if proposal.get("review_status") == "needs_review"
                    ),
                    "boundary_note": "Proposal records are append-only and reviewable; direct in-place UI editing remains unavailable.",
                }
        elif resource == "decisions":
            decisions = self.chronicle.index.load_decisions()
            record = _dump_model(decisions[record_id]) if record_id in decisions else None
        elif resource == "rde":
            records = self.chronicle.index.load_rde_records()
            record = _dump_model(records[record_id]) if record_id in records else None
        elif resource == "boundary":
            rules = self.chronicle.index.load_boundary_rules()
            record = _dump_model(rules[record_id]) if record_id in rules else None
        elif resource == "audit":
            record = _find_by_attr(self.audit.list_events(), "audit_id", record_id)
        elif resource == "lifecycle":
            record = _find_by_attr(self.lifecycle.list_events(), "lifecycle_id", record_id)
        else:
            return None
        return {"record": record} if record is not None else None

    def api_payload(self, path: str) -> dict[str, Any] | None:
        routes = {
            "/api/overview": self.overview,
            "/api/events": self.events,
            "/api/contexts": self.contexts,
            "/api/artifacts": self.artifacts,
            "/api/decisions": self.decisions,
            "/api/rde": self.rde_records,
            "/api/boundary": self.boundary_rules,
            "/api/audit": self.audit_events,
            "/api/lifecycle": self.lifecycle_markers,
            "/api/runtime-records": self.runtime_records,
            "/api/review-queue": self.review_queue,
            "/api/summary-jobs": self.summary_jobs_list,
            "/api/proposals": self.proposal_records,
            "/api/ui-boundary": self.ui_boundary,
            "/api/runtime-config": self.runtime_config_state,
            "/api/package-review": lambda: {"package_review": self.package_review_snapshot()},
            "/api/graph-summary": lambda: {"graph_summary": self.graph_summary()},
            "/api/ai-index-status": self.ai_index_status,
            "/api/ai-index-vector": self.ai_index_vector_entries,
            "/api/ai-index-graph-nodes": self.ai_index_graph_nodes,
            "/api/ai-index-graph-edges": self.ai_index_graph_edges,
        }
        handler = routes.get(path)
        if handler:
            return handler()
        return self.detail_payload(path)

    def review_action_blocked_response(self, path: str) -> tuple[HTTPStatus, dict[str, Any]] | None:
        parts = [unquote(part) for part in path.strip("/").split("/")]
        if len(parts) != 4 or parts[0] != "api" or parts[1] != "review-actions":
            return None
        event_id, action = parts[2], parts[3]
        if action not in {"approve", "reject", "request-changes"}:
            return None
        boundary = self.ui_boundary()["ui_boundary"]
        cli_equivalent = f"chronicle review {action} --event {event_id}"
        return (
            HTTPStatus.FORBIDDEN,
            self._review_action_failure_payload(
                error_code="mutation_disabled",
                mutation_enabled=False,
                event_id=event_id,
                action=action,
                cli_equivalent=cli_equivalent,
                reviewer_context_requirements=boundary.get("reviewer_context_requirements", {}),
                reviewer_enforcement_summary=boundary.get("reviewer_enforcement_summary", {}),
                reviewer_validation_gate_summary=boundary.get("reviewer_validation_gate_summary", {}),
                write_route_contract=boundary.get("write_route_contract", {}),
                success_contract=self._review_action_success_contract(
                    cli_equivalent=cli_equivalent,
                    event_id=event_id,
                ),
                failure_contract=self._review_action_failure_contract(
                    mutation_enabled=False,
                    cli_equivalent=cli_equivalent,
                    event_id=event_id,
                    action=action,
                    error_code="mutation_disabled",
                ),
            ),
        )

    def review_action_response(
        self,
        path: str,
        payload: dict[str, Any],
    ) -> tuple[HTTPStatus, dict[str, Any]] | None:
        parts = [unquote(part) for part in path.strip("/").split("/")]
        if len(parts) != 4 or parts[0] != "api" or parts[1] != "review-actions":
            return None
        event_id, action = parts[2], parts[3]
        action_map = {
            "approve": self.review.approve,
            "reject": self.review.reject,
            "request-changes": self.review.request_changes,
        }
        review_action = action_map.get(action)
        if review_action is None:
            return None

        boundary = self.ui_boundary()["ui_boundary"]
        reviewer_context_requirements = boundary.get("reviewer_context_requirements", {})
        reviewer_enforcement_summary = boundary.get("reviewer_enforcement_summary", {})
        reviewer_validation_gate_summary = boundary.get("reviewer_validation_gate_summary", {})
        write_route_contract = boundary.get("write_route_contract", {})
        cli_equivalent = f"chronicle review {action} --event {event_id}"
        success_contract = self._review_action_success_contract(
            cli_equivalent=cli_equivalent,
            event_id=event_id,
        )
        if not boundary.get("mutation_enabled", False):
            return self.review_action_blocked_response(path)

        reviewer_label = str(payload.get("reviewer_label", "")).strip()
        reviewer_kind_value = str(payload.get("reviewer_kind", ReviewerIdentityKind.USER_DECLARED.value))
        session_label = payload.get("session_label")
        session_label_value = str(session_label).strip() if isinstance(session_label, str) else None
        note = payload.get("note")
        note_value = str(note).strip() if isinstance(note, str) and str(note).strip() else None
        ui_intent = str(payload.get("ui_intent", "")).strip()

        if not reviewer_label:
            return (
                HTTPStatus.BAD_REQUEST,
                self._review_action_failure_payload(
                    error_code="reviewer_label_required",
                    mutation_enabled=True,
                    event_id=event_id,
                    action=action,
                    reviewer_context_requirements=reviewer_context_requirements,
                    reviewer_enforcement_summary=reviewer_enforcement_summary,
                    reviewer_validation_gate_summary=reviewer_validation_gate_summary,
                    write_route_contract=write_route_contract,
                    success_contract=success_contract,
                    failure_contract=self._review_action_failure_contract(
                        mutation_enabled=True,
                        cli_equivalent=cli_equivalent,
                        event_id=event_id,
                        action=action,
                        error_code="reviewer_label_required",
                    ),
                ),
            )
        if not REVIEWER_LABEL_PATTERN.fullmatch(reviewer_label):
            return (
                HTTPStatus.BAD_REQUEST,
                self._review_action_failure_payload(
                    error_code="invalid_reviewer_label",
                    mutation_enabled=True,
                    event_id=event_id,
                    action=action,
                    reviewer_context_requirements=reviewer_context_requirements,
                    reviewer_enforcement_summary=reviewer_enforcement_summary,
                    reviewer_validation_gate_summary=reviewer_validation_gate_summary,
                    write_route_contract=write_route_contract,
                    success_contract=success_contract,
                    failure_contract=self._review_action_failure_contract(
                        mutation_enabled=True,
                        cli_equivalent=cli_equivalent,
                        event_id=event_id,
                        action=action,
                        error_code="invalid_reviewer_label",
                    ),
                ),
            )
        if boundary.get("session_gating", False) and not session_label_value:
            return (
                HTTPStatus.BAD_REQUEST,
                self._review_action_failure_payload(
                    error_code="session_label_required",
                    mutation_enabled=True,
                    event_id=event_id,
                    action=action,
                    reviewer_context_requirements=reviewer_context_requirements,
                    reviewer_enforcement_summary=reviewer_enforcement_summary,
                    reviewer_validation_gate_summary=reviewer_validation_gate_summary,
                    write_route_contract=write_route_contract,
                    success_contract=success_contract,
                    failure_contract=self._review_action_failure_contract(
                        mutation_enabled=True,
                        cli_equivalent=cli_equivalent,
                        event_id=event_id,
                        action=action,
                        error_code="session_label_required",
                    ),
                ),
            )
        if session_label_value and not SESSION_LABEL_PATTERN.fullmatch(session_label_value):
            return (
                HTTPStatus.BAD_REQUEST,
                self._review_action_failure_payload(
                    error_code="invalid_session_label",
                    mutation_enabled=True,
                    event_id=event_id,
                    action=action,
                    reviewer_context_requirements=reviewer_context_requirements,
                    reviewer_enforcement_summary=reviewer_enforcement_summary,
                    reviewer_validation_gate_summary=reviewer_validation_gate_summary,
                    write_route_contract=write_route_contract,
                    success_contract=success_contract,
                    failure_contract=self._review_action_failure_contract(
                        mutation_enabled=True,
                        cli_equivalent=cli_equivalent,
                        event_id=event_id,
                        action=action,
                        error_code="invalid_session_label",
                    ),
                ),
            )
        if ui_intent != action:
            return (
                HTTPStatus.BAD_REQUEST,
                self._review_action_failure_payload(
                    error_code="ui_intent_mismatch",
                    mutation_enabled=True,
                    event_id=event_id,
                    action=action,
                    reviewer_context_requirements=reviewer_context_requirements,
                    reviewer_enforcement_summary=reviewer_enforcement_summary,
                    reviewer_validation_gate_summary=reviewer_validation_gate_summary,
                    write_route_contract=write_route_contract,
                    success_contract=success_contract,
                    failure_contract=self._review_action_failure_contract(
                        mutation_enabled=True,
                        cli_equivalent=cli_equivalent,
                        event_id=event_id,
                        action=action,
                        error_code="ui_intent_mismatch",
                    ),
                ),
            )
        try:
            reviewer_kind = ReviewerIdentityKind(reviewer_kind_value)
        except ValueError:
            return (
                HTTPStatus.BAD_REQUEST,
                self._review_action_failure_payload(
                    error_code="invalid_reviewer_kind",
                    mutation_enabled=True,
                    event_id=event_id,
                    action=action,
                    reviewer_context_requirements=reviewer_context_requirements,
                    reviewer_enforcement_summary=reviewer_enforcement_summary,
                    reviewer_validation_gate_summary=reviewer_validation_gate_summary,
                    write_route_contract=write_route_contract,
                    success_contract=success_contract,
                    failure_contract=self._review_action_failure_contract(
                        mutation_enabled=True,
                        cli_equivalent=cli_equivalent,
                        event_id=event_id,
                        action=action,
                        error_code="invalid_reviewer_kind",
                    ),
                ),
            )

        reviewer_identity = ReviewerIdentity(
            label=reviewer_label,
            kind=reviewer_kind,
            auth_mode="loopback_local",
            session_label=session_label_value,
        )
        capability = self._review_capability(
            pending=True,
            boundary=boundary,
            identity=reviewer_identity,
        )
        assurance = self._identity_assurance(reviewer_identity, boundary)
        if capability.get("can_review_now") is not True or assurance.get("status") != "boundary_aligned":
            return (
                HTTPStatus.FORBIDDEN,
                self._review_action_failure_payload(
                    error_code="authorization_failed",
                    mutation_enabled=True,
                    event_id=event_id,
                    action=action,
                    cli_equivalent=cli_equivalent,
                    reviewer_context_requirements=reviewer_context_requirements,
                    reviewer_enforcement_summary=reviewer_enforcement_summary,
                    reviewer_validation_gate_summary=reviewer_validation_gate_summary,
                    write_route_contract=write_route_contract,
                    success_contract=success_contract,
                    failure_contract=self._review_action_failure_contract(
                        mutation_enabled=True,
                        cli_equivalent=cli_equivalent,
                        event_id=event_id,
                        action=action,
                        error_code="authorization_failed",
                    ),
                    warning_codes=capability.get("warnings", []),
                    warning_details=capability.get("warning_details", []),
                    identity_assurance_status=assurance.get("status"),
                    identity_assurance_message=assurance.get("message"),
                ),
            )

        review_row = self._review_queue_row_including_resolved(event_id)
        if review_row is None:
            return (
                HTTPStatus.NOT_FOUND,
                self._review_action_failure_payload(
                    error_code="review_target_not_found",
                    mutation_enabled=True,
                    event_id=event_id,
                    action=action,
                    reviewer_context_requirements=reviewer_context_requirements,
                    reviewer_enforcement_summary=reviewer_enforcement_summary,
                    reviewer_validation_gate_summary=reviewer_validation_gate_summary,
                    write_route_contract=write_route_contract,
                    success_contract=success_contract,
                    failure_contract=self._review_action_failure_contract(
                        mutation_enabled=True,
                        cli_equivalent=cli_equivalent,
                        event_id=event_id,
                        action=action,
                        error_code="review_target_not_found",
                    ),
                ),
            )
        if review_row.get("pending") is not True:
            return (
                HTTPStatus.CONFLICT,
                self._review_action_failure_payload(
                    error_code="review_not_pending",
                    mutation_enabled=True,
                    event_id=event_id,
                    action=action,
                    cli_equivalent=cli_equivalent,
                    reviewer_context_requirements=reviewer_context_requirements,
                    reviewer_enforcement_summary=reviewer_enforcement_summary,
                    reviewer_validation_gate_summary=reviewer_validation_gate_summary,
                    write_route_contract=write_route_contract,
                    success_contract=success_contract,
                    failure_contract=self._review_action_failure_contract(
                        mutation_enabled=True,
                        cli_equivalent=cli_equivalent,
                        event_id=event_id,
                        action=action,
                        error_code="review_not_pending",
                    ),
                ),
            )

        try:
            result = review_action(
                event_id=event_id,
                reviewer=reviewer_label,
                reviewer_kind=reviewer_kind,
                session_label=session_label_value,
                note=note_value,
            )
        except ReviewAuditInsertionError as exc:
            return (
                HTTPStatus.INTERNAL_SERVER_ERROR,
                self._review_action_failure_payload(
                    error_code="audit_insertion_failed",
                    mutation_enabled=True,
                    event_id=event_id,
                    action=action,
                    cli_equivalent=cli_equivalent,
                    reviewer_context_requirements=reviewer_context_requirements,
                    reviewer_enforcement_summary=reviewer_enforcement_summary,
                    reviewer_validation_gate_summary=reviewer_validation_gate_summary,
                    write_route_contract=write_route_contract,
                    success_contract=success_contract,
                    failure_contract=self._review_action_failure_contract(
                        mutation_enabled=True,
                        cli_equivalent=cli_equivalent,
                        event_id=event_id,
                        action=action,
                        error_code="audit_insertion_failed",
                    ),
                    detail=exc.hint,
                ),
            )
        except ReviewDecisionPersistenceError as exc:
            return (
                HTTPStatus.INTERNAL_SERVER_ERROR,
                self._review_action_failure_payload(
                    error_code="decision_persistence_failed",
                    mutation_enabled=True,
                    event_id=event_id,
                    action=action,
                    cli_equivalent=cli_equivalent,
                    reviewer_context_requirements=reviewer_context_requirements,
                    reviewer_enforcement_summary=reviewer_enforcement_summary,
                    reviewer_validation_gate_summary=reviewer_validation_gate_summary,
                    write_route_contract=write_route_contract,
                    success_contract=success_contract,
                    failure_contract=self._review_action_failure_contract(
                        mutation_enabled=True,
                        cli_equivalent=cli_equivalent,
                        event_id=event_id,
                        action=action,
                        error_code="decision_persistence_failed",
                        audit_id=exc.audit_id,
                    ),
                    detail=exc.hint,
                    audit_id=exc.audit_id,
                ),
            )
        return (
            HTTPStatus.OK,
            {
                "ok": True,
                "status": "applied",
                "event_id": event_id,
                "action": action,
                "audit_id": result.audit_id,
                "decision_event_id": result.review_event_id,
                "cli_equivalent": cli_equivalent,
                "mutation_enabled": True,
                "reviewer_identity": result.reviewer_identity.model_dump(mode="json"),
                "reviewer_context_requirements": reviewer_context_requirements,
                "reviewer_enforcement_summary": reviewer_enforcement_summary,
                "reviewer_validation_gate_summary": reviewer_validation_gate_summary,
                "write_route_contract": write_route_contract,
                "success_contract": self._review_action_success_contract(
                    cli_equivalent=cli_equivalent,
                    event_id=event_id,
                    audit_id=result.audit_id,
                ),
            },
        )

    def html_shell(self) -> str:
        metadata = self.chronicle.require_initialized()
        title = html.escape(metadata.title)
        root = html.escape(str(self.root.resolve()))
        review_warning_labels_json = json.dumps(REVIEW_WARNING_LABELS, ensure_ascii=False)
        ui_i18n_catalog_json = json.dumps(UI_I18N_CATALOG, ensure_ascii=False)
        mutation_token_json = json.dumps(self.mutation_session_token, ensure_ascii=False)
        mutation_session_id_json = json.dumps(self.mutation_session_id, ensure_ascii=False)
        return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Chronicle Stack ローカルUI — {title}</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; max-width: 1280px; margin: 0 auto; padding: 20px; color: #1f2937; background: #ffffff; }}
button {{ margin: 3px; padding: 6px 9px; cursor: pointer; }}
select, input {{ margin: 3px; padding: 6px 8px; }}
nav {{ display: flex; flex-wrap: wrap; gap: 4px; margin: 14px 0 16px; padding-bottom: 4px; }}
.shell-grid {{ display: grid; grid-template-columns: minmax(0, 1.25fr) minmax(320px, 0.95fr); gap: 16px; align-items: start; }}
.panel {{ border: 1px solid #e5e7eb; border-radius: 10px; padding: 14px; margin: 12px 0; background: #ffffff; overflow: auto; box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04); }}
.panel > :first-child {{ margin-top: 0; }}
#view, #detail {{ min-width: 0; }}
#detail {{ position: sticky; top: 16px; max-height: calc(100vh - 32px); }}
.warning {{ background: #fefce8; border-left: 4px solid #eab308; padding: 10px 12px; }}
.notice {{ background: #eff6ff; border-left: 4px solid #3b82f6; padding: 10px 12px; margin: 10px 0; }}
.notice-section {{ margin-top: 12px; padding-top: 10px; border-top: 1px solid #bfdbfe; }}
.notice-section:first-of-type {{ margin-top: 0; padding-top: 0; border-top: none; }}
.notice-section h4 {{ margin: 0 0 8px; font-size: 0.95rem; color: #1d4ed8; }}
.fold-section {{ margin: 12px 0 0; }}
.fold-section summary {{ cursor: pointer; font-weight: 600; color: #1f2937; }}
.fold-section[open] summary {{ margin-bottom: 8px; }}
.badge {{ display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 0.85em; margin-right: 6px; }}
.badge-warning {{ background: #fef3c7; color: #92400e; }}
.badge-ready {{ background: #dcfce7; color: #166534; }}
.badge-neutral {{ background: #e5e7eb; color: #374151; }}
.fact-line {{ display: grid; grid-template-columns: minmax(132px, 220px) minmax(0, 1fr); gap: 8px 12px; align-items: start; margin: 8px 0; }}
.fact-label {{ font-weight: 600; color: #374151; }}
.fact-value {{ min-width: 0; overflow-wrap: anywhere; }}
.fact-code {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.9em; }}
.cell-title {{ font-weight: 600; color: #111827; }}
.cell-meta {{ color: #4b5563; font-size: 0.92em; }}
.cell-stack > * + * {{ margin-top: 4px; }}
.cell-details {{ margin-top: 6px; }}
.cell-details summary {{ cursor: pointer; color: #1f2937; font-size: 0.9em; }}
.cell-details[open] summary {{ margin-bottom: 6px; }}
.cell-details-body > * + * {{ margin-top: 4px; }}
.cell-actions {{ display: flex; flex-wrap: wrap; gap: 4px; }}
.cell-code {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.85em; }}
.json-block {{ margin: 12px 0 0; border-top: 1px solid #e5e7eb; padding-top: 12px; }}
.json-block summary {{ cursor: pointer; font-weight: 600; color: #111827; }}
.json-block[open] summary {{ margin-bottom: 10px; }}
pre {{ white-space: pre-wrap; word-break: break-word; background: #f9fafb; padding: 12px; border-radius: 8px; overflow-x: auto; }}
table {{ width: 100%; border-collapse: collapse; display: block; overflow-x: auto; }}
thead, tbody {{ width: 100%; }}
th, td {{ padding: 6px; border-bottom: 1px solid #e5e7eb; vertical-align: top; }}
th {{ position: sticky; top: 0; background: #ffffff; }}
.id {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.85em; }}
@media (max-width: 980px) {{
  .shell-grid {{ grid-template-columns: 1fr; }}
  #detail {{ position: static; max-height: none; }}
}}
</style>
</head>
<body>
<div class="notice">
  <label for="locale-select" id="locale-label">表示言語</label>
  <select id="locale-select">
    <option value="ja">日本語</option>
    <option value="en">English</option>
    <option value="zh-CN">简体中文</option>
  </select>
</div>
<h1 id="shell-title">Chronicle Stack ローカルUI</h1>
<p><strong>{title}</strong></p>
<p><span id="shell-root-label">ルート</span>: <span class="id">{root}</span></p>
<div class="warning" id="shell-warning">
  <p><strong id="shell-warning-title">読み取り専用の前景ローカルUIです。</strong> <span id="shell-warning-body">このUIはローカルの Chronicle ファイルを読み取りますが、レコードは書き込みません。</span></p>
  <p id="shell-boundary-body">daemon なし、自動起動なし、外部 model API なし、GraphRAG runtime なし、vector DB なし、graph DB なし。UI の可視化は correctness proof ではありません。</p>
</div>
<nav>
  <button data-endpoint="/api/overview">概要</button>
  <button data-endpoint="/api/events">イベント</button>
  <button data-endpoint="/api/contexts">コンテキスト</button>
  <button data-endpoint="/api/artifacts">成果物</button>
  <button data-endpoint="/api/decisions">判断</button>
  <button data-endpoint="/api/rde">RDE</button>
  <button data-endpoint="/api/boundary">境界</button>
  <button data-endpoint="/api/audit">監査</button>
  <button data-endpoint="/api/lifecycle">ライフサイクル</button>
  <button data-endpoint="/api/runtime-records">Runtime Records</button>
  <button data-endpoint="/api/review-queue">Review Queue</button>
  <button data-endpoint="/api/summary-jobs">Summary Jobs</button>
  <button data-endpoint="/api/proposals">Proposals</button>
  <button data-endpoint="/api/ui-boundary">UI Boundary</button>
  <button data-endpoint="/api/runtime-config">Runtime Config</button>
  <button data-endpoint="/api/package-review">Package Review</button>
  <button data-endpoint="/api/graph-summary">Graph Summary</button>
  <button data-endpoint="/api/ai-index-status">AI Index Status</button>
  <button data-endpoint="/api/ai-index-vector">AI Index Vector</button>
  <button data-endpoint="/api/ai-index-graph-nodes">AI Index Graph Nodes</button>
  <button data-endpoint="/api/ai-index-graph-edges">AI Index Graph Edges</button>
</nav>
<div class="shell-grid">
  <section id="view" class="panel"><p id="shell-loading-overview">概要を読み込み中...</p></section>
  <section id="detail" class="panel"><p id="shell-select-json">テーブル行の JSON を選択して単一レコードを確認します。</p></section>
</div>
<script>
const idFields = ['event_id', 'context_id', 'artifact_id', 'decision_id', 'rde_record_id', 'rule_id', 'audit_id', 'lifecycle_id', 'record_id', 'node_id', 'summary_job_id'];
const reviewWarningLabels = {review_warning_labels_json};
const uiLabelKeys = {{
  'Action': 'ui.label.action',
  'Event': 'ui.label.event',
  'Error code': 'ui.label.error_code',
  'Identity assurance': 'ui.label.identity_assurance',
  'Identity assurance message': 'ui.label.identity_assurance_message',
  'CLI equivalent': 'ui.label.cli_equivalent',
  'Failure summary': 'ui.label.failure_summary',
  'Warnings': 'ui.label.warnings',
  'Recovery path': 'ui.label.recovery_path',
  'Rollback status': 'ui.label.rollback_status',
  'Transaction status': 'ui.label.transaction_status',
  'Durable mutation on failure': 'ui.label.durable_mutation_on_failure',
  'Possible errors': 'ui.label.possible_errors',
  'Recovery commands': 'ui.label.recovery_commands',
  'Follow-up commands': 'ui.label.follow_up_commands',
  'Kind': 'ui.label.kind',
  'Source counts': 'ui.label.source_counts',
  'Referenced IDs': 'ui.label.referenced_ids',
  'Query': 'ui.label.query',
  'Hit counts': 'ui.label.hit_counts',
  'Eligible contexts': 'ui.label.eligible_contexts',
  'Skipped records': 'ui.label.skipped_records',
  'Package review status': 'ui.label.package_review_status',
  'Package warnings': 'ui.label.package_warnings',
  'Manifest refs': 'ui.label.manifest_refs',
  'Provider': 'ui.label.provider',
  'Model': 'ui.label.model',
  'Operation': 'ui.label.operation',
  'Invocation ready': 'ui.label.invocation_ready',
  'Would use network': 'ui.label.would_use_network',
  'Network allowed by contract': 'ui.label.network_allowed_by_contract',
  'Blocking reasons': 'ui.label.blocking_reasons',
  'Request preview': 'ui.label.request_preview',
  'Execution request': 'ui.label.execution_request',
  'Downstream commands': 'ui.label.downstream_commands',
  'Notes': 'ui.label.notes',
  'Response ID': 'ui.label.response_id',
  'Finish reason': 'ui.label.finish_reason',
  'Provider status': 'ui.label.provider_status',
  'Usage input tokens': 'ui.label.usage_input_tokens',
  'Usage output tokens': 'ui.label.usage_output_tokens',
  'Usage total tokens': 'ui.label.usage_total_tokens',
  'Metadata fields': 'ui.label.metadata_fields',
  'Top-level response keys': 'ui.label.top_level_response_keys',
  'Response keys': 'ui.label.response_keys',
  'Suggested commands': 'ui.label.suggested_commands',
  'Review capability': 'ui.label.review_capability',
  'Status': 'ui.label.status',
  'Next steps': 'ui.label.next_steps',
  'Read-only': 'ui.label.read_only',
  'External model API': 'ui.label.external_model_api',
  'GraphRAG runtime': 'ui.label.graphrag_runtime',
  'Vector DB': 'ui.label.vector_db',
  'Graph DB': 'ui.label.graph_db',
  'Source': 'ui.label.source',
  'Provider kind': 'ui.label.provider_kind',
  'Provider name': 'ui.label.provider_name',
  'Allow network': 'ui.label.allow_network',
  'Allow external context': 'ui.label.allow_external_context',
  'Bind scope': 'ui.label.bind_scope',
  'Mutation enabled': 'ui.label.mutation_enabled',
  'Mutation capability flag': 'ui.label.mutation_capability_flag',
  'Auth mode': 'ui.label.auth_mode',
  'Authorization mode': 'ui.label.authorization_mode',
  'Session gating': 'ui.label.session_gating',
  'Mutation readiness': 'ui.label.mutation_readiness',
  'Write route': 'ui.label.write_route',
  'Write actions': 'ui.label.write_actions',
  'Write request fields': 'ui.label.write_request_fields',
  'Write success status': 'ui.label.write_success_status',
  'Write blocked status': 'ui.label.write_blocked_status',
  'Identity proof status': 'ui.label.identity_proof_status',
  'Identity proof fields': 'ui.label.identity_proof_fields',
  'Shared machine safe': 'ui.label.shared_machine_safe',
  'Auth blockers': 'ui.label.auth_blockers',
  'Auth next steps': 'ui.label.auth_next_steps',
  'Identity assurance counts': 'ui.label.identity_assurance_counts',
  'Status: ': 'ui.label.status_prefix',
  'Route: ': 'ui.label.route_prefix',
  'Reviewer': 'ui.label.reviewer',
  'Session': 'ui.label.session',
  'Note': 'ui.label.note',
  'Approve': 'ui.label.approve',
  'Reject': 'ui.label.reject',
  'Request Changes': 'ui.label.request_changes',
  'POST enabled': 'ui.label.post_enabled',
  'Preview blocked route': 'ui.label.preview_blocked_route',
  'Detail': 'ui.label.detail_heading',
  'No matching runtime records for current filter.': 'ui.label.empty_runtime_records',
  'No matching review rows for current filter.': 'ui.label.empty_review_rows',
  'No matching summary jobs for current filter.': 'ui.label.empty_summary_jobs',
  'Local Review Mutation': 'ui.label.local_review_mutation',
  'Summary Review Mutation': 'ui.label.summary_review_mutation',
  'Chronicle ID': 'ui.label.chronicle_id',
  'Root': 'ui.label.root',
  'Identity aligned': 'ui.label.identity_aligned'
}};
function uiLabel(text) {{
  const rawText = String(text || '');
  const key = uiLabelKeys[rawText];
  return key ? t(key, rawText) : localizeTextValue(rawText);
}}
const uiI18nCatalog = {ui_i18n_catalog_json};
const supportedLocales = {json.dumps(list(SUPPORTED_UI_LOCALES), ensure_ascii=False)};
const defaultLocale = {json.dumps(DEFAULT_UI_LOCALE, ensure_ascii=False)};
function normalizeLocale(locale) {{
  const value = String(locale || '').trim();
  if (supportedLocales.includes(value)) return value;
  if (value.startsWith('ja')) return 'ja';
  if (value.startsWith('zh')) return 'zh-CN';
  return {json.dumps(FALLBACK_UI_LOCALE, ensure_ascii=False)};
}}
function currentLocale() {{ return window.__chronicleLocale || defaultLocale; }}
function t(key, fallback = '') {{
  const locale = currentLocale();
  const localeCatalog = uiI18nCatalog[locale] || {{}};
  const englishCatalog = uiI18nCatalog.en || {{}};
  return localeCatalog[key] || englishCatalog[key] || fallback || key;
}}
function formatLabel(key, replacements = {{}}, fallback = '') {{
  let text = t(key, fallback);
  for (const [name, value] of Object.entries(replacements || {{}})) {{
    text = text.replaceAll('{' + name + '}', String(value ?? ''));
  }}
  return text;
}}
function exactTranslations() {{ return (uiI18nCatalog[currentLocale()] || {{}}).exact || {{}}; }}
function prefixTranslations() {{ return (uiI18nCatalog[currentLocale()] || {{}}).prefix || {{}}; }}
function localizeTextValue(value) {{
  const text = String(value || '');
  const exact = exactTranslations();
  const trimmed = text.trim();
  if (trimmed && exact[trimmed]) {{
    return text.replace(trimmed, exact[trimmed]);
  }}
  const prefixes = prefixTranslations();
  for (const [source, translated] of Object.entries(prefixes)) {{
    if (text.includes(source)) {{
      return text.replace(source, translated);
    }}
  }}
  return text;
}}
function label(key, fallback = '') {{
  return t(key, fallback || key);
}}
function reviewerBoundaryDatasetLabel(datasetKey) {{
  const normalizedDatasetKey = String(datasetKey || '');
  if (!normalizedDatasetKey) return '';
  if (normalizedDatasetKey === 'runtime_records') return label('ui.dataset.runtime_records', 'Runtime records');
  if (normalizedDatasetKey === 'review_queue') return label('ui.dataset.review_queue', 'Review queue');
  if (normalizedDatasetKey === 'summary_jobs') return label('ui.dataset.summary_jobs', 'Summary jobs');
  return normalizedDatasetKey;
}}
function reviewerBoundaryStatusText(status) {{
  const normalizedStatus = String(status || '');
  if (!normalizedStatus) return '';
  return label('ui.reviewer_boundary_status.' + normalizedStatus, normalizedStatus);
}}
function localizeRenderedRegion(element) {{
  if (!element) return;
  const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT, {{
    acceptNode(node) {{
      const parent = node.parentElement;
      if (!parent) return NodeFilter.FILTER_REJECT;
      if (parent.closest('pre, code, .id')) return NodeFilter.FILTER_REJECT;
      return NodeFilter.FILTER_ACCEPT;
    }}
  }});
  const nodes = [];
  while (walker.nextNode()) nodes.push(walker.currentNode);
  nodes.forEach(node => {{
    node.nodeValue = localizeTextValue(node.nodeValue || '');
  }});
}}
function applyDynamicAttributeTranslations(root) {{
  if (!root) return;
  root.querySelectorAll('[data-filter-input]').forEach(input => {{
    const target = String(input.getAttribute('data-filter-input') || '');
    if (target === 'runtimeRecords') input.setAttribute('placeholder', t('placeholder.runtime_filter'));
    if (target === 'reviewQueue') input.setAttribute('placeholder', t('placeholder.review_filter'));
    if (target === 'summaryJobs') input.setAttribute('placeholder', t('placeholder.summary_filter'));
  }});
  root.querySelectorAll('input[id$=\"-reviewer-note\"]').forEach(input => input.setAttribute('placeholder', t('placeholder.review_note')));
  root.querySelectorAll('input[id$=\"-reviewer-label\"]').forEach(input => input.setAttribute('placeholder', t('placeholder.reviewer')));
  root.querySelectorAll('input[id$=\"-reviewer-session-label\"]').forEach(input => input.setAttribute('placeholder', t('placeholder.session')));
}}
function applyShellTranslations() {{
  document.title = t('shell.title') + ' — ' + {json.dumps(metadata.title, ensure_ascii=False)};
  document.documentElement.lang = currentLocale();
  const localeLabel = document.getElementById('locale-label');
  if (localeLabel) localeLabel.textContent = t('label.language');
  const shellTitle = document.getElementById('shell-title');
  if (shellTitle) shellTitle.textContent = t('shell.title');
  const shellRootLabel = document.getElementById('shell-root-label');
  if (shellRootLabel) shellRootLabel.textContent = t('shell.root');
  const warningTitle = document.getElementById('shell-warning-title');
  if (warningTitle) warningTitle.textContent = t('shell.warning_title');
  const warningBody = document.getElementById('shell-warning-body');
  if (warningBody) warningBody.textContent = t('shell.warning_body');
  const boundaryBody = document.getElementById('shell-boundary-body');
  if (boundaryBody) boundaryBody.textContent = t('shell.boundary_body');
  const loadingOverview = document.getElementById('shell-loading-overview');
  if (loadingOverview) loadingOverview.textContent = t('shell.loading_overview');
  const selectJson = document.getElementById('shell-select-json');
  if (selectJson) selectJson.textContent = t('shell.select_json');
  document.querySelectorAll('button[data-endpoint]').forEach(button => {{
    button.textContent = t('nav.' + button.dataset.endpoint, button.textContent || '');
  }});
  const localeSelect = document.getElementById('locale-select');
  if (localeSelect) {{
    Array.from(localeSelect.options).forEach(option => {{
      option.textContent = t('locale.' + option.value, option.textContent || option.value);
    }});
    localeSelect.value = currentLocale();
  }}
}}
function applyLocaleToPage() {{
  applyShellTranslations();
  const view = document.getElementById('view');
  const detail = document.getElementById('detail');
  localizeRenderedRegion(view);
  localizeRenderedRegion(detail);
  applyDynamicAttributeTranslations(view);
  applyDynamicAttributeTranslations(detail);
}}
function initialLocale() {{
  const params = new URLSearchParams(window.location.search);
  const queryLocale = params.get('locale');
  if (queryLocale) return normalizeLocale(queryLocale);
  const storedLocale = window.localStorage.getItem('chronicle-ui-locale');
  if (storedLocale) return normalizeLocale(storedLocale);
  return normalizeLocale(navigator.language || defaultLocale);
}}
function setLocale(locale, rerender = true) {{
  window.__chronicleLocale = normalizeLocale(locale);
  window.localStorage.setItem('chronicle-ui-locale', window.__chronicleLocale);
  applyLocaleToPage();
  if (!rerender) return;
  if (window.__chronicleCurrentEndpoint) loadEndpoint(window.__chronicleCurrentEndpoint);
  if (window.__chronicleLastDetail) loadDetail(window.__chronicleLastDetail);
}}
function esc(value) {{ return String(value).replace(/[&<>\"']/g, ch => ({{'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}}[ch])); }}
function firstArray(payload) {{ for (const key of Object.keys(payload)) if (Array.isArray(payload[key])) return payload[key]; return null; }}
function badge(text, cls) {{ return '<span class="badge ' + cls + '">' + esc(text) + '</span>'; }}
function jumpBadge(text, cls, endpoint, filterTarget, filterValue) {{
  const targetAttr = filterTarget ? ' data-filter-target="' + esc(filterTarget) + '"' : '';
  const valueAttr = filterValue ? ' data-filter-value="' + esc(filterValue) + '"' : '';
  return '<button data-jump="' + esc(endpoint) + '"' + targetAttr + valueAttr + '>'
    + badge(text, cls) + '</button>';
}}
function copyCommandButton(command, targetId, label = '') {{
  if (!command) return '';
  return '<button data-copy-command="' + esc(command) + '" data-copy-target="' + esc(targetId || 'action-preview-response') + '">' + esc(label || t('button.copy_cli')) + '</button>';
}}
function sourceCountBadges(sourceCounts) {{
  return Object.entries(sourceCounts || {{}}).map(([key, value]) =>
    badge(key + ':' + value, 'badge-neutral')
  ).join('');
}}
function detailMessages(items, fallbackItems = []) {{
  const details = Array.isArray(items) ? items : [];
  const fallback = Array.isArray(fallbackItems) ? fallbackItems : [];
  const detailMessages = details.map(item =>
    item && item.message_key
      ? formatLabel(item.message_key, item.message_params || {{}}, item.message || '')
      : localizeTextValue(item.message || '')
  );
  if (detailMessages.length > 0) return detailMessages.join(' | ');
  return fallback.map(item => reviewWarningLabel(item)).join(' | ') || '';
}}
function localizedPayloadText(item, keyField = 'message_key', fallbackField = 'message', paramsField = 'message_params') {{
  if (!item || typeof item !== 'object') return '';
  if (item[keyField]) return formatLabel(item[keyField], item[paramsField] || {{}}, item[fallbackField] || '');
  return localizeTextValue(item[fallbackField] || '');
}}
function localizedLinkLabel(item) {{
  if (!item || typeof item !== 'object') return '';
  if (item.label_key) return formatLabel(item.label_key, item.label_params || {{}}, item.label || '');
  return localizeTextValue(item.label || '');
}}
function reviewerContextDetailLines(reviewerContext, identityProofContract = {{}}) {{
  const effectiveFields = Array.isArray(reviewerContext.effective_required_fields)
    ? reviewerContext.effective_required_fields
    : [];
  const acceptedKinds = Array.isArray(reviewerContext.accepted_reviewer_kinds)
    ? reviewerContext.accepted_reviewer_kinds
    : [];
  const advisoryKinds = Array.isArray(reviewerContext.advisory_only_reviewer_kinds)
    ? reviewerContext.advisory_only_reviewer_kinds
    : [];
  const sessionExamples = Array.isArray(reviewerContext.session_label_examples)
    ? reviewerContext.session_label_examples
    : [];
  const expectationSummary = reviewerContext.expectation_summary_key
    ? formatLabel(reviewerContext.expectation_summary_key, reviewerContext.expectation_summary_params || {{}}, reviewerContext.expectation_summary || '')
    : (reviewerContext.expectation_summary || '');
  const authorityNote = reviewerContext.authority_note_key
    ? formatLabel(reviewerContext.authority_note_key, reviewerContext.authority_note_params || {{}}, reviewerContext.authority_note || '')
    : (reviewerContext.authority_note || '');
  const reviewerLabelNote = reviewerContext.reviewer_label_note_key
    ? formatLabel(reviewerContext.reviewer_label_note_key, reviewerContext.reviewer_label_note_params || {{}}, reviewerContext.reviewer_label_note || '')
    : (reviewerContext.reviewer_label_note || '');
  const reviewerKindNote = reviewerContext.reviewer_kind_note_key
    ? formatLabel(reviewerContext.reviewer_kind_note_key, reviewerContext.reviewer_kind_note_params || {{}}, reviewerContext.reviewer_kind_note || '')
    : (reviewerContext.reviewer_kind_note || '');
  const sessionNote = reviewerContext.session_note_key
    ? formatLabel(reviewerContext.session_note_key, reviewerContext.session_note_params || {{}}, reviewerContext.session_note || '')
    : (reviewerContext.session_note || '');
  const uiIntentNote = reviewerContext.ui_intent_note_key
    ? formatLabel(reviewerContext.ui_intent_note_key, reviewerContext.ui_intent_note_params || {{}}, reviewerContext.ui_intent_note || '')
    : (reviewerContext.ui_intent_note || '');
  const localizedEffectiveFields = (Array.isArray(reviewerContext.effective_required_field_details) ? reviewerContext.effective_required_field_details : []).map(item => (
    item && item.summary_key
      ? formatLabel(item.summary_key, item.summary_params || {{}}, item.summary || item.field || '')
      : (item.summary || item.field || '')
  ));
  const localizedAcceptedKinds = (Array.isArray(reviewerContext.accepted_reviewer_kind_details) ? reviewerContext.accepted_reviewer_kind_details : []).map(item => (
    item && item.summary_key
      ? formatLabel(item.summary_key, item.summary_params || {{}}, item.summary || item.kind || '')
      : (item.summary || item.kind || '')
  ));
  const localizedAdvisoryKinds = (Array.isArray(reviewerContext.advisory_only_reviewer_kind_details) ? reviewerContext.advisory_only_reviewer_kind_details : []).map(item => (
    item && item.summary_key
      ? formatLabel(item.summary_key, item.summary_params || {{}}, item.summary || item.kind || '')
      : (item.summary || item.kind || '')
  ));
  const localizedSessionBoundary = reviewerContext.session_boundary_status_summary_key
    ? formatLabel(reviewerContext.session_boundary_status_summary_key, reviewerContext.session_boundary_status_summary_params || {{}}, reviewerContext.session_boundary_status_summary || reviewerContext.session_boundary_status || '')
    : (reviewerContext.session_boundary_status_summary || reviewerContext.session_boundary_status || '');
  const localizedUiIntentRequired = reviewerContext.ui_intent_required_summary_key
    ? formatLabel(reviewerContext.ui_intent_required_summary_key, reviewerContext.ui_intent_required_summary_params || {{}}, reviewerContext.ui_intent_required_summary || String(reviewerContext.ui_intent_required))
    : (reviewerContext.ui_intent_required_summary || String(reviewerContext.ui_intent_required));
  return ''
    + detailLine('Reviewer expectation summary', expectationSummary)
    + detailListLine('Reviewer fields', localizedEffectiveFields.length > 0 ? localizedEffectiveFields : effectiveFields, ' | ')
    + detailListLine('Reviewer kinds', localizedAcceptedKinds.length > 0 ? localizedAcceptedKinds : acceptedKinds, ' | ')
    + detailListLine('Advisory-only reviewer kinds', localizedAdvisoryKinds.length > 0 ? localizedAdvisoryKinds : advisoryKinds, ' | ')
    + detailLine('Session boundary', localizedSessionBoundary)
    + detailLine('UI intent required', localizedUiIntentRequired)
    + detailListLine('Session label examples', sessionExamples, ' | ')
    + detailLine('Authority note', authorityNote)
    + detailLine('Reviewer label note', reviewerLabelNote)
    + detailLine('Reviewer kind note', reviewerKindNote)
    + detailLine('Session note', sessionNote)
    + detailLine('UI intent note', uiIntentNote)
    + detailLine('Identity proof note', identityProofContract.proof_note || '');
}}
function reviewActionCoreDetailLines(payload, action = '', recordId = '') {{
  const reviewerContext = payload.reviewer_context_requirements || {{}};
  const writeRouteContract = payload.write_route_contract || {{}};
  const identityProofContract = writeRouteContract.identity_proof_contract || {{}};
  const localizedCliEquivalent = payload.cli_equivalent_detail && payload.cli_equivalent_detail.summary_key
    ? formatLabel(
        payload.cli_equivalent_detail.summary_key,
        payload.cli_equivalent_detail.summary_params || {{}},
        payload.cli_equivalent_detail.summary || payload.cli_equivalent || ''
      )
    : (payload.cli_equivalent || '');
  const localizedFailureSummary = payload.failure_summary_key
    ? formatLabel(payload.failure_summary_key, payload.failure_summary_params || {{}}, payload.failure_summary || '')
    : (payload.failure_summary || '');
  return ''
    + detailLine('Action', payload.action || action || '')
    + detailLine('Event', payload.event_id || recordId || '')
    + detailLine('Error code', payload.error_code || '')
    + detailLine('Identity assurance', payload.identity_assurance_status || '')
    + detailLine('Identity assurance message', payload.identity_assurance_message || '')
    + detailLine('CLI equivalent', localizedCliEquivalent)
    + detailLine('Failure summary', localizedFailureSummary)
    + detailLine('Warnings', detailMessages(payload.warning_details, payload.warning_codes))
    + reviewerContextDetailLines(reviewerContext, identityProofContract);
}}
function contractDetailLines(successContract, failureContract, targetId) {{
  const resolvedContract = (successContract || failureContract) || {{}};
  const failureFamilies = Array.isArray((failureContract || {{}}).failure_families)
    ? failureContract.failure_families
    : [];
  const targetStateRecovery = (failureContract || {{}}).target_state_recovery || {{}};
  const localizedFailureFamilies = failureFamilies.map(item => {{
    const summary = item && item.summary_key
      ? formatLabel(item.summary_key, item.summary_params || {{}}, item.summary || '')
      : (item.summary || '');
    return ((item.family || 'family') + ': ' + summary + '; ' + ((item.possible_error_codes || []).join(', ')));
  }});
  const localizedTargetStateSummary = targetStateRecovery.summary_key
    ? formatLabel(targetStateRecovery.summary_key, targetStateRecovery.summary_params || {{}}, targetStateRecovery.summary || '')
    : (targetStateRecovery.summary || '');
  const localizedTargetStateStatus = targetStateRecovery.status_summary_key
    ? formatLabel(targetStateRecovery.status_summary_key, targetStateRecovery.status_summary_params || {{}}, targetStateRecovery.status_summary || targetStateRecovery.status || '')
    : (targetStateRecovery.status_summary || targetStateRecovery.status || '');
  const localizedPendingQueueSufficient = typeof targetStateRecovery.pending_queue_sufficient === 'boolean'
    ? (
      targetStateRecovery.pending_queue_sufficient_summary_key
        ? formatLabel(targetStateRecovery.pending_queue_sufficient_summary_key, targetStateRecovery.pending_queue_sufficient_summary_params || {{}}, targetStateRecovery.pending_queue_sufficient_summary || String(targetStateRecovery.pending_queue_sufficient))
        : (targetStateRecovery.pending_queue_sufficient_summary || String(targetStateRecovery.pending_queue_sufficient))
    )
    : '';
  const localizedResolvedQueueReason = targetStateRecovery.resolved_queue_reason_key
    ? formatLabel(targetStateRecovery.resolved_queue_reason_key, targetStateRecovery.resolved_queue_reason_params || {{}}, targetStateRecovery.resolved_queue_reason || '')
    : (targetStateRecovery.resolved_queue_reason || '');
  const localizedPossibleErrors = (Array.isArray((failureContract || {{}}).possible_error_details) ? failureContract.possible_error_details : []).map(item => (
    item && item.message_key
      ? formatLabel(item.message_key, item.message_params || {{}}, item.message || item.code || '')
      : (item.message || item.code || '')
  ));
  const localizedRecoveryCommands = (Array.isArray((failureContract || {{}}).recovery_command_details) ? failureContract.recovery_command_details : []).map(item => (
    item && item.summary_key
      ? formatLabel(item.summary_key, item.summary_params || {{}}, item.summary || item.command || '')
      : (item.summary || item.command || '')
  ));
  const localizedFollowUpCommands = (Array.isArray((successContract || {{}}).follow_up_command_details) ? successContract.follow_up_command_details : []).map(item => (
    item && item.summary_key
      ? formatLabel(item.summary_key, item.summary_params || {{}}, item.summary || item.command || '')
      : (item.summary || item.command || '')
  ));
  const localizedRollbackStatus = resolvedContract.rollback_status_summary_key
    ? formatLabel(resolvedContract.rollback_status_summary_key, resolvedContract.rollback_status_summary_params || {{}}, resolvedContract.rollback_status_summary || resolvedContract.rollback_status || '')
    : (resolvedContract.rollback_status_summary || resolvedContract.rollback_status || '');
  const localizedTransactionStatus = (successContract || {{}}).transaction_status_summary_key
    ? formatLabel(successContract.transaction_status_summary_key, successContract.transaction_status_summary_params || {{}}, successContract.transaction_status_summary || successContract.transaction_status || '')
    : ((successContract || {{}}).transaction_status_summary || (successContract || {{}}).transaction_status || '');
  const localizedDurableOnFailure = typeof (failureContract || {{}}).durable_mutation_reported_on_failure === 'boolean'
    ? (
      failureContract.durable_mutation_reported_on_failure_summary_key
        ? formatLabel(failureContract.durable_mutation_reported_on_failure_summary_key, failureContract.durable_mutation_reported_on_failure_summary_params || {{}}, failureContract.durable_mutation_reported_on_failure_summary || String(failureContract.durable_mutation_reported_on_failure))
        : (failureContract.durable_mutation_reported_on_failure_summary || String(failureContract.durable_mutation_reported_on_failure))
    )
    : '';
  const lines = []
    + detailLine('Recovery path', resolvedContract.recovery_path || '')
    + detailLine('Rollback status', localizedRollbackStatus)
    + detailLine('Transaction status', localizedTransactionStatus)
    + detailListLine('Durable success requirements', (successContract || {{}}).durable_success_requirements, ' | ')
    + detailLine('Durable mutation on failure', localizedDurableOnFailure)
    + detailLine('Target-state recovery status', localizedTargetStateStatus)
    + detailLine('Target-state recovery summary', localizedTargetStateSummary)
    + detailLine('Pending queue sufficient', localizedPendingQueueSufficient)
    + detailLine('Resolved queue reason', localizedResolvedQueueReason)
    + detailLine('Resolved queue command', targetStateRecovery.resolved_queue_command || '')
    + detailLine('Chronicle state command', targetStateRecovery.chronicle_state_command || '')
    + detailListLine('Possible errors', localizedPossibleErrors.length > 0 ? localizedPossibleErrors : ((failureContract || {{}}).possible_error_codes), ' | ')
    + detailListLine('Failure families', localizedFailureFamilies, ' | ')
    + detailListLine('Recovery commands', localizedRecoveryCommands.length > 0 ? localizedRecoveryCommands : ((failureContract || {{}}).recovery_commands), ' | ')
    + detailListLine('Follow-up commands', localizedFollowUpCommands.length > 0 ? localizedFollowUpCommands : ((successContract || {{}}).follow_up_commands), ' | ');
  return lines + (resolvedContract.recovery_path ? '<p>' + copyCommandButton(resolvedContract.recovery_path, targetId, t('button.copy_recovery_cli')) + '</p>' : '');
}}
function renderReviewActionResultPanel(title, responseStatus, path, payload, targetId, options = {{}}) {{
  const action = options.action || '';
  const recordId = options.recordId || '';
  const localizedMessage = payload && payload.message_key
    ? formatLabel(payload.message_key, payload.message_params || {{}}, payload.message || '')
    : (payload.message || '');
  const message = options.useStatusFallback
    ? (localizedMessage || payload.status || t('status.no_message'))
    : (localizedMessage || t('status.no_message'));
  const extraLines = options.extraLines || '';
  return ''
    + '<p><strong>' + esc(title) + '</strong></p>'
    + '<p>' + esc(uiLabel('Status: ')) + esc(responseStatus) + '</p>'
    + '<p>' + esc(uiLabel('Route: ')) + '<span class="id">' + esc(path) + '</span></p>'
    + '<p>' + esc(message) + '</p>'
    + reviewActionCoreDetailLines(payload, action, recordId)
    + extraLines
    + contractDetailLines(payload.success_contract, payload.failure_contract, targetId);
}}
function renderReviewMutationForm(title, prefix) {{
  return '<div class="notice"><strong>' + esc(title) + '</strong><p>'
    + '<label>' + esc(uiLabel('Reviewer')) + ' <input id="' + esc(prefix) + '-reviewer-label" value="local-ui" placeholder="' + esc(t('placeholder.reviewer')) + '"></label> '
    + '<label>' + esc(uiLabel('Kind')) + ' <select id="' + esc(prefix) + '-reviewer-kind"><option value="local_operator">local_operator</option><option value="user_declared">user_declared</option></select></label> '
    + '<label>' + esc(uiLabel('Session')) + ' <input id="' + esc(prefix) + '-reviewer-session-label" value="local-ui-session" placeholder="' + esc(t('placeholder.session')) + '"></label> '
    + '<label>' + esc(uiLabel('Note')) + ' <input id="' + esc(prefix) + '-reviewer-note" placeholder="' + esc(t('placeholder.review_note')) + '"></label></p></div>';
}}
function renderPreviewSummary(preview) {{
  const localizedCliEquivalent = preview.cli_equivalent_summary_key
    ? formatLabel(preview.cli_equivalent_summary_key, preview.cli_equivalent_summary_params || {{}}, preview.cli_equivalent_summary || preview.cli_equivalent || '')
    : (preview.cli_equivalent || '');
  const localizedRecoverySummary = preview.recovery_summary_key
    ? formatLabel(preview.recovery_summary_key, preview.recovery_summary_params || {{}}, preview.recovery_summary || '')
    : (preview.recovery_summary || '');
  const localizedFollowUpSummary = preview.follow_up_summary_key
    ? formatLabel(preview.follow_up_summary_key, preview.follow_up_summary_params || {{}}, preview.follow_up_summary || '')
    : (preview.follow_up_summary || '');
  const statusLine = preview.status
    ? '<strong>' + esc(preview.status) + '</strong><br>' + esc(localizeTextValue(preview.message || ''))
    : esc(localizeTextValue(preview.message || ''));
  const extras = [
    localizedCliEquivalent
      ? '<br><span class="id">cli=' + esc(localizedCliEquivalent) + '</span>'
      : '',
    localizedRecoverySummary
      ? '<br><span class="id">recovery=' + esc(localizedRecoverySummary) + '</span>'
      : '',
    localizedFollowUpSummary
      ? '<br><span class="id">follow-up=' + esc(localizedFollowUpSummary) + '</span>'
      : '',
  ].join('');
  return statusLine + extras;
}}
function renderPreviewContractSummary(preview, previewTarget = 'action-preview-response') {{
  const failureContract = (preview && preview.failure_contract) || {{}};
  const successContract = (preview && preview.success_contract) || {{}};
  const writeRouteContract = (preview && preview.write_route_contract) || {{}};
  const identityProofContract = writeRouteContract.identity_proof_contract || {{}};
  const authorizationContract = writeRouteContract.authorization_contract || {{}};
  const targetStateContract = writeRouteContract.target_state_contract || {{}};
  const recoveryPath = failureContract.recovery_path || '';
  const localizedRecoverySummary = preview && preview.recovery_summary_key
    ? formatLabel(preview.recovery_summary_key, preview.recovery_summary_params || {{}}, preview.recovery_summary || recoveryPath || '')
    : (preview && preview.recovery_summary) || recoveryPath;
  const possibleErrors = Array.isArray(failureContract.possible_error_codes)
    ? failureContract.possible_error_codes
    : [];
  const localizedPossibleErrors = (Array.isArray(failureContract.possible_error_details) ? failureContract.possible_error_details : []).map(item => (
    item && item.message_key
      ? formatLabel(item.message_key, item.message_params || {{}}, item.message || item.code || '')
      : (item.message || item.code || '')
  ));
  const followUpCommands = Array.isArray(successContract.follow_up_commands)
    ? successContract.follow_up_commands
    : [];
  const localizedFollowUpCommands = (Array.isArray(successContract.follow_up_command_details) ? successContract.follow_up_command_details : []).map(item => (
    item && item.summary_key
      ? formatLabel(item.summary_key, item.summary_params || {{}}, item.summary || item.command || '')
      : (item.summary || item.command || '')
  ));
  const localizedProofStatus = identityProofContract.proof_status_message_key
    ? formatLabel(identityProofContract.proof_status_message_key, identityProofContract.proof_status_message_params || {{}}, identityProofContract.proof_status_message || identityProofContract.proof_status || '')
    : (identityProofContract.proof_status_message || identityProofContract.proof_status || '');
  const localizedProofFields = (Array.isArray(identityProofContract.required_identity_field_details) ? identityProofContract.required_identity_field_details : []).map(item => (
    item && item.summary_key
      ? formatLabel(item.summary_key, item.summary_params || {{}}, item.summary || item.field || '')
      : (item.summary || item.field || '')
  ));
  const localizedRequestFields = (Array.isArray(writeRouteContract.expected_request_field_details) ? writeRouteContract.expected_request_field_details : []).map(item => (
    item && item.summary_key
      ? formatLabel(item.summary_key, item.summary_params || {{}}, item.summary || item.field || '')
      : (item.summary || item.field || '')
  ));
  const localizedTransactionOrder = (Array.isArray(writeRouteContract.transaction_order_details) ? writeRouteContract.transaction_order_details : []).map(item => (
    item && item.summary_key
      ? formatLabel(item.summary_key, item.summary_params || {{}}, item.summary || item.step || '')
      : (item.summary || item.step || '')
  ));
  const localizedAuthorizationChecks = (Array.isArray(authorizationContract.server_side_check_details) ? authorizationContract.server_side_check_details : []).map(item => (
    item && item.summary_key
      ? formatLabel(item.summary_key, item.summary_params || {{}}, item.summary || item.code || '')
      : (item.summary || item.code || '')
  ));
  const localizedTargetStateChecks = (Array.isArray(targetStateContract.target_state_check_details) ? targetStateContract.target_state_check_details : []).map(item => (
    item && item.summary_key
      ? formatLabel(item.summary_key, item.summary_params || {{}}, item.summary || item.code || '')
      : (item.summary || item.code || '')
  ));
  const localizedSuccessStatus = writeRouteContract.success_status_summary_key
    ? formatLabel(writeRouteContract.success_status_summary_key, writeRouteContract.success_status_summary_params || {{}}, writeRouteContract.success_status_summary || String(writeRouteContract.success_status_code || ''))
    : (writeRouteContract.success_status_summary || String(writeRouteContract.success_status_code || ''));
  const localizedBlockedStatus = writeRouteContract.blocked_status_summary_key
    ? formatLabel(writeRouteContract.blocked_status_summary_key, writeRouteContract.blocked_status_summary_params || {{}}, writeRouteContract.blocked_status_summary || String(writeRouteContract.blocked_status_code || ''))
    : (writeRouteContract.blocked_status_summary || String(writeRouteContract.blocked_status_code || ''));
  const localizedRollbackStatus = failureContract.rollback_status_summary_key
    ? formatLabel(failureContract.rollback_status_summary_key, failureContract.rollback_status_summary_params || {{}}, failureContract.rollback_status_summary || failureContract.rollback_status || '')
    : (failureContract.rollback_status_summary || failureContract.rollback_status || '');
  const localizedTransactionStatus = successContract.transaction_status_summary_key
    ? formatLabel(successContract.transaction_status_summary_key, successContract.transaction_status_summary_params || {{}}, successContract.transaction_status_summary || successContract.transaction_status || '')
    : (successContract.transaction_status_summary || successContract.transaction_status || '');
  const localizedDurableOnFailure = typeof failureContract.durable_mutation_reported_on_failure === 'boolean'
    ? (
      failureContract.durable_mutation_reported_on_failure_summary_key
        ? formatLabel(failureContract.durable_mutation_reported_on_failure_summary_key, failureContract.durable_mutation_reported_on_failure_summary_params || {{}}, failureContract.durable_mutation_reported_on_failure_summary || String(failureContract.durable_mutation_reported_on_failure))
        : (failureContract.durable_mutation_reported_on_failure_summary || String(failureContract.durable_mutation_reported_on_failure))
    )
    : '';
  const requestFields = Array.isArray(writeRouteContract.expected_request_fields)
    ? writeRouteContract.expected_request_fields
    : [];
  const transactionOrder = Array.isArray(writeRouteContract.transaction_order)
    ? writeRouteContract.transaction_order
    : [];
  const serverSideChecks = Array.isArray(authorizationContract.server_side_checks)
    ? authorizationContract.server_side_checks
    : [];
  const targetStateChecks = Array.isArray(targetStateContract.target_state_checks)
    ? targetStateContract.target_state_checks
    : [];
  if (!recoveryPath && possibleErrors.length === 0 && followUpCommands.length === 0 && requestFields.length === 0 && transactionOrder.length === 0 && serverSideChecks.length === 0 && targetStateChecks.length === 0) return '';
  return [
    failureContract.rollback_status
      ? '<br><span class="id">rollback=' + esc(localizedRollbackStatus) + '</span>'
      : '',
    successContract.transaction_status
      ? '<br><span class="id">transaction=' + esc(localizedTransactionStatus) + '</span>'
      : '',
    typeof failureContract.durable_mutation_reported_on_failure === 'boolean'
      ? '<br><span class="id">durable-on-failure=' + esc(localizedDurableOnFailure) + '</span>'
      : '',
    writeRouteContract.route_template
      ? '<br><span class="id">write-route=' + esc(writeRouteContract.route_template) + '</span>'
      : '',
    requestFields.length > 0
      ? '<br><span class="id">request-fields=' + esc((localizedRequestFields.length > 0 ? localizedRequestFields : requestFields).join(' | ')) + '</span>'
      : '',
    transactionOrder.length > 0
      ? '<br><span class="id">transaction-order=' + esc((localizedTransactionOrder.length > 0 ? localizedTransactionOrder : transactionOrder).join(' -> ')) + '</span>'
      : '',
    serverSideChecks.length > 0
      ? '<br><span class="id">authorization-checks=' + esc((localizedAuthorizationChecks.length > 0 ? localizedAuthorizationChecks : serverSideChecks).join(' | ')) + '</span>'
      : '',
    targetStateChecks.length > 0
      ? '<br><span class="id">target-state-checks=' + esc((localizedTargetStateChecks.length > 0 ? localizedTargetStateChecks : targetStateChecks).join(' | ')) + '</span>'
      : '',
    writeRouteContract.success_status_code
      ? '<br><span class="id">success-status=' + esc(localizedSuccessStatus) + '</span>'
      : '',
    writeRouteContract.blocked_status_code
      ? '<br><span class="id">blocked-status=' + esc(localizedBlockedStatus) + '</span>'
      : '',
    identityProofContract.proof_status
      ? '<br><span class="id">proof-status=' + esc(localizedProofStatus) + '</span>'
      : '',
    Array.isArray(identityProofContract.required_identity_fields) && identityProofContract.required_identity_fields.length > 0
      ? '<br><span class="id">proof-fields=' + esc((localizedProofFields.length > 0 ? localizedProofFields : identityProofContract.required_identity_fields).join(' | ')) + '</span>'
      : '',
    recoveryPath
      ? '<br><span class="id">recovery=' + esc(localizedRecoverySummary) + '</span> '
        + copyCommandButton(recoveryPath, previewTarget, t('button.copy_recovery_cli'))
      : '',
    possibleErrors.length > 0
      ? '<br><span class="id">errors=' + esc((localizedPossibleErrors.length > 0 ? localizedPossibleErrors : possibleErrors).join(' | ')) + '</span>'
      : '',
    followUpCommands.length > 0
      ? '<br><span class="id">follow-up=' + esc((localizedFollowUpCommands.length > 0 ? localizedFollowUpCommands : followUpCommands).join(' | ')) + '</span>'
      : '',
  ].join('');
}}
function renderPreviewButtons(previewActions, options = {{}}) {{
  const actions = Array.isArray(previewActions) ? previewActions : [];
  const mutationEnabled = Boolean(options.mutationEnabled);
  const recordId = options.recordId || '';
  const fieldPrefix = options.fieldPrefix || '';
  const successDetail = options.successDetail || '';
  const previewTarget = options.previewTarget || 'action-preview-response';
  const actionButtons = actions.map(item =>
    mutationEnabled
      ? '<button data-submit-review-action="' + esc(item.post_path || '') + '" data-review-action="' + esc(item.action || '') + '" data-review-record="' + esc(recordId) + '" data-review-fields="' + esc(fieldPrefix) + '" data-success-detail="' + esc(successDetail) + '" data-preview-target="' + esc(previewTarget) + '">' + esc(item.label || item.action || t('button.apply')) + '</button>'
      : '<button data-preview-post="' + esc(item.post_path || '') + '" data-preview-target="' + esc(previewTarget) + '">' + esc(t('button.preview_blocked_route')) + '</button>'
  );
  const extraButtons = Array.isArray(options.extraButtons) ? options.extraButtons.filter(Boolean) : [];
  return [...actionButtons, ...extraButtons].join(' ');
}}
function authReadinessBadge(status) {{
  return status === 'boundary_aligned'
    ? jumpBadge(label('badge.auth_aligned', 'Auth aligned'), 'badge-ready', '/api/review-queue', 'reviewQueue', 'boundary_aligned')
    : jumpBadge(label('badge.auth_advisory', 'Auth advisory'), 'badge-warning', '/api/review-queue', 'reviewQueue', status || 'advisory_only');
}}
function identityAssuranceBadge(status) {{
  return status === 'boundary_aligned'
    ? jumpBadge(label('badge.identity_aligned', 'Identity aligned'), 'badge-ready', '/api/review-queue', 'reviewQueue', 'boundary_aligned')
    : status
      ? jumpBadge(label('badge.identity_advisory', 'Identity advisory'), 'badge-warning', '/api/review-queue', 'reviewQueue', status)
      : badge(label('badge.identity_na', 'Identity n/a'), 'badge-neutral');
}}
function summaryReviewStatusBadge(status) {{
  return status === 'ready'
    ? jumpBadge(label('badge.ready', 'Ready'), 'badge-ready', '/api/review-queue', 'reviewQueue', 'ready')
    : status === 'resolved'
      ? jumpBadge(label('badge.resolved', 'Resolved'), 'badge-neutral', '/api/review-queue', 'reviewQueue', 'resolved')
      : jumpBadge(label('badge.advisory', 'Advisory'), 'badge-warning', '/api/review-queue', 'reviewQueue', 'advisory');
}}
function packageStatusBadge(status) {{
  return status === 'package_context_available'
    ? jumpBadge(label('badge.package_ready', 'Package Ready'), 'badge-ready', '/api/review-queue', 'reviewQueue', 'package:package_context_available')
    : status === 'no_context_records'
      ? jumpBadge(label('badge.package_advisory', 'Package Advisory'), 'badge-warning', '/api/review-queue', 'reviewQueue', 'package:no_context_records')
      : badge(status || label('badge.package_unknown', 'Package Unknown'), 'badge-neutral');
}}
function previewButtonsConfig(row, config) {{
  return {{
    mutationEnabled: row.ui_mutation_enabled,
    recordId: config.recordId || '',
    fieldPrefix: config.fieldPrefix || '',
    successDetail: config.successDetail || '',
    previewTarget: config.previewTarget || 'action-preview-response',
    extraButtons: config.extraButtons || [],
  }};
}}
function mutationEnablementBadge(summary) {{
  if (!summary || !summary.status) return badge(label('badge.mutation_na', 'Mutation n/a'), 'badge-neutral');
  if (summary.enablement_ready) return badge(label('badge.mutation_ready', 'Mutation ready'), 'badge-ready');
  return badge(label('badge.mutation_preview', 'Mutation preview'), 'badge-warning');
}}
function renderMutationEnablementSummary(summary) {{
  if (!summary || !summary.status) return '';
  const proofFields = Array.isArray(summary.identity_proof_fields) ? summary.identity_proof_fields : [];
  const localizedProofStatus = summary.identity_proof_status_message_key
    ? formatLabel(summary.identity_proof_status_message_key, summary.identity_proof_status_message_params || {{}}, summary.identity_proof_status_message || summary.identity_proof_status || '')
    : (summary.identity_proof_status_message || summary.identity_proof_status || '');
  const localizedProofFields = (Array.isArray(summary.identity_proof_field_details) ? summary.identity_proof_field_details : []).map(item => (
    item && item.summary_key
      ? formatLabel(item.summary_key, item.summary_params || {{}}, item.summary || item.field || '')
      : (item.summary || item.field || '')
  ));
  const localizedBlockedStatus = summary.blocked_status_summary_key
    ? formatLabel(summary.blocked_status_summary_key, summary.blocked_status_summary_params || {{}}, summary.blocked_status_summary || String(summary.blocked_status_code || ''))
    : (summary.blocked_status_summary || String(summary.blocked_status_code || ''));
  const localizedMessage = summary.message_key
    ? formatLabel(summary.message_key, summary.message_params || {{}}, summary.message || '')
    : localizeTextValue(summary.message || '');
  const localizedScopeNote = summary.scope_note_key
    ? formatLabel(summary.scope_note_key, summary.scope_note_params || {{}}, summary.scope_note || '')
    : localizeTextValue(summary.scope_note || '');
  const localizedRemainingSummary = summary.remaining_summary_key
    ? formatLabel(summary.remaining_summary_key, summary.remaining_summary_params || {{}}, summary.remaining_summary || '')
    : localizeTextValue(summary.remaining_summary || '');
  return [
    '<span class="id">mutation=' + esc(summary.status || '') + '</span>',
    localizedMessage
      ? '<span class="id">message=' + esc(localizedMessage) + '</span>'
      : '',
    localizedScopeNote
      ? '<span class="id">scope=' + esc(localizedScopeNote) + '</span>'
      : '',
    summary.operational_status
      ? '<span class="id">operational=' + esc(summary.operational_status) + '</span>'
      : '',
    typeof summary.remaining_count === 'number'
      ? '<span class="id">remaining=' + esc(summary.remaining_count) + '</span>'
      : '',
    localizedRemainingSummary
      ? '<span class="id">remaining-summary=' + esc(localizedRemainingSummary) + '</span>'
      : '',
    summary.blocked_status_code
      ? '<span class="id">blocked-status=' + esc(localizedBlockedStatus) + '</span>'
      : '',
    summary.identity_proof_status
      ? '<span class="id">proof-status=' + esc(localizedProofStatus) + '</span>'
      : '',
    proofFields.length > 0
      ? '<span class="id">proof-fields=' + esc((localizedProofFields.length > 0 ? localizedProofFields : proofFields).join(' | ')) + '</span>'
      : '',
  ].filter(Boolean).join('<br>');
}}
function detailJsonButton(endpoint, row) {{
  const path = detailPath(endpoint, row);
  return path ? '<button data-detail="' + esc(path) + '">JSON</button>' : '';
}}
function stackedCell(parts, separator = '<br>') {{
  return parts.filter(part => part).join(separator);
}}
function cellTitle(text) {{
  return text ? '<div class="cell-title">' + esc(text) + '</div>' : '';
}}
function cellMeta(text) {{
  return text ? '<div class="cell-meta">' + esc(text) + '</div>' : '';
}}
function cellCode(text) {{
  return text ? '<div class="cell-code">' + esc(text) + '</div>' : '';
}}
function cellStack(parts) {{
  return '<div class="cell-stack">' + parts.filter(part => part).join('') + '</div>';
}}
function cellDetails(summary, parts, open = false) {{
  const body = parts.filter(part => part).join('');
  if (!body) return '';
  return '<details class="cell-details"' + (open ? ' open' : '') + '><summary>'
    + esc(summary)
    + '</summary><div class="cell-details-body">' + body + '</div></details>';
}}
function responseSummaryLine(responseMetadata) {{
  if (!responseMetadata || !responseMetadata.present) return '';
  return cellMeta(
    'Response ' + String(responseMetadata.response_id || '(no response_id)')
    + (responseMetadata.finish_reason ? ' / ' + String(responseMetadata.finish_reason) : '')
  );
}}
function renderReviewerBoundaryDrilldownSummary(summary) {{
  if (!summary || !summary.dataset_key) return '';
  const enforcementStatus = summary.enforcement_status || summary.dominant_enforcement_status || '';
  const gateStatus = summary.validation_gate_status || summary.dominant_validation_gate_status || '';
  const datasetLabel = reviewerBoundaryDatasetLabel(summary.dataset_key || '');
  const messageParams = Object.assign({{}}, summary.message_params || {{}}, {{
    dataset: datasetLabel,
  }});
  const factLineParams = Object.assign({{}}, summary.fact_line_params || {{}}, {{
    dataset: datasetLabel,
    enforcement_status: reviewerBoundaryStatusText(enforcementStatus),
    validation_gate_status: reviewerBoundaryStatusText(gateStatus),
  }});
  const message = summary.message_template_key
    ? formatLabel(summary.message_template_key, messageParams, summary.message || '')
    : summary.message_key
      ? label(summary.message_key, summary.message || '')
      : (summary.message || '');
  const factLine = summary.fact_line_template_key
    ? formatLabel(summary.fact_line_template_key, factLineParams, summary.fact_line || '')
    : (summary.fact_line || '');
  return cellStack([
    cellMeta(message),
    cellMeta(factLine),
    cellCode(label('ui.label.dataset', 'Dataset') + '=' + datasetLabel),
    cellCode(label('ui.label.dominant_enforcement_status', 'Dominant enforcement status') + '=' + reviewerBoundaryStatusLabel('reviewer_enforcement', enforcementStatus)),
    cellCode(label('ui.label.dominant_validation_gate_status', 'Dominant gate status') + '=' + reviewerBoundaryStatusLabel('reviewer_gate', gateStatus)),
    navigationCluster([
      listJumpButton(label('button.open_list', 'Open List'), summary.list_path || ''),
      detailJumpButton(summary.detail_path || '', label('button.open_detail', 'Open Detail')),
    ]),
  ]);
}}
function reviewerBoundaryDominantButtons(drilldownSummaries) {{
  const rows = Array.isArray(drilldownSummaries) ? drilldownSummaries : [];
  return rows.map(item => {{
    const datasetKey = String(item.dataset_key || '');
    const datasetLabel = reviewerBoundaryDatasetLabel(datasetKey);
    const filterTarget = datasetKey === 'runtime_records'
      ? 'runtimeRecords'
      : datasetKey === 'review_queue'
        ? 'reviewQueue'
        : datasetKey === 'summary_jobs'
          ? 'summaryJobs'
          : '';
    if (!filterTarget) return '';
    const enforcementStatus = String(item.dominant_enforcement_status || '');
    const gateStatus = String(item.dominant_validation_gate_status || '');
    return [
      enforcementStatus
        ? jumpBadge(
            datasetLabel + ' · ' + reviewerBoundaryStatusLabel('reviewer_enforcement', enforcementStatus),
            'badge-neutral',
            item.list_path || '',
            filterTarget,
            'reviewer_enforcement:' + enforcementStatus,
          )
        : '',
      gateStatus
        ? jumpBadge(
            datasetLabel + ' · ' + reviewerBoundaryStatusLabel('reviewer_gate', gateStatus),
            'badge-neutral',
            item.list_path || '',
            filterTarget,
            'reviewer_gate:' + gateStatus,
          )
        : '',
    ].filter(Boolean).join('');
  }}).join('');
}}
function previewCell(preview, previewActions, options) {{
  const previewSummary = renderPreviewSummary(preview || {{}});
  const previewContractSummary = renderPreviewContractSummary(
    preview || {{}},
    (options && options.previewTarget) || 'action-preview-response',
  );
  const previewButtons = renderPreviewButtons(previewActions, options);
  return cellStack([
    previewSummary,
    cellDetails(label('button.more_details', 'More details'), [previewContractSummary]),
    cellDetails(label('button.actions', 'Actions'), [
      previewButtons ? '<div class="cell-actions">' + previewButtons + '</div>' : '',
    ]),
  ]);
}}
function reviewerCell(identity, fallbackLabel = '') {{
  const reviewerBadge = reviewerIdentityBadge(identity);
  const label = (identity && identity.label) || fallbackLabel || '';
  return reviewerBadge + (reviewerBadge ? '<br>' : '') + esc(label);
}}
function summaryIdentityCell(identityBadge, reviewerIdentity) {{
  const reviewerBadge = reviewerIdentityBadge(reviewerIdentity);
  const reviewerLabel = (reviewerIdentity && reviewerIdentity.label) || '';
  return identityBadge
    + (reviewerBadge ? '<br>' + reviewerBadge : '')
    + (reviewerLabel ? '<br>' + esc(reviewerLabel) : '');
}}
function resetFilterButton(query, target) {{
  return query ? '<p><button data-reset-filter="' + esc(target) + '">' + esc(label('button.reset_filter', 'Reset Filter')) + '</button></p>' : '';
}}
function emptyFilterButtons(target) {{
  if (target === 'runtimeRecords') return [
    openEndpointButton('/api/runtime-records'),
    openEndpointButton('/api/review-queue'),
  ];
  if (target === 'reviewQueue') return [
    openEndpointButton('/api/review-queue'),
    openEndpointButton('/api/runtime-records'),
    openEndpointButton('/api/summary-jobs'),
  ];
  if (target === 'summaryJobs') return [
    openEndpointButton('/api/summary-jobs'),
    openEndpointButton('/api/review-queue'),
  ];
  return [];
}}
function emptyFilterState(query, rows, message, target) {{
  return query && rows.length === 0
    ? '<div><p>' + esc(message) + '</p>' + navigationCluster(emptyFilterButtons(target)) + '</div>'
    : '';
}}
function actionPreviewStatus(targetId, mutationEnabled, enabledMessage, disabledMessage) {{
  return '<div id="' + esc(targetId) + '"><p>'
    + (mutationEnabled ? enabledMessage : disabledMessage)
    + '</p></div>';
}}
function tableHtml(headers, body) {{
  return '<table><thead><tr>' + headers.map(header => '<th>' + esc(header) + '</th>').join('')
    + '</tr></thead><tbody>' + body + '</tbody></table>';
}}
function listToolbar(endpoint, target, placeholder, sortOptions, filterChipHtml, query) {{
  return activeViewSummary(endpoint, 'list')
    + textInput(target, placeholder)
    + sortSelect(target, currentSortValue(endpoint), sortOptions)
    + filterChipHtml
    + resetFilterButton(query, target);
}}
function renderRuntimeRecordRow(row, endpoint) {{
  const button = detailJsonButton(endpoint, row);
  const preview = row.runtime_record_preview || {{}};
  const actionPreview = row.action_preview_summary || {{}};
  const previewActions = Array.isArray(actionPreview.actions) ? actionPreview.actions : [];
  const mutationEnablement = row.mutation_enablement_summary || {{}};
  const responseMetadata = row.response_metadata_summary || {{}};
  const sourceBadges = sourceCountBadges(preview.source_counts || {{}});
  const authBadge = row.auth_readiness_status === 'boundary_aligned'
    ? jumpBadge(label('badge.auth_aligned', 'Auth aligned'), 'badge-ready', '/api/review-queue', 'reviewQueue', 'boundary_aligned')
    : row.auth_readiness_status
      ? jumpBadge(label('badge.auth_advisory', 'Auth advisory'), 'badge-warning', '/api/review-queue', 'reviewQueue', row.auth_readiness_status)
      : badge(label('badge.auth_na', 'Auth n/a'), 'badge-neutral');
  const mutationBadge = mutationEnablementBadge(mutationEnablement);
  const reviewerEnforcementBadge = row.reviewer_enforcement_status
    ? badge(reviewerBoundaryStatusLabel('reviewer_enforcement', row.reviewer_enforcement_status), 'badge-neutral')
    : '';
  const reviewerGateBadge = row.reviewer_validation_gate_status
    ? badge(reviewerBoundaryStatusLabel('reviewer_gate', row.reviewer_validation_gate_status), 'badge-neutral')
    : '';
  const kindBadge = jumpBadge(
    row.runtime_record_kind || 'unknown',
    'badge-neutral',
    '/api/runtime-records',
    'runtimeRecords',
    row.runtime_record_kind || 'unknown',
  );
  const runtimeRowShortcutButtons = [
    reviewDetailButton(row.review_target_event_id || ''),
    relatedDetailButton(row, '/api/summary-jobs/', 'Open summary job'),
    relatedDetailButton(row, '/api/artifacts/', 'Open artifact'),
  ].filter(Boolean);
  return '<tr>'
    + '<td>' + button + '</td>'
    + '<td><span class="id">' + esc(row.event_id || '') + '</span></td>'
    + '<td>' + kindBadge + '</td>'
    + '<td>' + cellStack([
      authBadge,
      mutationBadge,
      reviewerEnforcementBadge,
      reviewerGateBadge,
      cellDetails(label('button.more_details', 'More details'), [
        cellMeta(renderMutationEnablementSummary(mutationEnablement)),
        renderReviewerBoundaryDrilldownSummary(row.reviewer_boundary_drilldown_summary || {{}}),
      ]),
    ]) + '</td>'
    + '<td>' + cellStack([
      cellTitle(preview.title || ''),
      cellMeta(preview.preview_text || ''),
      sourceBadges,
      cellDetails(label('button.more_details', 'More details'), [
        cellCode(JSON.stringify(preview.source_counts || {{}})),
        responseSummaryLine(responseMetadata),
      ]),
    ]) + '</td>'
    + '<td>' + previewCell(actionPreview, previewActions, previewButtonsConfig(row, {{
      recordId: row.review_target_event_id || row.event_id || '',
      fieldPrefix: 'runtime-records',
      successDetail: '/api/runtime-records/' + esc(row.event_id || ''),
      previewTarget: 'runtime-records-action-preview-response',
      extraButtons: runtimeRowShortcutButtons,
    }})) + '</td>'
    + '</tr>';
}}
function renderReviewQueueRow(row, endpoint) {{
  const button = detailJsonButton(endpoint, row);
  const capability = row.review_capability || {{}};
  const readiness = row.package_readiness_summary || {{}};
  const parity = row.cli_parity_summary || {{}};
  const preview = row.action_preview_summary || {{}};
  const previewActions = Array.isArray(preview.actions) ? preview.actions : [];
  const authReadiness = row.auth_boundary_notice || {{}};
  const mutationEnablement = row.mutation_enablement_summary || {{}};
  const responseMetadata = row.response_metadata_summary || {{}};
  const warnList = Array.isArray(capability.warnings) ? capability.warnings : [];
  const warnDetails = Array.isArray(capability.warning_details) ? capability.warning_details : [];
  const warnBadges = reviewWarningBadges(warnList);
  const reviewKindBadge = row.review_kind
    ? jumpBadge(row.review_kind, 'badge-neutral', '/api/review-queue', 'reviewQueue', row.review_kind)
    : '';
  const statusBadge = reviewCapabilityBadge(capability);
  const readinessBadge = packageReadinessBadge(readiness);
  const parityBadge = reviewParityBadge(parity);
  const authBadge = authReadinessBadge(authReadiness.status || '');
  const reviewerEnforcementBadge = row.reviewer_enforcement_status
    ? badge(reviewerBoundaryStatusLabel('reviewer_enforcement', row.reviewer_enforcement_status), 'badge-neutral')
    : '';
  const reviewerGateBadge = row.reviewer_validation_gate_status
    ? badge(reviewerBoundaryStatusLabel('reviewer_gate', row.reviewer_validation_gate_status), 'badge-neutral')
    : '';
  const reviewRowShortcutButtons = [
    relatedDetailButton(row, '/api/runtime-records/', 'Open matching runtime record'),
  ].filter(Boolean);
  return '<tr>'
    + '<td>' + button + '</td>'
    + '<td>' + cellStack([
      '<div><span class="id">' + esc(row.target_event_id || '') + '</span></div>',
      reviewKindBadge,
      cellMeta(row.target_summary || ''),
      cellDetails(label('button.more_details', 'More details'), [
        responseSummaryLine(responseMetadata),
      ]),
    ]) + '</td>'
    + '<td>' + cellStack([
      statusBadge,
      reviewerEnforcementBadge,
      reviewerGateBadge,
      cellDetails(label('button.more_details', 'More details'), [
        readinessBadge,
        parityBadge,
        authBadge,
        renderReviewerBoundaryDrilldownSummary(row.reviewer_boundary_drilldown_summary || {{}}),
      ]),
    ]) + '</td>'
    + '<td>' + cellStack([
      mutationEnablementBadge(mutationEnablement),
      previewCell(preview, previewActions, previewButtonsConfig(row, {{
        recordId: row.target_event_id || '',
        fieldPrefix: 'review-queue',
        successDetail: '/api/review-queue/' + esc(row.target_event_id || ''),
        previewTarget: 'review-queue-action-preview-response',
        extraButtons: reviewRowShortcutButtons,
      }})),
      cellDetails(label('button.more_details', 'More details'), [
        cellMeta(renderMutationEnablementSummary(mutationEnablement)),
      ]),
    ]) + '</td>'
    + '<td>' + cellStack([
      warnBadges,
      cellDetails(label('button.more_details', 'More details'), [
        cellMeta(warnDetails.map(item => item.message).join(' | ') || warnList.join(', ') || '(none)'),
      ]),
    ]) + '</td>'
    + '<td>' + reviewerCell(row.latest_reviewer_identity, row.latest_reviewer || '') + '</td>'
    + '</tr>';
}}
function renderSummaryJobRow(row, endpoint) {{
  const button = detailJsonButton(endpoint, row);
  const reviewStatus = row.review_capability_status || '';
  const authReadinessStatus = row.auth_readiness_status || '';
  const packageStatus = row.package_readiness_status || '';
  const identityAssuranceStatus = row.identity_assurance_status || '';
  const preview = row.action_preview_summary || {{}};
  const previewActions = Array.isArray(preview.actions) ? preview.actions : [];
  const mutationEnablement = row.mutation_enablement_summary || {{}};
  const reviewBadge = summaryReviewStatusBadge(reviewStatus);
  const authBadge = authReadinessBadge(authReadinessStatus);
  const identityBadge = identityAssuranceBadge(identityAssuranceStatus);
  const packageBadge = packageStatusBadge(packageStatus);
  const responseMetadata = row.response_metadata_summary || {{}};
  const reviewerEnforcementBadge = row.reviewer_enforcement_status
    ? badge(reviewerBoundaryStatusLabel('reviewer_enforcement', row.reviewer_enforcement_status), 'badge-neutral')
    : '';
  const reviewerGateBadge = row.reviewer_validation_gate_status
    ? badge(reviewerBoundaryStatusLabel('reviewer_gate', row.reviewer_validation_gate_status), 'badge-neutral')
    : '';
  const targetButton = reviewDetailButton(row.review_target_event_id || '');
  const summaryRowShortcutButtons = [
    reviewDetailButton(row.review_target_event_id || ''),
    relatedDetailButton(row, '/api/artifacts/', 'Open artifact'),
  ].filter(Boolean);
  return '<tr>'
    + '<td>' + button + '</td>'
    + '<td>' + cellStack(['<div><span class="id">' + esc(row.summary_job_id || '') + '</span></div>', cellTitle(row.title || ''), targetButton]) + '</td>'
    + '<td>' + cellStack([
      cellMeta(row.status || ''),
      reviewBadge,
      reviewerEnforcementBadge,
      reviewerGateBadge,
      cellDetails(label('button.more_details', 'More details'), [
        authBadge,
        packageBadge,
        mutationEnablementBadge(mutationEnablement),
        cellMeta(renderMutationEnablementSummary(mutationEnablement)),
        renderReviewerBoundaryDrilldownSummary(row.reviewer_boundary_drilldown_summary || {{}}),
      ]),
    ]) + '</td>'
    + '<td>' + summaryIdentityCell(identityBadge, row.latest_reviewer_identity) + '</td>'
    + '<td>' + previewCell(preview, previewActions, previewButtonsConfig(row, {{
      recordId: row.review_target_event_id || '',
      fieldPrefix: 'summary-jobs',
      successDetail: '/api/summary-jobs/' + esc(row.summary_job_id || ''),
      previewTarget: 'summary-jobs-action-preview-response',
      extraButtons: summaryRowShortcutButtons,
    }})) + '</td>'
    + '<td>' + cellStack([
      cellMeta(row.runtime_provider_kind || ''),
      cellMeta('sources: ' + String(row.summary_source_count ?? 0)),
      cellDetails(label('button.more_details', 'More details'), [
        responseSummaryLine(responseMetadata),
      ]),
    ]) + '</td>'
    + '</tr>';
}}
function renderRuntimeRecordsTable(endpoint, rows) {{
  const query = (window.__chronicleFilters && window.__chronicleFilters.runtimeRecords || '').toLowerCase();
  const filtered = filterRows(rows, row => {{
    if (!query) return true;
    if (matchesReviewerBoundaryFilter(query, row.reviewer_enforcement_status, row.reviewer_validation_gate_status)) return true;
    if (query.startsWith('reviewer_enforcement:') || query.startsWith('reviewer_gate:')) return false;
    const preview = row.runtime_record_preview || {{}};
    const actionPreview = row.action_preview_summary || {{}};
    const mutationEnablement = row.mutation_enablement_summary || {{}};
    const responseMetadata = row.response_metadata_summary || {{}};
    return includesQuery([
      row.event_id || '',
      row.runtime_record_kind || '',
      row.auth_readiness_status || '',
      row.reviewer_enforcement_status || '',
      row.reviewer_validation_gate_status || '',
      row.review_capability_status || '',
      row.identity_assurance_status || '',
      preview.title || '',
      preview.preview_text || '',
      actionPreview.status || '',
      mutationEnablement.status || '',
      mutationEnablement.operational_status || '',
      mutationEnablement.identity_proof_status || '',
      String(mutationEnablement.remaining_count ?? ''),
      String(mutationEnablement.blocked_status_code ?? ''),
      responseMetadata.response_id || '',
      responseMetadata.finish_reason || '',
      responseMetadata.provider_status || '',
      String(responseMetadata.usage_input_tokens ?? ''),
      String(responseMetadata.usage_output_tokens ?? ''),
      String(responseMetadata.usage_total_tokens ?? ''),
      ...(Array.isArray(responseMetadata.response_keys) ? responseMetadata.response_keys : []),
    ], query);
  }});
  const sorted = sortRuntimeRows(filtered);
  const mutationEnabled = sorted.some(row => row.ui_mutation_enabled);
  return listToolbar(endpoint, 'runtimeRecords', t('placeholder.runtime_filter'), [
      {{ value: 'latest', label: t('sort.runtime.latest') }},
      {{ value: 'mutation', label: t('sort.runtime.mutation') }},
      {{ value: 'auth', label: t('sort.runtime.auth') }},
      {{ value: 'kind', label: t('sort.runtime.kind') }},
    ], runtimeRecordsFilterChips(), query)
    + sliceButtonRow(runtimeRecordsSliceButtons())
    + sliceButtonRow(reviewerBoundaryListButtons('runtimeRecords', '/api/runtime-records', sorted))
    + emptyFilterState(query, sorted, uiLabel('No matching runtime records for current filter.'), 'runtimeRecords')
    + (
      mutationEnabled
        ? renderReviewMutationForm(uiLabel('Local Review Mutation'), 'runtime-records')
        : ''
    )
    + actionPreviewStatus(
      'runtime-records-action-preview-response',
      mutationEnabled,
      t('notice.mutation_enabled_runtime_records'),
      t('notice.blocked_route_preview_runtime_records')
    )
    + tableHtml([
      label('label.table_detail', 'Detail'),
      label('label.table_event', 'Event'),
      label('label.table_kind', 'Kind'),
      label('label.table_auth', 'Auth'),
      label('label.table_preview', 'Preview'),
      label('label.table_review_route', 'Review Route'),
    ], sorted.map(row => renderRuntimeRecordRow(row, endpoint)).join(''));
}}
function renderReviewQueueTable(endpoint, rows) {{
  const query = (window.__chronicleFilters && window.__chronicleFilters.reviewQueue || '').toLowerCase();
  const filtered = filterRows(rows, row => {{
    if (!query) return true;
    if (matchesReviewerBoundaryFilter(query, row.reviewer_enforcement_status, row.reviewer_validation_gate_status)) return true;
    if (query.startsWith('reviewer_enforcement:') || query.startsWith('reviewer_gate:')) return false;
    const capability = row.review_capability || {{}};
    const readiness = row.package_readiness_summary || {{}};
    const parity = row.cli_parity_summary || {{}};
    const authReadiness = row.auth_boundary_notice || {{}};
    const mutationEnablement = row.mutation_enablement_summary || {{}};
    const responseMetadata = row.response_metadata_summary || {{}};
    return includesQuery([
      row.target_event_id || '',
      row.target_summary || '',
      row.review_kind || '',
      row.reviewer_enforcement_status || '',
      row.reviewer_validation_gate_status || '',
      capability.status || '',
      readiness.label || '',
      parity.status || '',
      authReadiness.status || '',
      mutationEnablement.status || '',
      mutationEnablement.operational_status || '',
      mutationEnablement.identity_proof_status || '',
      (row.latest_identity_assurance && row.latest_identity_assurance.status) || '',
      (row.latest_reviewer_identity && row.latest_reviewer_identity.kind) || '',
      (row.latest_reviewer_identity && row.latest_reviewer_identity.label) || row.latest_reviewer || '',
      responseMetadata.response_id || '',
      responseMetadata.finish_reason || '',
      responseMetadata.provider_status || '',
      String(responseMetadata.usage_input_tokens ?? ''),
      String(responseMetadata.usage_output_tokens ?? ''),
      String(responseMetadata.usage_total_tokens ?? ''),
      ...(Array.isArray(responseMetadata.response_keys) ? responseMetadata.response_keys : []),
    ], query);
  }});
  const sorted = sortReviewRows(filtered);
  const mutationEnabled = sorted.some(row => row.ui_mutation_enabled);
  return listToolbar(endpoint, 'reviewQueue', t('placeholder.review_filter'), [
      {{ value: 'attention', label: t('sort.review.attention') }},
      {{ value: 'parity', label: t('sort.review.parity') }},
      {{ value: 'latest', label: t('sort.review.latest') }},
      {{ value: 'reviewer', label: t('sort.review.reviewer') }},
    ], reviewQueueFilterChips(), query)
    + sliceButtonRow(reviewQueueSliceButtons())
    + sliceButtonRow(reviewerBoundaryListButtons('reviewQueue', '/api/review-queue', sorted))
    + emptyFilterState(query, sorted, uiLabel('No matching review rows for current filter.'), 'reviewQueue')
    + (
      mutationEnabled
        ? renderReviewMutationForm(uiLabel('Local Review Mutation'), 'review-queue')
        : ''
    )
    + actionPreviewStatus(
      'review-queue-action-preview-response',
      mutationEnabled,
      t('notice.mutation_enabled_review_queue'),
      t('notice.blocked_route_preview_review_queue')
    )
    + tableHtml([
      label('label.table_detail', 'Detail'),
      label('label.table_target', 'Target'),
      label('label.table_status', 'Status'),
      label('label.table_preview', 'Preview'),
      label('label.table_warnings', 'Warnings'),
      label('label.table_latest_reviewer', 'Latest Reviewer'),
    ], sorted.map(row => renderReviewQueueRow(row, endpoint)).join(''));
}}
function renderSummaryJobsTable(endpoint, rows) {{
  const query = (window.__chronicleFilters && window.__chronicleFilters.summaryJobs || '').toLowerCase();
  const filtered = filterRows(rows, row => {{
    if (!query) return true;
    if (matchesReviewerBoundaryFilter(query, row.reviewer_enforcement_status, row.reviewer_validation_gate_status)) return true;
    if (query.startsWith('reviewer_enforcement:') || query.startsWith('reviewer_gate:')) return false;
    const responseMetadata = row.response_metadata_summary || {{}};
    const mutationEnablement = row.mutation_enablement_summary || {{}};
    return includesQuery([
      row.summary_job_id || '',
      row.title || '',
      row.status || '',
      row.review_capability_status || '',
      row.auth_readiness_status || '',
      row.reviewer_enforcement_status || '',
      row.reviewer_validation_gate_status || '',
      row.package_readiness_status || '',
      row.identity_assurance_status || '',
      mutationEnablement.status || '',
      mutationEnablement.operational_status || '',
      mutationEnablement.identity_proof_status || '',
      String(mutationEnablement.remaining_count ?? ''),
      (row.latest_reviewer_identity && row.latest_reviewer_identity.kind) || '',
      (row.latest_reviewer_identity && row.latest_reviewer_identity.label) || '',
      row.cli_parity_status || '',
      row.runtime_provider_kind || '',
      responseMetadata.response_id || '',
      responseMetadata.finish_reason || '',
      responseMetadata.provider_status || '',
      String(responseMetadata.usage_input_tokens ?? ''),
      String(responseMetadata.usage_output_tokens ?? ''),
      String(responseMetadata.usage_total_tokens ?? ''),
      ...(Array.isArray(responseMetadata.response_keys) ? responseMetadata.response_keys : []),
    ], query);
  }});
  const sorted = sortSummaryJobRows(filtered);
  const mutationEnabled = sorted.some(row => row.ui_mutation_enabled);
  return listToolbar(endpoint, 'summaryJobs', t('placeholder.summary_filter'), [
      {{ value: 'latest', label: t('sort.summary.latest') }},
      {{ value: 'mutation', label: t('sort.summary.mutation') }},
      {{ value: 'review', label: t('sort.summary.review') }},
      {{ value: 'title', label: t('sort.summary.title') }},
    ], summaryJobsFilterChips(), query)
    + sliceButtonRow(summaryJobsSliceButtons())
    + sliceButtonRow(reviewerBoundaryListButtons('summaryJobs', '/api/summary-jobs', sorted))
    + emptyFilterState(query, sorted, uiLabel('No matching summary jobs for current filter.'), 'summaryJobs')
    + (
      mutationEnabled
        ? renderReviewMutationForm(uiLabel('Summary Review Mutation'), 'summary-jobs')
        : ''
    )
    + actionPreviewStatus(
      'summary-jobs-action-preview-response',
      mutationEnabled,
      t('notice.mutation_enabled_summary_jobs'),
      t('notice.blocked_route_preview_summary_jobs')
    )
    + tableHtml([
      label('label.table_detail', 'Detail'),
      label('label.table_summary_job', 'Summary Job'),
      label('label.table_status', 'Status'),
      label('label.table_identity', 'Identity'),
      label('label.table_preview', 'Preview'),
      label('label.table_runtime', 'Runtime'),
    ], sorted.map(row => renderSummaryJobRow(row, endpoint)).join(''));
}}
function renderGenericTable(endpoint, rows) {{
  const keys = Object.keys(rows[0]).slice(0, 8);
  return '<table><thead><tr><th>' + esc(label('label.table_detail', 'Detail')) + '</th>' + keys.map(k => '<th>' + esc(k) + '</th>').join('') + '</tr></thead><tbody>'
    + rows.map(row => {{
      const path = detailPath(endpoint, row);
      const button = path ? '<button data-detail="' + esc(path) + '">JSON</button>' : '';
      return '<tr><td>' + button + '</td>'
        + keys.map(k => '<td>' + esc(typeof row[k] === 'object' ? JSON.stringify(row[k]) : row[k] ?? '') + '</td>').join('')
        + '</tr>';
    }}).join('') + '</tbody></table>';
}}
const endpointRenderers = {{
  '/api/runtime-records': renderRuntimeRecordsTable,
  '/api/review-queue': renderReviewQueueTable,
  '/api/summary-jobs': renderSummaryJobsTable,
}};
function reviewerIdentityBadge(identity) {{
  if (!identity) return '';
  const kind = identity.kind || 'reviewer';
  const label = identity.label || 'unknown';
  return badge(kind + ':' + label, 'badge-neutral');
}}
function reviewWarningBadges(warnings) {{
  return (warnings || []).map(code => {{
    const text = reviewWarningLabel(code);
    return jumpBadge(text, 'badge-warning', '/api/review-queue', 'reviewQueue', String(code || ''));
  }}).join('');
}}
function reviewCapabilityBadge(capability) {{
  const status = String((capability && capability.status) || '');
  if (status === 'ready') return badge('Ready', 'badge-ready');
  if (status === 'resolved') return badge('Resolved', 'badge-neutral');
  return badge('Advisory', 'badge-warning');
}}
function packageReadinessBadge(readiness) {{
  const status = String((readiness && readiness.status) || '');
  const label = String((readiness && readiness.label) || '');
  const localizedLabel = readiness && readiness.label_key
    ? formatLabel(readiness.label_key, readiness.message_params || {{}}, label)
    : label;
  if (status === 'package_context_available') {{
    return badge(localizedLabel || 'Package Ready', 'badge-ready');
  }}
  if (status === 'no_context_records') {{
    return badge(localizedLabel || 'Package Advisory', 'badge-warning');
  }}
  return badge(localizedLabel || 'Package Unknown', 'badge-neutral');
}}
function reviewParityBadge(parity) {{
  const status = String((parity && parity.status) || '');
  if (status === 'aligned') {{
    return jumpBadge('CLI aligned', 'badge-ready', '/api/review-queue', 'reviewQueue', 'aligned');
  }}
  return jumpBadge('CLI drift', 'badge-warning', '/api/review-queue', 'reviewQueue', 'drift_detected');
}}
function textInput(id, placeholder) {{
  return '<input id="' + esc(id) + '" data-filter-input="' + esc(id) + '" placeholder="' + esc(placeholder)
    + '" style="margin: 6px 6px 10px 0; padding: 6px 8px; width: 260px;">';
}}
function filterRows(rows, predicate) {{
  return rows.filter(predicate);
}}
function reviewerBoundaryFilterValue(kind, status) {{
  return String(kind || '') + ':' + String(status || '');
}}
function reviewerBoundaryStatusLabel(kind, status) {{
  const normalizedKind = String(kind || '');
  const normalizedStatus = String(status || '');
  if (!normalizedStatus) return '';
  if (normalizedKind === 'reviewer_enforcement') {{
    return label('badge.reviewer_enforcement', 'Reviewer enforcement') + ': ' + reviewerBoundaryStatusText(normalizedStatus);
  }}
  if (normalizedKind === 'reviewer_gate') {{
    return label('badge.reviewer_gate', 'Reviewer gate') + ': ' + reviewerBoundaryStatusText(normalizedStatus);
  }}
  return reviewerBoundaryStatusText(normalizedStatus);
}}
function matchesReviewerBoundaryFilter(filterValue, enforcementStatus, gateStatus) {{
  const normalizedFilter = String(filterValue || '');
  if (normalizedFilter.startsWith('reviewer_enforcement:')) {{
    return normalizedFilter === reviewerBoundaryFilterValue('reviewer_enforcement', enforcementStatus || '');
  }}
  if (normalizedFilter.startsWith('reviewer_gate:')) {{
    return normalizedFilter === reviewerBoundaryFilterValue('reviewer_gate', gateStatus || '');
  }}
  return false;
}}
function includesQuery(values, query) {{
  return JSON.stringify(values).toLowerCase().includes(query);
}}
function includesQuery(values, query) {{
  return JSON.stringify(values).toLowerCase().includes(query);
}}
function sortRows(rows, comparator) {{
  return [...rows].sort(comparator);
}}
const endpointFilterTargets = {{
  '/api/runtime-records': 'runtimeRecords',
  '/api/review-queue': 'reviewQueue',
  '/api/summary-jobs': 'summaryJobs',
}};
const endpointSortDefaults = {{
  '/api/runtime-records': 'latest',
  '/api/review-queue': 'attention',
  '/api/summary-jobs': 'latest',
}};
function currentSortValue(endpoint) {{
  if (!window.__chronicleSorts) return '';
  const target = endpointFilterTargets[endpoint];
  if (!target) return '';
  return window.__chronicleSorts[target] || endpointSortDefaults[endpoint] || '';
}}
function currentFilterValue(endpoint) {{
  if (!window.__chronicleFilters) return '';
  const target = endpointFilterTargets[endpoint];
  return target ? window.__chronicleFilters[target] || '' : '';
}}
function setFilterValue(target, value) {{
  if (!window.__chronicleFilters || !target) return;
  window.__chronicleFilters[target] = value || '';
}}
function setSortValue(target, value) {{
  if (!window.__chronicleSorts || !target) return;
  const endpoint = Object.keys(endpointFilterTargets).find(key => endpointFilterTargets[key] === target) || '';
  window.__chronicleSorts[target] = value || endpointSortDefaults[endpoint] || '';
}}
function clearFilterValue(target) {{
  if (!window.__chronicleFilters || !target) return;
  window.__chronicleFilters[target] = '';
}}
function resetAllFilterValues() {{
  if (!window.__chronicleFilters) return;
  Object.values(endpointFilterTargets).forEach(target => {{
    window.__chronicleFilters[target] = '';
  }});
}}
function endpointStateLabel(kind, endpoint) {{
  const value = kind === 'filter' ? currentFilterValue(endpoint) : currentSortValue(endpoint);
  return value ? stateLabel(kind, value) : '';
}}
function endpointFilterTarget(endpoint) {{
  return endpointFilterTargets[endpoint] || '';
}}
function stateLabel(kind, value, suffix) {{
  const normalizedValue = String(value || '');
  if (!normalizedValue) return '';
  const normalizedSuffix = String(suffix || '');
  return normalizedSuffix
    ? kind + '=' + normalizedValue + ' (' + normalizedSuffix + ')'
    : kind + '=' + normalizedValue;
}}
function activeReviewWarningFilter() {{
  const value = String((window.__chronicleFilters && window.__chronicleFilters.reviewQueue) || '');
  if (!value) return '';
  if (value.includes('warning')) return value;
  if (value.startsWith('ui_')) return value;
  if (value.startsWith('reviewer_')) return value;
  if (value.startsWith('no_')) return value;
  return '';
}}
function sortSelect(id, value, options) {{
  return '<label style="margin-right: 10px;">Sort: <select data-sort-input="' + esc(id)
    + '" style="margin: 6px 6px 10px 6px; padding: 6px 8px;">'
    + options.map(option =>
      '<option value="' + esc(option.value) + '"' + (option.value === value ? ' selected' : '') + '>'
      + esc(option.label) + '</option>'
    ).join('')
    + '</select></label>';
}}
function compareTextDesc(left, right) {{
  return String(right || '').localeCompare(String(left || ''));
}}
function compareReviewerLabel(left, right) {{
  const leftReviewer = (left.latest_reviewer_identity && left.latest_reviewer_identity.label) || left.latest_reviewer || '';
  const rightReviewer = (right.latest_reviewer_identity && right.latest_reviewer_identity.label) || right.latest_reviewer || '';
  return String(leftReviewer).localeCompare(String(rightReviewer));
}}
function compareReviewTargetDesc(left, right) {{
  return compareTextDesc(left.target_event_id, right.target_event_id);
}}
function reviewAttentionRank(row) {{
  const capability = row.review_capability || {{}};
  const readiness = row.package_readiness_summary || {{}};
  const parity = row.cli_parity_summary || {{}};
  if (parity.status === 'drift_detected') return 0;
  if (row.review_kind === 'review_requested') return 0;
  if (capability.status === 'advisory_only') return 1;
  if (capability.status === 'ready') return 2;
  if (readiness.status === 'package_context_available') return 3;
  if (capability.status === 'resolved') return 4;
  return 5;
}}
function reviewParityRank(row) {{
  const parity = row.cli_parity_summary || {{}};
  if (parity.status === 'drift_detected') return 0;
  if (parity.status === 'aligned') return 1;
  return 2;
}}
function reviewWarningFilterRank(row) {{
  const warningFilter = activeReviewWarningFilter();
  if (!warningFilter) return 0;
  const warnings = ((row.review_capability || {{}}).warnings || []).map(value => String(value || ''));
  return warnings.includes(warningFilter) ? 0 : 1;
}}
function mutationSummaryRank(summary) {{
  const status = String((summary && summary.status) || '');
  const operationalStatus = String((summary && summary.operational_status) || '');
  const remainingCount = Number((summary && summary.remaining_count) || 0);
  if (status === 'enabled') return 0;
  if (operationalStatus === 'blocked') return 1;
  if (status === 'preview_only') return 2;
  if (operationalStatus === 'ready') return 3;
  return 4 + Math.max(0, remainingCount);
}}
function authStatusRank(status) {{
  const value = String(status || '');
  if (value === 'boundary_aligned') return 0;
  if (value === 'advisory_only') return 1;
  if (value) return 2;
  return 3;
}}
function sortRuntimeRows(rows) {{
  const sortValue = currentSortValue('/api/runtime-records');
  if (sortValue === 'mutation') {{
    return sortRows(rows, (left, right) => {{
      const mutationCompare = mutationSummaryRank(left.mutation_enablement_summary) - mutationSummaryRank(right.mutation_enablement_summary);
      if (mutationCompare !== 0) return mutationCompare;
      const authCompare = authStatusRank(left.auth_readiness_status) - authStatusRank(right.auth_readiness_status);
      if (authCompare !== 0) return authCompare;
      return compareTextDesc(left.event_id, right.event_id);
    }});
  }}
  if (sortValue === 'auth') {{
    return sortRows(rows, (left, right) => {{
      const authCompare = authStatusRank(left.auth_readiness_status) - authStatusRank(right.auth_readiness_status);
      if (authCompare !== 0) return authCompare;
      const mutationCompare = mutationSummaryRank(left.mutation_enablement_summary) - mutationSummaryRank(right.mutation_enablement_summary);
      if (mutationCompare !== 0) return mutationCompare;
      return compareTextDesc(left.event_id, right.event_id);
    }});
  }}
  if (sortValue === 'kind') {{
    return sortRows(rows, (left, right) => {{
      const kindCompare = String(left.runtime_record_kind || '').localeCompare(String(right.runtime_record_kind || ''));
      if (kindCompare !== 0) return kindCompare;
      return compareTextDesc(left.event_id, right.event_id);
    }});
  }}
  return sortRows(rows, (left, right) => compareTextDesc(left.event_id, right.event_id));
}}
function sortReviewRows(rows) {{
  const sortValue = currentSortValue('/api/review-queue');
  if (sortValue === 'latest') {{
    return sortRows(rows, compareReviewTargetDesc);
  }}
  if (sortValue === 'reviewer') {{
    return sortRows(rows, (left, right) => {{
      const reviewerCompare = compareReviewerLabel(left, right);
      if (reviewerCompare !== 0) return reviewerCompare;
      return compareReviewTargetDesc(left, right);
    }});
  }}
  if (sortValue === 'parity') {{
    return sortRows(rows, (left, right) => {{
      const warningCompare = reviewWarningFilterRank(left) - reviewWarningFilterRank(right);
      if (warningCompare !== 0) return warningCompare;
      const parityCompare = reviewParityRank(left) - reviewParityRank(right);
      if (parityCompare !== 0) return parityCompare;
      const attentionCompare = reviewAttentionRank(left) - reviewAttentionRank(right);
      if (attentionCompare !== 0) return attentionCompare;
      return compareReviewTargetDesc(left, right);
    }});
  }}
  return sortRows(rows, (left, right) => {{
    const warningCompare = reviewWarningFilterRank(left) - reviewWarningFilterRank(right);
    if (warningCompare !== 0) return warningCompare;
    const rankCompare = reviewAttentionRank(left) - reviewAttentionRank(right);
    if (rankCompare !== 0) return rankCompare;
    return compareReviewTargetDesc(left, right);
  }});
}}
function summaryJobAttentionRank(row) {{
  const reviewStatus = String(row.review_capability_status || '');
  const packageStatus = String(row.package_readiness_status || '');
  const parityStatus = String(row.cli_parity_status || '');
  if (parityStatus === 'drift_detected') return 0;
  if (reviewStatus === 'advisory_only') return 1;
  if (reviewStatus === 'ready') return 2;
  if (packageStatus === 'package_context_available') return 3;
  if (reviewStatus === 'resolved') return 4;
  return 5;
}}
function compareSummaryJobDesc(left, right) {{
  return compareTextDesc(left.summary_job_id, right.summary_job_id);
}}
function sortSummaryJobRows(rows) {{
  const sortValue = currentSortValue('/api/summary-jobs');
  if (sortValue === 'mutation') {{
    return sortRows(rows, (left, right) => {{
      const mutationCompare = mutationSummaryRank(left.mutation_enablement_summary) - mutationSummaryRank(right.mutation_enablement_summary);
      if (mutationCompare !== 0) return mutationCompare;
      const reviewCompare = summaryJobAttentionRank(left) - summaryJobAttentionRank(right);
      if (reviewCompare !== 0) return reviewCompare;
      return compareSummaryJobDesc(left, right);
    }});
  }}
  if (sortValue === 'title') {{
    return sortRows(rows, (left, right) => {{
      const titleCompare = String(left.title || '').localeCompare(String(right.title || ''));
      if (titleCompare !== 0) return titleCompare;
      return compareSummaryJobDesc(left, right);
    }});
  }}
  if (sortValue === 'review') {{
    return sortRows(rows, (left, right) => {{
      const rankCompare = summaryJobAttentionRank(left) - summaryJobAttentionRank(right);
      if (rankCompare !== 0) return rankCompare;
      const reviewCompare = String(left.review_capability_status || '').localeCompare(String(right.review_capability_status || ''));
      if (reviewCompare !== 0) return reviewCompare;
      return compareSummaryJobDesc(left, right);
    }});
  }}
  return sortRows(rows, compareSummaryJobDesc);
}}
function currentFilterLabel() {{
  if (!window.__chronicleCurrentEndpoint || !window.__chronicleFilters) return '';
  const endpoint = window.__chronicleCurrentEndpoint;
  const target = endpointFilterTarget(endpoint);
  const value = target ? window.__chronicleFilters[target] || '' : '';
  return value ? stateLabel('filter', value, filterValueLabel(target, value)) : '';
}}
function sortValueLabel(endpoint, sortValue) {{
  const normalizedEndpoint = String(endpoint || '');
  const normalizedSort = String(sortValue || '');
  if (!normalizedSort) return '';
  if (normalizedEndpoint === '/api/runtime-records') {{
    if (normalizedSort === 'latest') return label('sort.runtime.latest', 'Latest first');
    if (normalizedSort === 'mutation') return label('sort.runtime.mutation', 'Mutation readiness');
    if (normalizedSort === 'auth') return label('sort.runtime.auth', 'Auth readiness');
    if (normalizedSort === 'kind') return label('sort.runtime.kind', 'Kind');
  }}
  if (normalizedEndpoint === '/api/review-queue') {{
    if (normalizedSort === 'attention') return label('sort.review.attention', 'Needs attention first');
    if (normalizedSort === 'parity') return label('sort.review.parity', 'CLI drift first');
    if (normalizedSort === 'latest') return label('sort.review.latest', 'Latest first');
    if (normalizedSort === 'reviewer') return label('sort.review.reviewer', 'Reviewer');
  }}
  if (normalizedEndpoint === '/api/summary-jobs') {{
    if (normalizedSort === 'latest') return label('sort.summary.latest', 'Latest first');
    if (normalizedSort === 'mutation') return label('sort.summary.mutation', 'Mutation readiness');
    if (normalizedSort === 'review') return label('sort.summary.review', 'Needs attention first');
    if (normalizedSort === 'title') return label('sort.summary.title', 'Title');
  }}
  return normalizedSort.replaceAll('_', ' ');
}}
function sortStateLabel(endpoint, sortValue) {{
  if (!sortValue) return '';
  if (endpoint === '/api/review-queue') {{
    const warningFilter = activeReviewWarningFilter();
    if (warningFilter) {{
      return stateLabel(
        'sort',
        sortValue,
        sortValueLabel(endpoint, sortValue) + ' / warning-first:' + warningFilter,
      );
    }}
  }}
  return stateLabel('sort', sortValue, sortValueLabel(endpoint, sortValue));
}}
function currentSortLabel(endpoint) {{
  const currentEndpoint = endpoint || window.__chronicleCurrentEndpoint || '';
  const sortValue = currentSortValue(currentEndpoint);
  return sortStateLabel(currentEndpoint, sortValue);
}}
function hasActiveFilters() {{
  if (!window.__chronicleFilters) return false;
  return Object.values(endpointFilterTargets).some(target => Boolean(window.__chronicleFilters[target]));
}}
function resetFilters(target) {{
  if (!window.__chronicleFilters) return;
  if (!target || target === 'all') {{
    resetAllFilterValues();
    return;
  }}
  clearFilterValue(target);
}}
function currentTrailLabel() {{
  if (!Array.isArray(window.__chronicleDetailTrail) || window.__chronicleDetailTrail.length === 0) return '';
  return window.__chronicleDetailTrail.slice(-3).join(' <- ');
}}
function currentTrailButtons() {{
  if (!Array.isArray(window.__chronicleDetailTrail) || window.__chronicleDetailTrail.length === 0) return '';
  return window.__chronicleDetailTrail.slice(-3).map(path =>
    '<button data-detail-trail="' + esc(path) + '">' + esc(humanizeDetailPath(path)) + '</button>'
  ).join('');
}}
function filterValueLabel(target, value) {{
  const normalizedTarget = String(target || '');
  const normalizedValue = String(value || '');
  if (!normalizedValue) return '';
  if (normalizedValue.startsWith('reviewer_enforcement:')) {{
    return reviewerBoundaryStatusLabel('reviewer_enforcement', normalizedValue.split(':').slice(1).join(':'));
  }}
  if (normalizedValue.startsWith('reviewer_gate:')) {{
    return reviewerBoundaryStatusLabel('reviewer_gate', normalizedValue.split(':').slice(1).join(':'));
  }}
  if (normalizedTarget === 'runtimeRecords') {{
    if (normalizedValue === 'preview_only') return label('filter.runtime.preview_only', 'Runtime mutation preview');
    if (normalizedValue === 'advisory_only') return label('filter.runtime.advisory_only', 'Runtime auth advisory');
    if (normalizedValue === 'boundary_aligned') return label('filter.runtime.boundary_aligned', 'Runtime identity aligned');
    if (normalizedValue === 'retrieval_plan') return label('filter.runtime.retrieval_plan', 'Runtime retrieval plans');
    if (normalizedValue === 'response_id') return label('filter.runtime.response_id', 'Runtime provider response');
  }}
  if (normalizedTarget === 'summaryJobs') {{
    if (normalizedValue === 'preview_only') return label('filter.summary.preview_only', 'Summary mutation preview');
    if (normalizedValue === 'advisory_only') return label('filter.summary.advisory_only', 'Summary advisory');
    if (normalizedValue === 'package_context_available') return label('filter.summary.package_context_available', 'Summary package ready');
    if (normalizedValue === 'boundary_aligned') return label('filter.summary.boundary_aligned', 'Summary identity aligned');
    if (normalizedValue === 'response_id') return label('filter.summary.response_id', 'Summary provider response');
  }}
  if (normalizedTarget === 'reviewQueue') {{
    if (normalizedValue === 'review_requested') return label('filter.review.review_requested', 'Review requested');
    if (normalizedValue === 'ready') return label('filter.review.ready', 'Review ready');
    if (normalizedValue === 'advisory_only' || normalizedValue === 'advisory') return label('filter.review.advisory', 'Review advisory');
    if (normalizedValue === 'drift_detected') return label('filter.review.drift_detected', 'CLI drift');
    if (normalizedValue === 'aligned') return label('filter.review.aligned', 'CLI aligned');
    if (normalizedValue === 'boundary_aligned') return label('filter.review.boundary_aligned', 'Identity aligned');
    if (normalizedValue === 'response_id') return label('filter.review.response_id', 'Provider response');
    if (
      normalizedValue === 'ui_auth_not_enabled'
      || normalizedValue === 'ui_authorization_not_enabled'
      || normalizedValue === 'no_reviewer_identity_recorded'
      || normalizedValue === 'reviewer_identity_declared_only'
      || normalizedValue === 'reviewer_session_label_missing'
    ) return reviewWarningLabel(normalizedValue);
    if (normalizedValue === 'package:package_context_available') return label('filter.review.package_context_available', 'Package ready');
    if (normalizedValue === 'package:no_context_records') return label('filter.review.no_context_records', 'Package advisory');
  }}
  return normalizedValue.replaceAll('_', ' ');
}}
function reviewWarningLabel(code) {{
  const normalizedCode = String(code || '');
  if (normalizedCode === 'ui_auth_not_enabled') return label('filter.review.ui_auth_not_enabled', 'Auth boundary warnings');
  if (normalizedCode === 'ui_authorization_not_enabled') return label('filter.review.ui_authorization_not_enabled', 'Authorization warnings');
  if (normalizedCode === 'no_reviewer_identity_recorded') return label('filter.review.no_reviewer_identity_recorded', 'Missing identity');
  if (normalizedCode === 'reviewer_identity_declared_only') return label('filter.review.reviewer_identity_declared_only', 'Declared identity only');
  if (normalizedCode === 'reviewer_session_label_missing') return label('filter.review.reviewer_session_label_missing', 'Session label required');
  return localizeTextValue(reviewWarningLabels[normalizedCode] || normalizedCode.replaceAll('_', ' '));
}}
function sliceChip(filterValue, cls, resetTarget) {{
  const value = String(filterValue || '');
  if (!value) return '';
  const filterLabel = filterValueLabel(resetTarget, value);
  return '<p>'
    + badge('slice:' + filterLabel, cls)
    + ' <span class="id">' + esc(value) + '</span>'
    + ' <button data-reset-filter="' + esc(resetTarget) + '">' + esc(label('button.clear_slice', 'Clear Slice')) + '</button>'
    + '</p>';
}}
function sliceBadge(text, count, cls) {{
  return badge(text + ': ' + count, cls);
}}
function overviewCountButton(text, count, cls, endpoint, filterTarget, filterValue) {{
  return overviewJumpButton(sliceBadge(text, esc(count ?? 0), cls), endpoint, filterTarget, filterValue);
}}
function filterChips(target, cls) {{
  const filterValue = String((window.__chronicleFilters && window.__chronicleFilters[target]) || '');
  return sliceChip(filterValue, cls, target);
}}
function sliceButtonRow(buttons) {{
  return buttons.length > 0 ? '<p>' + buttons.join('') + '</p>' : '';
}}
function reviewerBoundaryListButtons(target, endpoint, rows) {{
  const enforcementCounts = {{}};
  const gateCounts = {{}};
  (rows || []).forEach(row => {{
    const enforcementStatus = String(row.reviewer_enforcement_status || '');
    const gateStatus = String(row.reviewer_validation_gate_status || '');
    if (enforcementStatus) enforcementCounts[enforcementStatus] = (enforcementCounts[enforcementStatus] || 0) + 1;
    if (gateStatus) gateCounts[gateStatus] = (gateCounts[gateStatus] || 0) + 1;
  }});
  return [
    ...Object.entries(enforcementCounts).map(([status]) =>
      listJumpButton(
        reviewerBoundaryStatusLabel('reviewer_enforcement', status),
        endpoint,
        target,
        reviewerBoundaryFilterValue('reviewer_enforcement', status),
      )
    ),
    ...Object.entries(gateCounts).map(([status]) =>
      listJumpButton(
        reviewerBoundaryStatusLabel('reviewer_gate', status),
        endpoint,
        target,
        reviewerBoundaryFilterValue('reviewer_gate', status),
      )
    ),
  ];
}}
function reviewerBoundaryCountButtons(target, endpoint, enforcementCounts, gateCounts) {{
  return [
    ...Object.entries(enforcementCounts || {{}}).map(([status, count]) =>
      overviewCountButton(
        reviewerBoundaryStatusLabel('reviewer_enforcement', status),
        count,
        'badge-neutral',
        endpoint,
        target,
        reviewerBoundaryFilterValue('reviewer_enforcement', status),
      )
    ),
    ...Object.entries(gateCounts || {{}}).map(([status, count]) =>
      overviewCountButton(
        reviewerBoundaryStatusLabel('reviewer_gate', status),
        count,
        'badge-neutral',
        endpoint,
        target,
        reviewerBoundaryFilterValue('reviewer_gate', status),
      )
    ),
  ].join('');
}}
function reviewQueueFilterChips() {{
  return filterChips('reviewQueue', 'badge-warning');
}}
function reviewQueueSliceButtons() {{
  return [
    listJumpButton(filterValueLabel('reviewQueue', 'review_requested'), '/api/review-queue', 'reviewQueue', 'review_requested'),
    listJumpButton(filterValueLabel('reviewQueue', 'ready'), '/api/review-queue', 'reviewQueue', 'ready'),
    listJumpButton(filterValueLabel('reviewQueue', 'advisory'), '/api/review-queue', 'reviewQueue', 'advisory'),
    listJumpButton(filterValueLabel('reviewQueue', 'drift_detected'), '/api/review-queue', 'reviewQueue', 'drift_detected'),
    listJumpButton(filterValueLabel('reviewQueue', 'package:package_context_available'), '/api/review-queue', 'reviewQueue', 'package:package_context_available'),
    listJumpButton(reviewWarningLabel('ui_auth_not_enabled'), '/api/review-queue', 'reviewQueue', 'ui_auth_not_enabled'),
    listJumpButton(reviewWarningLabel('reviewer_identity_declared_only'), '/api/review-queue', 'reviewQueue', 'reviewer_identity_declared_only'),
  ];
}}
function runtimeRecordsFilterChips() {{
  return filterChips('runtimeRecords', 'badge-neutral');
}}
function summaryJobsFilterChips() {{
  return filterChips('summaryJobs', 'badge-neutral');
}}
function runtimeRecordsSliceButtons() {{
  return [
    listJumpButton(filterValueLabel('runtimeRecords', 'preview_only'), '/api/runtime-records', 'runtimeRecords', 'preview_only'),
    listJumpButton(filterValueLabel('runtimeRecords', 'advisory_only'), '/api/runtime-records', 'runtimeRecords', 'advisory_only'),
    listJumpButton(filterValueLabel('runtimeRecords', 'boundary_aligned'), '/api/runtime-records', 'runtimeRecords', 'boundary_aligned'),
    listJumpButton(filterValueLabel('runtimeRecords', 'retrieval_plan'), '/api/runtime-records', 'runtimeRecords', 'retrieval_plan'),
    listJumpButton(filterValueLabel('runtimeRecords', 'response_id'), '/api/runtime-records', 'runtimeRecords', 'response_id'),
  ];
}}
function summaryJobsSliceButtons() {{
  return [
    listJumpButton(filterValueLabel('summaryJobs', 'preview_only'), '/api/summary-jobs', 'summaryJobs', 'preview_only'),
    listJumpButton(filterValueLabel('summaryJobs', 'advisory_only'), '/api/summary-jobs', 'summaryJobs', 'advisory_only'),
    listJumpButton(filterValueLabel('summaryJobs', 'package_context_available'), '/api/summary-jobs', 'summaryJobs', 'package_context_available'),
    listJumpButton(filterValueLabel('summaryJobs', 'boundary_aligned'), '/api/summary-jobs', 'summaryJobs', 'boundary_aligned'),
    listJumpButton(filterValueLabel('summaryJobs', 'response_id'), '/api/summary-jobs', 'summaryJobs', 'response_id'),
  ];
}}
function activeViewSummary(endpoint, mode) {{
  const parts = [];
  const currentEndpoint = endpoint || window.__chronicleCurrentEndpoint || '/api/overview';
  parts.push(label('status.view', 'view') + '=' + currentEndpoint);
  const filterLabel = currentFilterLabel();
  if (filterLabel) parts.push(filterLabel);
  const sortLabel = currentSortLabel(currentEndpoint);
  if (sortLabel) parts.push(sortLabel);
  if (mode === 'detail') {{
    const trailLabel = currentTrailLabel();
    if (trailLabel) parts.push(label('status.trail', 'trail') + '=' + trailLabel);
  }}
  return '<p class="id">' + esc(label('status.active_view', 'Active view')) + ': ' + esc(parts.join(' | ')) + '</p>';
}}
function humanizeDetailPath(path) {{
  const parts = String(path || '').split('/').filter(Boolean);
  if (parts.length < 3 || parts[0] !== 'api') return String(path || '');
  const resource = parts[1];
  const recordId = parts[2];
  return label('detail.resource.' + resource, resource) + ': ' + recordId;
}}
function overviewJumpButton(label, endpoint, filterTarget, filterValue, variant) {{
  const targetAttr = filterTarget ? ' data-filter-target="' + esc(filterTarget) + '"' : '';
  const valueAttr = filterValue ? ' data-filter-value="' + esc(filterValue) + '"' : '';
  const className = variant ? ' class="' + esc(variant) + '"' : '';
  return '<button' + className + ' data-jump="' + esc(endpoint) + '"' + targetAttr + valueAttr + '>'
    + label + '</button>';
}}
function listJumpButton(label, endpoint, filterTarget, filterValue, variant) {{
  return overviewJumpButton(esc(label), endpoint, filterTarget, filterValue, variant);
}}
function openEndpointButton(endpoint) {{
  if (endpoint === '/api/runtime-records') return listJumpButton(label('button.open_runtime_records', 'Open Runtime Records'), endpoint);
  if (endpoint === '/api/review-queue') return listJumpButton(label('button.open_review_queue', 'Open Review Queue'), endpoint);
  if (endpoint === '/api/summary-jobs') return listJumpButton(label('button.open_summary_jobs', 'Open Summary Jobs'), endpoint);
  if (endpoint === '/api/runtime-config') return listJumpButton(label('button.open_runtime_config', 'Open Runtime Config'), endpoint);
  if (endpoint === '/api/package-review') return listJumpButton(label('button.open_package_review', 'Open Package Review'), endpoint);
  return listJumpButton(humanizeDetailPath(endpoint), endpoint);
}}
function latestResponseButton(path, labelKey, fallbackLabel) {{
  return path ? listJumpButton(label(labelKey, fallbackLabel), path) : '';
}}
function endpointLatestResponseCluster(endpoint, path, labelKey, fallbackLabel) {{
  return navigationCluster([
    openEndpointButton(endpoint),
    latestResponseButton(path, labelKey, fallbackLabel),
  ]);
}}
function moreSliceButton(filterValue, endpoint, filterTarget) {{
  const value = String(filterValue || '');
  if (!value) return '';
  return listJumpButton('More ' + value, endpoint, filterTarget, value);
}}
function sectionTitle(text) {{
  return '<h3>' + esc(uiLabel(text)) + '</h3>';
}}
function detailLine(label, value) {{
  return '<div class="fact-line"><div class="fact-label">' + esc(uiLabel(label))
    + '</div><div class="fact-value">' + esc(value || '') + '</div></div>';
}}
function detailListLine(label, values, separator) {{
  const items = Array.isArray(values) ? values : [];
  const joiner = separator || ', ';
  return detailLine(label, items.join(joiner) || '(none)');
}}
function summaryJsonLine(label, value) {{
  return '<div class="fact-line"><div class="fact-label">' + esc(uiLabel(label))
    + '</div><div class="fact-value fact-code">' + esc(JSON.stringify(value || {{}})) + '</div></div>';
}}
function messageParagraph(message) {{
  return '<p>' + esc(localizeTextValue(message || '')) + '</p>';
}}
function buttonRow(buttons) {{
  return buttons.length > 0 ? '<p>' + buttons.join('') + '</p>' : '';
}}
function navigationCluster(buttons) {{
  const items = Array.isArray(buttons) ? buttons.filter(Boolean) : [];
  return items.length > 0 ? '<p>' + items.join('') + '</p>' : '';
}}
function detailNavButton(path, labelText) {{
  if (!path) return '';
  const resolvedLabel = labelText || humanizeDetailPath(path);
  return '<button data-detail-nav="' + esc(path) + '">'
    + esc(localizeTextValue(resolvedLabel))
    + '</button>';
}}
function reviewDetailButton(eventId) {{
  return eventId ? detailNavButton('/api/review-queue/' + eventId, label('button.open_review', 'Open review')) : '';
}}
function moreStatusButtons(status, endpoint, filterTarget, prefix = '') {{
  if (!status) return [];
  return [listJumpButton(label('status.more', 'More') + ' ' + status, endpoint, filterTarget, prefix + status)];
}}
function reviewQueueStatusButtons(status, prefix = '') {{
  return moreStatusButtons(status, '/api/review-queue', 'reviewQueue', prefix);
}}
function statusMessageBody(status, message, buttons = []) {{
  return detailLine('Status', status || '') + buttonRow(buttons) + messageParagraph(message);
}}
function routeHeading(endpoint) {{
  return '<h2>' + esc(endpoint === '/api/overview' ? label('nav./api/overview', 'Overview') : endpoint) + '</h2>';
}}
function prettyJsonPre(value) {{
  return '<pre>' + esc(JSON.stringify(value, null, 2)) + '</pre>';
}}
function collapsibleJsonBlock(summaryLabel, value, open = false) {{
  return '<details class="json-block"' + (open ? ' open' : '') + '><summary>'
    + esc(summaryLabel)
    + '</summary>'
    + prettyJsonPre(value)
    + '</details>';
}}
function noticeSection(title, body) {{
  return '<section class="notice-section"><h4>' + esc(title) + '</h4>' + body + '</section>';
}}
function collapsibleSection(title, body, open = false) {{
  return '<details class="fold-section"' + (open ? ' open' : '') + '><summary>'
    + esc(title)
    + '</summary>'
    + body
    + '</details>';
}}
function metricsSection(body) {{
  return collapsibleSection(label('section.metrics', 'Metrics'), body, false);
}}
function renderNotice(title, body) {{
  return '<div class="notice">' + sectionTitle(title) + body + '</div>';
}}
function packageReviewButtons(record) {{
  return (record.package_handoff_preview || record.package_readiness)
    ? [openEndpointButton('/api/package-review')]
    : [];
}}
function firstRelatedLink(record, prefix) {{
  const links = Array.isArray(record.related_links) ? record.related_links : [];
  return links.find(item => String(item.path || '').startsWith(prefix)) || null;
}}
function relatedDetailButton(record, prefix, fallbackLabel = '') {{
  const link = firstRelatedLink(record, prefix);
  return link ? detailNavButton(link.path || '', link.label || fallbackLabel) : '';
}}
function runtimeRelatedButtons(record) {{
  const buttons = [openEndpointButton('/api/runtime-records')];
  const runtimeKind = record.runtime_record_kind || (record.runtime_record_preview && record.runtime_record_preview.record_kind) || '';
  if (runtimeKind) buttons.push(moreSliceButton(runtimeKind, '/api/runtime-records', 'runtimeRecords'));
  const summaryLink = firstRelatedLink(record, '/api/summary-jobs/');
  if (summaryLink) buttons.push(listJumpButton(localizeTextValue(summaryLink.label || 'Open summary job'), summaryLink.path));
  const artifactLink = firstRelatedLink(record, '/api/artifacts/');
  if (artifactLink) buttons.push(listJumpButton(localizeTextValue(artifactLink.label || 'Open artifact'), artifactLink.path));
  return buttons;
}}
function reviewRelatedButtons(record) {{
  const buttons = [openEndpointButton('/api/review-queue')];
  const capability = record.review_capability || {{}};
  const readiness = record.package_readiness || {{}};
  const warnings = Array.isArray(capability.warnings) ? capability.warnings : [];
  if (record.review_kind) buttons.push(moreSliceButton(record.review_kind, '/api/review-queue', 'reviewQueue'));
  if (capability.status) buttons.push(moreSliceButton(capability.status, '/api/review-queue', 'reviewQueue'));
  warnings.slice(0, 2).forEach(code => buttons.push(moreSliceButton(code, '/api/review-queue', 'reviewQueue')));
  if (readiness.status) buttons.push(listJumpButton(label('status.more', 'More') + ' ' + readiness.status, '/api/review-queue', 'reviewQueue', 'package:' + readiness.status));
  return buttons;
}}
function summaryRelatedButtons(record) {{
  const buttons = [openEndpointButton('/api/summary-jobs')];
  if (record.review_target_event_id) buttons.push(openEndpointButton('/api/review-queue'));
  const capability = record.review_capability || {{}};
  const readiness = record.package_readiness || {{}};
  const parity = record.cli_parity || {{}};
  if (capability.status) buttons.push(moreSliceButton(capability.status, '/api/review-queue', 'reviewQueue'));
  if (readiness.status) buttons.push(listJumpButton(label('status.more', 'More') + ' ' + readiness.status, '/api/review-queue', 'reviewQueue', 'package:' + readiness.status));
  if (parity.status) buttons.push(moreSliceButton(parity.status, '/api/review-queue', 'reviewQueue'));
  return buttons;
}}
function relatedListButtons(detailEndpoint, record) {{
  const buttons = [];
  if (detailEndpoint.startsWith('/api/runtime-records/')) buttons.push(...runtimeRelatedButtons(record));
  if (detailEndpoint.startsWith('/api/review-queue/')) buttons.push(...reviewRelatedButtons(record));
  if (detailEndpoint.startsWith('/api/summary-jobs/')) buttons.push(...summaryRelatedButtons(record));
  buttons.push(...packageReviewButtons(record));
  return navigationCluster(buttons);
}}
function renderNavigationNotice(endpoint, record, options = {{}}) {{
  const filterLabel = options.filterLabel || '';
  const previousDetail = options.previousDetail || '';
  const trailLabel = options.trailLabel || '';
  const trailButtons = options.trailButtons || '';
  const listButtons = options.listButtons || relatedListButtons(endpoint, record);
  return renderNotice(
    label('notice.navigation', 'Navigation'),
    activeViewSummary(endpoint, 'detail')
      + '<p><button data-back-view="true">' + esc(label('button.back_current_list', 'Back to current list')) + '</button> '
      + (previousDetail ? '<button data-back-detail="true">' + esc(label('button.back_previous_detail', 'Back to previous detail')) + '</button> ' : '')
      + (hasActiveFilters() ? '<button data-reset-filters="all">' + esc(label('button.reset_filter', 'Reset Filter')) + '</button> ' : '')
      + '<span class="id">' + esc(window.__chronicleCurrentEndpoint || '/api/overview') + '</span> → '
      + '<span class="id">' + esc(endpoint) + '</span>'
      + (filterLabel ? ' <span class="id">(' + esc(filterLabel) + ')</span>' : '')
      + (previousDetail ? ' <span class="id">prev=' + esc(previousDetail) + '</span>' : '')
      + '</p>'
      + (trailLabel ? '<p><span class="id">trail=' + esc(trailLabel) + '</span></p>' : '')
      + (trailButtons ? '<p>' + trailButtons + '</p>' : '')
      + (listButtons ? '<p>' + listButtons + '</p>' : '')
  );
}}
function renderRuntimePreviewNotice(record) {{
  if (!record.runtime_record_preview) return '';
  const preview = record.runtime_record_preview;
  const localizedTitle = preview.title_key
    ? formatLabel(preview.title_key, preview.title_params || {{}}, preview.title || '')
    : (preview.title || '');
  return renderNotice(
    label('notice.runtime_preview', 'Runtime Preview'),
    '<p><strong>' + esc(localizedTitle) + '</strong></p>'
      + '<p>' + esc(preview.preview_text || '') + '</p>'
      + detailLine('Kind', preview.record_kind || record.runtime_record_kind || '')
      + summaryJsonLine('Source counts', preview.source_counts)
      + detailListLine('Referenced IDs', preview.referenced_record_ids)
      + detailLine('CLI', preview.suggested_cli_family || '')
  );
}}
function packageContextDetailLines(packageReview, manifest, eligibleContextIds = [], extraLines = '') {{
  return detailListLine('Eligible contexts', eligibleContextIds)
    + extraLines
    + detailLine('Package review status', (packageReview && packageReview.status) || '(not available)')
    + detailListLine('Package warnings', packageReview && packageReview.package_warnings)
    + detailListLine('Manifest refs', manifest && manifest.referenced_records);
}}
function writeRouteDetailLines(writeRouteContract, identityProofContract, authorizationContract, targetStateContract, includeRequestFields = false) {{
  const localizedFailureFamilies = (writeRouteContract.failure_families || []).map(item => {{
    const summary = item && item.summary_key
      ? formatLabel(item.summary_key, item.summary_params || {{}}, item.summary || '')
      : (item.summary || '');
    return ((item.family || 'family') + ': ' + summary + '; ' + ((item.possible_error_codes || []).join(', ')));
  }});
  const localizedTargetStateScopeNote = targetStateContract.scope_note_key
    ? formatLabel(targetStateContract.scope_note_key, targetStateContract.scope_note_params || {{}}, targetStateContract.scope_note || '')
    : (targetStateContract.scope_note || '');
  const localizedResolvedBehaviorNote = targetStateContract.resolved_behavior_note_key
    ? formatLabel(targetStateContract.resolved_behavior_note_key, targetStateContract.resolved_behavior_params || {{}}, targetStateContract.resolved_behavior_note || '')
    : (targetStateContract.resolved_behavior_note || '');
  const localizedActionTargetMatrix = (targetStateContract.action_target_matrix || []).map(item => (
    item && item.summary_key
      ? formatLabel(item.summary_key, item.summary_params || {{}}, item.summary || '')
      : ((item.action || 'action') + ': pending=' + String(item.requires_pending) + '; queue=' + (item.resulting_queue_state || '') + '; disposition=' + (item.resulting_disposition || ''))
  ));
  const localizedActionAuthorizationMatrix = (authorizationContract.action_authorization_matrix || []).map(item => (
    item && item.summary_key
      ? formatLabel(item.summary_key, item.summary_params || {{}}, item.summary || '')
      : ((item.action || 'action') + ': intent=' + (item.ui_intent || '') + '; pending=' + String(item.pending_required) + '; note=' + (item.note_status || ''))
  ));
  const localizedStatusCodeContract = (writeRouteContract.status_code_contract || []).map(item => {{
    if (item && item.summary_key) {{
      return formatLabel(item.summary_key, item.summary_params || {{}}, item.summary || '');
    }}
    const localizedWhen = item && item.when_key
      ? formatLabel(item.when_key, item.when_params || {{}}, item.when || '')
      : (item.when || '');
    return (String(item.status_code ?? '') + ': ' + (item.family || 'family') + '; ' + localizedWhen);
  }});
  const localizedActionRoutes = (writeRouteContract.action_routes || []).map(item => (
    item && item.path_summary_key
      ? formatLabel(item.path_summary_key, item.path_summary_params || {{}}, item.path_summary || '')
      : ((item.action || 'action') + ': ' + (item.path_template || ''))
  ));
  const localizedCliRouteEquivalents = (writeRouteContract.action_routes || []).map(item => (
    item && item.cli_summary_key
      ? formatLabel(item.cli_summary_key, item.cli_summary_params || {{}}, item.cli_summary || '')
      : ((item.action || 'action') + ': ' + (item.cli_equivalent_template || ''))
  ));
  const localizedWriteRequestFields = (writeRouteContract.expected_request_field_details || []).map(item => (
    item && item.summary_key
      ? formatLabel(item.summary_key, item.summary_params || {{}}, item.summary || '')
      : (item.summary || item.field || '')
  ));
  const localizedWriteSuccessStatus = writeRouteContract.success_status_summary_key
    ? formatLabel(writeRouteContract.success_status_summary_key, writeRouteContract.success_status_summary_params || {{}}, writeRouteContract.success_status_summary || String(writeRouteContract.success_status_code ?? ''))
    : (writeRouteContract.success_status_summary || String(writeRouteContract.success_status_code ?? ''));
  const localizedWriteBlockedStatus = writeRouteContract.blocked_status_summary_key
    ? formatLabel(writeRouteContract.blocked_status_summary_key, writeRouteContract.blocked_status_summary_params || {{}}, writeRouteContract.blocked_status_summary || String(writeRouteContract.blocked_status_code ?? ''))
    : (writeRouteContract.blocked_status_summary || String(writeRouteContract.blocked_status_code ?? ''));
  const localizedTransactionOrder = (writeRouteContract.transaction_order_details || []).map(item => (
    item && item.summary_key
      ? formatLabel(item.summary_key, item.summary_params || {{}}, item.summary || '')
      : (item.summary || item.step || '')
  ));
  const localizedAuthorizationStatus = authorizationContract.authorization_status_summary_key
    ? formatLabel(authorizationContract.authorization_status_summary_key, authorizationContract.authorization_status_summary_params || {{}}, authorizationContract.authorization_status_summary || authorizationContract.authorization_status || '')
    : (authorizationContract.authorization_status_summary || authorizationContract.authorization_status || '');
  const localizedRequiredAssurance = authorizationContract.required_identity_assurance_status_summary_key
    ? formatLabel(authorizationContract.required_identity_assurance_status_summary_key, authorizationContract.required_identity_assurance_status_summary_params || {{}}, authorizationContract.required_identity_assurance_status_summary || authorizationContract.required_identity_assurance_status || '')
    : (authorizationContract.required_identity_assurance_status_summary || authorizationContract.required_identity_assurance_status || '');
  const localizedAuthorizationChecks = (authorizationContract.server_side_check_details || []).map(item => (
    item && item.summary_key
      ? formatLabel(item.summary_key, item.summary_params || {{}}, item.summary || '')
      : (item.summary || item.code || '')
  ));
  const localizedRequiredReviewStatus = targetStateContract.required_current_review_status_summary_key
    ? formatLabel(targetStateContract.required_current_review_status_summary_key, targetStateContract.required_current_review_status_summary_params || {{}}, targetStateContract.required_current_review_status_summary || targetStateContract.required_current_review_status || '')
    : (targetStateContract.required_current_review_status_summary || targetStateContract.required_current_review_status || '');
  const localizedTargetStateChecks = (targetStateContract.target_state_check_details || []).map(item => (
    item && item.summary_key
      ? formatLabel(item.summary_key, item.summary_params || {{}}, item.summary || '')
      : (item.summary || item.code || '')
  ));
  const localizedIdentityProofStatus = identityProofContract.proof_status_message_key
    ? formatLabel(identityProofContract.proof_status_message_key, identityProofContract.proof_status_message_params || {{}}, identityProofContract.proof_status_message || identityProofContract.proof_status || '')
    : (identityProofContract.proof_status_message || identityProofContract.proof_status || '');
  const localizedIdentityProofFields = (identityProofContract.required_identity_field_details || []).map(item => (
    item && item.summary_key
      ? formatLabel(item.summary_key, item.summary_params || {{}}, item.summary || '')
      : (item.summary || item.field || '')
  ));
  return detailLine('Write route', writeRouteContract.route_template || '')
    + detailListLine('Write actions', writeRouteContract.actions, ' | ')
    + detailListLine('Action routes', localizedActionRoutes, ' | ')
    + detailListLine('CLI route equivalents', localizedCliRouteEquivalents, ' | ')
    + detailListLine('Status-code contract', localizedStatusCodeContract, ' | ')
    + (includeRequestFields ? detailListLine('Write request fields', localizedWriteRequestFields.length > 0 ? localizedWriteRequestFields : writeRouteContract.expected_request_fields, ' | ') : '')
    + detailLine('Mutation token required', String(writeRouteContract.mutation_token_required))
    + detailLine('Mutation token header', writeRouteContract.mutation_token_header || '')
    + detailLine('Write success status', localizedWriteSuccessStatus)
    + detailLine('Write blocked status', localizedWriteBlockedStatus)
    + detailListLine('Durable success requirements', writeRouteContract.durable_success_requirements, ' | ')
    + detailListLine('Transaction order', localizedTransactionOrder.length > 0 ? localizedTransactionOrder : writeRouteContract.transaction_order, ' | ')
    + detailLine('Authorization status', localizedAuthorizationStatus)
    + detailLine('Required assurance', localizedRequiredAssurance)
    + detailLine('Pending target required', authorizationContract.target_pending_required)
    + detailListLine('Authorization checks', localizedAuthorizationChecks.length > 0 ? localizedAuthorizationChecks : authorizationContract.server_side_checks, ' | ')
    + detailListLine('Action authorization matrix', localizedActionAuthorizationMatrix, ' | ')
    + detailLine('Required review status', localizedRequiredReviewStatus)
    + detailLine('Resolved status code', targetStateContract.resolved_status_code ?? '')
    + detailListLine('Target-state checks', localizedTargetStateChecks.length > 0 ? localizedTargetStateChecks : targetStateContract.target_state_checks, ' | ')
    + detailLine('Target-state scope note', localizedTargetStateScopeNote)
    + detailListLine('Action target matrix', localizedActionTargetMatrix, ' | ')
    + detailLine('Resolved behavior note', localizedResolvedBehaviorNote)
    + detailListLine('Failure families', localizedFailureFamilies, ' | ')
    + detailLine('Identity proof status', localizedIdentityProofStatus)
    + detailListLine('Identity proof fields', localizedIdentityProofFields.length > 0 ? localizedIdentityProofFields : identityProofContract.required_identity_fields, ' | ');
}}
function mutationOperationalDetailLines(operationalReadiness, blockerSummaries, enablementChecks, checksLabel = 'Enablement checks') {{
  const localizedChecks = enablementChecks.map(check => {{
    const label = check && check.label_key
      ? formatLabel(check.label_key, check.label_params || {{}}, check.label || check.code || 'check')
      : (check.label || check.code || 'check');
    return (check.satisfied ? 'ok: ' : 'blocked: ') + label;
  }});
  const localizedRemainingChecks = (Array.isArray(operationalReadiness.unsatisfied_checks) ? operationalReadiness.unsatisfied_checks : []).map(item => (
    item && item.summary_key
      ? formatLabel(item.summary_key, item.summary_params || {{}}, ((item.label || item.code || 'check') + ': ' + (item.detail || '')))
      : ((item.label || item.code || 'check') + ': ' + (item.detail || ''))
  ));
  const localizedOperationalMessage = operationalReadiness.message_key
    ? formatLabel(operationalReadiness.message_key, operationalReadiness.message_params || {{}}, operationalReadiness.message || '')
    : localizeTextValue(operationalReadiness.message || '');
  return detailLine('Operational readiness', operationalReadiness.status || '')
    + detailLine('Operational summary', localizedOperationalMessage)
    + detailLine('Remaining prerequisites', operationalReadiness.remaining_count ?? 0)
    + detailListLine('Blocker sources', blockerSummaries.map(item => (
      item && item.summary_key
        ? formatLabel(item.summary_key, item.summary_params || {{}}, item.summary || item.code || 'blocker')
        : (item.summary || ((item.source_label || item.source || 'unknown') + ': ' + (item.message || item.code || 'blocker')))
    )), ' | ')
    + detailListLine(checksLabel, localizedChecks, ' | ')
    + detailListLine('Remaining checks', localizedRemainingChecks.length > 0 ? localizedRemainingChecks : (operationalReadiness.blocking_summaries || []), ' | ');
}}
function reviewerLabelDetailLines(reviewerContext) {{
  return detailLine('Reviewer label pattern', reviewerContext.reviewer_label_pattern || '')
    + detailListLine('Reviewer label examples', reviewerContext.reviewer_label_examples, ' | ')
    + detailLine('Session label pattern', reviewerContext.session_label_pattern || '');
}}
function recoveryContractDetailLines(failureContract, targetId = 'action-preview-response') {{
  const recoveryCommands = Array.isArray(failureContract.recovery_commands) ? failureContract.recovery_commands : [];
  const localizedPossibleErrors = (Array.isArray(failureContract.possible_error_details) ? failureContract.possible_error_details : []).map(item => (
    item && item.message_key
      ? formatLabel(item.message_key, item.message_params || {{}}, item.message || item.code || '')
      : (item.message || item.code || '')
  ));
  const localizedRecoveryCommands = (Array.isArray(failureContract.recovery_command_details) ? failureContract.recovery_command_details : []).map(item => (
    item && item.summary_key
      ? formatLabel(item.summary_key, item.summary_params || {{}}, item.summary || item.command || '')
      : (item.summary || item.command || '')
  ));
  const localizedRollbackStatus = failureContract.rollback_status_summary_key
    ? formatLabel(failureContract.rollback_status_summary_key, failureContract.rollback_status_summary_params || {{}}, failureContract.rollback_status_summary || failureContract.rollback_status || '')
    : (failureContract.rollback_status_summary || failureContract.rollback_status || '');
  const localizedDurableOnFailure = typeof failureContract.durable_mutation_reported_on_failure === 'boolean'
    ? (
      failureContract.durable_mutation_reported_on_failure_summary_key
        ? formatLabel(failureContract.durable_mutation_reported_on_failure_summary_key, failureContract.durable_mutation_reported_on_failure_summary_params || {{}}, failureContract.durable_mutation_reported_on_failure_summary || String(failureContract.durable_mutation_reported_on_failure))
        : (failureContract.durable_mutation_reported_on_failure_summary || String(failureContract.durable_mutation_reported_on_failure))
    )
    : '';
  return detailLine('Rollback status', localizedRollbackStatus)
    + detailLine('Durable mutation on failure', localizedDurableOnFailure)
    + detailLine('Recovery path', failureContract.recovery_path || '')
    + detailListLine('Possible errors', localizedPossibleErrors.length > 0 ? localizedPossibleErrors : failureContract.possible_error_codes, ' | ')
    + detailListLine('Recovery commands', localizedRecoveryCommands.length > 0 ? localizedRecoveryCommands : recoveryCommands, ' | ')
    + (failureContract.recovery_path ? '<p>' + copyCommandButton(failureContract.recovery_path, targetId, t('button.copy_recovery_cli')) + '</p>' : '')
    + (recoveryCommands.length > 0 ? '<p>' + recoveryCommands.map(command => copyCommandButton(command, targetId, t('button.copy_cli'))).join(' ') + '</p>' : '');
}}
function identityBoundaryDetailLines(identityBoundary) {{
  return detailLine('Missing identity rows', identityBoundary.missing_identity_count ?? 0)
    + detailLine('Declared-only rows', identityBoundary.declared_identity_count ?? 0)
    + detailLine('Session-label-missing rows', identityBoundary.session_label_missing_count ?? 0)
    + detailListLine('Identity blockers', identityBoundary.blockers, ' | ')
    + detailListLine('Identity next steps', identityBoundary.next_steps, ' | ');
}}
function renderRetrievalHandoffNotice(record) {{
  if (!record.retrieval_handoff) return '';
  const handoff = record.retrieval_handoff;
  const localizedMessage = localizedPayloadText(handoff);
  const localizedDownstreamCommands = (Array.isArray(handoff.downstream_command_details) ? handoff.downstream_command_details : []).map(item => (
    item && item.summary_key
      ? formatLabel(item.summary_key, item.summary_params || {{}}, item.summary || item.command || '')
      : (item.summary || item.command || '')
  ));
  const localizedHitCounts = handoff.hit_counts_summary_key
    ? formatLabel(
        handoff.hit_counts_summary_key,
        handoff.hit_counts_summary_params || {{}},
        'Hit counts: vector=' + String(handoff.vector_hit_count || 0)
          + ', graph=' + String(handoff.graph_hit_count || 0)
          + ', chronicle=' + String(handoff.chronicle_hit_count || 0)
      )
    : ('Hit counts: vector=' + String(handoff.vector_hit_count || 0)
        + ', graph=' + String(handoff.graph_hit_count || 0)
        + ', chronicle=' + String(handoff.chronicle_hit_count || 0));
  return renderNotice(
    label('notice.retrieval_handoff', 'Retrieval Handoff'),
    messageParagraph(localizedMessage)
      + detailLine('Query', handoff.query || '')
      + '<p>' + esc(localizedHitCounts) + '</p>'
      + detailListLine('Referenced IDs', handoff.referenced_record_ids)
      + detailListLine('Downstream commands', localizedDownstreamCommands.length > 0 ? localizedDownstreamCommands : handoff.downstream_commands, ' | ')
      + detailListLine('Notes', handoff.notes, ' | ')
  );
}}
function packageContextNoticeBody(status, message, packageReview, manifest, eligibleContextIds = [], extraLines = '', buttons = []) {{
  return statusMessageBody(status, message, buttons)
    + packageContextDetailLines(
      packageReview,
      manifest,
      eligibleContextIds,
      extraLines,
    );
}}
function statusScopeNoticeBody(status, message, buttons = [], scopeNote = '') {{
  return statusMessageBody(status, message, buttons)
    + detailLine('Scope note', scopeNote || '');
}}
function blockerSummaryDetailLines(blockerDetails, blockers, blockerSummaries = [], nextSteps = []) {{
  return detailLine('Blockers', detailMessages(blockerDetails, blockers))
    + detailListLine('Blocker summaries', blockerSummaries.map(item => (
      item && item.summary_key
        ? formatLabel(item.summary_key, item.summary_params || {{}}, item.summary || item.code || 'blocker')
        : (item.summary || item.code || 'blocker')
    )), ' | ')
    + detailListLine('Next steps', nextSteps, ' | ');
}}
function renderPackageHandoffPreviewNotice(record) {{
  if (!record.package_handoff_preview) return '';
  const preview = record.package_handoff_preview;
  const packageReview = preview.package_review || {{}};
  const manifest = preview.package_manifest_preview || {{}};
  const localizedSuggestedCommands = (Array.isArray(preview.suggested_command_details) ? preview.suggested_command_details : []).map(item => (
    item && item.summary_key
      ? formatLabel(item.summary_key, item.summary_params || {{}}, item.summary || item.command || '')
      : (item.summary || item.command || '')
  ));
  const localizedCounts = preview.counts_summary_key
    ? formatLabel(preview.counts_summary_key, preview.counts_summary_params || {{}}, '')
    : '';
  const localizedBoundaryNote = preview.boundary_note_key
    ? formatLabel(preview.boundary_note_key, {{}}, preview.boundary_note || '')
    : (preview.boundary_note || '');
  return renderNotice(
    label('notice.package_handoff_preview', 'Package Handoff Preview'),
    packageContextNoticeBody(
      preview.status,
      localizedPayloadText(preview),
      packageReview,
      manifest,
      preview.eligible_context_ids,
      detailLine('Hit counts', localizedCounts)
      + detailListLine('Skipped records', preview.skipped_record_ids)
      + detailListLine('Suggested commands', localizedSuggestedCommands.length > 0 ? localizedSuggestedCommands : preview.suggested_commands, ' | ')
      + detailLine('Scope note', localizedBoundaryNote),
    )
  );
}}
function renderInvocationPlanNotice(record) {{
  if (!record.invocation_plan) return '';
  const plan = record.invocation_plan;
  const requestPreview = plan.request_preview || {{}};
  const executionRequest = plan.execution_request || {{}};
  const downstreamCommands = Array.isArray(plan.downstream_commands) ? plan.downstream_commands : [];
  const localizedDownstreamCommands = (Array.isArray(plan.downstream_command_details) ? plan.downstream_command_details : []).map(item => (
    item && item.summary_key
      ? formatLabel(item.summary_key, item.summary_params || {{}}, item.summary || item.command || '')
      : (item.summary || item.command || '')
  ));
  const localizedMessage = localizedPayloadText(plan);
  const localizedProviderSummary = plan.provider_summary_key
    ? formatLabel(
        plan.provider_summary_key,
        plan.provider_summary_params || {{}},
        (plan.provider_kind || '') + ' / ' + (plan.provider_name || '')
      )
    : ((plan.provider_kind || '') + ' / ' + (plan.provider_name || ''));
  const localizedInvocationReady = plan.invocation_ready_summary_key
    ? formatLabel(plan.invocation_ready_summary_key, plan.invocation_ready_summary_params || {{}}, plan.invocation_ready_summary || String(plan.invocation_ready))
    : (plan.invocation_ready_summary || String(plan.invocation_ready));
  const localizedWouldUseNetwork = plan.would_use_network_summary_key
    ? formatLabel(plan.would_use_network_summary_key, plan.would_use_network_summary_params || {{}}, plan.would_use_network_summary || String(plan.would_use_network))
    : (plan.would_use_network_summary || String(plan.would_use_network));
  const localizedNetworkAllowed = plan.network_allowed_by_contract_summary_key
    ? formatLabel(plan.network_allowed_by_contract_summary_key, plan.network_allowed_by_contract_summary_params || {{}}, plan.network_allowed_by_contract_summary || String(plan.network_allowed_by_contract))
    : (plan.network_allowed_by_contract_summary || String(plan.network_allowed_by_contract));
  return renderNotice(
    label('notice.invocation_plan', 'Invocation Plan'),
    messageParagraph(localizedMessage)
      + detailLine('Provider', localizedProviderSummary)
      + detailLine('Model', plan.model_name || '')
      + detailLine('Operation', plan.operation || '')
      + detailLine('Invocation ready', localizedInvocationReady)
      + detailLine('Would use network', localizedWouldUseNetwork)
      + detailLine('Network allowed by contract', localizedNetworkAllowed)
      + detailListLine('Blocking reasons', plan.blocking_reasons, ' | ')
      + summaryJsonLine('Request preview', requestPreview)
      + summaryJsonLine('Execution request', executionRequest)
      + detailListLine('Downstream commands', localizedDownstreamCommands.length > 0 ? localizedDownstreamCommands : plan.downstream_commands, ' | ')
      + (downstreamCommands.length > 0 ? '<p>' + downstreamCommands.map(command => copyCommandButton(command, 'action-preview-response', t('button.copy_cli'))).join(' ') + '</p>' : '')
      + detailListLine('Notes', plan.notes, ' | ')
  );
}}
function responseMetadataDetailLines(summary) {{
  const localizedFinishReason = summary.finish_reason_summary_key
    ? formatLabel(summary.finish_reason_summary_key, summary.finish_reason_summary_params || {{}}, summary.finish_reason_summary || summary.finish_reason || '')
    : (summary.finish_reason_summary || summary.finish_reason || '');
  const localizedProviderStatus = summary.provider_status_summary_key
    ? formatLabel(summary.provider_status_summary_key, summary.provider_status_summary_params || {{}}, summary.provider_status_summary || summary.provider_status || '')
    : (summary.provider_status_summary || summary.provider_status || '');
  return detailLine('Response ID', summary.response_id || '')
    + detailLine('Finish reason', localizedFinishReason)
    + detailLine('Provider status', localizedProviderStatus)
    + detailLine('Usage input tokens', summary.usage_input_tokens ?? '')
    + detailLine('Usage output tokens', summary.usage_output_tokens ?? '')
    + detailLine('Usage total tokens', summary.usage_total_tokens ?? '')
    + detailLine('Metadata fields', summary.metadata_count ?? 0)
    + detailLine('Top-level response keys', summary.response_key_count ?? 0)
    + detailListLine('Response keys', summary.response_keys, ' | ');
}}
function renderResponseMetadataNotice(record) {{
  if (!record.response_metadata_summary || !record.response_metadata_summary.present) return '';
  const summary = record.response_metadata_summary;
  const localizedCounts = summary.counts_summary_key
    ? formatLabel(summary.counts_summary_key, summary.counts_summary_params || {{}}, '')
    : '';
  const localizedBoundaryNote = summary.boundary_note_key
    ? formatLabel(summary.boundary_note_key, {{}}, summary.boundary_note || '')
    : (summary.boundary_note || '');
  return renderNotice(
    label('notice.provider_response', 'Provider Response'),
    messageParagraph(localizedPayloadText(summary))
      + responseMetadataDetailLines(summary)
      + detailLine('Hit counts', localizedCounts)
      + detailLine('Scope note', localizedBoundaryNote)
  );
}}
function renderPackageReadinessNotice(record) {{
  if (!record.package_readiness) return '';
  const readiness = record.package_readiness;
  const packageReview = readiness.package_review || {{}};
  const manifest = readiness.package_manifest_preview || {{}};
  const readinessButtons = reviewQueueStatusButtons(readiness.status, 'package:');
  const localizedSuggestedCommands = (Array.isArray(readiness.suggested_command_details) ? readiness.suggested_command_details : []).map(item => (
    item && item.summary_key
      ? formatLabel(item.summary_key, item.summary_params || {{}}, item.summary || item.command || '')
      : (item.summary || item.command || '')
  ));
  const localizedCounts = readiness.counts_summary_key
    ? formatLabel(readiness.counts_summary_key, readiness.counts_summary_params || {{}}, '')
    : '';
  const localizedBoundaryNote = readiness.boundary_note_key
    ? formatLabel(readiness.boundary_note_key, {{}}, readiness.boundary_note || '')
    : (readiness.boundary_note || '');
  return renderNotice(
    label('notice.review_package_readiness', 'Review Package Readiness'),
    packageContextNoticeBody(
      readiness.status,
      localizedPayloadText(readiness),
      packageReview,
      manifest,
      readiness.eligible_context_ids,
      detailLine('Hit counts', localizedCounts)
      + detailListLine('Suggested commands', localizedSuggestedCommands.length > 0 ? localizedSuggestedCommands : readiness.suggested_commands, ' | ')
      + detailLine('Scope note', localizedBoundaryNote),
      readinessButtons,
    )
  );
}}
function renderRelatedLinksNotice(record) {{
  if (!Array.isArray(record.related_links) || record.related_links.length === 0) return '';
  return renderNotice(
    label('notice.related_links', 'Related Links'),
    '<p>' + record.related_links.map(item => detailNavButton(item.path || '', localizedLinkLabel(item))).join('') + '</p>'
  );
}}
function renderAuthReadinessNotice(record) {{
  if (!record.auth_boundary_notice) return '';
  const notice = record.auth_boundary_notice;
  const blockerDetails = Array.isArray(notice.blocker_details) ? notice.blocker_details : [];
  const blockerSummaries = Array.isArray(notice.blocker_summaries) ? notice.blocker_summaries : [];
  const noticeButtons = reviewQueueStatusButtons(notice.status);
  const localizedMessage = localizedPayloadText(notice);
  const localizedScopeNote = notice.scope_note_key
    ? formatLabel(notice.scope_note_key, notice.scope_note_params || {{}}, notice.scope_note || '')
    : (notice.scope_note || '');
  const localizedCapabilityStatus = notice.capability_status_summary_key
    ? formatLabel(notice.capability_status_summary_key, notice.capability_status_summary_params || {{}}, notice.capability_status_summary || notice.capability_status || '')
    : (notice.capability_status_summary || notice.capability_status || '');
  const localizedIdentityAssuranceStatus = notice.identity_assurance_status_summary_key
    ? formatLabel(notice.identity_assurance_status_summary_key, notice.identity_assurance_status_summary_params || {{}}, notice.identity_assurance_status_summary || notice.identity_assurance_status || '')
    : (notice.identity_assurance_status_summary || notice.identity_assurance_status || '');
  return renderNotice(
    label('notice.auth_readiness', 'Auth Readiness'),
    statusScopeNoticeBody(notice.status, localizedMessage, noticeButtons, localizedScopeNote)
      + detailLine('Review capability', localizedCapabilityStatus)
      + detailLine('Identity assurance', localizedIdentityAssuranceStatus)
      + blockerSummaryDetailLines(blockerDetails, notice.blockers, blockerSummaries, notice.next_steps)
  );
}}
function renderReviewCapabilityNotice(record) {{
  if (!record.review_capability) return '';
  const capability = record.review_capability;
  const warnList = Array.isArray(capability.warnings) ? capability.warnings : [];
  const warnDetails = Array.isArray(capability.warning_details) ? capability.warning_details : [];
  const warnBadges = reviewWarningBadges(warnList);
  const localizedCapabilityStatus = capability.status_summary_key
    ? formatLabel(capability.status_summary_key, capability.status_summary_params || {{}}, capability.status_summary || capability.status || '')
    : (capability.status_summary || capability.status || '');
  const localizedCanReviewNow = capability.can_review_now_summary_key
    ? formatLabel(capability.can_review_now_summary_key, capability.can_review_now_summary_params || {{}}, capability.can_review_now_summary || String(capability.can_review_now))
    : (capability.can_review_now_summary || String(capability.can_review_now));
  return renderNotice(
    label('notice.review_capability', 'Review Capability'),
    statusMessageBody(capability.status, localizedPayloadText(capability))
      + detailLine('Status', localizedCapabilityStatus)
      + detailLine('Can review now', localizedCanReviewNow)
      + (warnBadges ? '<p>' + warnBadges + '</p>' : '')
      + detailLine('Warnings', detailMessages(warnDetails, warnList) || '(none)')
  );
}}
function renderMutationEnablementNotice(record) {{
  if (!record.mutation_enablement) return '';
  const readiness = record.mutation_enablement;
  const blockerDetails = Array.isArray(readiness.blocker_details) ? readiness.blocker_details : [];
  const blockerSummaries = Array.isArray(readiness.blocker_summaries) ? readiness.blocker_summaries : [];
  const enablementChecks = Array.isArray(readiness.enablement_checks) ? readiness.enablement_checks : [];
  const operationalReadiness = readiness.operational_readiness || {{}};
  const reviewerContext = readiness.reviewer_context_requirements || {{}};
  const writeRouteContract = readiness.write_route_contract || {{}};
  const identityProofContract = writeRouteContract.identity_proof_contract || {{}};
  const authorizationContract = writeRouteContract.authorization_contract || {{}};
  const targetStateContract = writeRouteContract.target_state_contract || {{}};
  const readinessButtons = reviewQueueStatusButtons(readiness.status);
  const localizedEnablementReady = readiness.enablement_ready_summary_key
    ? formatLabel(readiness.enablement_ready_summary_key, readiness.enablement_ready_summary_params || {{}}, readiness.enablement_ready_summary || String(readiness.enablement_ready))
    : (readiness.enablement_ready_summary || String(readiness.enablement_ready));
  return renderNotice(
    label('notice.mutation_enablement', 'Mutation Enablement'),
    statusScopeNoticeBody(readiness.status, readiness.message, readinessButtons, readiness.scope_note)
      + detailLine('Enablement ready', localizedEnablementReady)
      + detailLine('Enablement checks', String(readiness.enablement_satisfied_count ?? 0) + '/' + String(readiness.enablement_required_count ?? 0))
      + detailLine('Blockers', detailMessages(blockerDetails, readiness.blockers))
      + mutationOperationalDetailLines(operationalReadiness, blockerSummaries, enablementChecks, 'Checks')
      + reviewerContextDetailLines(reviewerContext, identityProofContract)
      + reviewerLabelDetailLines(reviewerContext)
      + writeRouteDetailLines(writeRouteContract, identityProofContract, authorizationContract, targetStateContract)
      + detailListLine('Next steps', readiness.next_steps, ' | ')
  );
}}
function renderDetailActionPreviewControls(preview, actions, mutationTargetEventId) {{
  const activeActionButtons = actions.map(item =>
    '<button data-submit-review-action="' + esc(item.post_path || '') + '" data-review-action="' + esc(item.action || '') + '" data-review-record="' + esc(mutationTargetEventId) + '">'
    + esc(item.label || item.action || 'Apply')
    + '</button>'
  ).join(' ');
  return preview.ui_mutation_enabled
    ? '<p><label>' + esc(uiLabel('Reviewer')) + ' <input id="reviewer-label" value="local-ui" placeholder="' + esc(t('placeholder.reviewer')) + '"></label> '
      + '<label>' + esc(uiLabel('Kind')) + ' <select id="reviewer-kind"><option value="local_operator">local_operator</option><option value="user_declared">user_declared</option></select></label> '
      + '<label>' + esc(uiLabel('Session')) + ' <input id="reviewer-session-label" value="local-ui-session" placeholder="' + esc(t('placeholder.session')) + '"></label>'
      + '<input type="hidden" id="reviewer-record-id" value="' + esc(mutationTargetEventId || '') + '"></p>'
      + '<p><label>' + esc(uiLabel('Note')) + ' <input id="reviewer-note" placeholder="' + esc(t('placeholder.review_note')) + '"></label></p>'
      + '<p>' + activeActionButtons + '</p>'
    : '<p><button disabled>' + esc(uiLabel('Approve')) + '</button> <button disabled>' + esc(uiLabel('Reject')) + '</button> <button disabled>' + esc(uiLabel('Request Changes')) + '</button></p>';
}}
function renderDetailActionPreviewList(preview, actions) {{
  return '<ul>' + actions.map(item =>
    '<li><strong>' + esc(item.label || '') + ':</strong> <span class="id">' + esc(item.command || '') + '</span>'
    + (item.command ? ' ' + copyCommandButton(item.command, 'action-preview-response') : '')
    + (item.post_path
      ? (
          preview.ui_mutation_enabled
            ? '<br><span class="id">' + esc(item.post_path || '') + '</span> <span class="id">' + esc(uiLabel('POST enabled')) + '</span>'
            : '<br><span class="id">' + esc(item.post_path || '') + '</span> <button data-preview-post="' + esc(item.post_path || '') + '">' + esc(uiLabel('Preview blocked route')) + '</button>'
        )
      : '')
    + '</li>'
  ).join('') + '</ul>';
}}
function renderDetailActionPreviewNotice(record) {{
  if (!record.action_preview) return '';
  const preview = record.action_preview;
  const actions = Array.isArray(preview.actions) ? preview.actions : [];
  const failureContract = preview.failure_contract || {{}};
  const capability = record.review_capability || {{}};
  const parity = record.cli_parity || {{}};
  const mutationTargetEventId = record.target_event_id || record.review_target_event_id || record.event_id || '';
  const previewButtons = [
    ...reviewQueueStatusButtons(capability.status),
    ...reviewQueueStatusButtons(parity.status),
  ];
  const localizedPreviewMessage = localizedPayloadText(preview);
  const recoveryContractSection = noticeSection(
    label('section.recovery_contract', 'Recovery Contract'),
    recoveryContractDetailLines(failureContract, 'action-preview-response')
  );
  const reviewActionSection = noticeSection(
    label('section.review_action', 'Review Action'),
    renderDetailActionPreviewControls(preview, actions, mutationTargetEventId)
      + renderDetailActionPreviewList(preview, actions)
  );
  const actionResultSection = noticeSection(
    label('section.action_result', 'Current Result'),
    '<div id="action-preview-response"><p>'
      + (
        preview.ui_mutation_enabled
          ? t('notice.mutation_enabled_detail')
          : t('notice.blocked_route_preview_detail')
      )
      + '</p></div>'
  );
  return renderNotice(
    label('notice.action_preview', 'Action Preview'),
    noticeSection(
      label('status.detail', 'Detail'),
      statusMessageBody(preview.status, localizedPreviewMessage, previewButtons)
    )
      + recoveryContractSection
      + reviewActionSection
      + actionResultSection
  );
}}
function renderCliParityNotice(record) {{
  if (!record.cli_parity) return '';
  const parity = record.cli_parity;
  const parityButtons = reviewQueueStatusButtons(parity.status);
  return renderNotice(
    label('notice.cli_parity', 'CLI Parity'),
    statusMessageBody(parity.status, localizedPayloadText(parity), parityButtons)
      + detailListLine('Expected actions', parity.expected_actions)
      + detailListLine('Missing preview commands', parity.missing_preview_commands, ' | ')
      + detailListLine('Missing queue commands', parity.missing_queue_commands, ' | ')
  );
}}
function renderIdentityAssuranceNotice(record) {{
  if (!record.latest_identity_assurance) return '';
  const assurance = record.latest_identity_assurance;
  const assuranceButtons = reviewQueueStatusButtons(assurance.status);
  return renderNotice(
    label('notice.identity_assurance', 'Identity Assurance'),
      statusMessageBody(assurance.status, localizedPayloadText(assurance), assuranceButtons)
  );
}}
function renderReviewerBoundaryDrilldownNotice(record) {{
  if (!record.reviewer_boundary_drilldown_summary) return '';
  return renderNotice(
    label('notice.reviewer_boundary_drilldown', 'Reviewer Boundary Drilldown'),
    renderReviewerBoundaryDrilldownSummary(record.reviewer_boundary_drilldown_summary)
  );
}}
function renderReviewTimelineNotice(record) {{
  if (!Array.isArray(record.history) || record.history.length === 0) return '';
  return renderNotice(
    label('notice.review_timeline', 'Review Timeline'),
    '<ul>' + record.history.map(item => {{
      const timelineButtons = [
        ...reviewQueueStatusButtons(item.disposition),
        ...reviewQueueStatusButtons(item.identity_assurance && item.identity_assurance.status),
      ];
      return '<li>'
        + esc(item.reviewed_at || '') + ' — '
        + esc(item.disposition || '') + ' by '
        + esc((item.reviewer_identity && item.reviewer_identity.label) || item.reviewer || '')
        + ' (' + esc((item.identity_assurance && item.identity_assurance.status) || '') + ')'
        + (timelineButtons.length > 0 ? '<br>' + timelineButtons.join('') : '')
        + '</li>';
      }}).join('') + '</ul>'
  );
}}
async function responseJsonOrEmpty(response) {{
  try {{
    return await response.json();
  }} catch (_error) {{
    return {{}};
  }}
}}
async function postJson(path, body = undefined) {{
  const options = {{ method: 'POST' }};
  const headers = {{}};
  if (window.__chronicleMutationToken) {{
    headers['{MUTATION_TOKEN_HEADER}'] = window.__chronicleMutationToken;
  }}
  if (body !== undefined) {{
    headers['Content-Type'] = 'application/json';
    options.body = JSON.stringify(body);
  }}
  if (Object.keys(headers).length > 0) {{
    options.headers = headers;
  }}
  const response = await fetch(path, options);
  const payload = await responseJsonOrEmpty(response);
  return {{ response, payload }};
}}
function appendCommandFeedback(target, command, copied) {{
  if (!target) return;
  target.innerHTML += '<p>' + esc(copied ? t('status.copied_recovery_cli') : t('status.copy_failed_command')) + '<span class="id">' + esc(command) + '</span></p>';
}}
async function tryCopyText(command) {{
  if (navigator.clipboard && navigator.clipboard.writeText) {{
    try {{
      await navigator.clipboard.writeText(command);
      return true;
    }} catch (_error) {{
      return false;
    }}
  }}
  const textArea = document.createElement('textarea');
  textArea.value = command;
  textArea.setAttribute('readonly', 'readonly');
  textArea.style.position = 'absolute';
  textArea.style.left = '-9999px';
  document.body.appendChild(textArea);
  textArea.select();
  const copied = document.execCommand('copy');
  document.body.removeChild(textArea);
  return copied;
}}
function reviewActionRequestBody(action, fieldPrefix = 'reviewer') {{
  const sessionId = window.__chronicleMutationSessionId || '';
  const recordId = reviewFieldValue(fieldPrefix, 'record-id', '') || '';
  const nextSequence = (window.__chronicleMutationRequestSequence || 0) + 1;
  window.__chronicleMutationRequestSequence = nextSequence;
  return {{
    reviewer_label: reviewFieldValue(fieldPrefix, 'reviewer-label', ''),
    reviewer_kind: reviewFieldValue(fieldPrefix, 'reviewer-kind', 'local_operator') || 'local_operator',
    session_label: reviewFieldValue(fieldPrefix, 'reviewer-session-label', ''),
    note: reviewFieldValue(fieldPrefix, 'reviewer-note', ''),
    ui_intent: action || '',
    mutation_session_id: sessionId,
    mutation_request_id: 'mrq-' + sessionId + '-' + String(recordId || 'review') + '-' + String(nextSequence),
  }};
}}
function reloadCurrentEndpoint() {{
  if (window.__chronicleCurrentEndpoint) loadEndpoint(window.__chronicleCurrentEndpoint);
}}
function applyJumpFilter(filterTarget, filterValue) {{
  setFilterValue(filterTarget, filterValue);
}}
function updateFilterState(filterId, value) {{
  setFilterValue(filterId, value);
}}
function updateSortState(sortId, value) {{
  setSortValue(sortId, value);
}}
function handleDetailTrailNavigation(target) {{
  if (!target) return;
  const index = window.__chronicleDetailTrail.lastIndexOf(target);
  if (index >= 0) window.__chronicleDetailTrail = window.__chronicleDetailTrail.slice(0, index);
  window.__chronicleLastDetail = '';
  loadDetail(target);
}}
function handleBackDetail() {{
  if (window.__chronicleDetailTrail.length <= 0) return;
  const previousDetail = window.__chronicleDetailTrail.pop();
  if (!previousDetail) return;
  window.__chronicleLastDetail = '';
  loadDetail(previousDetail);
}}
function handleViewClick(event) {{
  if (event.target.dataset.copyCommand) {{
    copyCommand(
      event.target.dataset.copyCommand,
      event.target.dataset.copyTarget || 'review-queue-action-preview-response',
    );
  }}
  if (event.target.dataset.detail) loadDetail(event.target.dataset.detail);
  if (event.target.dataset.jump) {{
    applyJumpFilter(event.target.dataset.filterTarget, event.target.dataset.filterValue || '');
    loadEndpoint(event.target.dataset.jump);
  }}
  if (event.target.dataset.resetFilter) {{
    resetFilters(event.target.dataset.resetFilter);
    reloadCurrentEndpoint();
  }}
  if (event.target.dataset.resetFilters) {{
    resetFilters(event.target.dataset.resetFilters);
    reloadCurrentEndpoint();
  }}
}}
function handleDetailClick(event) {{
  if (event.target.dataset.copyCommand) copyCommand(event.target.dataset.copyCommand, event.target.dataset.copyTarget || 'action-preview-response');
  if (event.target.dataset.previewPost) previewBlockedRoute(event.target.dataset.previewPost);
  if (event.target.dataset.submitReviewAction) {{
    submitReviewAction(
      event.target.dataset.submitReviewAction,
      event.target.dataset.reviewAction || '',
      event.target.dataset.reviewRecord || '',
      event.target.dataset.previewTarget || 'action-preview-response',
      event.target.dataset.reviewFields || 'reviewer',
      event.target.dataset.successDetail || '',
    );
  }}
  if (event.target.dataset.detailNav) loadDetail(event.target.dataset.detailNav);
  if (event.target.dataset.detailTrail) handleDetailTrailNavigation(event.target.dataset.detailTrail);
  if (event.target.dataset.backDetail) handleBackDetail();
  if (event.target.dataset.resetFilters) {{
    resetFilters(event.target.dataset.resetFilters);
    reloadCurrentEndpoint();
  }}
  if (event.target.dataset.backView) reloadCurrentEndpoint();
}}
function handleViewPreviewPost(event) {{
  if (!event.target.dataset.previewPost) return;
  previewBlockedRoute(
    event.target.dataset.previewPost,
    event.target.dataset.previewTarget || 'review-queue-action-preview-response',
  );
}}
function handleViewInput(event) {{
  const filterId = event.target.dataset.filterInput;
  if (!filterId) return;
  updateFilterState(filterId, event.target.value || '');
  reloadCurrentEndpoint();
}}
function handleViewChange(event) {{
  const sortId = event.target.dataset.sortInput;
  if (!sortId || !window.__chronicleSorts) return;
  updateSortState(sortId, event.target.value || '');
  reloadCurrentEndpoint();
}}
function renderPanel(body) {{
  return '<div class="panel">' + body + '</div>';
}}
function renderOverviewHeaderPanel(chronicle) {{
  return renderPanel(
    '<p><strong>' + esc(chronicle.title || '') + '</strong></p>'
    + '<p>' + esc(uiLabel('Chronicle ID')) + ': <span class="id">' + esc(chronicle.id || '') + '</span></p>'
    + '<p>' + esc(uiLabel('Root')) + ': <span class="id">' + esc(chronicle.root || '') + '</span></p>'
  );
}}
function renderOverviewCountsPanel(counts) {{
  const countRows = Object.entries(counts || {{}}).map(([key, value]) =>
    '<tr><th>' + esc(key) + '</th><td>' + esc(value ?? '') + '</td></tr>'
  ).join('');
  return renderPanel(
    sectionTitle(label('section.counts', 'Counts'))
    + '<table><tbody>' + countRows + '</tbody></table>'
  );
}}
function renderOverviewRuntimeBoundaryPanel(runtime) {{
  const localizedReadOnly = runtime.read_only_summary_key
    ? formatLabel(runtime.read_only_summary_key, runtime.read_only_summary_params || {{}}, runtime.read_only_summary || String(runtime.read_only))
    : (runtime.read_only_summary || String(runtime.read_only));
  const localizedExternalModelApi = runtime.external_model_api_summary_key
    ? formatLabel(runtime.external_model_api_summary_key, runtime.external_model_api_summary_params || {{}}, runtime.external_model_api_summary || String(runtime.external_model_api))
    : (runtime.external_model_api_summary || String(runtime.external_model_api));
  const localizedGraphragRuntime = runtime.graphrag_runtime_summary_key
    ? formatLabel(runtime.graphrag_runtime_summary_key, runtime.graphrag_runtime_summary_params || {{}}, runtime.graphrag_runtime_summary || String(runtime.graphrag_runtime))
    : (runtime.graphrag_runtime_summary || String(runtime.graphrag_runtime));
  const localizedVectorDb = runtime.vector_db_summary_key
    ? formatLabel(runtime.vector_db_summary_key, runtime.vector_db_summary_params || {{}}, runtime.vector_db_summary || String(runtime.vector_db))
    : (runtime.vector_db_summary || String(runtime.vector_db));
  const localizedGraphDb = runtime.graph_db_summary_key
    ? formatLabel(runtime.graph_db_summary_key, runtime.graph_db_summary_params || {{}}, runtime.graph_db_summary || String(runtime.graph_db))
    : (runtime.graph_db_summary || String(runtime.graph_db));
  return renderPanel(
    sectionTitle(label('section.runtime_boundary', 'Runtime Boundary'))
    + detailLine('Read-only', localizedReadOnly)
    + detailLine('External model API', localizedExternalModelApi)
    + detailLine('GraphRAG runtime', localizedGraphragRuntime)
    + detailLine('Vector DB', localizedVectorDb)
    + detailLine('Graph DB', localizedGraphDb)
  );
}}
function renderOverviewRuntimeConfigPanel(runtimeConfig, runtimeConfigContract) {{
  const localizedSource = runtimeConfig.source_summary_key
    ? formatLabel(runtimeConfig.source_summary_key, runtimeConfig.source_summary_params || {{}}, runtimeConfig.source_summary || runtimeConfig.source || '')
    : (runtimeConfig.source_summary || runtimeConfig.source || '');
  const localizedProviderKind = runtimeConfigContract.provider_kind_summary_key
    ? formatLabel(runtimeConfigContract.provider_kind_summary_key, runtimeConfigContract.provider_kind_summary_params || {{}}, runtimeConfigContract.provider_kind_summary || runtimeConfigContract.provider_kind || '')
    : (runtimeConfigContract.provider_kind_summary || runtimeConfigContract.provider_kind || '');
  const localizedAllowNetwork = runtimeConfigContract.allow_network_summary_key
    ? formatLabel(runtimeConfigContract.allow_network_summary_key, runtimeConfigContract.allow_network_summary_params || {{}}, runtimeConfigContract.allow_network_summary || String(runtimeConfigContract.allow_network))
    : (runtimeConfigContract.allow_network_summary || String(runtimeConfigContract.allow_network));
  const localizedAllowExternalContext = runtimeConfigContract.allow_external_context_summary_key
    ? formatLabel(runtimeConfigContract.allow_external_context_summary_key, runtimeConfigContract.allow_external_context_summary_params || {{}}, runtimeConfigContract.allow_external_context_summary || String(runtimeConfigContract.allow_external_context))
    : (runtimeConfigContract.allow_external_context_summary || String(runtimeConfigContract.allow_external_context));
  return renderPanel(
    sectionTitle(label('section.runtime_config', 'Runtime Config'))
    + detailLine('Source', localizedSource)
    + detailLine('Provider kind', localizedProviderKind)
    + detailLine('Provider name', runtimeConfigContract.provider_name || '')
    + detailLine('Model', runtimeConfigContract.model_name || '')
    + detailLine('Allow network', localizedAllowNetwork)
    + detailLine('Allow external context', localizedAllowExternalContext)
    + detailListLine('Warnings', runtimeConfig.warnings, ' | ')
    + '<p>' + listJumpButton(label('button.open_runtime_config', 'Open Runtime Config'), '/api/runtime-config') + '</p>'
  );
}}
function renderOverviewUiBoundaryPanel(uiBoundary) {{
  const writeRouteContract = uiBoundary.write_route_contract || {{}};
  const identityProofContract = writeRouteContract.identity_proof_contract || {{}};
  const authorizationContract = writeRouteContract.authorization_contract || {{}};
  const targetStateContract = writeRouteContract.target_state_contract || {{}};
  const localizedMutationEnabled = uiBoundary.mutation_enabled_summary_key
    ? formatLabel(uiBoundary.mutation_enabled_summary_key, uiBoundary.mutation_enabled_summary_params || {{}}, uiBoundary.mutation_enabled_summary || String(uiBoundary.mutation_enabled))
    : (uiBoundary.mutation_enabled_summary || String(uiBoundary.mutation_enabled));
  const localizedMutationCapabilityFlag = uiBoundary.mutation_capability_flag_summary_key
    ? formatLabel(uiBoundary.mutation_capability_flag_summary_key, uiBoundary.mutation_capability_flag_summary_params || {{}}, uiBoundary.mutation_capability_flag_summary || String(uiBoundary.mutation_capability_flag))
    : (uiBoundary.mutation_capability_flag_summary || String(uiBoundary.mutation_capability_flag));
  const localizedSessionGating = uiBoundary.session_gating_summary_key
    ? formatLabel(uiBoundary.session_gating_summary_key, uiBoundary.session_gating_summary_params || {{}}, uiBoundary.session_gating_summary || String(uiBoundary.session_gating))
    : (uiBoundary.session_gating_summary || String(uiBoundary.session_gating));
  return renderPanel(
    sectionTitle(label('section.ui_boundary', 'UI Boundary'))
    + detailLine('Bind scope', uiBoundary.bind_scope || '')
    + detailLine('Mutation enabled', localizedMutationEnabled)
    + detailLine('Mutation capability flag', localizedMutationCapabilityFlag)
    + detailLine('Auth mode', uiBoundary.auth_mode || '')
    + detailLine('Authorization mode', uiBoundary.authorization_mode || '')
    + detailLine('Session gating', localizedSessionGating)
    + detailLine('Mutation readiness', uiBoundary.mutation_readiness_status || '')
    + writeRouteDetailLines(writeRouteContract, identityProofContract, authorizationContract, targetStateContract, true)
  );
}}
function renderOverviewAuthBoundaryPanel(authBoundary, authBoundaryOverview) {{
  const blockerSummaries = Array.isArray(authBoundary.blocker_summaries) ? authBoundary.blocker_summaries : [];
  const metricsBody =
    summaryJsonLine('Auth review capability counts', authBoundaryOverview.review_capability_counts)
      + summaryJsonLine('Provider finish reasons', authBoundaryOverview.provider_response_finish_reason_counts)
      + summaryJsonLine('Provider statuses', authBoundaryOverview.provider_response_status_counts);
  return renderPanel(
    sectionTitle(label('section.auth_boundary', 'Auth Boundary'))
    + '<p>'
    + overviewCountButton(reviewWarningLabel('ui_auth_not_enabled'), authBoundaryOverview.auth_warning_count, 'badge-warning', '/api/review-queue', 'reviewQueue', 'ui_auth_not_enabled')
    + overviewCountButton(reviewWarningLabel('ui_authorization_not_enabled'), authBoundaryOverview.authorization_warning_count, 'badge-warning', '/api/review-queue', 'reviewQueue', 'ui_auth_not_enabled')
    + overviewCountButton(reviewWarningLabel('no_reviewer_identity_recorded'), authBoundaryOverview.missing_identity_count, 'badge-warning', '/api/review-queue', 'reviewQueue', 'no_reviewer_identity_recorded')
    + overviewCountButton(label('overview.provider_response', 'Provider response'), authBoundaryOverview.provider_response_present_count, 'badge-ready', '/api/review-queue', 'reviewQueue', 'response_id')
    + '</p>'
    + statusMessageBody(authBoundary.status, localizedPayloadText(authBoundary))
    + detailLine('Scope note', authBoundary.scope_note_key ? formatLabel(authBoundary.scope_note_key, authBoundary.scope_note_params || {{}}, authBoundary.scope_note || '') : (authBoundary.scope_note || ''))
    + detailLine('Session gating', authBoundary.session_gating_summary_key ? formatLabel(authBoundary.session_gating_summary_key, authBoundary.session_gating_summary_params || {{}}, authBoundary.session_gating_summary || String(authBoundary.session_gating)) : (authBoundary.session_gating_summary || String(authBoundary.session_gating)))
    + detailLine('Shared machine safe', authBoundary.shared_machine_safe_summary_key ? formatLabel(authBoundary.shared_machine_safe_summary_key, authBoundary.shared_machine_safe_summary_params || {{}}, authBoundary.shared_machine_safe_summary || String(authBoundary.shared_machine_safe)) : (authBoundary.shared_machine_safe_summary || String(authBoundary.shared_machine_safe)))
    + metricsSection(metricsBody)
    + detailListLine('Auth blockers', authBoundary.blockers, ' | ')
    + detailListLine('Auth blocker summaries', blockerSummaries.map(item => (item.summary || item.code || 'blocker')), ' | ')
    + navigationCluster([latestResponseButton(authBoundaryOverview.latest_provider_response_detail_path, 'button.open_latest_review_response', 'Open Latest Review Response')])
    + detailListLine('Auth next steps', authBoundary.next_steps, ' | ')
  );
}}
function renderOverviewIdentityBoundaryPanel(identityBoundary) {{
  const metricsBody = summaryJsonLine('Identity assurance counts', identityBoundary.assurance_counts);
  return renderPanel(
    sectionTitle(label('section.identity_boundary', 'Identity Boundary'))
    + '<p>'
    + overviewCountButton(reviewWarningLabel('reviewer_identity_declared_only'), identityBoundary.declared_identity_count, 'badge-warning', '/api/review-queue', 'reviewQueue', 'reviewer_identity_declared_only')
    + overviewCountButton(reviewWarningLabel('reviewer_session_label_missing'), identityBoundary.session_label_missing_count, 'badge-warning', '/api/review-queue', 'reviewQueue', 'reviewer_session_label_missing')
    + overviewCountButton(uiLabel('Identity aligned'), (identityBoundary.assurance_counts && identityBoundary.assurance_counts.boundary_aligned) ?? 0, 'badge-ready', '/api/review-queue', 'reviewQueue', 'boundary_aligned')
    + '</p>'
    + statusMessageBody(identityBoundary.status, localizedPayloadText(identityBoundary))
    + metricsSection(metricsBody)
    + identityBoundaryDetailLines(identityBoundary)
  );
}}
function renderOverviewReviewerBoundaryPanel(reviewerBoundary) {{
  const metricsBody =
    summaryJsonLine(label('overview.reviewer_runtime_enforcement_counts', 'Runtime enforcement counts'), reviewerBoundary.runtime_record_enforcement_counts)
      + summaryJsonLine(label('overview.reviewer_runtime_gate_counts', 'Runtime gate counts'), reviewerBoundary.runtime_record_validation_gate_counts)
      + summaryJsonLine(label('overview.reviewer_review_enforcement_counts', 'Review enforcement counts'), reviewerBoundary.review_queue_enforcement_counts)
      + summaryJsonLine(label('overview.reviewer_review_gate_counts', 'Review gate counts'), reviewerBoundary.review_queue_validation_gate_counts)
      + summaryJsonLine(label('overview.reviewer_summary_enforcement_counts', 'Summary enforcement counts'), reviewerBoundary.summary_job_enforcement_counts)
      + summaryJsonLine(label('overview.reviewer_summary_gate_counts', 'Summary gate counts'), reviewerBoundary.summary_job_validation_gate_counts);
  const drilldownSummaries = Array.isArray(reviewerBoundary.drilldown_summaries) ? reviewerBoundary.drilldown_summaries : [];
  return renderPanel(
    sectionTitle(label('section.reviewer_boundary', 'Reviewer Boundary'))
    + detailLine(label('ui.label.enforcement_status', 'Enforcement status'), reviewerBoundaryStatusText(reviewerBoundary.enforcement_status || ''))
    + detailLine(label('ui.label.validation_gate_status', 'Validation gate status'), reviewerBoundaryStatusText(reviewerBoundary.validation_gate_status || ''))
    + detailLine(label('ui.label.session_gated', 'Session gated'), reviewerBoundary.session_gated)
    + detailLine(label('ui.label.fail_closed_route_checks', 'Fail closed route checks'), reviewerBoundary.route_enforced)
    + '<p>' + reviewerBoundaryDominantButtons(drilldownSummaries) + '</p>'
    + '<p>' + reviewerBoundaryCountButtons('runtimeRecords', '/api/runtime-records', reviewerBoundary.runtime_record_enforcement_counts, reviewerBoundary.runtime_record_validation_gate_counts) + '</p>'
    + '<p>' + reviewerBoundaryCountButtons('reviewQueue', '/api/review-queue', reviewerBoundary.review_queue_enforcement_counts, reviewerBoundary.review_queue_validation_gate_counts) + '</p>'
    + '<p>' + reviewerBoundaryCountButtons('summaryJobs', '/api/summary-jobs', reviewerBoundary.summary_job_enforcement_counts, reviewerBoundary.summary_job_validation_gate_counts) + '</p>'
    + detailListLine(label('ui.label.drilldown_datasets', 'Drilldown datasets'), drilldownSummaries.map(item => item.dataset_key || ''), ' | ')
    + drilldownSummaries.map(item =>
      cellDetails(label('ui.label.drilldown_summary', 'Drilldown summary'), [
        renderReviewerBoundaryDrilldownSummary(item),
      ])
    ).join('')
    + metricsSection(metricsBody)
  );
}}
function renderOverviewMutationReadinessPanel(mutationReadiness) {{
  const blockerDetails = Array.isArray(mutationReadiness.blocker_details) ? mutationReadiness.blocker_details : [];
  const blockerSummaries = Array.isArray(mutationReadiness.blocker_summaries) ? mutationReadiness.blocker_summaries : [];
  const reviewerContextRequirements = mutationReadiness.reviewer_context_requirements || {{}};
  const writeRouteContract = mutationReadiness.write_route_contract || {{}};
  const identityProofContract = writeRouteContract.identity_proof_contract || {{}};
  const authorizationContract = writeRouteContract.authorization_contract || {{}};
  const targetStateContract = writeRouteContract.target_state_contract || {{}};
  const localizedActionTargetMatrix = (targetStateContract.action_target_matrix || []).map(item => (
    item && item.summary_key
      ? formatLabel(item.summary_key, item.summary_params || {{}}, item.summary || '')
      : ((item.action || 'action') + ': pending=' + String(item.requires_pending) + '; queue=' + (item.resulting_queue_state || '') + '; disposition=' + (item.resulting_disposition || ''))
  ));
  const localizedActionAuthorizationMatrix = (authorizationContract.action_authorization_matrix || []).map(item => (
    item && item.summary_key
      ? formatLabel(item.summary_key, item.summary_params || {{}}, item.summary || '')
      : ((item.action || 'action') + ': intent=' + (item.ui_intent || '') + '; pending=' + String(item.pending_required) + '; note=' + (item.note_status || ''))
  ));
  const localizedFailureFamilies = (writeRouteContract.failure_families || []).map(item => {{
    const summary = item && item.summary_key
      ? formatLabel(item.summary_key, item.summary_params || {{}}, item.summary || '')
      : (item.summary || '');
    return ((item.family || 'family') + ': ' + summary + '; ' + ((item.possible_error_codes || []).join(', ')));
  }});
  const enablementChecks = Array.isArray(mutationReadiness.enablement_checks) ? mutationReadiness.enablement_checks : [];
  const operationalReadiness = mutationReadiness.operational_readiness || {{}};
  const localizedEnablementReady = mutationReadiness.enablement_ready_summary_key
    ? formatLabel(mutationReadiness.enablement_ready_summary_key, mutationReadiness.enablement_ready_summary_params || {{}}, mutationReadiness.enablement_ready_summary || String(mutationReadiness.enablement_ready))
    : (mutationReadiness.enablement_ready_summary || String(mutationReadiness.enablement_ready));
  return renderPanel(
    sectionTitle(label('section.mutation_readiness', 'Mutation Readiness'))
    + statusMessageBody(mutationReadiness.status, localizedPayloadText(mutationReadiness))
    + detailLine('Scope note', mutationReadiness.scope_note_key ? formatLabel(mutationReadiness.scope_note_key, mutationReadiness.scope_note_params || {{}}, mutationReadiness.scope_note || '') : (mutationReadiness.scope_note || ''))
    + detailLine('Ready rows', mutationReadiness.ready_row_count ?? 0)
    + detailLine('Advisory rows', mutationReadiness.advisory_row_count ?? 0)
    + detailLine('Enablement ready', localizedEnablementReady)
    + detailLine('Enablement checks', String(mutationReadiness.enablement_satisfied_count ?? 0) + '/' + String(mutationReadiness.enablement_required_count ?? 0))
    + detailListLine('Blockers', mutationReadiness.blockers, ' | ')
    + detailLine('Blocker details', detailMessages(blockerDetails, mutationReadiness.blockers))
    + detailListLine('Durable success requirements', writeRouteContract.durable_success_requirements, ' | ')
    + detailListLine('Transaction order', writeRouteContract.transaction_order, ' | ')
    + detailLine('Authorization status', authorizationContract.authorization_status || '')
    + detailLine('Required assurance', authorizationContract.required_identity_assurance_status || '')
    + detailLine('Pending target required', authorizationContract.target_pending_required)
    + detailListLine('Authorization checks', authorizationContract.server_side_checks, ' | ')
    + detailListLine('Action authorization matrix', localizedActionAuthorizationMatrix, ' | ')
    + detailLine('Required review status', targetStateContract.required_current_review_status || '')
    + detailLine('Resolved status code', targetStateContract.resolved_status_code ?? '')
    + detailListLine('Target-state checks', targetStateContract.target_state_checks, ' | ')
    + detailListLine('Action target matrix', localizedActionTargetMatrix, ' | ')
    + detailListLine('Failure families', localizedFailureFamilies, ' | ')
    + mutationOperationalDetailLines(operationalReadiness, blockerSummaries, enablementChecks)
    + detailListLine('Effective reviewer fields', reviewerContextRequirements.effective_required_fields, ' | ')
    + detailListLine('Reviewer fields', reviewerContextRequirements.required_fields, ' | ')
    + reviewerContextDetailLines(reviewerContextRequirements, identityProofContract)
    + reviewerLabelDetailLines(reviewerContextRequirements)
    + detailLine('Session label required', reviewerContextRequirements.session_label_required)
    + writeRouteDetailLines(writeRouteContract, identityProofContract, authorizationContract, targetStateContract, true)
    + detailListLine('Next steps', mutationReadiness.next_steps, ' | ')
  );
}}
function renderOverviewAiIndexPanel(aiIndex, counts) {{
  const vectorEntryCount = aiIndex.vector && aiIndex.vector.entry_count ? aiIndex.vector.entry_count : 0;
  const graphNodeCount = aiIndex.graph && aiIndex.graph.node_count ? aiIndex.graph.node_count : 0;
  const graphEdgeCount = aiIndex.graph && aiIndex.graph.edge_count ? aiIndex.graph.edge_count : 0;
  return renderPanel(
    sectionTitle(label('section.ai_index_snapshot', 'AI Index Snapshot'))
    + detailLine('Vector entries', vectorEntryCount)
    + detailLine('Graph nodes', graphNodeCount)
    + detailLine('Graph edges', graphEdgeCount)
    + detailLine('Runtime records', counts.runtime_records ?? 0)
    + detailLine('Summary jobs', counts.summary_jobs ?? 0)
    + detailLine('Needs-review records', counts.review_queue ?? 0)
  );
}}
function overviewRuntimeRecordCountButtons(counts, runtimeRecords) {{
  return buttonRow([
    overviewCountButton(label('section.runtime_records', 'Runtime Records'), counts.runtime_records, 'badge-neutral', '/api/runtime-records'),
    overviewCountButton(filterValueLabel('runtimeRecords', 'response_id'), runtimeRecords.provider_response_present_count, 'badge-ready', '/api/runtime-records', 'runtimeRecords', 'response_id'),
    overviewCountButton(filterValueLabel('runtimeRecords', 'advisory_only'), (runtimeRecords.auth_readiness_counts && runtimeRecords.auth_readiness_counts.advisory_only) ?? 0, 'badge-warning', '/api/runtime-records', 'runtimeRecords', 'advisory_only'),
    overviewCountButton(filterValueLabel('runtimeRecords', 'preview_only'), (runtimeRecords.mutation_readiness_counts && runtimeRecords.mutation_readiness_counts.preview_only) ?? 0, 'badge-warning', '/api/runtime-records', 'runtimeRecords', 'preview_only'),
  ]);
}}
function renderOverviewRuntimeRecordsPanel(counts, runtimeRecords) {{
  const metricsBody =
    summaryJsonLine('Runtime kinds', runtimeRecords.kind_counts)
      + summaryJsonLine('Auth readiness counts', runtimeRecords.auth_readiness_counts)
      + summaryJsonLine('Mutation readiness counts', runtimeRecords.mutation_readiness_counts)
      + summaryJsonLine('Mutation operational counts', runtimeRecords.mutation_operational_counts)
      + summaryJsonLine('Provider finish reasons', runtimeRecords.provider_response_finish_reason_counts)
      + summaryJsonLine('Provider statuses', runtimeRecords.provider_response_status_counts);
  return renderPanel(
    sectionTitle(label('section.runtime_records', 'Runtime Records'))
    + overviewRuntimeRecordCountButtons(counts, runtimeRecords)
    + metricsSection(metricsBody)
    + sliceButtonRow(runtimeRecordsSliceButtons())
    + endpointLatestResponseCluster('/api/runtime-records', runtimeRecords.latest_provider_response_detail_path, 'button.open_latest_runtime_response', 'Open Latest Runtime Response')
  );
}}
function overviewSummaryJobCountButtons(counts, summaryJobs) {{
  return buttonRow([
    overviewCountButton(label('section.summary_jobs', 'Summary Jobs'), counts.summary_jobs, 'badge-neutral', '/api/summary-jobs'),
    overviewCountButton(filterValueLabel('summaryJobs', 'response_id'), summaryJobs.provider_response_present_count, 'badge-ready', '/api/summary-jobs', 'summaryJobs', 'response_id'),
    overviewCountButton(filterValueLabel('summaryJobs', 'advisory_only'), (summaryJobs.review_capability_counts && summaryJobs.review_capability_counts.advisory_only) ?? 0, 'badge-warning', '/api/summary-jobs', 'summaryJobs', 'advisory_only'),
    overviewCountButton(label('overview.summary_auth_advisory', 'Summary auth advisory'), (summaryJobs.auth_readiness_counts && summaryJobs.auth_readiness_counts.advisory_only) ?? 0, 'badge-warning', '/api/summary-jobs', 'summaryJobs', 'advisory_only'),
    overviewCountButton(filterValueLabel('summaryJobs', 'package_context_available'), (summaryJobs.package_readiness_counts && summaryJobs.package_readiness_counts.package_context_available) ?? 0, 'badge-ready', '/api/summary-jobs', 'summaryJobs', 'package_context_available'),
    overviewCountButton(filterValueLabel('summaryJobs', 'boundary_aligned'), (summaryJobs.identity_assurance_counts && summaryJobs.identity_assurance_counts.boundary_aligned) ?? 0, 'badge-ready', '/api/summary-jobs', 'summaryJobs', 'boundary_aligned'),
    overviewCountButton(filterValueLabel('summaryJobs', 'preview_only'), (summaryJobs.mutation_readiness_counts && summaryJobs.mutation_readiness_counts.preview_only) ?? 0, 'badge-warning', '/api/summary-jobs', 'summaryJobs', 'preview_only'),
  ]);
}}
function renderOverviewSummaryJobsPanel(counts, summaryJobs) {{
  const metricsBody =
    summaryJsonLine('Status counts', summaryJobs.status_counts)
      + summaryJsonLine('Review capability counts', summaryJobs.review_capability_counts)
      + summaryJsonLine('Auth readiness counts', summaryJobs.auth_readiness_counts)
      + summaryJsonLine('Package readiness counts', summaryJobs.package_readiness_counts)
      + summaryJsonLine('Mutation readiness counts', summaryJobs.mutation_readiness_counts)
      + summaryJsonLine('Mutation operational counts', summaryJobs.mutation_operational_counts)
      + summaryJsonLine('Provider finish reasons', summaryJobs.provider_response_finish_reason_counts)
      + summaryJsonLine('Provider statuses', summaryJobs.provider_response_status_counts)
      + summaryJsonLine('Identity assurance counts', summaryJobs.identity_assurance_counts)
      + summaryJsonLine('Reviewer kind counts', summaryJobs.reviewer_kind_counts)
      + summaryJsonLine('Runtime provider counts', summaryJobs.runtime_provider_counts);
  return renderPanel(
    sectionTitle(label('section.summary_jobs', 'Summary Jobs'))
    + overviewSummaryJobCountButtons(counts, summaryJobs)
    + metricsSection(metricsBody)
    + detailLine('Source refs total', summaryJobs.summary_source_total ?? 0)
    + sliceButtonRow(summaryJobsSliceButtons())
    + endpointLatestResponseCluster('/api/summary-jobs', summaryJobs.latest_provider_response_detail_path, 'button.open_latest_summary_response', 'Open Latest Summary Response')
  );
}}
function overviewTriageCountRows(triage) {{
  return buttonRow([
    overviewCountButton(filterValueLabel('reviewQueue', 'review_requested'), triage.needs_attention_reviews, 'badge-warning', '/api/review-queue', 'reviewQueue', 'review_requested'),
  ])
    + buttonRow([
      overviewCountButton(filterValueLabel('reviewQueue', 'ready'), triage.ready_now_reviews, 'badge-ready', '/api/review-queue', 'reviewQueue', 'ready'),
      overviewCountButton(filterValueLabel('reviewQueue', 'advisory'), triage.advisory_only_reviews, 'badge-warning', '/api/review-queue', 'reviewQueue', 'advisory'),
    ])
    + buttonRow([
      overviewCountButton(filterValueLabel('reviewQueue', 'package:package_context_available'), triage.package_ready_reviews, 'badge-ready', '/api/review-queue', 'reviewQueue', 'package:package_context_available'),
    ])
    + buttonRow([
      overviewCountButton(filterValueLabel('reviewQueue', 'aligned'), triage.cli_parity_aligned_reviews, 'badge-ready', '/api/review-queue', 'reviewQueue', 'aligned'),
      overviewCountButton(filterValueLabel('reviewQueue', 'drift_detected'), triage.cli_parity_drift_reviews, 'badge-warning', '/api/review-queue', 'reviewQueue', 'drift_detected'),
    ])
    + buttonRow([
      overviewCountButton(filterValueLabel('reviewQueue', 'boundary_aligned'), triage.identity_boundary_aligned_reviews, 'badge-ready', '/api/review-queue', 'reviewQueue', 'boundary_aligned'),
      overviewCountButton(reviewWarningLabel('reviewer_identity_declared_only'), triage.identity_declared_only_reviews, 'badge-warning', '/api/review-queue', 'reviewQueue', 'reviewer_identity_declared_only'),
    ])
    + buttonRow([
      overviewCountButton(filterValueLabel('reviewQueue', 'response_id'), triage.provider_response_present_reviews, 'badge-ready', '/api/review-queue', 'reviewQueue', 'response_id'),
    ]);
}}
function renderOverviewTriagePanel(triage, warningButtons, warningSummaries) {{
  const metricsBody =
    summaryJsonLine('Runtime kinds', triage.runtime_record_kinds)
      + summaryJsonLine('Review capability counts', triage.review_capability_counts)
      + summaryJsonLine('Package readiness counts', triage.package_readiness_counts)
      + summaryJsonLine('CLI parity counts', triage.cli_parity_counts)
      + summaryJsonLine('Identity assurance counts', triage.identity_assurance_counts)
      + summaryJsonLine('Reviewer kind counts', triage.reviewer_kind_counts)
      + summaryJsonLine('Warning counts', triage.warning_counts);
  return renderPanel(
    sectionTitle(label('section.triage', 'Triage'))
    + overviewTriageCountRows(triage)
    + '<p>' + (warningButtons || '') + '</p>'
    + metricsSection(metricsBody)
    + '<p>' + esc(label('overview.warning_priority', 'Warning priority')) + ': '
    + overviewWarningPriorityBadges(warningSummaries)
    + '</p>'
    + overviewTriageNavigationCluster(triage)
    + sliceButtonRow(reviewQueueSliceButtons())
    + '<p>' + overviewTriageJumpButtons() + '</p>'
  );
}}
function overviewWarningButtons(warningSummaries) {{
  return warningSummaries.map(item =>
    overviewJumpButton(
      sliceBadge((item.label_key ? formatLabel(item.label_key, item.label_params || {{}}, item.label || item.code || 'warning') : (item.label || item.code || 'warning')), item.count ?? 0, 'badge-warning'),
      '/api/review-queue',
      'reviewQueue',
      item.code || ''
    )
  ).join('');
}}
function overviewWarningPriorityBadges(warningSummaries) {{
  return warningSummaries.length > 0
    ? warningSummaries.map(item =>
        sliceBadge((item.label_key ? formatLabel(item.label_key, item.label_params || {{}}, item.label || item.code || 'warning') : (item.label || item.code || 'warning')), item.count ?? 0, 'badge-warning')
      ).join('')
    : '(none)';
}}
function overviewTriageNavigationCluster(triage) {{
  return navigationCluster([
    openEndpointButton('/api/review-queue'),
    openEndpointButton('/api/runtime-records'),
    openEndpointButton('/api/summary-jobs'),
    latestResponseButton(triage.latest_provider_response_detail_path, 'button.open_latest_review_response', 'Open Latest Review Response'),
    openEndpointButton('/api/runtime-config'),
    openEndpointButton('/api/package-review'),
    '<button data-reset-filters="all">' + esc(label('button.reset_filter', 'Reset Filter')) + '</button>',
  ]);
}}
function overviewTriageJumpButtons() {{
  return [
    listJumpButton(filterValueLabel('reviewQueue', 'advisory'), '/api/review-queue', 'reviewQueue', 'advisory'),
    listJumpButton(filterValueLabel('reviewQueue', 'package:package_context_available'), '/api/review-queue', 'reviewQueue', 'package:package_context_available'),
    listJumpButton(filterValueLabel('reviewQueue', 'aligned'), '/api/review-queue', 'reviewQueue', 'aligned'),
    listJumpButton(filterValueLabel('reviewQueue', 'boundary_aligned'), '/api/review-queue', 'reviewQueue', 'boundary_aligned'),
    listJumpButton(reviewWarningLabel('ui_auth_not_enabled'), '/api/review-queue', 'reviewQueue', 'ui_auth_not_enabled'),
    listJumpButton(reviewWarningLabel('reviewer_identity_declared_only'), '/api/review-queue', 'reviewQueue', 'reviewer_identity_declared_only'),
    listJumpButton(filterValueLabel('runtimeRecords', 'retrieval_plan'), '/api/runtime-records', 'runtimeRecords', 'retrieval_plan'),
  ].join('');
}}
const overviewPanelRenderers = [
  data => renderOverviewHeaderPanel(data.chronicle),
  data => renderOverviewCountsPanel(data.counts),
  data => renderOverviewRuntimeBoundaryPanel(data.runtime),
  data => renderOverviewRuntimeConfigPanel(data.runtimeConfig, data.runtimeConfigContract),
  data => renderOverviewUiBoundaryPanel(data.uiBoundary),
  data => renderOverviewAuthBoundaryPanel(data.authBoundary, data.authBoundaryOverview),
  data => renderOverviewIdentityBoundaryPanel(data.identityBoundary),
  data => renderOverviewReviewerBoundaryPanel(data.reviewerBoundary),
  data => renderOverviewMutationReadinessPanel(data.mutationReadiness),
  data => renderOverviewAiIndexPanel(data.aiIndex, data.counts),
  data => renderOverviewRuntimeRecordsPanel(data.counts, data.runtimeRecords),
  data => renderOverviewSummaryJobsPanel(data.counts, data.summaryJobs),
  data => renderOverviewTriagePanel(data.triage, data.warningButtons, data.warningSummaries),
];
function renderOverviewPanels(data) {{
  return overviewPanelRenderers.map(renderer => renderer(data)).join('');
}}
function renderOverview(payload) {{
  const chronicle = payload.chronicle || {{}};
  const counts = payload.counts || {{}};
  const runtime = payload.runtime_boundary || {{}};
  const uiBoundary = payload.ui_boundary || {{}};
  const authBoundary = payload.auth_boundary_summary || uiBoundary.auth_boundary_summary || {{}};
  const authBoundaryOverview = payload.auth_boundary_overview || {{}};
  const identityBoundary = payload.identity_boundary_summary || {{}};
  const reviewerBoundary = payload.reviewer_boundary_overview || {{}};
  const aiIndex = payload.ai_index || {{}};
  const triage = payload.triage || {{}};
  const mutationReadiness = payload.mutation_readiness || {{}};
  const runtimeConfig = payload.runtime_config || {{}};
  const runtimeConfigContract = runtimeConfig.config || {{}};
  const runtimeRecords = payload.runtime_records_summary || {{}};
  const summaryJobs = payload.summary_jobs_summary || {{}};
  const warningSummaries = Array.isArray(triage.warning_summaries) ? triage.warning_summaries : [];
  const warningButtons = overviewWarningButtons(warningSummaries);
  const overviewData = {{
    aiIndex,
    authBoundary,
    authBoundaryOverview,
    chronicle,
    counts,
    identityBoundary,
    reviewerBoundary,
    mutationReadiness,
    runtime,
    runtimeConfig,
    runtimeConfigContract,
    runtimeRecords,
    summaryJobs,
    triage,
    uiBoundary,
    warningButtons,
    warningSummaries,
  }};
  return ''
    + '<h2>/api/overview</h2>'
    + renderPanel(activeViewSummary('/api/overview', 'overview'))
    + renderOverviewPanels(overviewData);
}}
const detailPathResolvers = {{
  '/api/ai-index-graph-edges': () => null,
  '/api/ai-index-vector': row => row.record_id ? '/api/ai-index/vector/' + encodeURIComponent(row.record_id) : null,
  '/api/ai-index-graph-nodes': row => row.node_id ? '/api/ai-index/graph-nodes/' + encodeURIComponent(row.node_id) : null,
  '/api/runtime-records': row => row.event_id ? '/api/runtime-records/' + encodeURIComponent(row.event_id) : null,
  '/api/review-queue': row => row.event_id ? '/api/review-queue/' + encodeURIComponent(row.event_id) : null,
}};
function detailPath(endpoint, row) {{
  const resolver = detailPathResolvers[endpoint];
  if (resolver) return resolver(row);
  for (const key of idFields) if (row[key]) return endpoint + '/' + encodeURIComponent(row[key]);
  return null;
}}
function renderTable(endpoint, rows) {{
  if (!rows || rows.length === 0) return messageParagraph('No records.');
  const renderer = endpointRenderers[endpoint];
  return renderer ? renderer(endpoint, rows) : renderGenericTable(endpoint, rows);
}}
function endpointBody(endpoint, payload) {{
  if (endpoint === '/api/overview') return renderOverview(payload);
  const rows = firstArray(payload);
  return rows
    ? routeHeading(endpoint) + renderTable(endpoint, rows)
    : routeHeading(endpoint) + collapsibleJsonBlock(label('label.response_json', 'Response JSON'), payload, true);
}}
function detailNavigationOptions(endpoint, record) {{
  const previousDetail = window.__chronicleDetailTrail.length > 0
    ? window.__chronicleDetailTrail[window.__chronicleDetailTrail.length - 1]
    : '';
  return {{
    filterLabel: currentFilterLabel(),
    listButtons: relatedListButtons(endpoint, record),
    previousDetail: previousDetail,
    trailLabel: currentTrailLabel(),
    trailButtons: currentTrailButtons(),
  }};
}}
const detailNoticeRenderers = [
  renderRuntimePreviewNotice,
  renderResponseMetadataNotice,
  renderRetrievalHandoffNotice,
  renderPackageHandoffPreviewNotice,
  renderInvocationPlanNotice,
  renderPackageReadinessNotice,
  renderRelatedLinksNotice,
  renderAuthReadinessNotice,
  renderReviewCapabilityNotice,
  renderMutationEnablementNotice,
  renderDetailActionPreviewNotice,
  renderCliParityNotice,
  renderIdentityAssuranceNotice,
  renderReviewerBoundaryDrilldownNotice,
  renderReviewTimelineNotice,
];
function renderDetailNotices(record) {{
  return detailNoticeRenderers.map(renderer => renderer(record)).join('');
}}
function detailNoticeBody(endpoint, record) {{
  const options = detailNavigationOptions(endpoint, record);
  return renderNavigationNotice(endpoint, record, options) + renderDetailNotices(record);
}}
function detailBody(endpoint, payload) {{
  const record = payload.record || {{}};
  return routeHeading(endpoint)
    + detailNoticeBody(endpoint, record)
    + collapsibleJsonBlock(label('label.record_json', 'Record JSON'), payload, false);
}}
async function loadEndpoint(endpoint) {{
  window.__chronicleCurrentEndpoint = endpoint;
  const response = await fetch(endpoint);
  const payload = await response.json();
  document.getElementById('view').innerHTML = endpointBody(endpoint, payload);
  applyLocaleToPage();
}}
async function loadDetail(endpoint) {{
  if (window.__chronicleLastDetail && window.__chronicleLastDetail !== endpoint) {{
    window.__chronicleDetailTrail.push(window.__chronicleLastDetail);
  }}
  window.__chronicleLastDetail = endpoint;
  const response = await fetch(endpoint);
  if (!response.ok) {{
    document.getElementById('detail').innerHTML = '<h2>' + esc(uiLabel('Detail')) + '</h2><p>' + esc(t('status.not_found')) + '</p>';
    applyLocaleToPage();
    return;
  }}
  const payload = await response.json();
  document.getElementById('detail').innerHTML = detailBody(endpoint, payload);
  applyLocaleToPage();
}}
async function previewBlockedRoute(path, targetId = 'action-preview-response') {{
  const target = document.getElementById(targetId);
  if (!target) return;
  target.innerHTML = '<p>' + esc(t('status.loading_blocked_preview')) + '</p>';
  const {{ response, payload }} = await postJson(path);
  target.innerHTML = renderReviewActionResultPanel(
    t('status.blocked_route_preview'),
    response.status,
    path,
    payload,
    targetId,
    {{
      extraLines: detailLine('Mutation enabled', payload.mutation_enabled),
    }},
  );
  applyLocaleToPage();
}}
function reviewFieldValue(prefix, suffix, fallback = '') {{
  const element = prefix === 'reviewer'
    ? document.getElementById(suffix)
    : document.getElementById(prefix + '-' + suffix);
  return element && typeof element.value === 'string' ? element.value : fallback;
}}
async function copyCommand(command, targetId = 'action-preview-response') {{
  const target = document.getElementById(targetId);
  if (!command) return;
  const copied = await tryCopyText(command);
  appendCommandFeedback(target, command, copied);
}}
async function submitReviewAction(path, action, recordId, targetId = 'action-preview-response', fieldPrefix = 'reviewer', successDetail = '') {{
  const target = document.getElementById(targetId);
  if (!target) return;
  target.innerHTML = '<p>' + esc(t('status.applying_review_action')) + '</p>';
  const {{ response, payload }} = await postJson(path, reviewActionRequestBody(action, fieldPrefix));
  target.innerHTML = renderReviewActionResultPanel(
    t('status.review_action_result'),
    response.status,
    path,
    payload,
    targetId,
    {{
      action: action,
      recordId: recordId,
      useStatusFallback: true,
      extraLines: ''
        + detailLine('Audit ID', payload.audit_id || '')
        + detailLine('Decision event', payload.decision_event_id || ''),
    }},
  );
  applyLocaleToPage();
  if (response.ok) {{
    if (window.__chronicleCurrentEndpoint) loadEndpoint(window.__chronicleCurrentEndpoint);
    if (successDetail) {{
      loadDetail(successDetail);
    }} else if (recordId) {{
      loadDetail('/api/review-queue/' + encodeURIComponent(recordId));
    }}
  }}
}}
document.querySelectorAll('button[data-endpoint]').forEach(button => button.addEventListener('click', () => loadEndpoint(button.dataset.endpoint)));
document.getElementById('view').addEventListener('click', handleViewClick);
document.getElementById('detail').addEventListener('click', handleDetailClick);
document.getElementById('view').addEventListener('click', handleViewPreviewPost);
window.__chronicleFilters = {{ runtimeRecords: '', reviewQueue: '', summaryJobs: '' }};
window.__chronicleSorts = {{ runtimeRecords: 'latest', reviewQueue: 'attention', summaryJobs: 'latest' }};
window.__chronicleDetailTrail = [];
window.__chronicleLocale = initialLocale();
window.__chronicleMutationToken = {mutation_token_json};
window.__chronicleMutationSessionId = {mutation_session_id_json};
window.__chronicleMutationRequestSequence = 0;
document.getElementById('view').addEventListener('input', handleViewInput);
document.getElementById('view').addEventListener('change', handleViewChange);
document.getElementById('locale-select').addEventListener('change', event => setLocale(event.target.value));
applyLocaleToPage();
loadEndpoint('/api/overview');
</script>
</body>
</html>"""

    def static_review_console(self) -> str:
        return HtmlDashboardExporter(self.root).export()


def create_handler(
    root: Path | None = None,
    *,
    host: str = DEFAULT_UI_HOST,
    mutation_capability_flag: bool = False,
    enable_ui_mutation: bool = False,
    auth_mode: str = UIAuthMode.NOT_ENABLED,
    authorization_mode: str = UIAuthorizationMode.NOT_ENABLED,
) -> type[BaseHTTPRequestHandler]:
    mutation_session_token = secrets.token_urlsafe(24)
    mutation_session_id = f"msn-{secrets.token_hex(8)}"
    mutation_request_ids_seen: set[str] = set()
    service = ChronicleUIDataService(
        root,
        host=host,
        mutation_capability_flag=mutation_capability_flag,
        enable_ui_mutation=enable_ui_mutation,
        auth_mode=auth_mode,
        authorization_mode=authorization_mode,
        mutation_session_token=mutation_session_token,
        mutation_session_id=mutation_session_id,
    )

    class ChronicleUIRequestHandler(BaseHTTPRequestHandler):
        server_version = "ChronicleUILocal/0.3"

        def do_GET(self) -> None:  # noqa: N802 - stdlib API
            parsed = urlparse(self.path)
            if parsed.path in ("/", "/index.html"):
                self._send_html(service.html_shell())
                return
            if parsed.path == "/review-console":
                self._send_html(service.static_review_console())
                return
            payload = service.api_payload(parsed.path)
            if payload is not None:
                self._send_json(payload)
                return
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")

        def do_POST(self) -> None:  # noqa: N802 - stdlib API
            parsed = urlparse(self.path)
            boundary = service.ui_boundary()["ui_boundary"]
            if parsed.path.startswith("/api/review-actions/") and boundary.get("mutation_enabled", False):
                supplied_token = str(self.headers.get(MUTATION_TOKEN_HEADER, "") or "")
                if supplied_token != mutation_session_token:
                    self._send_json(
                        service._review_action_failure_payload(
                            error_code="invalid_mutation_token",
                            mutation_enabled=True,
                            reviewer_context_requirements=boundary.get("reviewer_context_requirements", {}),
                            reviewer_enforcement_summary=boundary.get("reviewer_enforcement_summary", {}),
                            reviewer_validation_gate_summary=boundary.get("reviewer_validation_gate_summary", {}),
                            write_route_contract=boundary.get("write_route_contract", {}),
                            success_contract=service._review_action_success_contract(),
                            failure_contract=service._review_action_failure_contract(
                                mutation_enabled=True,
                                error_code="invalid_mutation_token",
                            ),
                        ),
                        status=HTTPStatus.FORBIDDEN,
                    )
                    return
            content_length = int(self.headers.get("Content-Length", "0") or 0)
            raw_body = self.rfile.read(content_length) if content_length > 0 else b"{}"
            try:
                body = json.loads(raw_body.decode("utf-8"))
            except json.JSONDecodeError:
                self._send_json(
                    service._review_action_failure_payload(
                        error_code="invalid_json",
                        mutation_enabled=service.ui_boundary()["ui_boundary"]["mutation_enabled"],
                        failure_contract=service._review_action_failure_contract(
                            mutation_enabled=service.ui_boundary()["ui_boundary"]["mutation_enabled"],
                            error_code="invalid_json",
                        ),
                    ),
                    status=HTTPStatus.BAD_REQUEST,
                )
                return
            if not isinstance(body, dict):
                self._send_json(
                    service._review_action_failure_payload(
                        error_code="invalid_request_body",
                        mutation_enabled=service.ui_boundary()["ui_boundary"]["mutation_enabled"],
                    ),
                    status=HTTPStatus.BAD_REQUEST,
                )
                return
            if parsed.path.startswith("/api/review-actions/") and boundary.get("mutation_enabled", False):
                mutation_session_id = str(body.get("mutation_session_id", "") or "").strip()
                mutation_request_id = str(body.get("mutation_request_id", "") or "").strip()
                if mutation_session_id != service.mutation_session_id:
                    self._send_json(
                        service._review_action_failure_payload(
                            error_code="invalid_mutation_session",
                            mutation_enabled=True,
                            reviewer_context_requirements=boundary.get("reviewer_context_requirements", {}),
                            reviewer_enforcement_summary=boundary.get("reviewer_enforcement_summary", {}),
                            reviewer_validation_gate_summary=boundary.get("reviewer_validation_gate_summary", {}),
                            write_route_contract=boundary.get("write_route_contract", {}),
                            success_contract=service._review_action_success_contract(),
                            failure_contract=service._review_action_failure_contract(
                                mutation_enabled=True,
                                error_code="invalid_mutation_session",
                            ),
                        ),
                        status=HTTPStatus.FORBIDDEN,
                    )
                    return
                if not mutation_request_id:
                    self._send_json(
                        service._review_action_failure_payload(
                            error_code="mutation_request_id_required",
                            mutation_enabled=True,
                            reviewer_context_requirements=boundary.get("reviewer_context_requirements", {}),
                            reviewer_enforcement_summary=boundary.get("reviewer_enforcement_summary", {}),
                            reviewer_validation_gate_summary=boundary.get("reviewer_validation_gate_summary", {}),
                            write_route_contract=boundary.get("write_route_contract", {}),
                            success_contract=service._review_action_success_contract(),
                            failure_contract=service._review_action_failure_contract(
                                mutation_enabled=True,
                                error_code="mutation_request_id_required",
                            ),
                        ),
                        status=HTTPStatus.BAD_REQUEST,
                    )
                    return
                if not MUTATION_REQUEST_ID_PATTERN.fullmatch(mutation_request_id):
                    self._send_json(
                        service._review_action_failure_payload(
                            error_code="invalid_mutation_request_id",
                            mutation_enabled=True,
                            reviewer_context_requirements=boundary.get("reviewer_context_requirements", {}),
                            reviewer_enforcement_summary=boundary.get("reviewer_enforcement_summary", {}),
                            reviewer_validation_gate_summary=boundary.get("reviewer_validation_gate_summary", {}),
                            write_route_contract=boundary.get("write_route_contract", {}),
                            success_contract=service._review_action_success_contract(),
                            failure_contract=service._review_action_failure_contract(
                                mutation_enabled=True,
                                error_code="invalid_mutation_request_id",
                            ),
                        ),
                        status=HTTPStatus.BAD_REQUEST,
                    )
                    return
                if mutation_request_id in mutation_request_ids_seen:
                    self._send_json(
                        service._review_action_failure_payload(
                            error_code="duplicate_mutation_request",
                            mutation_enabled=True,
                            reviewer_context_requirements=boundary.get("reviewer_context_requirements", {}),
                            reviewer_enforcement_summary=boundary.get("reviewer_enforcement_summary", {}),
                            reviewer_validation_gate_summary=boundary.get("reviewer_validation_gate_summary", {}),
                            write_route_contract=boundary.get("write_route_contract", {}),
                            success_contract=service._review_action_success_contract(),
                            failure_contract=service._review_action_failure_contract(
                                mutation_enabled=True,
                                error_code="duplicate_mutation_request",
                            ),
                        ),
                        status=HTTPStatus.CONFLICT,
                    )
                    return
                mutation_request_ids_seen.add(mutation_request_id)
            result = service.review_action_response(parsed.path, body)
            if result is not None:
                status, payload = result
                self._send_json(payload, status=status)
                return
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")

        def log_message(self, format: str, *args: object) -> None:
            return

        def _send_html(self, body: str) -> None:
            payload = body.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def _send_json(self, body: dict[str, Any], *, status: HTTPStatus = HTTPStatus.OK) -> None:
            payload = json.dumps(body, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    return ChronicleUIRequestHandler


def make_server(
    *,
    host: str = DEFAULT_UI_HOST,
    port: int = DEFAULT_UI_PORT,
    root: Path | None = None,
    mutation_capability_flag: bool = False,
    enable_ui_mutation: bool = False,
    auth_mode: str = UIAuthMode.NOT_ENABLED,
    authorization_mode: str = UIAuthorizationMode.NOT_ENABLED,
) -> ThreadingHTTPServer:
    return ThreadingHTTPServer(
        (host, port),
        create_handler(
            root,
            host=host,
            mutation_capability_flag=mutation_capability_flag,
            enable_ui_mutation=enable_ui_mutation,
            auth_mode=auth_mode,
            authorization_mode=authorization_mode,
        ),
    )


def serve_ui(
    *,
    host: str = DEFAULT_UI_HOST,
    port: int = DEFAULT_UI_PORT,
    root: Path | None = None,
    open_browser: bool = False,
    mutation_capability_flag: bool = False,
    enable_ui_mutation: bool = False,
    auth_mode: str = UIAuthMode.NOT_ENABLED,
    authorization_mode: str = UIAuthorizationMode.NOT_ENABLED,
) -> UIStartupMetadata:
    root_path = root or Path.cwd()
    service = ChronicleService(root_path)
    service.require_initialized()
    metadata = build_startup_metadata(
        host=host,
        port=port,
        root=root_path,
        mutation_capability_flag=mutation_capability_flag,
        enable_ui_mutation=enable_ui_mutation,
        auth_mode=auth_mode,
        authorization_mode=authorization_mode,
    )
    server = make_server(
        host=host,
        port=port,
        root=root_path,
        mutation_capability_flag=mutation_capability_flag,
        enable_ui_mutation=enable_ui_mutation,
        auth_mode=auth_mode,
        authorization_mode=authorization_mode,
    )
    if open_browser:
        webbrowser.open(metadata.url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:  # pragma: no cover - interactive shutdown path
        pass
    finally:
        server.server_close()
    return metadata


def validate_ui_root(root: Path | None = None) -> None:
    try:
        ChronicleService(root).require_initialized()
    except ChronicleError:
        raise


def validate_ui_host(host: str) -> None:
    if _is_loopback_host(host):
        return
    raise UIHostNotLoopbackError(host)


def _bind_scope(host: str) -> str:
    return "loopback-only" if _is_loopback_host(host) else "non-loopback"


def _is_loopback_host(host: str) -> bool:
    normalized = host.strip().lower()
    if normalized == "localhost":
        return True
    try:
        return ipaddress.ip_address(normalized).is_loopback
    except ValueError:
        return False
