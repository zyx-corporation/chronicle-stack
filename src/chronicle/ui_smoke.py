"""Read-only smoke checks for the Chronicle local UI data surface.

This module does not start a web server, open a browser, bind sockets, call
external model APIs, or certify correctness. It only checks that the local UI
read models can be derived from an initialized Chronicle root.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from chronicle.ui_server import ChronicleUIDataService


@dataclass(frozen=True)
class UISmokeCheck:
    """One smoke check result."""

    name: str
    passed: bool
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "passed": self.passed, "message": self.message}


@dataclass(frozen=True)
class UISmokeReport:
    """Summary of read-only UI smoke checks."""

    root: str
    passed: bool
    checks: list[UISmokeCheck] = field(default_factory=list)
    read_only: bool = True
    server_started: bool = False
    browser_required: bool = False
    external_runtime: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "root": self.root,
            "passed": self.passed,
            "read_only": self.read_only,
            "server_started": self.server_started,
            "browser_required": self.browser_required,
            "external_runtime": self.external_runtime,
            "checks": [check.to_dict() for check in self.checks],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


_COLLECTION_CHECKS: tuple[tuple[str, str], ...] = (
    ("/api/overview", "counts"),
    ("/api/events", "events"),
    ("/api/contexts", "contexts"),
    ("/api/artifacts", "artifacts"),
    ("/api/decisions", "decisions"),
    ("/api/rde", "rde_records"),
    ("/api/boundary", "boundary_rules"),
    ("/api/audit", "audit_events"),
    ("/api/lifecycle", "lifecycle_markers"),
    ("/api/runtime-records", "runtime_records"),
    ("/api/review-queue", "review_queue"),
    ("/api/summary-jobs", "summary_jobs"),
    ("/api/ui-boundary", "ui_boundary"),
    ("/api/runtime-config", "runtime_config"),
    ("/api/package-review", "package_review"),
    ("/api/graph-summary", "graph_summary"),
    ("/api/ai-index-status", "ai_index_status"),
    ("/api/ai-index-vector", "vector_entries"),
    ("/api/ai-index-graph-nodes", "graph_nodes"),
    ("/api/ai-index-graph-edges", "graph_edges"),
)

_DETAIL_ID_FIELDS: dict[str, str] = {
    "/api/events": "event_id",
    "/api/contexts": "context_id",
    "/api/artifacts": "artifact_id",
    "/api/decisions": "decision_id",
    "/api/rde": "rde_record_id",
    "/api/boundary": "rule_id",
    "/api/audit": "audit_id",
    "/api/lifecycle": "lifecycle_id",
    "/api/runtime-records": "event_id",
    "/api/review-queue": "target_event_id",
    "/api/summary-jobs": "summary_job_id",
    "/api/ai-index-vector": "record_id",
    "/api/ai-index-graph-nodes": "node_id",
}


def _first_array(payload: dict[str, Any]) -> list[dict[str, Any]] | None:
    for value in payload.values():
        if isinstance(value, list):
            return value
    return None


def run_ui_smoke(root: Path | None = None) -> UISmokeReport:
    """Run read-only UI smoke checks against a Chronicle root."""
    root_path = root or Path.cwd()
    service = ChronicleUIDataService(root_path)
    checks: list[UISmokeCheck] = []
    collection_payloads: dict[str, dict[str, Any]] = {}

    try:
        for endpoint, expected_key in _COLLECTION_CHECKS:
            payload = service.api_payload(endpoint)
            if payload is None:
                checks.append(UISmokeCheck(endpoint, False, "missing payload"))
                continue
            collection_payloads[endpoint] = payload
            checks.append(
                UISmokeCheck(
                    endpoint,
                    expected_key in payload,
                    "ok" if expected_key in payload else f"missing key: {expected_key}",
                )
            )
            if endpoint == "/api/ui-boundary":
                ui_boundary = payload.get("ui_boundary", {})
                write_route_contract = ui_boundary.get("write_route_contract", {})
                checks.append(
                    UISmokeCheck(
                        "/api/ui-boundary#write-route-contract",
                        isinstance(write_route_contract, dict)
                        and bool(write_route_contract.get("route_template"))
                        and isinstance(write_route_contract.get("actions"), list)
                        and isinstance(write_route_contract.get("action_routes"), list)
                        and all(
                            isinstance(item, dict)
                            and bool(item.get("action"))
                            and bool(item.get("path_template"))
                            and bool(item.get("cli_equivalent_template"))
                            for item in write_route_contract.get("action_routes", [])
                        )
                        and isinstance(write_route_contract.get("expected_request_fields"), list),
                        (
                            "ok"
                            if isinstance(write_route_contract, dict)
                            and bool(write_route_contract.get("route_template"))
                            and isinstance(write_route_contract.get("actions"), list)
                            and isinstance(write_route_contract.get("action_routes"), list)
                            and all(
                                isinstance(item, dict)
                                and bool(item.get("action"))
                                and bool(item.get("path_template"))
                                and bool(item.get("cli_equivalent_template"))
                                for item in write_route_contract.get("action_routes", [])
                            )
                            and isinstance(write_route_contract.get("expected_request_fields"), list)
                            else "ui boundary missing write route contract detail"
                        ),
                    )
                )

        for endpoint, id_field in _DETAIL_ID_FIELDS.items():
            payload = collection_payloads.get(endpoint)
            if payload is None:
                continue
            rows = _first_array(payload)
            if not rows:
                checks.append(UISmokeCheck(f"{endpoint}/<id>", True, "skipped: no records"))
                continue
            record_id = rows[0].get(id_field)
            if not isinstance(record_id, str) or not record_id:
                checks.append(UISmokeCheck(f"{endpoint}/<id>", False, f"missing id field: {id_field}"))
                continue
            detail = service.detail_payload(f"{endpoint}/{record_id}")
            checks.append(
                UISmokeCheck(
                    f"{endpoint}/{record_id}",
                    detail is not None and "record" in detail,
                    "ok" if detail is not None and "record" in detail else "missing detail record",
                )
            )
            if endpoint == "/api/review-queue" and detail is not None and "record" in detail:
                record = detail["record"]
                cli_parity = record.get("cli_parity")
                checks.append(
                    UISmokeCheck(
                        f"{endpoint}/{record_id}#cli-parity",
                        isinstance(cli_parity, dict) and cli_parity.get("status") == "aligned",
                        (
                            "ok"
                            if isinstance(cli_parity, dict) and cli_parity.get("status") == "aligned"
                            else "review detail missing aligned cli parity summary"
                        ),
                    )
                )
                auth_notice = record.get("auth_boundary_notice")
                checks.append(
                    UISmokeCheck(
                        f"{endpoint}/{record_id}#auth-readiness",
                        isinstance(auth_notice, dict)
                        and bool(auth_notice.get("status"))
                        and bool(auth_notice.get("scope_note"))
                        and isinstance(auth_notice.get("blocker_summaries"), list),
                        (
                            "ok"
                            if isinstance(auth_notice, dict)
                            and bool(auth_notice.get("status"))
                            and bool(auth_notice.get("scope_note"))
                            and isinstance(auth_notice.get("blocker_summaries"), list)
                            else "review detail missing auth readiness notice"
                        ),
                    )
                )
                mutation_enablement = record.get("mutation_enablement")
                checks.append(
                    UISmokeCheck(
                        f"{endpoint}/{record_id}#mutation-enablement",
                        (
                            isinstance(mutation_enablement, dict)
                            and isinstance(mutation_enablement.get("blocker_summaries"), list)
                            and all(
                                isinstance(item, dict) and bool(item.get("summary"))
                                for item in mutation_enablement.get("blocker_summaries", [])
                            )
                            and isinstance(mutation_enablement.get("operational_readiness"), dict)
                            and isinstance(
                                mutation_enablement.get("operational_readiness", {}).get(
                                    "blocking_summaries"
                                ),
                                list,
                            )
                            and isinstance(
                                mutation_enablement.get("reviewer_context_requirements", {}).get(
                                    "effective_required_fields"
                                ),
                                list,
                            )
                            and isinstance(
                                mutation_enablement.get("reviewer_context_requirements", {}).get(
                                    "required_reviewer_kinds_for_mutation"
                                ),
                                list,
                            )
                            and bool(
                                mutation_enablement.get("reviewer_context_requirements", {}).get(
                                    "expectation_summary"
                                )
                            )
                            and isinstance(mutation_enablement.get("write_route_contract", {}).get("actions"), list)
                            and isinstance(mutation_enablement.get("identity_proof_contract"), dict)
                        ),
                        (
                            "ok"
                            if isinstance(mutation_enablement, dict)
                            and isinstance(mutation_enablement.get("blocker_summaries"), list)
                            and all(
                                isinstance(item, dict) and bool(item.get("summary"))
                                for item in mutation_enablement.get("blocker_summaries", [])
                            )
                            and isinstance(mutation_enablement.get("operational_readiness"), dict)
                            and isinstance(
                                mutation_enablement.get("operational_readiness", {}).get(
                                    "blocking_summaries"
                                ),
                                list,
                            )
                            and isinstance(
                                mutation_enablement.get("reviewer_context_requirements", {}).get(
                                    "effective_required_fields"
                                ),
                                list,
                            )
                            and isinstance(
                                mutation_enablement.get("reviewer_context_requirements", {}).get(
                                    "required_reviewer_kinds_for_mutation"
                                ),
                                list,
                            )
                            and bool(
                                mutation_enablement.get("reviewer_context_requirements", {}).get(
                                    "expectation_summary"
                                )
                            )
                            and isinstance(mutation_enablement.get("write_route_contract", {}).get("actions"), list)
                            and isinstance(mutation_enablement.get("identity_proof_contract"), dict)
                            else "review detail missing mutation enablement contract detail"
                        ),
                    )
                )
                action_preview = record.get("action_preview")
                first_action = action_preview.get("actions", [None])[0] if isinstance(action_preview, dict) else None
                checks.append(
                    UISmokeCheck(
                        f"{endpoint}/{record_id}#blocked-route-preview",
                        isinstance(first_action, dict)
                        and first_action.get("post_expected_status") == 403
                        and first_action.get("post_expected_error_code") == "mutation_disabled"
                        and isinstance(action_preview.get("failure_contract"), dict)
                        and action_preview.get("failure_contract", {}).get("rollback_status") == "fail_closed",
                        (
                            "ok"
                            if isinstance(first_action, dict)
                            and first_action.get("post_expected_status") == 403
                            and first_action.get("post_expected_error_code") == "mutation_disabled"
                            and isinstance(action_preview.get("failure_contract"), dict)
                            and action_preview.get("failure_contract", {}).get("rollback_status") == "fail_closed"
                            else "review detail missing blocked route preview contract"
                        ),
                    )
                )
                checks.append(
                    UISmokeCheck(
                        f"{endpoint}/{record_id}#preview-follow-up-contract",
                        (
                            isinstance(action_preview, dict)
                            and isinstance(action_preview.get("success_contract"), dict)
                            and isinstance(action_preview.get("success_contract", {}).get("follow_up_commands"), list)
                            and bool(action_preview.get("write_route_contract", {}).get("route_template"))
                            and isinstance(action_preview.get("write_route_contract", {}).get("expected_request_fields"), list)
                            and isinstance(action_preview.get("write_route_contract", {}).get("identity_proof_contract"), dict)
                        ),
                        (
                            "ok"
                            if isinstance(action_preview, dict)
                            and isinstance(action_preview.get("success_contract"), dict)
                            and isinstance(action_preview.get("success_contract", {}).get("follow_up_commands"), list)
                            and bool(action_preview.get("write_route_contract", {}).get("route_template"))
                            and isinstance(action_preview.get("write_route_contract", {}).get("expected_request_fields"), list)
                            and isinstance(action_preview.get("write_route_contract", {}).get("identity_proof_contract"), dict)
                            else "review detail missing preview follow-up contract"
                        ),
                    )
                )
                blocked = service.review_action_blocked_response(
                    f"/api/review-actions/{record_id}/approve"
                )
                checks.append(
                    UISmokeCheck(
                        f"/api/review-actions/{record_id}/approve",
                        blocked is not None
                        and blocked[0].value == 403
                        and blocked[1].get("error_code") == "mutation_disabled"
                        and isinstance(blocked[1].get("reviewer_context_requirements"), dict)
                        and bool(blocked[1].get("write_route_contract", {}).get("route_template"))
                        and isinstance(blocked[1].get("success_contract"), dict)
                        and isinstance(blocked[1].get("success_contract", {}).get("follow_up_commands"), list)
                        and isinstance(blocked[1].get("failure_contract"), dict)
                        and blocked[1].get("failure_contract", {}).get("rollback_status") == "fail_closed",
                        (
                            "ok"
                            if blocked is not None
                            and blocked[0].value == 403
                            and blocked[1].get("error_code") == "mutation_disabled"
                            and isinstance(blocked[1].get("reviewer_context_requirements"), dict)
                            and bool(blocked[1].get("write_route_contract", {}).get("route_template"))
                            and isinstance(blocked[1].get("success_contract"), dict)
                            and isinstance(blocked[1].get("success_contract", {}).get("follow_up_commands"), list)
                            and isinstance(blocked[1].get("failure_contract"), dict)
                            and blocked[1].get("failure_contract", {}).get("rollback_status") == "fail_closed"
                            else "blocked review action route contract missing"
                        ),
                    )
                )
            if endpoint == "/api/runtime-records" and detail is not None and "record" in detail:
                record = detail["record"]
                auth_notice = record.get("auth_boundary_notice")
                checks.append(
                    UISmokeCheck(
                        f"{endpoint}/{record_id}#auth-readiness",
                        isinstance(auth_notice, dict)
                        and bool(auth_notice.get("status"))
                        and bool(auth_notice.get("scope_note"))
                        and isinstance(auth_notice.get("blocker_summaries"), list),
                        (
                            "ok"
                            if isinstance(auth_notice, dict)
                            and bool(auth_notice.get("status"))
                            and bool(auth_notice.get("scope_note"))
                            and isinstance(auth_notice.get("blocker_summaries"), list)
                            else "runtime detail missing auth readiness notice"
                        ),
                    )
                )
                mutation_enablement = record.get("mutation_enablement")
                checks.append(
                    UISmokeCheck(
                        f"{endpoint}/{record_id}#mutation-enablement",
                        isinstance(mutation_enablement, dict)
                        and isinstance(mutation_enablement.get("blocker_summaries"), list)
                        and all(
                            isinstance(item, dict) and bool(item.get("summary"))
                            for item in mutation_enablement.get("blocker_summaries", [])
                        )
                        and isinstance(mutation_enablement.get("operational_readiness"), dict)
                        and isinstance(
                            mutation_enablement.get("operational_readiness", {}).get("blocking_summaries"),
                            list,
                        )
                        and bool(mutation_enablement.get("write_route_contract", {}).get("route_template")),
                        (
                            "ok"
                            if isinstance(mutation_enablement, dict)
                            and isinstance(mutation_enablement.get("blocker_summaries"), list)
                            and all(
                                isinstance(item, dict) and bool(item.get("summary"))
                                for item in mutation_enablement.get("blocker_summaries", [])
                            )
                            and isinstance(mutation_enablement.get("operational_readiness"), dict)
                            and isinstance(
                                mutation_enablement.get("operational_readiness", {}).get(
                                    "blocking_summaries"
                                ),
                                list,
                            )
                            and bool(mutation_enablement.get("write_route_contract", {}).get("route_template"))
                            else "runtime detail missing mutation enablement contract detail"
                        ),
                    )
                )
            if endpoint == "/api/summary-jobs" and detail is not None and "record" in detail:
                record = detail["record"]
                auth_notice = record.get("auth_boundary_notice")
                checks.append(
                    UISmokeCheck(
                        f"{endpoint}/{record_id}#auth-readiness",
                        isinstance(auth_notice, dict)
                        and bool(auth_notice.get("status"))
                        and bool(auth_notice.get("scope_note"))
                        and isinstance(auth_notice.get("blocker_summaries"), list),
                        (
                            "ok"
                            if isinstance(auth_notice, dict)
                            and bool(auth_notice.get("status"))
                            and bool(auth_notice.get("scope_note"))
                            and isinstance(auth_notice.get("blocker_summaries"), list)
                            else "summary detail missing auth readiness notice"
                        ),
                    )
                )
                checks.append(
                    UISmokeCheck(
                        f"{endpoint}/{record_id}#identity-assurance",
                        bool(record.get("identity_assurance_status"))
                        or isinstance(record.get("latest_identity_assurance"), dict),
                        (
                            "ok"
                            if bool(record.get("identity_assurance_status"))
                            or isinstance(record.get("latest_identity_assurance"), dict)
                            else "summary detail missing identity/session assurance surface"
                        ),
                    )
                )
                mutation_enablement = record.get("mutation_enablement")
                checks.append(
                    UISmokeCheck(
                        f"{endpoint}/{record_id}#mutation-enablement",
                        (
                            isinstance(mutation_enablement, dict)
                            and isinstance(mutation_enablement.get("blocker_summaries"), list)
                            and isinstance(mutation_enablement.get("operational_readiness"), dict)
                            and isinstance(
                                mutation_enablement.get("reviewer_context_requirements", {}).get(
                                    "effective_required_fields"
                                ),
                                list,
                            )
                            and isinstance(
                                mutation_enablement.get("reviewer_context_requirements", {}).get(
                                    "required_reviewer_kinds_for_mutation"
                                ),
                                list,
                            )
                            and isinstance(mutation_enablement.get("write_route_contract", {}).get("actions"), list)
                            and isinstance(mutation_enablement.get("identity_proof_contract"), dict)
                        ),
                        (
                            "ok"
                            if isinstance(mutation_enablement, dict)
                            and isinstance(mutation_enablement.get("blocker_summaries"), list)
                            and isinstance(mutation_enablement.get("operational_readiness"), dict)
                            and isinstance(
                                mutation_enablement.get("reviewer_context_requirements", {}).get(
                                    "effective_required_fields"
                                ),
                                list,
                            )
                            and isinstance(
                                mutation_enablement.get("reviewer_context_requirements", {}).get(
                                    "required_reviewer_kinds_for_mutation"
                                ),
                                list,
                            )
                            and isinstance(mutation_enablement.get("write_route_contract", {}).get("actions"), list)
                            and isinstance(mutation_enablement.get("identity_proof_contract"), dict)
                            else "summary detail missing mutation enablement contract detail"
                        ),
                    )
                )
                preview = record.get("action_preview")
                first_action = preview.get("actions", [None])[0] if isinstance(preview, dict) else None
                checks.append(
                    UISmokeCheck(
                        f"{endpoint}/{record_id}#blocked-route-preview",
                        isinstance(first_action, dict)
                        and first_action.get("post_expected_status") == 403
                        and first_action.get("post_expected_error_code") == "mutation_disabled"
                        and isinstance(preview.get("failure_contract"), dict)
                        and preview.get("failure_contract", {}).get("rollback_status") == "fail_closed",
                        (
                            "ok"
                            if isinstance(first_action, dict)
                            and first_action.get("post_expected_status") == 403
                            and first_action.get("post_expected_error_code") == "mutation_disabled"
                            and isinstance(preview.get("failure_contract"), dict)
                            and preview.get("failure_contract", {}).get("rollback_status") == "fail_closed"
                            else "summary detail missing blocked route preview contract"
                        ),
                    )
                )
                checks.append(
                    UISmokeCheck(
                        f"{endpoint}/{record_id}#preview-follow-up-contract",
                        (
                            isinstance(preview, dict)
                            and isinstance(preview.get("success_contract"), dict)
                            and isinstance(preview.get("success_contract", {}).get("follow_up_commands"), list)
                            and bool(preview.get("write_route_contract", {}).get("route_template"))
                            and isinstance(preview.get("write_route_contract", {}).get("expected_request_fields"), list)
                            and isinstance(preview.get("write_route_contract", {}).get("identity_proof_contract"), dict)
                        ),
                        (
                            "ok"
                            if isinstance(preview, dict)
                            and isinstance(preview.get("success_contract"), dict)
                            and isinstance(preview.get("success_contract", {}).get("follow_up_commands"), list)
                            and bool(preview.get("write_route_contract", {}).get("route_template"))
                            and isinstance(preview.get("write_route_contract", {}).get("expected_request_fields"), list)
                            and isinstance(preview.get("write_route_contract", {}).get("identity_proof_contract"), dict)
                            else "summary detail missing preview follow-up contract"
                        ),
                    )
                )

        missing = service.detail_payload("/api/contexts/__chronicle_missing_context__")
        checks.append(
            UISmokeCheck(
                "/api/contexts/__chronicle_missing_context__",
                missing is None,
                "ok" if missing is None else "missing detail unexpectedly returned payload",
            )
        )

        html_shell = service.html_shell()
        shell_ok = all(
            marker in html_shell
            for marker in (
                "Active view:",
                "Auth Readiness",
                "CLI Parity",
                "Related Links",
                "Review Queue",
                "Runtime Records",
                "Summary jobs blocked-route preview stays read-only and returns the CLI fallback contract.",
                "Review queue blocked-route preview stays read-only and returns the CLI fallback contract.",
            )
        )
        overview = collection_payloads.get("/api/overview", {})
        runtime_summary = overview.get("runtime_records_summary")
        summary_jobs_summary = overview.get("summary_jobs_summary")
        checks.append(
            UISmokeCheck(
                "/api/overview#runtime-auth-readiness",
                isinstance(runtime_summary, dict) and isinstance(runtime_summary.get("auth_readiness_counts"), dict),
                (
                    "ok"
                    if isinstance(runtime_summary, dict) and isinstance(runtime_summary.get("auth_readiness_counts"), dict)
                    else "overview missing runtime auth readiness summary"
                ),
            )
        )
        checks.append(
            UISmokeCheck(
                "/api/overview#summary-auth-readiness",
                isinstance(summary_jobs_summary, dict) and isinstance(summary_jobs_summary.get("auth_readiness_counts"), dict),
                (
                    "ok"
                    if isinstance(summary_jobs_summary, dict) and isinstance(summary_jobs_summary.get("auth_readiness_counts"), dict)
                    else "overview missing summary auth readiness summary"
                ),
            )
        )
        checks.append(
            UISmokeCheck(
                "/api/overview#summary-identity-readiness",
                isinstance(summary_jobs_summary, dict)
                and isinstance(summary_jobs_summary.get("identity_assurance_counts"), dict)
                and isinstance(summary_jobs_summary.get("reviewer_kind_counts"), dict),
                (
                    "ok"
                    if isinstance(summary_jobs_summary, dict)
                    and isinstance(summary_jobs_summary.get("identity_assurance_counts"), dict)
                    and isinstance(summary_jobs_summary.get("reviewer_kind_counts"), dict)
                    else "overview missing summary identity/session readiness summary"
                ),
            )
        )
        mutation_readiness = overview.get("mutation_readiness")
        checks.append(
            UISmokeCheck(
                "/api/overview#mutation-readiness",
                (
                    isinstance(mutation_readiness, dict)
                    and isinstance(mutation_readiness.get("blocker_summaries"), list)
                    and all(
                        isinstance(item, dict) and bool(item.get("summary"))
                        for item in mutation_readiness.get("blocker_summaries", [])
                    )
                    and isinstance(mutation_readiness.get("operational_readiness"), dict)
                    and isinstance(
                        mutation_readiness.get("operational_readiness", {}).get("blocking_summaries"),
                        list,
                    )
                    and isinstance(
                        mutation_readiness.get("reviewer_context_requirements", {}).get(
                            "effective_required_fields"
                        ),
                        list,
                    )
                        and isinstance(
                            mutation_readiness.get("reviewer_context_requirements", {}).get(
                                "required_reviewer_kinds_for_mutation"
                            ),
                            list,
                        )
                        and bool(
                            mutation_readiness.get("reviewer_context_requirements", {}).get(
                                "expectation_summary"
                            )
                        )
                        and bool(mutation_readiness.get("write_route_contract", {}).get("route_template"))
                        and isinstance(
                            mutation_readiness.get("write_route_contract", {}).get("action_routes"), list
                        )
                        and isinstance(mutation_readiness.get("identity_proof_contract"), dict)
                ),
                (
                    "ok"
                    if isinstance(mutation_readiness, dict)
                    and isinstance(mutation_readiness.get("blocker_summaries"), list)
                    and all(
                        isinstance(item, dict) and bool(item.get("summary"))
                        for item in mutation_readiness.get("blocker_summaries", [])
                    )
                    and isinstance(mutation_readiness.get("operational_readiness"), dict)
                    and isinstance(
                        mutation_readiness.get("operational_readiness", {}).get("blocking_summaries"),
                        list,
                    )
                    and isinstance(
                        mutation_readiness.get("reviewer_context_requirements", {}).get(
                            "effective_required_fields"
                        ),
                        list,
                    )
                    and isinstance(
                        mutation_readiness.get("reviewer_context_requirements", {}).get(
                            "required_reviewer_kinds_for_mutation"
                        ),
                        list,
                    )
                    and bool(
                        mutation_readiness.get("reviewer_context_requirements", {}).get(
                            "expectation_summary"
                        )
                    )
                    and bool(mutation_readiness.get("write_route_contract", {}).get("route_template"))
                    and isinstance(
                        mutation_readiness.get("write_route_contract", {}).get("action_routes"), list
                    )
                    and isinstance(mutation_readiness.get("identity_proof_contract"), dict)
                    else "overview missing mutation readiness contract detail"
                ),
            )
        )
        checks.append(
            UISmokeCheck(
                "html-shell",
                shell_ok,
                "ok" if shell_ok else "missing expected interactive markers",
            )
        )
    except Exception as exc:  # pragma: no cover - converted to visible smoke failure
        checks.append(UISmokeCheck("ui-smoke", False, str(exc)))

    return UISmokeReport(
        root=str(root_path.resolve()),
        passed=all(check.passed for check in checks),
        checks=checks,
    )
