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
from chronicle.services.review_service import (
    ReviewAuditInsertionError,
    ReviewDecisionPersistenceError,
    ReviewService,
    review_action_commands,
)
from chronicle.services.runtime_config_service import RuntimeConfigService
from chronicle.services.runtime_service import RuntimeService
from chronicle.services.summary_job_service import SummaryJobService
from chronicle.services.vector_index_service import VectorIndexService

DEFAULT_UI_HOST = "127.0.0.1"
DEFAULT_UI_PORT = 8765
SESSION_LABEL_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{1,63}$")
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
OVERVIEW_SLICE_LABELS: dict[str, str] = {
    "reviewer_identity_declared_only": "Declared identity only",
    "reviewer_session_label_missing": "Session label required",
}


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
    mutation_blockers: tuple[str, ...] = (
        "write_routes_disabled",
        "auth_not_enabled",
        "authorization_not_enabled",
        "audit_insertion_cli_only",
    )
    mutation_blocker_details: list[dict[str, str]] | None = None
    reviewer_context_requirements: dict[str, Any] | None = None
    auth_boundary_summary: dict[str, Any] | None = None


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

    return {
        "status": status,
        "message": message,
        "blockers": blockers,
        "blocker_details": _serialize_auth_boundary_blocker_details(blockers),
        "next_steps": next_steps,
        "shared_machine_safe": metadata.shared_machine_safe,
        "session_gating": metadata.session_gating,
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
            "message": AUTH_BOUNDARY_BLOCKER_TEXT.get(blocker, blocker.replace("_", " ")),
        }
        for blocker in blockers
    ]


def _serialize_review_warning_details(warnings: list[str]) -> list[dict[str, str]]:
    return [
        {
            "code": warning,
            "message": REVIEW_WARNING_TEXT.get(warning, warning.replace("_", " ")),
        }
        for warning in warnings
    ]


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
            "message": MUTATION_BLOCKER_TEXT.get(blocker, blocker.replace("_", " ")),
        }
        for blocker in blockers
    ]


def _reviewer_context_requirements(metadata: UIBoundaryMetadata) -> dict[str, Any]:
    return {
        "required_fields": ["reviewer_label", "reviewer_kind", "ui_intent"],
        "session_label_required": bool(metadata.session_gating),
        "session_label_pattern": SESSION_LABEL_PATTERN.pattern,
        "session_label_examples": ["desk-session-1", "review.local-01"],
        "accepted_reviewer_kinds": [ReviewerIdentityKind.LOCAL_OPERATOR.value],
        "advisory_only_reviewer_kinds": [ReviewerIdentityKind.USER_DECLARED.value],
        "authority_note": "Request reviewer metadata is required local context, but it is not sufficient proof of authority on its own.",
        "session_note": (
            "Session label is required because the current local mutation boundary is session-gated."
            if metadata.session_gating
            else "Session label is optional while session-gated review is disabled."
        ),
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
        auth_mode=auth_mode,
        authorization_mode=authorization_mode,
        session_gating=auth_mode == UIAuthMode.LOOPBACK_LOCAL,
        shared_machine_safe=mutation_enabled,
        mutation_blockers=tuple(blockers),
        mutation_readiness_status="enabled" if mutation_enabled else "preview_only",
        mutation_readiness_message=(
            "GUI mutation is explicitly enabled for loopback-local reviewer-declared actions."
            if mutation_enabled
            else (
                "GUI mutation remains disabled; capability flag is noted as preview intent only."
                if mutation_capability_flag
                else "GUI mutation remains disabled; read-only preview only."
            )
        ),
    )
    return UIBoundaryMetadata(
        **{
            **asdict(metadata),
            "mutation_blocker_details": _serialize_mutation_blocker_details(list(metadata.mutation_blockers)),
            "reviewer_context_requirements": _reviewer_context_requirements(metadata),
            "auth_boundary_summary": _auth_boundary_summary(metadata),
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


def _related_link(path: str, label: str) -> dict[str, str]:
    return {"path": path, "label": label}


def _open_detail_label(resource: str, record_id: str) -> str:
    labels = {
        "contexts": "Open context",
        "events": "Open event",
    }
    prefix = labels.get(resource, f"Open {resource.rstrip('s')}")
    return f"{prefix} {record_id}".strip()


def _open_matching_detail_label(resource: str) -> str:
    labels = {
        "review-queue": "Open matching review detail",
        "runtime-records": "Open matching runtime record",
    }
    return labels.get(resource, f"Open matching {resource.rstrip('s')} detail")


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
    ) -> None:
        self.root = root or Path.cwd()
        self.host = host
        self.mutation_capability_flag = mutation_capability_flag
        self.enable_ui_mutation = enable_ui_mutation
        self.auth_mode = auth_mode
        self.authorization_mode = authorization_mode
        self.chronicle = ChronicleService(self.root)
        self.audit = AuditService(self.root)
        self.lifecycle = LifecycleService(self.root)
        self.packages = IntegrationPackageService(self.root)
        self.package_review = PackageReviewService(self.root)
        self.review = ReviewService(self.root)
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
            "runtime_records_summary": runtime_records_summary,
            "summary_jobs_summary": summary_jobs_summary,
            "mutation_readiness": self.mutation_readiness_summary(review_queue),
        }

    def runtime_records_overview(self, runtime_records: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        rows = runtime_records if runtime_records is not None else self.runtime_records()["runtime_records"]
        kind_counts: dict[str, int] = {}
        auth_counts: dict[str, int] = {}
        finish_reason_counts: dict[str, int] = {}
        provider_status_counts: dict[str, int] = {}
        response_present_count = 0
        for row in rows:
            kind = str(row.get("runtime_record_kind", "unknown"))
            auth_status = str(row.get("auth_readiness_status", "unknown"))
            response_summary = row.get("response_metadata_summary", {})
            kind_counts[kind] = kind_counts.get(kind, 0) + 1
            auth_counts[auth_status] = auth_counts.get(auth_status, 0) + 1
            if isinstance(response_summary, dict) and response_summary.get("present") is True:
                response_present_count += 1
                finish_reason = str(response_summary.get("finish_reason") or "unknown")
                provider_status = str(response_summary.get("provider_status") or "unknown")
                finish_reason_counts[finish_reason] = finish_reason_counts.get(finish_reason, 0) + 1
                provider_status_counts[provider_status] = provider_status_counts.get(provider_status, 0) + 1
        return {
            "kind_counts": kind_counts,
            "auth_readiness_counts": auth_counts,
            "provider_response_present_count": response_present_count,
            "provider_response_absent_count": len(rows) - response_present_count,
            "provider_response_finish_reason_counts": finish_reason_counts,
            "provider_response_status_counts": provider_status_counts,
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
        }

    def summary_jobs_overview(self, summary_jobs: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        rows = summary_jobs if summary_jobs is not None else self.summary_jobs_list()["summary_jobs"]
        status_counts: dict[str, int] = {}
        review_counts: dict[str, int] = {}
        auth_counts: dict[str, int] = {}
        package_counts: dict[str, int] = {}
        provider_counts: dict[str, int] = {}
        assurance_counts: dict[str, int] = {}
        reviewer_kind_counts: dict[str, int] = {}
        finish_reason_counts: dict[str, int] = {}
        provider_status_counts: dict[str, int] = {}
        response_present_count = 0
        source_count_total = 0
        for row in rows:
            status = str(row.get("status", "unknown"))
            review_status = str(row.get("review_capability_status", "unknown"))
            auth_status = str(row.get("auth_readiness_status", "unknown"))
            package_status = str(row.get("package_readiness_status", "unknown"))
            provider_kind = str(row.get("runtime_provider_kind", "unknown"))
            assurance_status = str(row.get("identity_assurance_status", "unknown"))
            reviewer_kind = str((row.get("latest_reviewer_identity") or {}).get("kind", "unknown"))
            status_counts[status] = status_counts.get(status, 0) + 1
            review_counts[review_status] = review_counts.get(review_status, 0) + 1
            auth_counts[auth_status] = auth_counts.get(auth_status, 0) + 1
            package_counts[package_status] = package_counts.get(package_status, 0) + 1
            provider_counts[provider_kind] = provider_counts.get(provider_kind, 0) + 1
            assurance_counts[assurance_status] = assurance_counts.get(assurance_status, 0) + 1
            reviewer_kind_counts[reviewer_kind] = reviewer_kind_counts.get(reviewer_kind, 0) + 1
            response_summary = row.get("response_metadata_summary", {})
            if isinstance(response_summary, dict) and response_summary.get("present") is True:
                response_present_count += 1
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
            "runtime_provider_counts": provider_counts,
            "provider_response_present_count": response_present_count,
            "provider_response_absent_count": len(rows) - response_present_count,
            "provider_response_finish_reason_counts": finish_reason_counts,
            "provider_response_status_counts": provider_status_counts,
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
            message = "Recorded reviewer identity metadata is aligned with the current preview auth boundary."
        elif assurance_counts:
            status = "partially_aligned"
            message = "Some reviewer identity metadata is present, but boundary alignment remains incomplete."
        else:
            status = "identity_unavailable"
            message = "Reviewer identity assurance is not yet available in the current derived queue view."

        return {
            "status": status,
            "message": message,
            "assurance_counts": assurance_counts,
            "missing_identity_count": missing_identity_count,
            "declared_identity_count": declared_identity_count,
            "session_label_missing_count": session_label_missing_count,
            "blockers": blockers,
            "next_steps": next_steps,
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
                    "label": code.replace("_", " "),
                    "message": self._warning_message(code),
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
        return {"contexts": [_dump_model(context) for context in contexts]}

    def artifacts(self) -> dict[str, Any]:
        self.chronicle.require_initialized()
        artifacts, versions = self.chronicle.index.load_artifacts()
        rows = []
        for artifact in sorted(artifacts.values(), key=lambda item: item.created_at):
            data = _dump_model(artifact)
            data["version_count"] = len(versions.get(artifact.artifact_id, []))
            rows.append(data)
        return {"artifacts": rows}

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
            data["runtime_record_kind"] = preview.record_kind
            data["runtime_record_preview"] = preview.model_dump(mode="json")
            review_row = self._review_queue_row(event.event_id)
            if review_row is not None:
                data["auth_readiness_status"] = str(
                    review_row.get("auth_boundary_notice", {}).get("status", "")
                )
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
            )
            data["cli_parity_summary"] = self._review_cli_parity_summary(
                entry.target_event_id,
                data.get("available_actions", []),
                data["action_preview_summary"],
            )
            data["ui_mutation_enabled"] = bool(boundary.get("mutation_enabled", False))
            data["review_preview_only"] = not bool(boundary.get("mutation_enabled", False))
            rows.append(data)
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
        for blocker in boundary.get("mutation_blockers", []):
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
        if ready_rows > 0:
            next_steps.append(
                "Preserve review-ready signals as preview-only until browser-triggered write ADR and audit semantics are explicit."
            )
        return {
            "status": boundary.get("mutation_readiness_status", "preview_only"),
            "message": boundary.get("mutation_readiness_message", "GUI mutation remains disabled."),
            "ready_row_count": ready_rows,
            "advisory_row_count": advisory_rows,
            "blockers": blockers,
            "blocker_details": _serialize_mutation_blocker_details(blockers),
            "pending_boundary_warning_counts": pending_boundary_warning_counts,
            "reviewer_context_requirements": boundary.get("reviewer_context_requirements", {}),
            "next_steps": next_steps,
        }

    def ai_index_status(self) -> dict[str, Any]:
        vector_status = self.vector_index.status()
        graph_snapshot = self.graph_index.snapshot()
        return {
            "ai_index_status": {
                "vector": vector_status.model_dump(mode="json"),
                "graph": {
                    "path": str(self.graph_index.paths.graph_index_file),
                    "node_count": len(graph_snapshot.nodes),
                    "edge_count": len(graph_snapshot.edges),
                    "external_call_made": False,
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
        return {"runtime_config": state.model_dump(mode="json")}

    def package_review_snapshot(self) -> dict[str, Any]:
        try:
            report = self.package_review.review_context_package(purpose="chronicle ui overview")
            return report.model_dump(mode="json")
        except Exception as exc:  # pragma: no cover - defensive UI degradation
            return {"status": "unavailable", "error": str(exc)}

    def graph_summary(self) -> dict[str, Any]:
        try:
            graph = GraphExportService(self.root).export_graph()
            return {"nodes": len(graph.nodes), "edges": len(graph.edges)}
        except Exception as exc:  # pragma: no cover - defensive UI degradation
            return {"nodes": 0, "edges": 0, "error": str(exc)}

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
        if not context_ids:
            payload["message"] = "No context records were selected by the retrieval dry-run, so package preview is advisory only."
            return payload
        package = self.packages.build_context_package(
            purpose=payload["purpose"],
            context_ids=context_ids,
        )
        review = self.package_review.review_package(package)
        payload["package_manifest_preview"] = package.manifest.model_dump(mode="json")
        payload["package_review"] = review.model_dump(mode="json")
        payload["message"] = "Read-only package preview derived from retrieval-plan context hits."
        return payload

    def runtime_related_links(self, event_id: str, payload: dict[str, Any]) -> list[dict[str, str]]:
        links = [
            _related_link(
                f"/api/review-queue/{event_id}",
                _open_matching_detail_label("review-queue"),
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
                    )
                )
        if "runtime_execution" in payload:
            execution = RuntimeExecutionResult.model_validate(payload["runtime_execution"])
            if execution.draft_summary_job_id:
                links.append(
                    _related_link(
                        f"/api/summary-jobs/{execution.draft_summary_job_id}",
                        f"Open summary job {execution.draft_summary_job_id}",
                    )
                )
            if execution.artifact_id:
                links.append(
                    _related_link(
                        f"/api/artifacts/{execution.artifact_id}",
                        f"Open artifact {execution.artifact_id}",
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
                        )
                    )
                elif record_id.startswith("evt_"):
                    links.append(
                        _related_link(
                            f"/api/events/{record_id}",
                            _open_detail_label("events", record_id),
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
                "suggested_commands": [],
            }

        payload = getattr(event, "payload", {})
        if "runtime_retrieval_plan" in payload:
            plan = RuntimeRetrievalPlan.model_validate(payload["runtime_retrieval_plan"])
            handoff = self.runtime_package_handoff(plan)
            handoff["suggested_commands"] = [
                'chronicle package review --purpose "runtime retrieval handoff"',
                'chronicle package context --purpose "runtime retrieval handoff" --persist',
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
                "suggested_commands": ["chronicle show --json", "chronicle review queue --json"],
                "package_review_required": True,
            }

        package = self.packages.build_context_package(
            purpose=f"review target handoff: {target_event_id}",
            context_ids=context_ids,
        )
        review = self.package_review.review_package(package)
        return {
            "status": "package_context_available",
            "eligible_context_ids": context_ids,
            "skipped_record_ids": [],
            "message": "Read-only package readiness derived from context-linked review target records.",
            "suggested_commands": [
                'chronicle package review --purpose "review target handoff"',
                'chronicle package context --purpose "review target handoff" --persist',
            ],
            "package_review_required": True,
            "package_manifest_preview": package.manifest.model_dump(mode="json"),
            "package_review": review.model_dump(mode="json"),
        }

    def review_related_links(self, target_event_id: str) -> list[dict[str, str]]:
        links = [
            _related_link(
                f"/api/runtime-records/{target_event_id}",
                _open_matching_detail_label("runtime-records"),
            )
        ]
        readiness = self.review_package_readiness(target_event_id)
        for context_id in readiness.get("eligible_context_ids", []):
            if isinstance(context_id, str) and context_id.startswith("ctx_"):
                links.append(
                    _related_link(
                        f"/api/contexts/{context_id}",
                        _open_detail_label("contexts", context_id),
                    )
                )
        return links

    def summary_job_related_links(self, summary_job_id: str, job: dict[str, Any]) -> list[dict[str, str]]:
        links: list[dict[str, str]] = []
        event_id = str(job.get("event_id", ""))
        if event_id.startswith("evt_"):
            links.append(
                _related_link(
                    f"/api/review-queue/{event_id}",
                    f"Open review target {event_id}",
                )
            )
        for ref in job.get("source_refs", []):
            record_type = str(ref.get("record_type", "event"))
            record_id = str(ref.get("record_id", ""))
            if record_type == "event" and record_id.startswith("evt_"):
                links.append(_related_link(f"/api/events/{record_id}", f"Open event {record_id}"))
            elif record_id.startswith("ctx_"):
                links.append(_related_link(f"/api/contexts/{record_id}", f"Open context {record_id}"))
        artifact_id = str(job.get("artifact_id", ""))
        if artifact_id.startswith("art_"):
            links.append(_related_link(f"/api/artifacts/{artifact_id}", f"Open artifact {artifact_id}"))
        return links

    def runtime_boundary(self) -> dict[str, Any]:
        return {
            "read_only": True,
            "foreground_process": True,
            "daemon": False,
            "server_default_host": DEFAULT_UI_HOST,
            "external_model_api": False,
            "graphrag_runtime": False,
            "vector_db": False,
            "graph_db": False,
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
        return {
            "present": bool(metadata or keys),
            "response_id": metadata.get("response_id"),
            "finish_reason": metadata.get("finish_reason"),
            "provider_status": metadata.get("provider_status"),
            "usage_input_tokens": metadata.get("usage_input_tokens"),
            "usage_output_tokens": metadata.get("usage_output_tokens"),
            "usage_total_tokens": metadata.get("usage_total_tokens"),
            "metadata_count": len(metadata),
            "response_key_count": len(keys),
            "response_keys": keys,
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
            message = "Current review metadata is aligned with the preview auth boundary, while GUI mutation remains disabled."
        elif blockers:
            status = "advisory_only"
            message = "Current review metadata remains advisory only until auth, authorization, and reviewer identity boundaries are explicit."
        elif assurance_status != "unknown":
            status = assurance_status
            message = "Some reviewer identity metadata is present, but auth-boundary alignment remains incomplete."
        else:
            status = capability_status
            message = "Auth-boundary readiness is not yet available in the current derived detail view."

        return {
            "status": status,
            "message": message,
            "blockers": blockers,
            "blocker_details": _serialize_auth_boundary_blocker_details(blockers),
            "next_steps": next_steps,
            "capability_status": capability_status,
            "identity_assurance_status": assurance_status,
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
            message = "Reviewer identity is self-declared only; UI auth is not enforcing reviewer identity."
        elif boundary_auth_mode == "not_enabled":
            status = "local_session_unverified"
            message = "Reviewer identity carries local session metadata, but UI auth/authz is not enabled."
        else:
            status = "boundary_aligned"
            message = "Reviewer identity metadata is aligned with the current UI auth boundary."
        return {
            "status": status,
            "reviewer_auth_mode": identity.auth_mode.value,
            "boundary_auth_mode": boundary_auth_mode,
            "session_gating": session_gating,
            "message": message,
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
                "can_review_now": False,
                "warnings": [],
                "message": "Review target is already resolved in the current derived queue view.",
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
        message = (
            "Boundary and reviewer identity conditions are aligned for future mutation-capable review."
            if can_review_now
            else "Review remains CLI-led and read-only in UI; see warnings for unmet boundary conditions."
        )
        return {
            "status": "ready" if can_review_now else "advisory_only",
            "can_review_now": can_review_now,
            "warnings": warnings,
            "warning_details": _serialize_review_warning_details(warnings),
            "message": message,
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
            "message": message,
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
        possible_error_codes = [
            "mutation_disabled",
            "reviewer_label_required",
            "session_label_required",
            "invalid_session_label",
            "ui_intent_mismatch",
            "invalid_reviewer_kind",
            "authorization_failed",
            "review_target_not_found",
            "review_not_pending",
            "invalid_json",
        ]
        recovery_commands = ChronicleUIDataService._review_recovery_commands(
            event_id=event_id,
            action=action,
            error_code=error_code,
            audit_id=audit_id,
        )
        return {
            "transaction_rule": (
                "No durable GUI review result is reported as applied unless both review decision persistence and audit insertion succeed."
            ),
            "rollback_status": "fail_closed",
            "durable_mutation_reported_on_failure": False,
            "partial_failure_visible": True,
            "possible_error_codes": possible_error_codes,
            "recovery_path": (
                recovery_commands[0]
                if recovery_commands
                else cli_equivalent or "Use the equivalent chronicle review CLI command for recovery or inspection."
            ),
            "recovery_commands": recovery_commands,
        }

    @staticmethod
    def _review_action_failure_message(error_code: str) -> str:
        messages = {
            "mutation_disabled": "GUI mutation remains disabled for this session; use the CLI review path instead.",
            "reviewer_label_required": "Reviewer label is missing, so the UI cannot attribute the review action.",
            "session_label_required": "Session label is required for the current session-gated local mutation boundary.",
            "invalid_session_label": "Session label must start with a lowercase letter or digit and use only lowercase letters, digits, dot, underscore, or hyphen.",
            "ui_intent_mismatch": "Requested route and submitted UI intent differ, so the action was rejected before mutation.",
            "invalid_reviewer_kind": "Reviewer kind is not one of the supported local reviewer identity kinds.",
            "authorization_failed": "Reviewer identity or session boundary is not aligned, so the action stays blocked.",
            "review_target_not_found": "The target review event is no longer available from the current Chronicle state.",
            "review_not_pending": "The review target is no longer pending; inspect the resolved queue before retrying.",
            "invalid_json": "The request body could not be parsed as JSON, so no mutation path was attempted.",
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
        if error_code == "authorization_failed":
            warning_text = " | ".join(
                ChronicleUIDataService._warning_message(code)
                for code in (warning_codes or [])
                if code
            )
            if warning_text and identity_assurance_status:
                return f"authorization_failed; identity={identity_assurance_status}; warnings={warning_text}"
            if identity_assurance_status:
                return f"authorization_failed; identity={identity_assurance_status}"
            if warning_text:
                return f"authorization_failed; warnings={warning_text}"
        if error_code == "review_not_pending":
            return "review_not_pending; inspect resolved queue state before retry"
        if error_code == "audit_insertion_failed":
            return "audit_insertion_failed; inspect local audit surface before retry"
        if error_code == "decision_persistence_failed":
            return "decision_persistence_failed; inspect audit trail and primary record state"
        return error_code

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
        return {
            "transaction_status": "decision_and_audit_persisted",
            "rollback_status": "not_required",
            "durable_mutation_reported": True,
            "audit_insertion_required": True,
            "recovery_path": follow_up_commands[0] if follow_up_commands else cli_equivalent or "Use the equivalent chronicle review CLI command for follow-up inspection.",
            "follow_up_commands": follow_up_commands,
        }

    @staticmethod
    def _review_action_preview(
        target_event_id: str,
        capability: dict[str, Any],
        *,
        mutation_enabled: bool = False,
    ) -> dict[str, Any]:
        can_review_now = bool(capability.get("can_review_now", False))
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
            "failure_contract": ChronicleUIDataService._review_action_failure_contract(
                mutation_enabled=mutation_enabled,
                cli_equivalent=f"chronicle review approve --event {target_event_id}",
                event_id=target_event_id,
                action="approve",
                error_code="mutation_disabled",
            ),
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
        }

    def detail_payload(self, path: str) -> dict[str, Any] | None:
        parts = [unquote(part) for part in path.strip("/").split("/")]
        if len(parts) == 4 and parts[0] == "api" and parts[1] == "ai-index":
            resource, record_id = parts[2], parts[3]
            if resource == "vector":
                entry = self.vector_index.get_entry(record_id)
                return {"record": _dump_model(entry)} if entry is not None else None
            if resource == "graph-nodes":
                node = self.graph_index.get_node(record_id)
                if node is None:
                    return None
                payload = _dump_model(node)
                neighbors = self.graph_index.neighbors(node_id=record_id)
                payload["neighbors"] = neighbors.model_dump(mode="json")
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
            record["runtime_record_kind"] = preview.record_kind
            record["runtime_record_preview"] = preview.model_dump(mode="json")
            record["suggested_cli_family"] = preview.suggested_cli_family
            record["related_links"] = self.runtime_related_links(parts[2], payload)
            record["response_metadata_summary"] = self._runtime_response_metadata_summary(payload=payload)
            review_row = self._review_queue_row(parts[2])
            if review_row is not None:
                record["auth_boundary_notice"] = review_row.get("auth_boundary_notice")
                record["auth_readiness_status"] = str(
                    review_row.get("auth_boundary_notice", {}).get("status", "")
                )
            if "runtime_retrieval_plan" in payload:
                plan = RuntimeRetrievalPlan.model_validate(payload["runtime_retrieval_plan"])
                record["retrieval_handoff"] = self.runtime.retrieval_handoff(plan).model_dump(mode="json")
                record["package_handoff_preview"] = self.runtime_package_handoff(plan)
            if "runtime_invocation_plan" in payload:
                plan = RuntimeInvocationPlan.model_validate(payload["runtime_invocation_plan"])
                record["invocation_plan"] = plan.model_dump(mode="json")
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
        elif resource == "artifacts":
            artifacts, versions = self.chronicle.index.load_artifacts()
            record = _dump_model(artifacts[record_id]) if record_id in artifacts else None
            if record is not None:
                record["versions"] = [_dump_model(version) for version in versions.get(record_id, [])]
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
        return (
            HTTPStatus.FORBIDDEN,
            {
                "ok": False,
                "status": "blocked",
                "event_id": event_id,
                "action": action,
                "error_code": "mutation_disabled",
                "message": self._review_action_failure_message("mutation_disabled"),
                "mutation_enabled": False,
                "cli_equivalent": f"chronicle review {action} --event {event_id}",
                "failure_contract": self._review_action_failure_contract(
                    mutation_enabled=False,
                    cli_equivalent=f"chronicle review {action} --event {event_id}",
                    event_id=event_id,
                    action=action,
                    error_code="mutation_disabled",
                ),
            },
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
                {
                    "ok": False,
                    "status": "blocked",
                    "event_id": event_id,
                    "action": action,
                    "error_code": "reviewer_label_required",
                    "message": self._review_action_failure_message("reviewer_label_required"),
                    "mutation_enabled": True,
                    "failure_contract": self._review_action_failure_contract(
                        mutation_enabled=True,
                        cli_equivalent=f"chronicle review {action} --event {event_id}",
                        event_id=event_id,
                        action=action,
                        error_code="reviewer_label_required",
                    ),
                },
            )
        if boundary.get("session_gating", False) and not session_label_value:
            return (
                HTTPStatus.BAD_REQUEST,
                {
                    "ok": False,
                    "status": "blocked",
                    "event_id": event_id,
                    "action": action,
                    "error_code": "session_label_required",
                    "message": self._review_action_failure_message("session_label_required"),
                    "mutation_enabled": True,
                    "failure_contract": self._review_action_failure_contract(
                        mutation_enabled=True,
                        cli_equivalent=f"chronicle review {action} --event {event_id}",
                        event_id=event_id,
                        action=action,
                        error_code="session_label_required",
                    ),
                },
            )
        if session_label_value and not SESSION_LABEL_PATTERN.fullmatch(session_label_value):
            return (
                HTTPStatus.BAD_REQUEST,
                {
                    "ok": False,
                    "status": "blocked",
                    "event_id": event_id,
                    "action": action,
                    "error_code": "invalid_session_label",
                    "message": self._review_action_failure_message("invalid_session_label"),
                    "mutation_enabled": True,
                    "failure_contract": self._review_action_failure_contract(
                        mutation_enabled=True,
                        cli_equivalent=f"chronicle review {action} --event {event_id}",
                        event_id=event_id,
                        action=action,
                        error_code="invalid_session_label",
                    ),
                },
            )
        if ui_intent != action:
            return (
                HTTPStatus.BAD_REQUEST,
                {
                    "ok": False,
                    "status": "blocked",
                    "event_id": event_id,
                    "action": action,
                    "error_code": "ui_intent_mismatch",
                    "message": self._review_action_failure_message("ui_intent_mismatch"),
                    "mutation_enabled": True,
                    "failure_contract": self._review_action_failure_contract(
                        mutation_enabled=True,
                        cli_equivalent=f"chronicle review {action} --event {event_id}",
                        event_id=event_id,
                        action=action,
                        error_code="ui_intent_mismatch",
                    ),
                },
            )
        try:
            reviewer_kind = ReviewerIdentityKind(reviewer_kind_value)
        except ValueError:
            return (
                HTTPStatus.BAD_REQUEST,
                {
                    "ok": False,
                    "status": "blocked",
                    "event_id": event_id,
                    "action": action,
                    "error_code": "invalid_reviewer_kind",
                    "message": self._review_action_failure_message("invalid_reviewer_kind"),
                    "mutation_enabled": True,
                    "failure_contract": self._review_action_failure_contract(
                        mutation_enabled=True,
                        cli_equivalent=f"chronicle review {action} --event {event_id}",
                        event_id=event_id,
                        action=action,
                        error_code="invalid_reviewer_kind",
                    ),
                },
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
                {
                    "ok": False,
                    "status": "blocked",
                    "event_id": event_id,
                    "action": action,
                    "error_code": "authorization_failed",
                    "message": self._review_action_failure_message("authorization_failed"),
                    "mutation_enabled": True,
                    "warning_codes": capability.get("warnings", []),
                    "warning_details": capability.get("warning_details", []),
                    "identity_assurance_status": assurance.get("status"),
                    "identity_assurance_message": assurance.get("message"),
                    "failure_summary": self._review_action_failure_summary(
                        error_code="authorization_failed",
                        warning_codes=capability.get("warnings", []),
                        identity_assurance_status=str(assurance.get("status", "")),
                    ),
                    "cli_equivalent": f"chronicle review {action} --event {event_id}",
                    "failure_contract": self._review_action_failure_contract(
                        mutation_enabled=True,
                        cli_equivalent=f"chronicle review {action} --event {event_id}",
                        event_id=event_id,
                        action=action,
                        error_code="authorization_failed",
                    ),
                },
            )

        review_row = self._review_queue_row_including_resolved(event_id)
        if review_row is None:
            return (
                HTTPStatus.NOT_FOUND,
                {
                    "ok": False,
                    "status": "blocked",
                    "event_id": event_id,
                    "action": action,
                    "error_code": "review_target_not_found",
                    "message": self._review_action_failure_message("review_target_not_found"),
                    "mutation_enabled": True,
                    "failure_contract": self._review_action_failure_contract(
                        mutation_enabled=True,
                        cli_equivalent=f"chronicle review {action} --event {event_id}",
                        event_id=event_id,
                        action=action,
                        error_code="review_target_not_found",
                    ),
                },
            )
        if review_row.get("pending") is not True:
            return (
                HTTPStatus.CONFLICT,
                {
                    "ok": False,
                    "status": "blocked",
                    "event_id": event_id,
                    "action": action,
                    "error_code": "review_not_pending",
                    "message": self._review_action_failure_message("review_not_pending"),
                    "mutation_enabled": True,
                    "failure_summary": self._review_action_failure_summary(
                        error_code="review_not_pending",
                    ),
                    "cli_equivalent": f"chronicle review {action} --event {event_id}",
                    "failure_contract": self._review_action_failure_contract(
                        mutation_enabled=True,
                        cli_equivalent=f"chronicle review {action} --event {event_id}",
                        event_id=event_id,
                        action=action,
                        error_code="review_not_pending",
                    ),
                },
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
                {
                    "ok": False,
                    "status": "blocked",
                    "event_id": event_id,
                    "action": action,
                    "error_code": "audit_insertion_failed",
                    "message": self._review_action_failure_message("audit_insertion_failed"),
                    "mutation_enabled": True,
                    "detail": exc.hint,
                    "failure_summary": self._review_action_failure_summary(
                        error_code="audit_insertion_failed",
                    ),
                    "cli_equivalent": f"chronicle review {action} --event {event_id}",
                    "failure_contract": self._review_action_failure_contract(
                        mutation_enabled=True,
                        cli_equivalent=f"chronicle review {action} --event {event_id}",
                        event_id=event_id,
                        action=action,
                        error_code="audit_insertion_failed",
                    ),
                },
            )
        except ReviewDecisionPersistenceError as exc:
            return (
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {
                    "ok": False,
                    "status": "blocked",
                    "event_id": event_id,
                    "action": action,
                    "error_code": "decision_persistence_failed",
                    "message": self._review_action_failure_message("decision_persistence_failed"),
                    "mutation_enabled": True,
                    "detail": exc.hint,
                    "audit_id": exc.audit_id,
                    "failure_summary": self._review_action_failure_summary(
                        error_code="decision_persistence_failed",
                    ),
                    "cli_equivalent": f"chronicle review {action} --event {event_id}",
                    "failure_contract": self._review_action_failure_contract(
                        mutation_enabled=True,
                        cli_equivalent=f"chronicle review {action} --event {event_id}",
                        event_id=event_id,
                        action=action,
                        error_code="decision_persistence_failed",
                        audit_id=exc.audit_id,
                    ),
                },
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
                "cli_equivalent": f"chronicle review {action} --event {event_id}",
                "mutation_enabled": True,
                "reviewer_identity": result.reviewer_identity.model_dump(mode="json"),
                "success_contract": self._review_action_success_contract(
                    cli_equivalent=f"chronicle review {action} --event {event_id}",
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
        return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Chronicle Local UI — {title}</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; max-width: 1180px; margin: 0 auto; padding: 20px; color: #1f2937; }}
button {{ margin: 3px; padding: 6px 9px; }}
.panel {{ border: 1px solid #e5e7eb; border-radius: 8px; padding: 14px; margin: 12px 0; }}
.warning {{ background: #fefce8; border-left: 4px solid #eab308; padding: 10px 12px; }}
.notice {{ background: #eff6ff; border-left: 4px solid #3b82f6; padding: 10px 12px; margin: 10px 0; }}
.badge {{ display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 0.85em; margin-right: 6px; }}
.badge-warning {{ background: #fef3c7; color: #92400e; }}
.badge-ready {{ background: #dcfce7; color: #166534; }}
.badge-neutral {{ background: #e5e7eb; color: #374151; }}
pre {{ white-space: pre-wrap; word-break: break-word; background: #f9fafb; padding: 12px; }}
table {{ width: 100%; border-collapse: collapse; }}
th, td {{ padding: 6px; border-bottom: 1px solid #e5e7eb; vertical-align: top; }}
.id {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.85em; }}
</style>
</head>
<body>
<h1>Chronicle Stack Local UI</h1>
<p><strong>{title}</strong></p>
<p>Root: <span class="id">{root}</span></p>
<div class="warning">
  <p><strong>Read-only foreground local UI.</strong> This UI reads local Chronicle files and does not write records.</p>
  <p>No daemon, no autostart, no external model API, no GraphRAG runtime, no vector DB, no graph DB. UI visibility is not correctness proof.</p>
</div>
<nav>
  <button data-endpoint="/api/overview">Overview</button>
  <button data-endpoint="/api/events">Events</button>
  <button data-endpoint="/api/contexts">Contexts</button>
  <button data-endpoint="/api/artifacts">Artifacts</button>
  <button data-endpoint="/api/decisions">Decisions</button>
  <button data-endpoint="/api/rde">RDE</button>
  <button data-endpoint="/api/boundary">Boundary</button>
  <button data-endpoint="/api/audit">Audit</button>
  <button data-endpoint="/api/lifecycle">Lifecycle</button>
  <button data-endpoint="/api/runtime-records">Runtime Records</button>
  <button data-endpoint="/api/review-queue">Review Queue</button>
  <button data-endpoint="/api/summary-jobs">Summary Jobs</button>
  <button data-endpoint="/api/ui-boundary">UI Boundary</button>
  <button data-endpoint="/api/runtime-config">Runtime Config</button>
  <button data-endpoint="/api/package-review">Package Review</button>
  <button data-endpoint="/api/graph-summary">Graph Summary</button>
  <button data-endpoint="/api/ai-index-status">AI Index Status</button>
  <button data-endpoint="/api/ai-index-vector">AI Index Vector</button>
  <button data-endpoint="/api/ai-index-graph-nodes">AI Index Graph Nodes</button>
  <button data-endpoint="/api/ai-index-graph-edges">AI Index Graph Edges</button>
</nav>
<section id="view" class="panel"><p>Loading overview...</p></section>
<section id="detail" class="panel"><p>Select JSON from a table row to inspect one record.</p></section>
<script>
const idFields = ['event_id', 'context_id', 'artifact_id', 'decision_id', 'rde_record_id', 'rule_id', 'audit_id', 'lifecycle_id', 'record_id', 'node_id', 'summary_job_id'];
const reviewWarningLabels = {review_warning_labels_json};
function esc(value) {{ return String(value).replace(/[&<>\"']/g, ch => ({{'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}}[ch])); }}
function firstArray(payload) {{ for (const key of Object.keys(payload)) if (Array.isArray(payload[key])) return payload[key]; return null; }}
function badge(text, cls) {{ return '<span class="badge ' + cls + '">' + esc(text) + '</span>'; }}
function jumpBadge(text, cls, endpoint, filterTarget, filterValue) {{
  const targetAttr = filterTarget ? ' data-filter-target="' + esc(filterTarget) + '"' : '';
  const valueAttr = filterValue ? ' data-filter-value="' + esc(filterValue) + '"' : '';
  return '<button data-jump="' + esc(endpoint) + '"' + targetAttr + valueAttr + '>'
    + badge(text, cls) + '</button>';
}}
function copyCommandButton(command, targetId, label = 'Copy CLI') {{
  if (!command) return '';
  return '<button data-copy-command="' + esc(command) + '" data-copy-target="' + esc(targetId || 'action-preview-response') + '">' + esc(label) + '</button>';
}}
function sourceCountBadges(sourceCounts) {{
  return Object.entries(sourceCounts || {{}}).map(([key, value]) =>
    badge(key + ':' + value, 'badge-neutral')
  ).join('');
}}
function detailMessages(items, fallbackItems = []) {{
  const details = Array.isArray(items) ? items : [];
  const fallback = Array.isArray(fallbackItems) ? fallbackItems : [];
  return details.map(item => item.message).join(' | ') || fallback.join(' | ') || '';
}}
function reviewActionCoreDetailLines(payload, action = '', recordId = '') {{
  return ''
    + detailLine('Action', payload.action || action || '')
    + detailLine('Event', payload.event_id || recordId || '')
    + detailLine('Error code', payload.error_code || '')
    + detailLine('Identity assurance', payload.identity_assurance_status || '')
    + detailLine('Identity assurance message', payload.identity_assurance_message || '')
    + detailLine('CLI equivalent', payload.cli_equivalent || '')
    + detailLine('Failure summary', payload.failure_summary || '')
    + detailLine('Warnings', detailMessages(payload.warning_details, payload.warning_codes));
}}
function contractDetailLines(successContract, failureContract, targetId) {{
  const resolvedContract = (successContract || failureContract) || {{}};
  const lines = []
    + detailLine('Recovery path', resolvedContract.recovery_path || '')
    + detailLine('Rollback status', resolvedContract.rollback_status || '')
    + detailLine('Transaction status', (successContract || {{}}).transaction_status || '')
    + detailLine('Durable mutation on failure', (failureContract || {{}}).durable_mutation_reported_on_failure)
    + detailListLine('Possible errors', (failureContract || {{}}).possible_error_codes, ' | ')
    + detailListLine('Recovery commands', (failureContract || {{}}).recovery_commands, ' | ')
    + detailListLine('Follow-up commands', (successContract || {{}}).follow_up_commands, ' | ');
  return lines + (resolvedContract.recovery_path ? '<p>' + copyCommandButton(resolvedContract.recovery_path, targetId, 'Copy Recovery CLI') + '</p>' : '');
}}
function renderReviewActionResultPanel(title, responseStatus, path, payload, targetId, options = {{}}) {{
  const action = options.action || '';
  const recordId = options.recordId || '';
  const message = options.useStatusFallback
    ? (payload.message || payload.status || 'No message returned.')
    : (payload.message || 'No message returned.');
  const extraLines = options.extraLines || '';
  return ''
    + '<p><strong>' + esc(title) + '</strong></p>'
    + '<p>Status: ' + esc(responseStatus) + '</p>'
    + '<p>Route: <span class="id">' + esc(path) + '</span></p>'
    + '<p>' + esc(message) + '</p>'
    + reviewActionCoreDetailLines(payload, action, recordId)
    + extraLines
    + contractDetailLines(payload.success_contract, payload.failure_contract, targetId);
}}
function renderReviewMutationForm(title, prefix) {{
  return '<div class="notice"><strong>' + esc(title) + '</strong><p>'
    + '<label>Reviewer <input id="' + esc(prefix) + '-reviewer-label" value="local-ui" placeholder="alice"></label> '
    + '<label>Kind <select id="' + esc(prefix) + '-reviewer-kind"><option value="local_operator">local_operator</option><option value="user_declared">user_declared</option></select></label> '
    + '<label>Session <input id="' + esc(prefix) + '-reviewer-session-label" value="local-ui-session" placeholder="desk-session-1"></label> '
    + '<label>Note <input id="' + esc(prefix) + '-reviewer-note" placeholder="optional review note"></label></p></div>';
}}
function renderPreviewSummary(preview) {{
  return preview.status
    ? '<strong>' + esc(preview.status) + '</strong><br>' + esc(preview.message || '')
    : esc(preview.message || '');
}}
function renderPreviewButtons(previewActions, options = {{}}) {{
  const actions = Array.isArray(previewActions) ? previewActions : [];
  const mutationEnabled = Boolean(options.mutationEnabled);
  const recordId = options.recordId || '';
  const fieldPrefix = options.fieldPrefix || '';
  const successDetail = options.successDetail || '';
  const previewTarget = options.previewTarget || 'action-preview-response';
  return actions.map(item =>
    mutationEnabled
      ? '<button data-submit-review-action="' + esc(item.post_path || '') + '" data-review-action="' + esc(item.action || '') + '" data-review-record="' + esc(recordId) + '" data-review-fields="' + esc(fieldPrefix) + '" data-success-detail="' + esc(successDetail) + '" data-preview-target="' + esc(previewTarget) + '">' + esc(item.label || item.action || 'Apply') + '</button>'
      : '<button data-preview-post="' + esc(item.post_path || '') + '" data-preview-target="' + esc(previewTarget) + '">Preview blocked route</button>'
  ).join(' ');
}}
function authReadinessBadge(status) {{
  return status === 'boundary_aligned'
    ? jumpBadge('Auth aligned', 'badge-ready', '/api/review-queue', 'reviewQueue', 'boundary_aligned')
    : jumpBadge('Auth advisory', 'badge-warning', '/api/review-queue', 'reviewQueue', status || 'advisory_only');
}}
function identityAssuranceBadge(status) {{
  return status === 'boundary_aligned'
    ? jumpBadge('Identity aligned', 'badge-ready', '/api/review-queue', 'reviewQueue', 'boundary_aligned')
    : status
      ? jumpBadge('Identity advisory', 'badge-warning', '/api/review-queue', 'reviewQueue', status)
      : badge('Identity n/a', 'badge-neutral');
}}
function summaryReviewStatusBadge(status) {{
  return status === 'ready'
    ? jumpBadge('Ready', 'badge-ready', '/api/review-queue', 'reviewQueue', 'ready')
    : status === 'resolved'
      ? jumpBadge('Resolved', 'badge-neutral', '/api/review-queue', 'reviewQueue', 'resolved')
      : jumpBadge('Advisory', 'badge-warning', '/api/review-queue', 'reviewQueue', 'advisory');
}}
function packageStatusBadge(status) {{
  return status === 'package_context_available'
    ? jumpBadge('Package Ready', 'badge-ready', '/api/review-queue', 'reviewQueue', 'package:package_context_available')
    : status === 'no_context_records'
      ? jumpBadge('Package Advisory', 'badge-warning', '/api/review-queue', 'reviewQueue', 'package:no_context_records')
      : badge(status || 'Package Unknown', 'badge-neutral');
}}
function previewButtonsConfig(row, config) {{
  return {{
    mutationEnabled: row.ui_mutation_enabled,
    recordId: config.recordId || '',
    fieldPrefix: config.fieldPrefix || '',
    successDetail: config.successDetail || '',
    previewTarget: config.previewTarget || 'action-preview-response',
  }};
}}
function detailJsonButton(endpoint, row) {{
  const path = detailPath(endpoint, row);
  return path ? '<button data-detail="' + esc(path) + '">JSON</button>' : '';
}}
function stackedCell(parts, separator = '<br>') {{
  return parts.filter(part => part).join(separator);
}}
function previewCell(preview, previewActions, options) {{
  const previewSummary = renderPreviewSummary(preview || {{}});
  const previewButtons = renderPreviewButtons(previewActions, options);
  return previewSummary + (previewButtons ? '<br>' + previewButtons : '');
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
  return query ? '<p><button data-reset-filter="' + esc(target) + '">Reset Filter</button></p>' : '';
}}
function emptyFilterState(query, rows, message) {{
  return query && rows.length === 0 ? '<p>' + esc(message) + '</p>' : '';
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
  const responseMetadata = row.response_metadata_summary || {{}};
  const sourceBadges = sourceCountBadges(preview.source_counts || {{}});
  const authBadge = row.auth_readiness_status === 'boundary_aligned'
    ? jumpBadge('Auth aligned', 'badge-ready', '/api/review-queue', 'reviewQueue', 'boundary_aligned')
    : row.auth_readiness_status
      ? jumpBadge('Auth advisory', 'badge-warning', '/api/review-queue', 'reviewQueue', row.auth_readiness_status)
      : badge('Auth n/a', 'badge-neutral');
  const kindBadge = jumpBadge(
    row.runtime_record_kind || 'unknown',
    'badge-neutral',
    '/api/runtime-records',
    'runtimeRecords',
    row.runtime_record_kind || 'unknown',
  );
  return '<tr>'
    + '<td>' + button + '</td>'
    + '<td><span class="id">' + esc(row.event_id || '') + '</span></td>'
    + '<td>' + kindBadge + '</td>'
    + '<td>' + authBadge + '</td>'
    + '<td>' + stackedCell([
      '<strong>' + esc(preview.title || '') + '</strong>',
      esc(preview.preview_text || ''),
      responseMetadata.present
        ? 'Response ' + esc(responseMetadata.response_id || '(no response_id)')
          + (responseMetadata.finish_reason ? ' / ' + esc(responseMetadata.finish_reason) : '')
        : ''
    ]) + '</td>'
    + '<td>' + stackedCell([sourceBadges, esc(JSON.stringify(preview.source_counts || {{}}))]) + '</td>'
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
  return '<tr>'
    + '<td>' + button + '</td>'
    + '<td>' + stackedCell([
      '<span class="id">' + esc(row.target_event_id || '') + '</span>',
      reviewKindBadge,
      esc(row.target_summary || ''),
      responseMetadata.present
        ? 'Response ' + esc(responseMetadata.response_id || '(no response_id)')
          + (responseMetadata.finish_reason ? ' / ' + esc(responseMetadata.finish_reason) : '')
        : ''
    ]) + '</td>'
    + '<td>' + stackedCell([statusBadge, readinessBadge, parityBadge]) + '</td>'
    + '<td>' + authBadge + '</td>'
    + '<td>' + previewCell(preview, previewActions, previewButtonsConfig(row, {{
      recordId: row.target_event_id || '',
      fieldPrefix: 'review-queue',
      successDetail: '/api/review-queue/' + esc(row.target_event_id || ''),
      previewTarget: 'review-queue-action-preview-response',
    }})) + '</td>'
    + '<td>' + stackedCell([warnBadges, esc(warnDetails.map(item => item.message).join(' | ') || warnList.join(', ') || '(none)')]) + '</td>'
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
  const reviewBadge = summaryReviewStatusBadge(reviewStatus);
  const authBadge = authReadinessBadge(authReadinessStatus);
  const identityBadge = identityAssuranceBadge(identityAssuranceStatus);
  const packageBadge = packageStatusBadge(packageStatus);
  const responseMetadata = row.response_metadata_summary || {{}};
  const targetButton = row.review_target_event_id
    ? '<button data-detail-nav="/api/review-queue/' + esc(row.review_target_event_id) + '">Open review</button>'
    : '';
  return '<tr>'
    + '<td>' + button + '</td>'
    + '<td>' + stackedCell(['<span class="id">' + esc(row.summary_job_id || '') + '</span>', esc(row.title || ''), targetButton]) + '</td>'
    + '<td>' + esc(row.status || '') + '</td>'
    + '<td>' + reviewBadge + '</td>'
    + '<td>' + authBadge + '</td>'
    + '<td>' + summaryIdentityCell(identityBadge, row.latest_reviewer_identity) + '</td>'
    + '<td>' + packageBadge + '</td>'
    + '<td>' + previewCell(preview, previewActions, previewButtonsConfig(row, {{
      recordId: row.review_target_event_id || '',
      fieldPrefix: 'summary-jobs',
      successDetail: '/api/summary-jobs/' + esc(row.summary_job_id || ''),
      previewTarget: 'summary-jobs-action-preview-response',
    }})) + '</td>'
    + '<td>' + stackedCell([
      esc(row.runtime_provider_kind || ''),
      responseMetadata.present
        ? 'Response ' + esc(responseMetadata.response_id || '(no response_id)')
          + (responseMetadata.finish_reason ? ' / ' + esc(responseMetadata.finish_reason) : '')
        : ''
    ]) + '</td>'
    + '<td>' + esc(row.summary_source_count ?? 0) + '</td>'
    + '</tr>';
}}
function renderRuntimeRecordsTable(endpoint, rows) {{
  const query = (window.__chronicleFilters && window.__chronicleFilters.runtimeRecords || '').toLowerCase();
  const filtered = filterRows(rows, row => {{
    if (!query) return true;
    const preview = row.runtime_record_preview || {{}};
    const responseMetadata = row.response_metadata_summary || {{}};
    return includesQuery([
      row.event_id || '',
      row.runtime_record_kind || '',
      row.auth_readiness_status || '',
      preview.title || '',
      preview.preview_text || '',
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
  return listToolbar(endpoint, 'runtimeRecords', 'Filter runtime records...', [
      {{ value: 'latest', label: 'Latest first' }},
      {{ value: 'kind', label: 'Kind' }},
    ], runtimeRecordsFilterChips(), query)
    + emptyFilterState(query, sorted, 'No matching runtime records for current filter.')
    + tableHtml(['detail', 'event', 'kind', 'auth', 'preview', 'source counts'], sorted.map(row => renderRuntimeRecordRow(row, endpoint)).join(''));
}}
function renderReviewQueueTable(endpoint, rows) {{
  const query = (window.__chronicleFilters && window.__chronicleFilters.reviewQueue || '').toLowerCase();
  const filtered = filterRows(rows, row => {{
    if (!query) return true;
    const capability = row.review_capability || {{}};
    const readiness = row.package_readiness_summary || {{}};
    const parity = row.cli_parity_summary || {{}};
    const authReadiness = row.auth_boundary_notice || {{}};
    const responseMetadata = row.response_metadata_summary || {{}};
    return includesQuery([
      row.target_event_id || '',
      row.target_summary || '',
      row.review_kind || '',
      capability.status || '',
      readiness.label || '',
      parity.status || '',
      authReadiness.status || '',
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
  return listToolbar(endpoint, 'reviewQueue', 'Filter review queue...', [
      {{ value: 'attention', label: 'Needs attention first' }},
      {{ value: 'parity', label: 'CLI drift first' }},
      {{ value: 'latest', label: 'Latest first' }},
      {{ value: 'reviewer', label: 'Reviewer' }},
    ], reviewQueueFilterChips(), query)
    + emptyFilterState(query, sorted, 'No matching review rows for current filter.')
    + (
      mutationEnabled
        ? renderReviewMutationForm('Local Review Mutation', 'review-queue')
        : ''
    )
    + actionPreviewStatus(
      'review-queue-action-preview-response',
      mutationEnabled,
      'Local mutation is enabled for this list view. Each action still requires explicit reviewer context and writes audit-backed review history.',
      'Review queue blocked-route preview stays read-only and returns the CLI fallback contract.'
    )
    + tableHtml(['detail', 'target', 'status', 'auth', 'preview', 'warnings', 'latest reviewer'], sorted.map(row => renderReviewQueueRow(row, endpoint)).join(''));
}}
function renderSummaryJobsTable(endpoint, rows) {{
  const query = (window.__chronicleFilters && window.__chronicleFilters.summaryJobs || '').toLowerCase();
  const filtered = filterRows(rows, row => {{
    if (!query) return true;
    const responseMetadata = row.response_metadata_summary || {{}};
    return includesQuery([
      row.summary_job_id || '',
      row.title || '',
      row.status || '',
      row.review_capability_status || '',
      row.auth_readiness_status || '',
      row.package_readiness_status || '',
      row.identity_assurance_status || '',
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
  return listToolbar(endpoint, 'summaryJobs', 'Filter summary jobs...', [
      {{ value: 'latest', label: 'Latest first' }},
      {{ value: 'review', label: 'Needs attention first' }},
      {{ value: 'title', label: 'Title' }},
    ], summaryJobsFilterChips(), query)
    + emptyFilterState(query, sorted, 'No matching summary jobs for current filter.')
    + (
      mutationEnabled
        ? renderReviewMutationForm('Summary Review Mutation', 'summary-jobs')
        : ''
    )
    + actionPreviewStatus(
      'summary-jobs-action-preview-response',
      mutationEnabled,
      'Local mutation is enabled for summary-backed review targets. Actions still require explicit reviewer context and write audit-backed review history.',
      'Summary jobs blocked-route preview stays read-only and returns the CLI fallback contract.'
    )
    + tableHtml(['detail', 'summary job', 'status', 'review', 'auth', 'identity', 'package', 'preview', 'runtime', 'sources'], sorted.map(row => renderSummaryJobRow(row, endpoint)).join(''));
}}
function renderGenericTable(endpoint, rows) {{
  const keys = Object.keys(rows[0]).slice(0, 8);
  return '<table><thead><tr><th>detail</th>' + keys.map(k => '<th>' + esc(k) + '</th>').join('') + '</tr></thead><tbody>'
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
    const text = reviewWarningLabels[String(code || '')] || String(code || '').replaceAll('_', ' ');
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
  if (status === 'package_context_available') {{
    return badge(label || 'Package Ready', 'badge-ready');
  }}
  if (status === 'no_context_records') {{
    return badge(label || 'Package Advisory', 'badge-warning');
  }}
  return badge(label || 'Package Unknown', 'badge-neutral');
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
function sortRuntimeRows(rows) {{
  const sortValue = currentSortValue('/api/runtime-records');
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
  return endpointStateLabel('filter', window.__chronicleCurrentEndpoint);
}}
function sortStateLabel(endpoint, sortValue) {{
  if (!sortValue) return '';
  if (endpoint === '/api/review-queue') {{
    const warningFilter = activeReviewWarningFilter();
    if (warningFilter) return stateLabel('sort', sortValue, 'warning-first:' + warningFilter);
  }}
  return stateLabel('sort', sortValue);
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
function sliceChip(filterValue, cls, resetTarget) {{
  const value = String(filterValue || '');
  if (!value) return '';
  return '<p>'
    + badge('slice:' + value, cls)
    + ' <button data-reset-filter="' + esc(resetTarget) + '">Clear Slice</button>'
    + '</p>';
}}
function sliceBadge(text, count, cls) {{
  return badge(text + ': ' + count, cls);
}}
function filterChips(target, cls) {{
  const filterValue = String((window.__chronicleFilters && window.__chronicleFilters[target]) || '');
  return sliceChip(filterValue, cls, target);
}}
function reviewQueueFilterChips() {{
  return filterChips('reviewQueue', 'badge-warning');
}}
function runtimeRecordsFilterChips() {{
  return filterChips('runtimeRecords', 'badge-neutral');
}}
function summaryJobsFilterChips() {{
  return filterChips('summaryJobs', 'badge-neutral');
}}
function activeViewSummary(endpoint, mode) {{
  const parts = [];
  const currentEndpoint = endpoint || window.__chronicleCurrentEndpoint || '/api/overview';
  parts.push('view=' + currentEndpoint);
  const filterLabel = currentFilterLabel();
  if (filterLabel) parts.push(filterLabel);
  const sortLabel = currentSortLabel(currentEndpoint);
  if (sortLabel) parts.push(sortLabel);
  if (mode === 'detail') {{
    const trailLabel = currentTrailLabel();
    if (trailLabel) parts.push('trail=' + trailLabel);
  }}
  return '<p class="id">Active view: ' + esc(parts.join(' | ')) + '</p>';
}}
function humanizeDetailPath(path) {{
  const parts = String(path || '').split('/').filter(Boolean);
  if (parts.length < 3 || parts[0] !== 'api') return String(path || '');
  const resource = parts[1];
  const recordId = parts[2];
  const labels = {{
    'runtime-records': 'Runtime',
    'review-queue': 'Review',
    'summary-jobs': 'Summary',
    'runtime-config': 'Runtime Config',
    'events': 'Event',
    'contexts': 'Context',
    'artifacts': 'Artifact',
    'decisions': 'Decision',
    'audit': 'Audit',
    'lifecycle': 'Lifecycle',
    'boundary': 'Boundary',
    'rde': 'RDE',
  }};
  return (labels[resource] || resource) + ': ' + recordId;
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
function moreSliceButton(filterValue, endpoint, filterTarget) {{
  const value = String(filterValue || '');
  if (!value) return '';
  return listJumpButton('More ' + value, endpoint, filterTarget, value);
}}
function sectionTitle(text) {{
  return '<h3>' + esc(text) + '</h3>';
}}
function detailLine(label, value) {{
  return '<p>' + esc(label) + ': ' + esc(value || '') + '</p>';
}}
function detailListLine(label, values, separator) {{
  const items = Array.isArray(values) ? values : [];
  const joiner = separator || ', ';
  return detailLine(label, items.join(joiner) || '(none)');
}}
function summaryJsonLine(label, value) {{
  return '<p>' + esc(label) + ': ' + esc(JSON.stringify(value || {{}})) + '</p>';
}}
function messageParagraph(message) {{
  return '<p>' + esc(message || '') + '</p>';
}}
function buttonRow(buttons) {{
  return buttons.length > 0 ? '<p>' + buttons.join('') + '</p>' : '';
}}
function moreStatusButtons(status, endpoint, filterTarget, prefix = '') {{
  if (!status) return [];
  return [listJumpButton('More ' + status, endpoint, filterTarget, prefix + status)];
}}
function statusMessageBody(status, message, buttons = []) {{
  return detailLine('Status', status || '') + buttonRow(buttons) + messageParagraph(message);
}}
function routeHeading(endpoint) {{
  return '<h2>' + esc(endpoint) + '</h2>';
}}
function prettyJsonPre(value) {{
  return '<pre>' + esc(JSON.stringify(value, null, 2)) + '</pre>';
}}
function renderNotice(title, body) {{
  return '<div class="notice">' + sectionTitle(title) + body + '</div>';
}}
function packageReviewButtons(record) {{
  return (record.package_handoff_preview || record.package_readiness)
    ? [listJumpButton('Open Package Review', '/api/package-review')]
    : [];
}}
function runtimeRelatedButtons(record) {{
  const buttons = [listJumpButton('Open Runtime Records', '/api/runtime-records')];
  const runtimeKind = record.runtime_record_kind || (record.runtime_record_preview && record.runtime_record_preview.record_kind) || '';
  if (runtimeKind) buttons.push(moreSliceButton(runtimeKind, '/api/runtime-records', 'runtimeRecords'));
  return buttons;
}}
function reviewRelatedButtons(record) {{
  const buttons = [listJumpButton('Open Review Queue', '/api/review-queue')];
  const capability = record.review_capability || {{}};
  const readiness = record.package_readiness || {{}};
  const warnings = Array.isArray(capability.warnings) ? capability.warnings : [];
  if (record.review_kind) buttons.push(moreSliceButton(record.review_kind, '/api/review-queue', 'reviewQueue'));
  if (capability.status) buttons.push(moreSliceButton(capability.status, '/api/review-queue', 'reviewQueue'));
  warnings.slice(0, 2).forEach(code => buttons.push(moreSliceButton(code, '/api/review-queue', 'reviewQueue')));
  if (readiness.status) buttons.push(listJumpButton('More ' + readiness.status, '/api/review-queue', 'reviewQueue', 'package:' + readiness.status));
  return buttons;
}}
function summaryRelatedButtons(record) {{
  const buttons = [listJumpButton('Open Summary Jobs', '/api/summary-jobs')];
  if (record.review_target_event_id) buttons.push(listJumpButton('Open Review Queue', '/api/review-queue'));
  const capability = record.review_capability || {{}};
  const readiness = record.package_readiness || {{}};
  const parity = record.cli_parity || {{}};
  if (capability.status) buttons.push(moreSliceButton(capability.status, '/api/review-queue', 'reviewQueue'));
  if (readiness.status) buttons.push(listJumpButton('More ' + readiness.status, '/api/review-queue', 'reviewQueue', 'package:' + readiness.status));
  if (parity.status) buttons.push(moreSliceButton(parity.status, '/api/review-queue', 'reviewQueue'));
  return buttons;
}}
function relatedListButtons(detailEndpoint, record) {{
  const buttons = [];
  if (detailEndpoint.startsWith('/api/runtime-records/')) buttons.push(...runtimeRelatedButtons(record));
  if (detailEndpoint.startsWith('/api/review-queue/')) buttons.push(...reviewRelatedButtons(record));
  if (detailEndpoint.startsWith('/api/summary-jobs/')) buttons.push(...summaryRelatedButtons(record));
  buttons.push(...packageReviewButtons(record));
  return buttons.join('');
}}
function renderNavigationNotice(endpoint, record, options = {{}}) {{
  const filterLabel = options.filterLabel || '';
  const previousDetail = options.previousDetail || '';
  const trailLabel = options.trailLabel || '';
  const trailButtons = options.trailButtons || '';
  const listButtons = options.listButtons || relatedListButtons(endpoint, record);
  return renderNotice(
    'Navigation',
    activeViewSummary(endpoint, 'detail')
      + '<p><button data-back-view="true">Back to current list</button> '
      + (previousDetail ? '<button data-back-detail="true">Back to previous detail</button> ' : '')
      + (hasActiveFilters() ? '<button data-reset-filters="all">Reset Filters</button> ' : '')
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
  return renderNotice(
    'Runtime Preview',
    '<p><strong>' + esc(preview.title || '') + '</strong></p>'
      + '<p>' + esc(preview.preview_text || '') + '</p>'
      + detailLine('Kind', preview.record_kind || record.runtime_record_kind || '')
      + summaryJsonLine('Source counts', preview.source_counts)
      + detailListLine('Referenced IDs', preview.referenced_record_ids)
      + detailLine('CLI', preview.suggested_cli_family || '')
  );
}}
function renderRetrievalHandoffNotice(record) {{
  if (!record.retrieval_handoff) return '';
  const handoff = record.retrieval_handoff;
  return renderNotice(
    'Retrieval Handoff',
    detailLine('Query', handoff.query || '')
      + '<p>Hit counts: vector=' + esc(handoff.vector_hit_count || 0)
      + ', graph=' + esc(handoff.graph_hit_count || 0)
      + ', chronicle=' + esc(handoff.chronicle_hit_count || 0) + '</p>'
      + detailListLine('Referenced IDs', handoff.referenced_record_ids)
      + detailListLine('Downstream commands', handoff.downstream_commands, ' | ')
      + detailListLine('Notes', handoff.notes, ' | ')
  );
}}
function renderPackageHandoffPreviewNotice(record) {{
  if (!record.package_handoff_preview) return '';
  const preview = record.package_handoff_preview;
  const packageReview = preview.package_review || {{}};
  const manifest = preview.package_manifest_preview || {{}};
  return renderNotice(
    'Package Handoff Preview',
    statusMessageBody(preview.status, preview.message)
      + detailListLine('Eligible contexts', preview.eligible_context_ids)
      + detailListLine('Skipped records', preview.skipped_record_ids)
      + detailLine('Package review status', packageReview.status || '(not available)')
      + detailListLine('Package warnings', packageReview.package_warnings)
      + detailListLine('Manifest refs', manifest.referenced_records)
  );
}}
function renderInvocationPlanNotice(record) {{
  if (!record.invocation_plan) return '';
  const plan = record.invocation_plan;
  const requestPreview = plan.request_preview || {{}};
  return renderNotice(
    'Invocation Plan',
    detailLine('Provider', (plan.provider_kind || '') + ' / ' + (plan.provider_name || ''))
      + detailLine('Model', plan.model_name || '')
      + detailLine('Operation', plan.operation || '')
      + detailLine('Invocation ready', plan.invocation_ready)
      + detailLine('Would use network', plan.would_use_network)
      + detailLine('Network allowed by contract', plan.network_allowed_by_contract)
      + detailListLine('Blocking reasons', plan.blocking_reasons, ' | ')
      + summaryJsonLine('Request preview', requestPreview)
      + detailListLine('Downstream commands', plan.downstream_commands, ' | ')
      + detailListLine('Notes', plan.notes, ' | ')
  );
}}
function renderResponseMetadataNotice(record) {{
  if (!record.response_metadata_summary || !record.response_metadata_summary.present) return '';
  const summary = record.response_metadata_summary;
  return renderNotice(
    'Provider Response',
    detailLine('Response ID', summary.response_id || '')
      + detailLine('Finish reason', summary.finish_reason || '')
      + detailLine('Provider status', summary.provider_status || '')
      + detailLine('Usage input tokens', summary.usage_input_tokens ?? '')
      + detailLine('Usage output tokens', summary.usage_output_tokens ?? '')
      + detailLine('Usage total tokens', summary.usage_total_tokens ?? '')
      + detailLine('Metadata fields', summary.metadata_count ?? 0)
      + detailLine('Top-level response keys', summary.response_key_count ?? 0)
      + detailListLine('Response keys', summary.response_keys, ' | ')
  );
}}
function renderPackageReadinessNotice(record) {{
  if (!record.package_readiness) return '';
  const readiness = record.package_readiness;
  const packageReview = readiness.package_review || {{}};
  const manifest = readiness.package_manifest_preview || {{}};
  const readinessButtons = moreStatusButtons(readiness.status, '/api/review-queue', 'reviewQueue', 'package:');
  return renderNotice(
    'Review Package Readiness',
    statusMessageBody(readiness.status, readiness.message, readinessButtons)
      + detailListLine('Eligible contexts', readiness.eligible_context_ids)
      + detailListLine('Suggested commands', readiness.suggested_commands, ' | ')
      + detailLine('Package review status', packageReview.status || '(not available)')
      + detailListLine('Package warnings', packageReview.package_warnings)
      + detailListLine('Manifest refs', manifest.referenced_records)
  );
}}
function renderRelatedLinksNotice(record) {{
  if (!Array.isArray(record.related_links) || record.related_links.length === 0) return '';
  return renderNotice(
    'Related Links',
    '<p>' + record.related_links.map(item =>
      '<button data-detail-nav="' + esc(item.path || '') + '">'
      + esc(item.label || humanizeDetailPath(item.path || ''))
      + '</button>'
    ).join('') + '</p>'
  );
}}
function renderAuthReadinessNotice(record) {{
  if (!record.auth_boundary_notice) return '';
  const notice = record.auth_boundary_notice;
  const blockerDetails = Array.isArray(notice.blocker_details) ? notice.blocker_details : [];
  const noticeButtons = moreStatusButtons(notice.status, '/api/review-queue', 'reviewQueue');
  return renderNotice(
    'Auth Readiness',
    statusMessageBody(notice.status, notice.message, noticeButtons)
      + detailLine('Review capability', notice.capability_status || '')
      + detailLine('Identity assurance', notice.identity_assurance_status || '')
      + detailLine('Blockers', detailMessages(blockerDetails, notice.blockers))
      + detailListLine('Next steps', notice.next_steps, ' | ')
  );
}}
function renderReviewCapabilityNotice(record) {{
  if (!record.review_capability) return '';
  const capability = record.review_capability;
  const warnList = Array.isArray(capability.warnings) ? capability.warnings : [];
  const warnDetails = Array.isArray(capability.warning_details) ? capability.warning_details : [];
  const warnBadges = reviewWarningBadges(warnList);
  return renderNotice(
    'Review Capability',
    messageParagraph(capability.message)
      + detailLine('Status', capability.status || '')
      + (warnBadges ? '<p>' + warnBadges + '</p>' : '')
      + detailLine('Warnings', detailMessages(warnDetails, warnList) || '(none)')
  );
}}
function renderDetailActionPreviewControls(preview, actions, mutationTargetEventId) {{
  const activeActionButtons = actions.map(item =>
    '<button data-submit-review-action="' + esc(item.post_path || '') + '" data-review-action="' + esc(item.action || '') + '" data-review-record="' + esc(mutationTargetEventId) + '">'
    + esc(item.label || item.action || 'Apply')
    + '</button>'
  ).join(' ');
  return preview.ui_mutation_enabled
    ? '<p><label>Reviewer <input id="reviewer-label" value="local-ui" placeholder="alice"></label> '
      + '<label>Kind <select id="reviewer-kind"><option value="local_operator">local_operator</option><option value="user_declared">user_declared</option></select></label> '
      + '<label>Session <input id="reviewer-session-label" value="local-ui-session" placeholder="desk-session-1"></label></p>'
      + '<p><label>Note <input id="reviewer-note" placeholder="optional review note"></label></p>'
      + '<p>' + activeActionButtons + '</p>'
    : '<p><button disabled>Approve</button> <button disabled>Reject</button> <button disabled>Request Changes</button></p>';
}}
function renderDetailActionPreviewList(preview, actions) {{
  return '<ul>' + actions.map(item =>
    '<li><strong>' + esc(item.label || '') + ':</strong> <span class="id">' + esc(item.command || '') + '</span>'
    + (item.command ? ' ' + copyCommandButton(item.command, 'action-preview-response') : '')
    + (item.post_path
      ? (
          preview.ui_mutation_enabled
            ? '<br><span class="id">' + esc(item.post_path || '') + '</span> <span class="id">POST enabled</span>'
            : '<br><span class="id">' + esc(item.post_path || '') + '</span> <button data-preview-post="' + esc(item.post_path || '') + '">Preview blocked route</button>'
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
    ...moreStatusButtons(capability.status, '/api/review-queue', 'reviewQueue'),
    ...moreStatusButtons(parity.status, '/api/review-queue', 'reviewQueue'),
  ];
  return renderNotice(
    'Action Preview',
    messageParagraph(preview.message)
      + detailLine('Status', preview.status || '')
      + buttonRow(previewButtons)
      + detailLine('Rollback status', failureContract.rollback_status || '')
      + detailLine('Durable mutation on failure', failureContract.durable_mutation_reported_on_failure)
      + detailLine('Recovery path', failureContract.recovery_path || '')
      + detailListLine('Possible errors', failureContract.possible_error_codes, ' | ')
      + detailListLine('Recovery commands', failureContract.recovery_commands, ' | ')
      + (failureContract.recovery_path ? '<p>' + copyCommandButton(failureContract.recovery_path, 'action-preview-response', 'Copy Recovery CLI') + '</p>' : '')
      + ((failureContract.recovery_commands || []).length > 0 ? '<p>' + (failureContract.recovery_commands || []).map(command => copyCommandButton(command, 'action-preview-response', 'Copy CLI')).join(' ') + '</p>' : '')
      + renderDetailActionPreviewControls(preview, actions, mutationTargetEventId)
      + renderDetailActionPreviewList(preview, actions)
      + '<div id="action-preview-response"><p>'
      + (
        preview.ui_mutation_enabled
          ? 'Local mutation is enabled for this detail view. Every action still requires explicit reviewer context and writes audit-backed review history.'
          : 'Blocked route preview stays read-only and returns the CLI fallback contract.'
      )
      + '</p></div>'
  );
}}
function renderCliParityNotice(record) {{
  if (!record.cli_parity) return '';
  const parity = record.cli_parity;
  const parityButtons = moreStatusButtons(parity.status, '/api/review-queue', 'reviewQueue');
  return renderNotice(
    'CLI Parity',
    messageParagraph(parity.message)
      + detailLine('Status', parity.status || '')
      + buttonRow(parityButtons)
      + detailListLine('Expected actions', parity.expected_actions)
      + detailListLine('Missing preview commands', parity.missing_preview_commands, ' | ')
      + detailListLine('Missing queue commands', parity.missing_queue_commands, ' | ')
  );
}}
function renderIdentityAssuranceNotice(record) {{
  if (!record.latest_identity_assurance) return '';
  const assurance = record.latest_identity_assurance;
  const assuranceButtons = moreStatusButtons(assurance.status, '/api/review-queue', 'reviewQueue');
  return renderNotice(
    'Identity Assurance',
    statusMessageBody(assurance.status, assurance.message, assuranceButtons)
  );
}}
function renderReviewTimelineNotice(record) {{
  if (!Array.isArray(record.history) || record.history.length === 0) return '';
  return renderNotice(
    'Review Timeline',
    '<ul>' + record.history.map(item => {{
      const timelineButtons = [
        ...moreStatusButtons(item.disposition, '/api/review-queue', 'reviewQueue'),
        ...moreStatusButtons(item.identity_assurance && item.identity_assurance.status, '/api/review-queue', 'reviewQueue'),
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
  if (body !== undefined) {{
    options.headers = {{ 'Content-Type': 'application/json' }};
    options.body = JSON.stringify(body);
  }}
  const response = await fetch(path, options);
  const payload = await responseJsonOrEmpty(response);
  return {{ response, payload }};
}}
function appendCommandFeedback(target, command, copied) {{
  if (!target) return;
  target.innerHTML += '<p>' + esc(copied ? 'Copied recovery CLI: ' : 'Copy failed; command: ') + '<span class="id">' + esc(command) + '</span></p>';
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
  return {{
    reviewer_label: reviewFieldValue(fieldPrefix, 'reviewer-label', ''),
    reviewer_kind: reviewFieldValue(fieldPrefix, 'reviewer-kind', 'local_operator') || 'local_operator',
    session_label: reviewFieldValue(fieldPrefix, 'reviewer-session-label', ''),
    note: reviewFieldValue(fieldPrefix, 'reviewer-note', ''),
    ui_intent: action || '',
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
    + '<p>Chronicle ID: <span class="id">' + esc(chronicle.id || '') + '</span></p>'
    + '<p>Root: <span class="id">' + esc(chronicle.root || '') + '</span></p>'
  );
}}
function renderOverviewCountsPanel(counts) {{
  const countRows = Object.entries(counts || {{}}).map(([key, value]) =>
    '<tr><th>' + esc(key) + '</th><td>' + esc(value ?? '') + '</td></tr>'
  ).join('');
  return renderPanel(
    sectionTitle('Counts')
    + '<table><tbody>' + countRows + '</tbody></table>'
  );
}}
function renderOverviewRuntimeBoundaryPanel(runtime) {{
  return renderPanel(
    sectionTitle('Runtime Boundary')
    + '<p>Read-only: ' + esc(runtime.read_only) + '</p>'
    + '<p>External model API: ' + esc(runtime.external_model_api) + '</p>'
    + '<p>GraphRAG runtime: ' + esc(runtime.graphrag_runtime) + '</p>'
    + '<p>Vector DB: ' + esc(runtime.vector_db) + '</p>'
    + '<p>Graph DB: ' + esc(runtime.graph_db) + '</p>'
  );
}}
function renderOverviewRuntimeConfigPanel(runtimeConfig, runtimeConfigContract) {{
  return renderPanel(
    sectionTitle('Runtime Config')
    + detailLine('Source', runtimeConfig.source || '')
    + detailLine('Provider kind', runtimeConfigContract.provider_kind || '')
    + detailLine('Provider name', runtimeConfigContract.provider_name || '')
    + detailLine('Model', runtimeConfigContract.model_name || '')
    + detailLine('Allow network', runtimeConfigContract.allow_network)
    + detailLine('Allow external context', runtimeConfigContract.allow_external_context)
    + detailListLine('Warnings', runtimeConfig.warnings, ' | ')
    + '<p>' + listJumpButton('Open Runtime Config', '/api/runtime-config') + '</p>'
  );
}}
function renderOverviewUiBoundaryPanel(uiBoundary) {{
  return renderPanel(
    sectionTitle('UI Boundary')
    + '<p>Bind scope: ' + esc(uiBoundary.bind_scope || '') + '</p>'
    + '<p>Mutation enabled: ' + esc(uiBoundary.mutation_enabled) + '</p>'
    + '<p>Mutation capability flag: ' + esc(uiBoundary.mutation_capability_flag) + '</p>'
    + '<p>Auth mode: ' + esc(uiBoundary.auth_mode || '') + '</p>'
    + '<p>Authorization mode: ' + esc(uiBoundary.authorization_mode || '') + '</p>'
    + '<p>Session gating: ' + esc(uiBoundary.session_gating) + '</p>'
    + '<p>Mutation readiness: ' + esc(uiBoundary.mutation_readiness_status || '') + '</p>'
  );
}}
function renderOverviewAuthBoundaryPanel(authBoundary, authBoundaryOverview) {{
  return renderPanel(
    sectionTitle('Auth Boundary')
    + '<p>'
    + overviewJumpButton(sliceBadge('Auth warnings', esc(authBoundaryOverview.auth_warning_count ?? 0), 'badge-warning'), '/api/review-queue', 'reviewQueue', 'ui_auth_not_enabled')
    + overviewJumpButton(sliceBadge('Authorization warnings', esc(authBoundaryOverview.authorization_warning_count ?? 0), 'badge-warning'), '/api/review-queue', 'reviewQueue', 'ui_authorization_not_enabled')
    + overviewJumpButton(sliceBadge('Missing identity', esc(authBoundaryOverview.missing_identity_count ?? 0), 'badge-warning'), '/api/review-queue', 'reviewQueue', 'no_reviewer_identity_recorded')
    + overviewJumpButton(sliceBadge('Provider response', esc(authBoundaryOverview.provider_response_present_count ?? 0), 'badge-ready'), '/api/review-queue', 'reviewQueue', 'response_id')
    + '</p>'
    + detailLine('Status', authBoundary.status || '')
    + '<p>' + esc(authBoundary.message || '') + '</p>'
    + detailLine('Session gating', authBoundary.session_gating)
    + detailLine('Shared machine safe', authBoundary.shared_machine_safe)
    + summaryJsonLine('Auth review capability counts', authBoundaryOverview.review_capability_counts)
    + summaryJsonLine('Provider finish reasons', authBoundaryOverview.provider_response_finish_reason_counts)
    + summaryJsonLine('Provider statuses', authBoundaryOverview.provider_response_status_counts)
    + detailListLine('Auth blockers', authBoundary.blockers, ' | ')
    + detailListLine('Auth next steps', authBoundary.next_steps, ' | ')
  );
}}
function renderOverviewIdentityBoundaryPanel(identityBoundary) {{
  return renderPanel(
    sectionTitle('Identity Boundary')
    + '<p>'
    + overviewJumpButton(sliceBadge('Declared identity only', esc(identityBoundary.declared_identity_count ?? 0), 'badge-warning'), '/api/review-queue', 'reviewQueue', 'reviewer_identity_declared_only')
    + overviewJumpButton(sliceBadge('Session label required', esc(identityBoundary.session_label_missing_count ?? 0), 'badge-warning'), '/api/review-queue', 'reviewQueue', 'reviewer_session_label_missing')
    + overviewJumpButton(sliceBadge('Identity aligned', esc((identityBoundary.assurance_counts && identityBoundary.assurance_counts.boundary_aligned) ?? 0), 'badge-ready'), '/api/review-queue', 'reviewQueue', 'boundary_aligned')
    + '</p>'
    + detailLine('Status', identityBoundary.status || '')
    + '<p>' + esc(identityBoundary.message || '') + '</p>'
    + summaryJsonLine('Identity assurance counts', identityBoundary.assurance_counts)
    + detailLine('Missing identity rows', identityBoundary.missing_identity_count ?? 0)
    + detailLine('Declared-only rows', identityBoundary.declared_identity_count ?? 0)
    + detailLine('Session-label-missing rows', identityBoundary.session_label_missing_count ?? 0)
    + detailListLine('Identity blockers', identityBoundary.blockers, ' | ')
    + detailListLine('Identity next steps', identityBoundary.next_steps, ' | ')
  );
}}
function renderOverviewMutationReadinessPanel(mutationReadiness) {{
  const blockerDetails = Array.isArray(mutationReadiness.blocker_details) ? mutationReadiness.blocker_details : [];
  const reviewerContextRequirements = mutationReadiness.reviewer_context_requirements || {{}};
  return renderPanel(
    sectionTitle('Mutation Readiness')
    + detailLine('Status', mutationReadiness.status || '')
    + '<p>' + esc(mutationReadiness.message || '') + '</p>'
    + detailLine('Ready rows', mutationReadiness.ready_row_count ?? 0)
    + detailLine('Advisory rows', mutationReadiness.advisory_row_count ?? 0)
    + detailListLine('Blockers', mutationReadiness.blockers, ' | ')
    + detailLine('Blocker details', detailMessages(blockerDetails, mutationReadiness.blockers))
    + detailListLine('Reviewer fields', reviewerContextRequirements.required_fields, ' | ')
    + detailListLine('Accepted reviewer kinds', reviewerContextRequirements.accepted_reviewer_kinds, ' | ')
    + detailLine('Session label required', reviewerContextRequirements.session_label_required)
    + detailListLine('Next steps', mutationReadiness.next_steps, ' | ')
  );
}}
function renderOverviewAiIndexPanel(aiIndex, counts) {{
  const vectorEntryCount = aiIndex.vector && aiIndex.vector.entry_count ? aiIndex.vector.entry_count : 0;
  const graphNodeCount = aiIndex.graph && aiIndex.graph.node_count ? aiIndex.graph.node_count : 0;
  const graphEdgeCount = aiIndex.graph && aiIndex.graph.edge_count ? aiIndex.graph.edge_count : 0;
  return renderPanel(
    sectionTitle('AI Index Snapshot')
    + '<p>Vector entries: ' + esc(vectorEntryCount) + '</p>'
    + '<p>Graph nodes: ' + esc(graphNodeCount) + '</p>'
    + '<p>Graph edges: ' + esc(graphEdgeCount) + '</p>'
    + '<p>Runtime records: ' + esc(counts.runtime_records ?? 0) + '</p>'
    + '<p>Summary jobs: ' + esc(counts.summary_jobs ?? 0) + '</p>'
    + '<p>Needs-review records: ' + esc(counts.review_queue ?? 0) + '</p>'
  );
}}
function renderOverviewRuntimeRecordsPanel(counts, runtimeRecords) {{
  return renderPanel(
    sectionTitle('Runtime Records')
    + '<p>'
    + overviewJumpButton(sliceBadge('Runtime records', esc(counts.runtime_records ?? 0), 'badge-neutral'), '/api/runtime-records')
    + overviewJumpButton(sliceBadge('Provider response', esc(runtimeRecords.provider_response_present_count ?? 0), 'badge-ready'), '/api/runtime-records', 'runtimeRecords', 'response_id')
    + overviewJumpButton(sliceBadge('Runtime auth advisory', esc((runtimeRecords.auth_readiness_counts && runtimeRecords.auth_readiness_counts.advisory_only) ?? 0), 'badge-warning'), '/api/runtime-records', 'runtimeRecords', 'advisory_only')
    + '</p>'
    + summaryJsonLine('Runtime kinds', runtimeRecords.kind_counts)
    + summaryJsonLine('Auth readiness counts', runtimeRecords.auth_readiness_counts)
    + summaryJsonLine('Provider finish reasons', runtimeRecords.provider_response_finish_reason_counts)
    + summaryJsonLine('Provider statuses', runtimeRecords.provider_response_status_counts)
    + '<p>' + listJumpButton('Open Runtime Records', '/api/runtime-records') + '</p>'
  );
}}
function renderOverviewSummaryJobsPanel(counts, summaryJobs) {{
  return renderPanel(
    sectionTitle('Summary Jobs')
    + '<p>'
    + overviewJumpButton(sliceBadge('Summary jobs', esc(counts.summary_jobs ?? 0), 'badge-neutral'), '/api/summary-jobs')
    + overviewJumpButton(sliceBadge('Provider response', esc(summaryJobs.provider_response_present_count ?? 0), 'badge-ready'), '/api/summary-jobs', 'summaryJobs', 'response_id')
    + overviewJumpButton(sliceBadge('Summary advisory', esc((summaryJobs.review_capability_counts && summaryJobs.review_capability_counts.advisory_only) ?? 0), 'badge-warning'), '/api/summary-jobs', 'summaryJobs', 'advisory_only')
    + overviewJumpButton(sliceBadge('Summary auth advisory', esc((summaryJobs.auth_readiness_counts && summaryJobs.auth_readiness_counts.advisory_only) ?? 0), 'badge-warning'), '/api/summary-jobs', 'summaryJobs', 'advisory_only')
    + overviewJumpButton(sliceBadge('Summary package ready', esc((summaryJobs.package_readiness_counts && summaryJobs.package_readiness_counts.package_context_available) ?? 0), 'badge-ready'), '/api/summary-jobs', 'summaryJobs', 'package_context_available')
    + overviewJumpButton(sliceBadge('Summary identity aligned', esc((summaryJobs.identity_assurance_counts && summaryJobs.identity_assurance_counts.boundary_aligned) ?? 0), 'badge-ready'), '/api/summary-jobs', 'summaryJobs', 'boundary_aligned')
    + '</p>'
    + summaryJsonLine('Status counts', summaryJobs.status_counts)
    + summaryJsonLine('Review capability counts', summaryJobs.review_capability_counts)
    + summaryJsonLine('Auth readiness counts', summaryJobs.auth_readiness_counts)
    + summaryJsonLine('Package readiness counts', summaryJobs.package_readiness_counts)
    + summaryJsonLine('Provider finish reasons', summaryJobs.provider_response_finish_reason_counts)
    + summaryJsonLine('Provider statuses', summaryJobs.provider_response_status_counts)
    + summaryJsonLine('Identity assurance counts', summaryJobs.identity_assurance_counts)
    + summaryJsonLine('Reviewer kind counts', summaryJobs.reviewer_kind_counts)
    + summaryJsonLine('Runtime provider counts', summaryJobs.runtime_provider_counts)
    + detailLine('Source refs total', summaryJobs.summary_source_total ?? 0)
    + '<p>' + listJumpButton('Open Summary Jobs', '/api/summary-jobs') + '</p>'
  );
}}
function renderOverviewTriagePanel(triage, warningButtons, warningSummaries) {{
  return renderPanel(
    sectionTitle('Triage')
    + '<p>'
    + overviewJumpButton(sliceBadge('Needs attention', esc(triage.needs_attention_reviews ?? 0), 'badge-warning'), '/api/review-queue', 'reviewQueue', 'review_requested')
    + '</p>'
    + '<p>'
    + overviewJumpButton(sliceBadge('Review ready', esc(triage.ready_now_reviews ?? 0), 'badge-ready'), '/api/review-queue', 'reviewQueue', 'ready')
    + overviewJumpButton(sliceBadge('Review advisory', esc(triage.advisory_only_reviews ?? 0), 'badge-warning'), '/api/review-queue', 'reviewQueue', 'advisory')
    + '</p>'
    + '<p>'
    + overviewJumpButton(sliceBadge('Package ready', esc(triage.package_ready_reviews ?? 0), 'badge-ready'), '/api/review-queue', 'reviewQueue', 'package:package_context_available')
    + '</p>'
    + '<p>'
    + overviewJumpButton(sliceBadge('CLI aligned', esc(triage.cli_parity_aligned_reviews ?? 0), 'badge-ready'), '/api/review-queue', 'reviewQueue', 'aligned')
    + overviewJumpButton(sliceBadge('CLI drift', esc(triage.cli_parity_drift_reviews ?? 0), 'badge-warning'), '/api/review-queue', 'reviewQueue', 'drift_detected')
    + '</p>'
    + '<p>'
    + overviewJumpButton(sliceBadge('Identity aligned', esc(triage.identity_boundary_aligned_reviews ?? 0), 'badge-ready'), '/api/review-queue', 'reviewQueue', 'boundary_aligned')
    + overviewJumpButton(sliceBadge('Declared identity only', esc(triage.identity_declared_only_reviews ?? 0), 'badge-warning'), '/api/review-queue', 'reviewQueue', 'reviewer_identity_declared_only')
    + '</p>'
    + '<p>'
    + overviewJumpButton(sliceBadge('Provider response', esc(triage.provider_response_present_reviews ?? 0), 'badge-ready'), '/api/review-queue', 'reviewQueue', 'response_id')
    + '</p>'
    + '<p>' + (warningButtons || '') + '</p>'
    + summaryJsonLine('Runtime kinds', triage.runtime_record_kinds)
    + summaryJsonLine('Review capability counts', triage.review_capability_counts)
    + summaryJsonLine('Package readiness counts', triage.package_readiness_counts)
    + summaryJsonLine('CLI parity counts', triage.cli_parity_counts)
    + summaryJsonLine('Identity assurance counts', triage.identity_assurance_counts)
    + summaryJsonLine('Reviewer kind counts', triage.reviewer_kind_counts)
    + summaryJsonLine('Warning counts', triage.warning_counts)
    + '<p>Warning priority: '
    + (warningSummaries.length > 0
      ? warningSummaries.map(item =>
          sliceBadge((item.label || item.code || 'warning'), item.count ?? 0, 'badge-warning')
        ).join('')
      : '(none)')
    + '</p>'
    + '<p>' + listJumpButton('Open Review Queue', '/api/review-queue')
    + listJumpButton('Open Runtime Records', '/api/runtime-records')
    + listJumpButton('Open Summary Jobs', '/api/summary-jobs')
    + listJumpButton('Open Runtime Config', '/api/runtime-config')
    + listJumpButton('Open Package Review', '/api/package-review')
    + '<button data-reset-filters="all">Reset Filters</button></p>'
    + '<p>' + listJumpButton('Advisory Reviews', '/api/review-queue', 'reviewQueue', 'advisory')
    + listJumpButton('Package Ready Reviews', '/api/review-queue', 'reviewQueue', 'package:package_context_available')
    + listJumpButton('CLI Aligned Reviews', '/api/review-queue', 'reviewQueue', 'aligned')
    + listJumpButton('Identity Aligned Reviews', '/api/review-queue', 'reviewQueue', 'boundary_aligned')
    + listJumpButton('Auth Boundary Warnings', '/api/review-queue', 'reviewQueue', 'ui_auth_not_enabled')
    + listJumpButton('Declared Identity Only', '/api/review-queue', 'reviewQueue', 'reviewer_identity_declared_only')
    + listJumpButton('Retrieval Plans', '/api/runtime-records', 'runtimeRecords', 'retrieval_plan')
    + '</p>'
  );
}}
function overviewWarningButtons(warningSummaries) {{
  return warningSummaries.map(item =>
    overviewJumpButton(
      sliceBadge((item.label || item.code || 'warning'), item.count ?? 0, 'badge-warning'),
      '/api/review-queue',
      'reviewQueue',
      item.code || ''
    )
  ).join('');
}}
const overviewPanelRenderers = [
  data => renderOverviewHeaderPanel(data.chronicle),
  data => renderOverviewCountsPanel(data.counts),
  data => renderOverviewRuntimeBoundaryPanel(data.runtime),
  data => renderOverviewRuntimeConfigPanel(data.runtimeConfig, data.runtimeConfigContract),
  data => renderOverviewUiBoundaryPanel(data.uiBoundary),
  data => renderOverviewAuthBoundaryPanel(data.authBoundary, data.authBoundaryOverview),
  data => renderOverviewIdentityBoundaryPanel(data.identityBoundary),
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
  return rows ? routeHeading(endpoint) + renderTable(endpoint, rows) : routeHeading(endpoint) + prettyJsonPre(payload);
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
  renderDetailActionPreviewNotice,
  renderCliParityNotice,
  renderIdentityAssuranceNotice,
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
  return routeHeading(endpoint) + detailNoticeBody(endpoint, record) + prettyJsonPre(payload);
}}
async function loadEndpoint(endpoint) {{
  window.__chronicleCurrentEndpoint = endpoint;
  const response = await fetch(endpoint);
  const payload = await response.json();
  document.getElementById('view').innerHTML = endpointBody(endpoint, payload);
}}
async function loadDetail(endpoint) {{
  if (window.__chronicleLastDetail && window.__chronicleLastDetail !== endpoint) {{
    window.__chronicleDetailTrail.push(window.__chronicleLastDetail);
  }}
  window.__chronicleLastDetail = endpoint;
  const response = await fetch(endpoint);
  if (!response.ok) {{
    document.getElementById('detail').innerHTML = '<h2>Detail</h2><p>Not found.</p>';
    return;
  }}
  const payload = await response.json();
  document.getElementById('detail').innerHTML = detailBody(endpoint, payload);
}}
async function previewBlockedRoute(path, targetId = 'action-preview-response') {{
  const target = document.getElementById(targetId);
  if (!target) return;
  target.innerHTML = '<p>Loading blocked route preview…</p>';
  const {{ response, payload }} = await postJson(path);
  target.innerHTML = renderReviewActionResultPanel(
    'Blocked Route Preview',
    response.status,
    path,
    payload,
    targetId,
    {{
      extraLines: detailLine('Mutation enabled', payload.mutation_enabled),
    }},
  );
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
  target.innerHTML = '<p>Applying review action…</p>';
  const {{ response, payload }} = await postJson(path, reviewActionRequestBody(action, fieldPrefix));
  target.innerHTML = renderReviewActionResultPanel(
    'Review Action Result',
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
document.getElementById('view').addEventListener('input', handleViewInput);
document.getElementById('view').addEventListener('change', handleViewChange);
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
    service = ChronicleUIDataService(
        root,
        host=host,
        mutation_capability_flag=mutation_capability_flag,
        enable_ui_mutation=enable_ui_mutation,
        auth_mode=auth_mode,
        authorization_mode=authorization_mode,
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
            content_length = int(self.headers.get("Content-Length", "0") or 0)
            raw_body = self.rfile.read(content_length) if content_length > 0 else b"{}"
            try:
                body = json.loads(raw_body.decode("utf-8"))
            except json.JSONDecodeError:
                self._send_json(
                    {
                        "ok": False,
                        "status": "blocked",
                        "error_code": "invalid_json",
                        "message": service._review_action_failure_message("invalid_json"),
                        "mutation_enabled": service.ui_boundary()["ui_boundary"]["mutation_enabled"],
                        "failure_contract": service._review_action_failure_contract(
                            mutation_enabled=service.ui_boundary()["ui_boundary"]["mutation_enabled"],
                            error_code="invalid_json",
                        ),
                    },
                    status=HTTPStatus.BAD_REQUEST,
                )
                return
            if not isinstance(body, dict):
                self._send_json(
                    {
                        "ok": False,
                        "status": "blocked",
                        "error_code": "invalid_request_body",
                        "message": "Request body must be a JSON object.",
                        "mutation_enabled": service.ui_boundary()["ui_boundary"]["mutation_enabled"],
                    },
                    status=HTTPStatus.BAD_REQUEST,
                )
                return
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
