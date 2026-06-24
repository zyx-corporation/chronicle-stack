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


def _count_statuses(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        status = str(row.get(key, "") or "")
        if not status:
            continue
        counts[status] = counts.get(status, 0) + 1
    return counts


def _has_reviewer_boundary_drilldown_contract(
    summary: dict[str, Any] | None, *, allow_detail_path_template: bool = False
) -> bool:
    if not isinstance(summary, dict):
        return False
    fact_line_params = summary.get("fact_line_params")
    detail_path_present = bool(summary.get("detail_path")) or (
        allow_detail_path_template and bool(summary.get("detail_path_template"))
    )
    return (
        bool(summary.get("summary_variant"))
        and bool(summary.get("dataset_key"))
        and bool(summary.get("list_path"))
        and detail_path_present
        and bool(summary.get("message"))
        and bool(summary.get("message_template_key"))
        and isinstance(summary.get("message_params"), dict)
        and bool(summary.get("message_params", {}).get("dataset_key"))
        and bool(summary.get("message_key"))
        and bool(summary.get("fact_line"))
        and bool(summary.get("fact_line_template_key"))
        and isinstance(fact_line_params, dict)
        and bool(fact_line_params.get("dataset_key"))
        and bool(fact_line_params.get("enforcement_status"))
        and bool(fact_line_params.get("validation_gate_status"))
    )


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
                        and isinstance(write_route_contract.get("status_code_contract"), list)
                        and all(
                            isinstance(item, dict)
                            and isinstance(item.get("status_code"), int)
                            and bool(item.get("family"))
                            and bool(item.get("when"))
                            for item in write_route_contract.get("status_code_contract", [])
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
                            and isinstance(write_route_contract.get("status_code_contract"), list)
                            and all(
                                isinstance(item, dict)
                                and isinstance(item.get("status_code"), int)
                                and bool(item.get("family"))
                                and bool(item.get("when"))
                                for item in write_route_contract.get("status_code_contract", [])
                            )
                            and isinstance(write_route_contract.get("expected_request_fields"), list)
                            else "ui boundary missing write route contract detail"
                        ),
                    )
                )

            if endpoint == "/api/overview":
                reviewer_boundary_overview = payload.get("reviewer_boundary_overview", {})
                checks.append(
                    UISmokeCheck(
                        "/api/overview#reviewer-boundary-overview",
                        isinstance(reviewer_boundary_overview, dict)
                        and bool(reviewer_boundary_overview.get("enforcement_status"))
                        and bool(reviewer_boundary_overview.get("validation_gate_status"))
                        and isinstance(
                            reviewer_boundary_overview.get("runtime_record_enforcement_counts"), dict
                        )
                        and isinstance(
                            reviewer_boundary_overview.get("review_queue_validation_gate_counts"), dict
                        )
                        and isinstance(
                            reviewer_boundary_overview.get("summary_job_enforcement_counts"), dict
                        ),
                        (
                            "ok"
                            if isinstance(reviewer_boundary_overview, dict)
                            and bool(reviewer_boundary_overview.get("enforcement_status"))
                            and bool(reviewer_boundary_overview.get("validation_gate_status"))
                            and isinstance(
                                reviewer_boundary_overview.get(
                                    "runtime_record_enforcement_counts"
                                ),
                                dict,
                            )
                            and isinstance(
                                reviewer_boundary_overview.get(
                                    "review_queue_validation_gate_counts"
                                ),
                                dict,
                            )
                            and isinstance(
                                reviewer_boundary_overview.get("summary_job_enforcement_counts"),
                                dict,
                            )
                            else "overview missing reviewer-boundary overview summary"
                        ),
                    )
                )
                checks.append(
                    UISmokeCheck(
                        "/api/overview#reviewer-boundary-drilldown",
                        isinstance(reviewer_boundary_overview.get("drilldown_summaries"), list)
                        and len(reviewer_boundary_overview.get("drilldown_summaries", [])) == 3
                        and all(
                            _has_reviewer_boundary_drilldown_contract(
                                item, allow_detail_path_template=True
                            )
                            for item in reviewer_boundary_overview.get("drilldown_summaries", [])
                        ),
                        (
                            "ok"
                            if isinstance(reviewer_boundary_overview.get("drilldown_summaries"), list)
                            and len(reviewer_boundary_overview.get("drilldown_summaries", [])) == 3
                            else "overview missing reviewer-boundary drilldown summaries"
                        ),
                    )
                )

        overview_payload = collection_payloads.get("/api/overview")
        reviewer_boundary_overview = (
            overview_payload.get("reviewer_boundary_overview", {})
            if isinstance(overview_payload, dict)
            else {}
        )
        runtime_rows = _first_array(collection_payloads.get("/api/runtime-records", {})) or []
        review_rows = _first_array(collection_payloads.get("/api/review-queue", {})) or []
        summary_rows = _first_array(collection_payloads.get("/api/summary-jobs", {})) or []
        checks.append(
            UISmokeCheck(
                "/api/overview#reviewer-boundary-count-consistency",
                isinstance(reviewer_boundary_overview, dict)
                and reviewer_boundary_overview.get("runtime_record_enforcement_counts", {})
                == _count_statuses(runtime_rows, "reviewer_enforcement_status")
                and reviewer_boundary_overview.get("runtime_record_validation_gate_counts", {})
                == _count_statuses(runtime_rows, "reviewer_validation_gate_status")
                and reviewer_boundary_overview.get("review_queue_enforcement_counts", {})
                == _count_statuses(review_rows, "reviewer_enforcement_status")
                and reviewer_boundary_overview.get("review_queue_validation_gate_counts", {})
                == _count_statuses(review_rows, "reviewer_validation_gate_status")
                and reviewer_boundary_overview.get("summary_job_enforcement_counts", {})
                == _count_statuses(summary_rows, "reviewer_enforcement_status")
                and reviewer_boundary_overview.get("summary_job_validation_gate_counts", {})
                == _count_statuses(summary_rows, "reviewer_validation_gate_status"),
                (
                    "ok"
                    if isinstance(reviewer_boundary_overview, dict)
                    and reviewer_boundary_overview.get("runtime_record_enforcement_counts", {})
                    == _count_statuses(runtime_rows, "reviewer_enforcement_status")
                    and reviewer_boundary_overview.get("runtime_record_validation_gate_counts", {})
                    == _count_statuses(runtime_rows, "reviewer_validation_gate_status")
                    and reviewer_boundary_overview.get("review_queue_enforcement_counts", {})
                    == _count_statuses(review_rows, "reviewer_enforcement_status")
                    and reviewer_boundary_overview.get("review_queue_validation_gate_counts", {})
                    == _count_statuses(review_rows, "reviewer_validation_gate_status")
                    and reviewer_boundary_overview.get("summary_job_enforcement_counts", {})
                    == _count_statuses(summary_rows, "reviewer_enforcement_status")
                    and reviewer_boundary_overview.get("summary_job_validation_gate_counts", {})
                    == _count_statuses(summary_rows, "reviewer_validation_gate_status")
                    else "reviewer-boundary overview counts drift from list-row statuses"
                ),
            )
        )
        package_review_payload = collection_payloads.get("/api/package-review", {})
        package_review = (
            package_review_payload.get("package_review", {})
            if isinstance(package_review_payload, dict)
            else {}
        )
        checks.append(
            UISmokeCheck(
                "/api/package-review#structured-contract",
                isinstance(package_review, dict)
                and bool(package_review.get("status"))
                and bool(package_review.get("message_key"))
                and bool(package_review.get("counts_summary_key"))
                and bool(package_review.get("boundary_note_key")),
                (
                    "ok"
                    if isinstance(package_review, dict)
                    and bool(package_review.get("status"))
                    and bool(package_review.get("message_key"))
                    and bool(package_review.get("counts_summary_key"))
                    and bool(package_review.get("boundary_note_key"))
                    else "package review missing structured contract fields"
                ),
            )
        )
        graph_summary_payload = collection_payloads.get("/api/graph-summary", {})
        graph_summary = (
            graph_summary_payload.get("graph_summary", {})
            if isinstance(graph_summary_payload, dict)
            else {}
        )
        checks.append(
            UISmokeCheck(
                "/api/graph-summary#structured-contract",
                isinstance(graph_summary, dict)
                and bool(graph_summary.get("status"))
                and bool(graph_summary.get("message_key"))
                and bool(graph_summary.get("counts_summary_key"))
                and bool(graph_summary.get("boundary_note_key")),
                (
                    "ok"
                    if isinstance(graph_summary, dict)
                    and bool(graph_summary.get("status"))
                    and bool(graph_summary.get("message_key"))
                    and bool(graph_summary.get("counts_summary_key"))
                    and bool(graph_summary.get("boundary_note_key"))
                    else "graph summary missing structured contract fields"
                ),
            )
        )
        ai_index_status_payload = collection_payloads.get("/api/ai-index-status", {})
        ai_index_status = (
            ai_index_status_payload.get("ai_index_status", {})
            if isinstance(ai_index_status_payload, dict)
            else {}
        )
        checks.append(
            UISmokeCheck(
                "/api/ai-index-status#structured-contract",
                isinstance(ai_index_status, dict)
                and bool(ai_index_status.get("status"))
                and bool(ai_index_status.get("message_key"))
                and bool(ai_index_status.get("boundary_note_key"))
                and bool(ai_index_status.get("vector", {}).get("counts_summary_key"))
                and bool(ai_index_status.get("graph", {}).get("counts_summary_key")),
                (
                    "ok"
                    if isinstance(ai_index_status, dict)
                    and bool(ai_index_status.get("status"))
                    and bool(ai_index_status.get("message_key"))
                    and bool(ai_index_status.get("boundary_note_key"))
                    and bool(ai_index_status.get("vector", {}).get("counts_summary_key"))
                    and bool(ai_index_status.get("graph", {}).get("counts_summary_key"))
                    else "ai index status missing structured contract fields"
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
            row_for_detail = rows[0]
            if endpoint == "/api/runtime-records":
                row_for_detail = next(
                    (
                        row
                        for row in rows
                        if str(row.get("runtime_record_preview", {}).get("record_kind", "")) == "retrieval_plan"
                    ),
                    rows[0],
                )
            elif endpoint == "/api/review-queue":
                row_for_detail = next(
                    (
                        row
                        for row in rows
                        if str(row.get("package_readiness_summary", {}).get("status", ""))
                        == "package_context_available"
                    ),
                    rows[0],
                )
            record_id = row_for_detail.get(id_field)
            if not isinstance(record_id, str) or not record_id:
                checks.append(UISmokeCheck(f"{endpoint}/<id>", False, f"missing id field: {id_field}"))
                continue
            if endpoint in {"/api/runtime-records", "/api/review-queue", "/api/summary-jobs"}:
                first_row = rows[0]
                checks.append(
                    UISmokeCheck(
                        f"{endpoint}#reviewer-boundary-statuses",
                        bool(first_row.get("reviewer_enforcement_status"))
                        and bool(first_row.get("reviewer_validation_gate_status")),
                        (
                            "ok"
                            if bool(first_row.get("reviewer_enforcement_status"))
                            and bool(first_row.get("reviewer_validation_gate_status"))
                            else "list row missing reviewer-boundary statuses"
                        ),
                    )
                )
                checks.append(
                    UISmokeCheck(
                        f"{endpoint}#reviewer-boundary-drilldown",
                        _has_reviewer_boundary_drilldown_contract(
                            first_row.get("reviewer_boundary_drilldown_summary")
                        ),
                        (
                            "ok"
                            if _has_reviewer_boundary_drilldown_contract(
                                first_row.get("reviewer_boundary_drilldown_summary")
                            )
                            else "list row missing reviewer-boundary drilldown summary"
                        ),
                    )
                )
            if endpoint == "/api/review-queue":
                readiness_summary = row_for_detail.get("package_readiness_summary", {})
                checks.append(
                    UISmokeCheck(
                        f"{endpoint}#package-readiness-summary-contract",
                        isinstance(readiness_summary, dict)
                        and bool(readiness_summary.get("status"))
                        and bool(readiness_summary.get("label_key"))
                        and bool(readiness_summary.get("message_key"))
                        and bool(readiness_summary.get("message_template_key")),
                        (
                            "ok"
                            if isinstance(readiness_summary, dict)
                            and bool(readiness_summary.get("status"))
                            and bool(readiness_summary.get("label_key"))
                            and bool(readiness_summary.get("message_key"))
                            and bool(readiness_summary.get("message_template_key"))
                            else "review queue row missing package readiness summary structured contract"
                        ),
                    )
                )
            detail = service.detail_payload(f"{endpoint}/{record_id}")
            checks.append(
                UISmokeCheck(
                    f"{endpoint}/{record_id}",
                    detail is not None and "record" in detail,
                    "ok" if detail is not None and "record" in detail else "missing detail record",
                )
            )
            if endpoint == "/api/ai-index-vector" and detail is not None and "record" in detail:
                record = detail["record"]
                checks.append(
                    UISmokeCheck(
                        f"{endpoint}/{record_id}#structured-contract",
                        bool(record.get("message_key"))
                        and bool(record.get("counts_summary_key"))
                        and bool(record.get("boundary_note_key")),
                        (
                            "ok"
                            if bool(record.get("message_key"))
                            and bool(record.get("counts_summary_key"))
                            and bool(record.get("boundary_note_key"))
                            else "ai index vector detail missing structured contract fields"
                        ),
                    )
                )
            if endpoint == "/api/ai-index-graph-nodes" and detail is not None and "record" in detail:
                record = detail["record"]
                checks.append(
                    UISmokeCheck(
                        f"{endpoint}/{record_id}#structured-contract",
                        bool(record.get("message_key"))
                        and bool(record.get("counts_summary_key"))
                        and bool(record.get("boundary_note_key")),
                        (
                            "ok"
                            if bool(record.get("message_key"))
                            and bool(record.get("counts_summary_key"))
                            and bool(record.get("boundary_note_key"))
                            else "ai index graph-node detail missing structured contract fields"
                        ),
                    )
                )
            if endpoint == "/api/runtime-records" and detail is not None and "record" in detail:
                record = detail["record"]
                retrieval_handoff = record.get("retrieval_handoff")
                if isinstance(retrieval_handoff, dict):
                    checks.append(
                        UISmokeCheck(
                            f"{endpoint}/{record_id}#retrieval-handoff-contract",
                            bool(retrieval_handoff.get("message_key"))
                            and bool(retrieval_handoff.get("hit_counts_summary_key")),
                            (
                                "ok"
                                if bool(retrieval_handoff.get("message_key"))
                                and bool(retrieval_handoff.get("hit_counts_summary_key"))
                                else "runtime detail missing structured retrieval handoff contract"
                            ),
                        )
                    )
                embedded_package_review = record.get("package_handoff_preview", {}).get("package_review", {})
                if isinstance(embedded_package_review, dict) and embedded_package_review:
                    checks.append(
                        UISmokeCheck(
                            f"{endpoint}/<id>#embedded-package-review-structured-contract",
                            bool(embedded_package_review.get("status"))
                            and bool(embedded_package_review.get("message_key"))
                            and bool(embedded_package_review.get("counts_summary_key"))
                            and bool(embedded_package_review.get("boundary_note_key")),
                            (
                                "ok"
                                if bool(embedded_package_review.get("status"))
                                and bool(embedded_package_review.get("message_key"))
                                and bool(embedded_package_review.get("counts_summary_key"))
                                and bool(embedded_package_review.get("boundary_note_key"))
                                else "runtime detail missing embedded package review structured contract"
                            ),
                        )
                    )
                handoff_preview = record.get("package_handoff_preview", {})
                if isinstance(handoff_preview, dict) and handoff_preview:
                    checks.append(
                        UISmokeCheck(
                            f"{endpoint}/<id>#package-handoff-structured-contract",
                            bool(handoff_preview.get("status"))
                            and bool(handoff_preview.get("message_key"))
                            and bool(handoff_preview.get("counts_summary_key"))
                            and bool(handoff_preview.get("boundary_note_key")),
                            (
                                "ok"
                                if bool(handoff_preview.get("status"))
                                and bool(handoff_preview.get("message_key"))
                                and bool(handoff_preview.get("counts_summary_key"))
                                and bool(handoff_preview.get("boundary_note_key"))
                                else "runtime detail missing package handoff structured contract"
                            ),
                        )
                    )
                invocation_plan = record.get("invocation_plan")
                if isinstance(invocation_plan, dict):
                    checks.append(
                        UISmokeCheck(
                            f"{endpoint}/{record_id}#invocation-plan-contract",
                            bool(invocation_plan.get("message_key"))
                            and bool(invocation_plan.get("provider_summary_key")),
                            (
                                "ok"
                                if bool(invocation_plan.get("message_key"))
                                and bool(invocation_plan.get("provider_summary_key"))
                                else "runtime detail missing structured invocation plan contract"
                            ),
                        )
                    )
            if endpoint == "/api/review-queue" and detail is not None and "record" in detail:
                record = detail["record"]
                checks.append(
                    UISmokeCheck(
                        f"{endpoint}/{record_id}#reviewer-boundary",
                        isinstance(record.get("reviewer_enforcement_summary"), dict)
                        and bool(record.get("reviewer_enforcement_summary", {}).get("status"))
                        and isinstance(record.get("reviewer_validation_gate_summary"), dict)
                        and bool(record.get("reviewer_validation_gate_summary", {}).get("status")),
                        (
                            "ok"
                            if isinstance(record.get("reviewer_enforcement_summary"), dict)
                            and bool(record.get("reviewer_enforcement_summary", {}).get("status"))
                            and isinstance(record.get("reviewer_validation_gate_summary"), dict)
                            and bool(record.get("reviewer_validation_gate_summary", {}).get("status"))
                            else "review detail missing reviewer-boundary summaries"
                        ),
                    )
                )
                embedded_package_review = record.get("package_readiness", {}).get("package_review", {})
                if isinstance(embedded_package_review, dict) and embedded_package_review:
                    checks.append(
                        UISmokeCheck(
                            f"{endpoint}/<id>#embedded-package-review-structured-contract",
                            bool(embedded_package_review.get("status"))
                            and bool(embedded_package_review.get("message_key"))
                            and bool(embedded_package_review.get("counts_summary_key"))
                            and bool(embedded_package_review.get("boundary_note_key")),
                            (
                                "ok"
                                if bool(embedded_package_review.get("status"))
                                and bool(embedded_package_review.get("message_key"))
                                and bool(embedded_package_review.get("counts_summary_key"))
                                and bool(embedded_package_review.get("boundary_note_key"))
                                else "review detail missing embedded package review structured contract"
                            ),
                        )
                    )
                checks.append(
                    UISmokeCheck(
                        f"{endpoint}/{record_id}#reviewer-boundary-drilldown",
                        _has_reviewer_boundary_drilldown_contract(
                            record.get("reviewer_boundary_drilldown_summary")
                        ),
                        (
                            "ok"
                            if _has_reviewer_boundary_drilldown_contract(
                                record.get("reviewer_boundary_drilldown_summary")
                            )
                            else "review detail missing reviewer-boundary drilldown summary"
                        ),
                    )
                )
                cli_parity = record.get("cli_parity")
                checks.append(
                    UISmokeCheck(
                        f"{endpoint}/{record_id}#cli-parity",
                        isinstance(cli_parity, dict)
                        and cli_parity.get("status") == "aligned"
                        and bool(cli_parity.get("message_key")),
                        (
                            "ok"
                            if isinstance(cli_parity, dict)
                            and cli_parity.get("status") == "aligned"
                            and bool(cli_parity.get("message_key"))
                            else "review detail missing aligned cli parity summary"
                        ),
                    )
                )
                runtime_preview = record.get("runtime_record_preview")
                if isinstance(runtime_preview, dict):
                    checks.append(
                        UISmokeCheck(
                            f"{endpoint}/{record_id}#runtime-preview-contract",
                            bool(runtime_preview.get("title"))
                            and bool(runtime_preview.get("title_key")),
                            (
                                "ok"
                                if bool(runtime_preview.get("title"))
                                and bool(runtime_preview.get("title_key"))
                                else "runtime detail missing structured preview title contract"
                            ),
                        )
                    )
                auth_notice = record.get("auth_boundary_notice")
                checks.append(
                    UISmokeCheck(
                        f"{endpoint}/{record_id}#auth-readiness",
                        isinstance(auth_notice, dict)
                        and bool(auth_notice.get("status"))
                        and bool(auth_notice.get("message_key"))
                        and bool(auth_notice.get("scope_note"))
                        and bool(auth_notice.get("scope_note_key"))
                        and isinstance(auth_notice.get("blocker_summaries"), list)
                        and all(
                            isinstance(item, dict)
                            and bool(item.get("summary"))
                            and bool(item.get("summary_key"))
                            for item in auth_notice.get("blocker_summaries", [])
                        ),
                        (
                            "ok"
                            if isinstance(auth_notice, dict)
                            and bool(auth_notice.get("status"))
                            and bool(auth_notice.get("message_key"))
                            and bool(auth_notice.get("scope_note"))
                            and bool(auth_notice.get("scope_note_key"))
                            and isinstance(auth_notice.get("blocker_summaries"), list)
                            and all(
                                isinstance(item, dict)
                                and bool(item.get("summary"))
                                and bool(item.get("summary_key"))
                                for item in auth_notice.get("blocker_summaries", [])
                            )
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
                                isinstance(item, dict)
                                and bool(item.get("summary"))
                                and bool(item.get("summary_key"))
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
                            and bool(
                                mutation_enablement.get("reviewer_context_requirements", {}).get(
                                    "expectation_summary_key"
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
                            and bool(
                                mutation_enablement.get("reviewer_context_requirements", {}).get(
                                    "expectation_summary_key"
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
                        and bool(action_preview.get("message_key"))
                        and isinstance(action_preview.get("failure_contract"), dict)
                        and action_preview.get("failure_contract", {}).get("rollback_status") == "fail_closed",
                        (
                            "ok"
                            if isinstance(first_action, dict)
                            and first_action.get("post_expected_status") == 403
                            and first_action.get("post_expected_error_code") == "mutation_disabled"
                            and bool(action_preview.get("message_key"))
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
                response_summary = record.get("response_metadata_summary")
                if isinstance(response_summary, dict):
                    checks.append(
                        UISmokeCheck(
                            f"{endpoint}/{record_id}#provider-response-contract",
                            bool(response_summary.get("message_key")),
                            (
                                "ok"
                                if bool(response_summary.get("message_key"))
                                else "review detail missing provider response message key"
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
                checks.append(
                    UISmokeCheck(
                        f"{endpoint}/{record_id}#reviewer-boundary",
                        isinstance(record.get("reviewer_enforcement_summary"), dict)
                        and bool(record.get("reviewer_enforcement_summary", {}).get("status"))
                        and isinstance(record.get("reviewer_validation_gate_summary"), dict)
                        and bool(record.get("reviewer_validation_gate_summary", {}).get("status")),
                        (
                            "ok"
                            if isinstance(record.get("reviewer_enforcement_summary"), dict)
                            and bool(record.get("reviewer_enforcement_summary", {}).get("status"))
                            and isinstance(record.get("reviewer_validation_gate_summary"), dict)
                            and bool(record.get("reviewer_validation_gate_summary", {}).get("status"))
                            else "runtime detail missing reviewer-boundary summaries"
                        ),
                    )
                )
                checks.append(
                    UISmokeCheck(
                        f"{endpoint}/{record_id}#reviewer-boundary-drilldown",
                        _has_reviewer_boundary_drilldown_contract(
                            record.get("reviewer_boundary_drilldown_summary")
                        ),
                        (
                            "ok"
                            if _has_reviewer_boundary_drilldown_contract(
                                record.get("reviewer_boundary_drilldown_summary")
                            )
                            else "runtime detail missing reviewer-boundary drilldown summary"
                        ),
                    )
                )
                auth_notice = record.get("auth_boundary_notice")
                checks.append(
                    UISmokeCheck(
                        f"{endpoint}/{record_id}#auth-readiness",
                        isinstance(auth_notice, dict)
                        and bool(auth_notice.get("status"))
                        and bool(auth_notice.get("message_key"))
                        and bool(auth_notice.get("scope_note"))
                        and bool(auth_notice.get("scope_note_key"))
                        and isinstance(auth_notice.get("blocker_summaries"), list),
                        (
                            "ok"
                            if isinstance(auth_notice, dict)
                            and bool(auth_notice.get("status"))
                            and bool(auth_notice.get("message_key"))
                            and bool(auth_notice.get("scope_note"))
                            and bool(auth_notice.get("scope_note_key"))
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
                checks.append(
                    UISmokeCheck(
                        f"{endpoint}/{record_id}#reviewer-boundary",
                        isinstance(record.get("reviewer_enforcement_summary"), dict)
                        and bool(record.get("reviewer_enforcement_summary", {}).get("status"))
                        and isinstance(record.get("reviewer_validation_gate_summary"), dict)
                        and bool(record.get("reviewer_validation_gate_summary", {}).get("status")),
                        (
                            "ok"
                            if isinstance(record.get("reviewer_enforcement_summary"), dict)
                            and bool(record.get("reviewer_enforcement_summary", {}).get("status"))
                            and isinstance(record.get("reviewer_validation_gate_summary"), dict)
                            and bool(record.get("reviewer_validation_gate_summary", {}).get("status"))
                            else "summary detail missing reviewer-boundary summaries"
                        ),
                    )
                )
                checks.append(
                    UISmokeCheck(
                        f"{endpoint}/{record_id}#reviewer-boundary-drilldown",
                        _has_reviewer_boundary_drilldown_contract(
                            record.get("reviewer_boundary_drilldown_summary")
                        ),
                        (
                            "ok"
                            if _has_reviewer_boundary_drilldown_contract(
                                record.get("reviewer_boundary_drilldown_summary")
                            )
                            else "summary detail missing reviewer-boundary drilldown summary"
                        ),
                    )
                )
                auth_notice = record.get("auth_boundary_notice")
                checks.append(
                    UISmokeCheck(
                        f"{endpoint}/{record_id}#auth-readiness",
                        isinstance(auth_notice, dict)
                        and bool(auth_notice.get("status"))
                        and bool(auth_notice.get("message_key"))
                        and bool(auth_notice.get("scope_note"))
                        and bool(auth_notice.get("scope_note_key"))
                        and isinstance(auth_notice.get("blocker_summaries"), list),
                        (
                            "ok"
                            if isinstance(auth_notice, dict)
                            and bool(auth_notice.get("status"))
                            and bool(auth_notice.get("message_key"))
                            and bool(auth_notice.get("scope_note"))
                            and bool(auth_notice.get("scope_note_key"))
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
                        and bool(preview.get("message_key"))
                        and isinstance(preview.get("failure_contract"), dict)
                        and preview.get("failure_contract", {}).get("rollback_status") == "fail_closed",
                        (
                            "ok"
                            if isinstance(first_action, dict)
                            and first_action.get("post_expected_status") == 403
                            and first_action.get("post_expected_error_code") == "mutation_disabled"
                            and bool(preview.get("message_key"))
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
                "Reviewer Boundary",
                "Related Links",
                "Review Queue",
                "Runtime Records",
                "reviewerBoundaryFilterValue",
                "reviewerBoundaryCountButtons",
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
                        isinstance(item, dict)
                        and bool(item.get("summary"))
                        and bool(item.get("summary_key"))
                        for item in mutation_readiness.get("blocker_summaries", [])
                    )
                    and isinstance(mutation_readiness.get("operational_readiness"), dict)
                    and isinstance(
                        mutation_readiness.get("operational_readiness", {}).get("blocking_summaries"),
                        list,
                    )
                    and isinstance(
                        mutation_readiness.get("operational_readiness", {}).get("unsatisfied_checks"),
                        list,
                    )
                    and all(
                        isinstance(item, dict)
                        and bool(item.get("summary_key"))
                        and bool(item.get("label_key"))
                        for item in mutation_readiness.get("operational_readiness", {}).get(
                            "unsatisfied_checks", []
                        )
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
                        and bool(
                            mutation_readiness.get("reviewer_context_requirements", {}).get(
                                "expectation_summary_key"
                            )
                        )
                        and bool(mutation_readiness.get("write_route_contract", {}).get("route_template"))
                        and isinstance(
                            mutation_readiness.get("write_route_contract", {}).get("action_routes"), list
                        )
                        and isinstance(
                            mutation_readiness.get("write_route_contract", {}).get("status_code_contract"),
                            list,
                        )
                        and isinstance(mutation_readiness.get("identity_proof_contract"), dict)
                ),
                (
                    "ok"
                    if isinstance(mutation_readiness, dict)
                    and isinstance(mutation_readiness.get("blocker_summaries"), list)
                    and all(
                        isinstance(item, dict)
                        and bool(item.get("summary"))
                        and bool(item.get("summary_key"))
                        for item in mutation_readiness.get("blocker_summaries", [])
                    )
                    and isinstance(mutation_readiness.get("operational_readiness"), dict)
                    and isinstance(
                        mutation_readiness.get("operational_readiness", {}).get("blocking_summaries"),
                        list,
                    )
                    and isinstance(
                        mutation_readiness.get("operational_readiness", {}).get("unsatisfied_checks"),
                        list,
                    )
                    and all(
                        isinstance(item, dict)
                        and bool(item.get("summary_key"))
                        and bool(item.get("label_key"))
                        for item in mutation_readiness.get("operational_readiness", {}).get(
                            "unsatisfied_checks", []
                        )
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
                    and bool(
                        mutation_readiness.get("reviewer_context_requirements", {}).get(
                            "expectation_summary_key"
                        )
                    )
                    and bool(mutation_readiness.get("write_route_contract", {}).get("route_template"))
                    and isinstance(
                        mutation_readiness.get("write_route_contract", {}).get("action_routes"), list
                    )
                    and isinstance(
                        mutation_readiness.get("write_route_contract", {}).get("status_code_contract"),
                        list,
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
