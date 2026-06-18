"""Explicit foreground local web UI for Chronicle Stack.

This module intentionally uses Python stdlib only. It serves read-only views over
local Chronicle files and must not be confused with a daemon, hosted service,
model runtime, GraphRAG engine, vector DB, or graph DB.
"""

from __future__ import annotations

import html
import ipaddress
import json
import webbrowser
from dataclasses import asdict, dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from chronicle.errors import ChronicleError, UIHostNotLoopbackError
from chronicle.exporters.html_exporter import HtmlDashboardExporter
from chronicle.models.runtime import RuntimeRetrievalPlan
from chronicle.models.review import ReviewerIdentity
from chronicle.services.audit_service import AuditService
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.graph_index_service import GraphIndexService
from chronicle.services.graph_export_service import GraphExportService
from chronicle.services.integration_package_service import IntegrationPackageService
from chronicle.services.lifecycle_service import LifecycleService
from chronicle.services.package_review_service import PackageReviewService
from chronicle.services.review_service import ReviewService
from chronicle.services.runtime_service import RuntimeService
from chronicle.services.vector_index_service import VectorIndexService

DEFAULT_UI_HOST = "127.0.0.1"
DEFAULT_UI_PORT = 8765
REVIEW_WARNING_TEXT: dict[str, str] = {
    "ui_auth_not_enabled": "UI auth mode is not enabled, so reviewer identity is not enforced by the local UI boundary.",
    "ui_authorization_not_enabled": "UI authorization mode is not enabled, so reviewer permissions remain advisory only.",
    "no_reviewer_identity_recorded": "No reviewer identity metadata is available for this pending target yet.",
    "reviewer_identity_declared_only": "Reviewer identity is self-declared and has not been strengthened by a local auth boundary.",
    "reviewer_session_label_missing": "Session-gated review expects a local session label, but none was recorded.",
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
    auth_mode: str = UIAuthMode.NOT_ENABLED,
    authorization_mode: str = UIAuthorizationMode.NOT_ENABLED,
) -> UIStartupMetadata:
    """Build local UI startup metadata without starting the server."""
    ui_boundary = build_ui_boundary_metadata(
        host=host,
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
        auth_mode=ui_boundary.auth_mode,
        authorization_mode=ui_boundary.authorization_mode,
        ui_boundary=ui_boundary,
    )


def build_ui_boundary_metadata(
    *,
    host: str = DEFAULT_UI_HOST,
    auth_mode: str = UIAuthMode.NOT_ENABLED,
    authorization_mode: str = UIAuthorizationMode.NOT_ENABLED,
) -> UIBoundaryMetadata:
    """Build explicit UI boundary metadata."""
    return UIBoundaryMetadata(
        bind_scope=_bind_scope(host),
        auth_mode=auth_mode,
        authorization_mode=authorization_mode,
        session_gating=auth_mode == UIAuthMode.LOOPBACK_LOCAL,
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


class ChronicleUIDataService:
    """Read-only data provider for the local UI."""

    def __init__(
        self,
        root: Path | None = None,
        *,
        host: str = DEFAULT_UI_HOST,
        auth_mode: str = UIAuthMode.NOT_ENABLED,
        authorization_mode: str = UIAuthorizationMode.NOT_ENABLED,
    ) -> None:
        self.root = root or Path.cwd()
        self.host = host
        self.auth_mode = auth_mode
        self.authorization_mode = authorization_mode
        self.chronicle = ChronicleService(self.root)
        self.audit = AuditService(self.root)
        self.lifecycle = LifecycleService(self.root)
        self.packages = IntegrationPackageService(self.root)
        self.package_review = PackageReviewService(self.root)
        self.review = ReviewService(self.root)
        self.runtime = RuntimeService(self.root)
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
        ai_index_status = self.ai_index_status()["ai_index_status"]
        triage = self.overview_triage(runtime_records, review_queue)
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
                "vector_index_entries": ai_index_status["vector"]["entry_count"],
                "graph_index_nodes": ai_index_status["graph"]["node_count"],
                "graph_index_edges": ai_index_status["graph"]["edge_count"],
            },
            "package_review": self.package_review_snapshot(),
            "graph_summary": self.graph_summary(),
            "ai_index": ai_index_status,
            "triage": triage,
            "runtime_boundary": self.runtime_boundary(),
            "ui_boundary": self.ui_boundary()["ui_boundary"],
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
        ready_now = 0
        advisory_only = 0
        package_ready = 0

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

        return {
            "runtime_record_kinds": runtime_by_kind,
            "review_capability_counts": review_capability_counts,
            "package_readiness_counts": readiness_counts,
            "ready_now_reviews": ready_now,
            "advisory_only_reviews": advisory_only,
            "package_ready_reviews": package_ready,
            "needs_attention_reviews": len(review_queue),
        }

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
                or "runtime_retrieval_plan" in event.payload
            )
        ]
        rows: list[dict[str, Any]] = []
        for event in reversed(events[-limit:]):
            data = _dump_model(event)
            preview = self.runtime.record_preview(event)
            data["runtime_record_kind"] = preview.record_kind
            data["runtime_record_preview"] = preview.model_dump(mode="json")
            rows.append(data)
        return {"runtime_records": rows}

    def review_queue(self, *, limit: int = 100) -> dict[str, Any]:
        self.chronicle.require_initialized()
        boundary = self.ui_boundary()["ui_boundary"]
        rows: list[dict[str, Any]] = []
        for entry in self.review.queue()[:limit]:
            data = entry.model_dump(mode="json")
            data["suggested_cli_family"] = self._suggested_cli_family_from_kind(entry.review_kind)
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
            readiness = self.review_package_readiness(entry.target_event_id)
            data["package_readiness_summary"] = self._package_readiness_summary(readiness)
            data["ui_mutation_enabled"] = False
            data["review_preview_only"] = True
            rows.append(data)
        return {"review_queue": rows}

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

    def ui_boundary(self) -> dict[str, Any]:
        metadata = build_ui_boundary_metadata(
            host=self.host,
            auth_mode=self.auth_mode,
            authorization_mode=self.authorization_mode,
        )
        return {"ui_boundary": asdict(metadata)}

    @staticmethod
    def _review_kind(payload: dict[str, Any]) -> str:
        if "runtime_summary" in payload:
            return "runtime_summary"
        if "runtime_retrieval_plan" in payload:
            return "runtime_retrieval_plan"
        return "assistant_output"

    @staticmethod
    def _suggested_cli_family(payload: dict[str, Any]) -> str:
        if "runtime_summary" in payload:
            return "chronicle runtime summarize --record"
        if "runtime_retrieval_plan" in payload:
            return "chronicle runtime retrieve-plan --record"
        return "chronicle show --json"

    @staticmethod
    def _suggested_cli_family_from_kind(review_kind: str) -> str:
        if review_kind == "runtime_summary":
            return "chronicle runtime summarize --record"
        if review_kind == "runtime_retrieval_plan":
            return "chronicle runtime retrieve-plan --record"
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
            "warning_details": [
                {"code": warning, "message": self._warning_message(warning)}
                for warning in warnings
            ],
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
    def _warning_message(code: str) -> str:
        return REVIEW_WARNING_TEXT.get(code, code.replace("_", " "))

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
            if "runtime_summary" not in payload and "runtime_retrieval_plan" not in payload:
                return None
            preview = self.runtime.record_preview(event)
            record["runtime_record_kind"] = preview.record_kind
            record["runtime_record_preview"] = preview.model_dump(mode="json")
            record["suggested_cli_family"] = preview.suggested_cli_family
            if "runtime_retrieval_plan" in payload:
                plan = RuntimeRetrievalPlan.model_validate(payload["runtime_retrieval_plan"])
                record["retrieval_handoff"] = self.runtime.retrieval_handoff(plan).model_dump(mode="json")
                record["package_handoff_preview"] = self.runtime_package_handoff(plan)
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
                    row["ui_mutation_enabled"] = False
                    row["review_preview_only"] = True
                    return {"record": row}
            return None

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
            "/api/ui-boundary": self.ui_boundary,
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

    def html_shell(self) -> str:
        metadata = self.chronicle.require_initialized()
        title = html.escape(metadata.title)
        root = html.escape(str(self.root.resolve()))
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
  <button data-endpoint="/api/ui-boundary">UI Boundary</button>
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
const idFields = ['event_id', 'context_id', 'artifact_id', 'decision_id', 'rde_record_id', 'rule_id', 'audit_id', 'lifecycle_id', 'record_id', 'node_id'];
function esc(value) {{ return String(value).replace(/[&<>\"']/g, ch => ({{'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}}[ch])); }}
function firstArray(payload) {{ for (const key of Object.keys(payload)) if (Array.isArray(payload[key])) return payload[key]; return null; }}
function badge(text, cls) {{ return '<span class="badge ' + cls + '">' + esc(text) + '</span>'; }}
function renderOverview(payload) {{
  const chronicle = payload.chronicle || {{}};
  const counts = payload.counts || {{}};
  const runtime = payload.runtime_boundary || {{}};
  const uiBoundary = payload.ui_boundary || {{}};
  const aiIndex = payload.ai_index || {{}};
  const triage = payload.triage || {{}};
  const countRows = Object.entries(counts).map(([key, value]) =>
    '<tr><th>' + esc(key) + '</th><td>' + esc(value ?? '') + '</td></tr>'
  ).join('');
  const vectorEntryCount = aiIndex.vector && aiIndex.vector.entry_count ? aiIndex.vector.entry_count : 0;
  const graphNodeCount = aiIndex.graph && aiIndex.graph.node_count ? aiIndex.graph.node_count : 0;
  const graphEdgeCount = aiIndex.graph && aiIndex.graph.edge_count ? aiIndex.graph.edge_count : 0;
  return ''
    + '<h2>/api/overview</h2>'
    + '<div class="panel">'
    + '<p><strong>' + esc(chronicle.title || '') + '</strong></p>'
    + '<p>Chronicle ID: <span class="id">' + esc(chronicle.id || '') + '</span></p>'
    + '<p>Root: <span class="id">' + esc(chronicle.root || '') + '</span></p>'
    + '</div>'
    + '<div class="panel">'
    + '<h3>Counts</h3>'
    + '<table><tbody>' + countRows + '</tbody></table>'
    + '</div>'
    + '<div class="panel">'
    + '<h3>Runtime Boundary</h3>'
    + '<p>Read-only: ' + esc(runtime.read_only) + '</p>'
    + '<p>External model API: ' + esc(runtime.external_model_api) + '</p>'
    + '<p>GraphRAG runtime: ' + esc(runtime.graphrag_runtime) + '</p>'
    + '<p>Vector DB: ' + esc(runtime.vector_db) + '</p>'
    + '<p>Graph DB: ' + esc(runtime.graph_db) + '</p>'
    + '</div>'
    + '<div class="panel">'
    + '<h3>UI Boundary</h3>'
    + '<p>Bind scope: ' + esc(uiBoundary.bind_scope || '') + '</p>'
    + '<p>Mutation enabled: ' + esc(uiBoundary.mutation_enabled) + '</p>'
    + '<p>Auth mode: ' + esc(uiBoundary.auth_mode || '') + '</p>'
    + '<p>Authorization mode: ' + esc(uiBoundary.authorization_mode || '') + '</p>'
    + '<p>Session gating: ' + esc(uiBoundary.session_gating) + '</p>'
    + '</div>'
    + '<div class="panel">'
    + '<h3>AI Index Snapshot</h3>'
    + '<p>Vector entries: ' + esc(vectorEntryCount) + '</p>'
    + '<p>Graph nodes: ' + esc(graphNodeCount) + '</p>'
    + '<p>Graph edges: ' + esc(graphEdgeCount) + '</p>'
    + '<p>Runtime records: ' + esc(counts.runtime_records ?? 0) + '</p>'
    + '<p>Needs-review records: ' + esc(counts.review_queue ?? 0) + '</p>'
    + '</div>'
    + '<div class="panel">'
    + '<h3>Triage</h3>'
    + '<p>' + badge('Needs attention: ' + esc(triage.needs_attention_reviews ?? 0), 'badge-warning') + '</p>'
    + '<p>' + badge('Review ready: ' + esc(triage.ready_now_reviews ?? 0), 'badge-ready')
    + badge('Review advisory: ' + esc(triage.advisory_only_reviews ?? 0), 'badge-warning') + '</p>'
    + '<p>' + badge('Package ready: ' + esc(triage.package_ready_reviews ?? 0), 'badge-ready') + '</p>'
    + '<p>Runtime kinds: ' + esc(JSON.stringify(triage.runtime_record_kinds || {{}})) + '</p>'
    + '<p>Review capability counts: ' + esc(JSON.stringify(triage.review_capability_counts || {{}})) + '</p>'
    + '<p>Package readiness counts: ' + esc(JSON.stringify(triage.package_readiness_counts || {{}})) + '</p>'
    + '<p><button data-jump="/api/review-queue">Open Review Queue</button>'
    + '<button data-jump="/api/runtime-records">Open Runtime Records</button>'
    + '<button data-jump="/api/package-review">Open Package Review</button></p>'
    + '</div>';
}}
function detailPath(endpoint, row) {{
  if (endpoint === '/api/ai-index-graph-edges') return null;
  if (endpoint === '/api/ai-index-vector' && row.record_id) return '/api/ai-index/vector/' + encodeURIComponent(row.record_id);
  if (endpoint === '/api/ai-index-graph-nodes' && row.node_id) return '/api/ai-index/graph-nodes/' + encodeURIComponent(row.node_id);
  if (endpoint === '/api/runtime-records' && row.event_id) return '/api/runtime-records/' + encodeURIComponent(row.event_id);
  if (endpoint === '/api/review-queue' && row.event_id) return '/api/review-queue/' + encodeURIComponent(row.event_id);
  for (const key of idFields) if (row[key]) return endpoint + '/' + encodeURIComponent(row[key]);
  return null;
}}
function renderTable(endpoint, rows) {{
  if (!rows || rows.length === 0) return '<p>No records.</p>';
  if (endpoint === '/api/runtime-records') {{
    return '<table><thead><tr><th>detail</th><th>event</th><th>kind</th><th>preview</th><th>source counts</th></tr></thead><tbody>'
      + rows.map(row => {{
        const path = detailPath(endpoint, row);
        const button = path ? '<button data-detail="' + esc(path) + '">JSON</button>' : '';
        const preview = row.runtime_record_preview || {{}};
        return '<tr>'
          + '<td>' + button + '</td>'
          + '<td><span class="id">' + esc(row.event_id || '') + '</span></td>'
          + '<td>' + esc(row.runtime_record_kind || '') + '</td>'
          + '<td><strong>' + esc(preview.title || '') + '</strong><br>' + esc(preview.preview_text || '') + '</td>'
          + '<td>' + esc(JSON.stringify(preview.source_counts || {{}})) + '</td>'
          + '</tr>';
      }}).join('') + '</tbody></table>';
  }}
  if (endpoint === '/api/review-queue') {{
    return '<table><thead><tr><th>detail</th><th>target</th><th>status</th><th>warnings</th><th>latest reviewer</th></tr></thead><tbody>'
      + rows.map(row => {{
        const path = detailPath(endpoint, row);
        const button = path ? '<button data-detail="' + esc(path) + '">JSON</button>' : '';
        const capability = row.review_capability || {{}};
        const readiness = row.package_readiness_summary || {{}};
        const warnList = Array.isArray(capability.warnings) ? capability.warnings : [];
        const warnDetails = Array.isArray(capability.warning_details) ? capability.warning_details : [];
        const statusBadge = capability.status === 'ready'
          ? badge('Ready', 'badge-ready')
          : capability.status === 'resolved'
            ? badge('Resolved', 'badge-neutral')
            : badge('Advisory', 'badge-warning');
        const readinessBadge = readiness.status === 'package_context_available'
          ? badge(readiness.label || 'Package Ready', 'badge-ready')
          : readiness.status === 'no_context_records'
            ? badge(readiness.label || 'Package Advisory', 'badge-warning')
            : badge(readiness.label || 'Package Unknown', 'badge-neutral');
        return '<tr>'
          + '<td>' + button + '</td>'
          + '<td><span class="id">' + esc(row.target_event_id || '') + '</span><br>' + esc(row.target_summary || '') + '</td>'
          + '<td>' + statusBadge + '<br>' + readinessBadge + '</td>'
          + '<td>' + esc(warnDetails.map(item => item.message).join(' | ') || warnList.join(', ') || '(none)') + '</td>'
          + '<td>' + esc((row.latest_reviewer_identity && row.latest_reviewer_identity.label) || row.latest_reviewer || '') + '</td>'
          + '</tr>';
      }}).join('') + '</tbody></table>';
  }}
  const keys = Object.keys(rows[0]).slice(0, 8);
  return '<table><thead><tr><th>detail</th>' + keys.map(k => '<th>' + esc(k) + '</th>').join('') + '</tr></thead><tbody>' +
    rows.map(row => {{
      const path = detailPath(endpoint, row);
      const button = path ? '<button data-detail="' + esc(path) + '">JSON</button>' : '';
      return '<tr><td>' + button + '</td>' + keys.map(k => '<td>' + esc(typeof row[k] === 'object' ? JSON.stringify(row[k]) : row[k] ?? '') + '</td>').join('') + '</tr>';
    }}).join('') + '</tbody></table>';
}}
async function loadEndpoint(endpoint) {{
  const response = await fetch(endpoint);
  const payload = await response.json();
  if (endpoint === '/api/overview') {{
    document.getElementById('view').innerHTML = renderOverview(payload);
    return;
  }}
  const rows = firstArray(payload);
  const body = rows ? renderTable(endpoint, rows) : '<pre>' + esc(JSON.stringify(payload, null, 2)) + '</pre>';
  document.getElementById('view').innerHTML = '<h2>' + esc(endpoint) + '</h2>' + body;
}}
async function loadDetail(endpoint) {{
  const response = await fetch(endpoint);
  if (!response.ok) {{
    document.getElementById('detail').innerHTML = '<h2>Detail</h2><p>Not found.</p>';
    return;
  }}
  const payload = await response.json();
  const record = payload.record || {{}};
  let extra = '';
  if (record.runtime_record_preview) {{
    const preview = record.runtime_record_preview;
    extra += '<div class="notice"><h3>Runtime Preview</h3>'
      + '<p><strong>' + esc(preview.title || '') + '</strong></p>'
      + '<p>' + esc(preview.preview_text || '') + '</p>'
      + '<p>Kind: ' + esc(preview.record_kind || record.runtime_record_kind || '') + '</p>'
      + '<p>Source counts: ' + esc(JSON.stringify(preview.source_counts || {{}})) + '</p>'
      + '<p>Referenced IDs: ' + esc((preview.referenced_record_ids || []).join(', ') || '(none)') + '</p>'
      + '<p>CLI: ' + esc(preview.suggested_cli_family || '') + '</p>'
      + '</div>';
  }}
  if (record.retrieval_handoff) {{
    const handoff = record.retrieval_handoff;
    extra += '<div class="notice"><h3>Retrieval Handoff</h3>'
      + '<p>Query: ' + esc(handoff.query || '') + '</p>'
      + '<p>Hit counts: vector=' + esc(handoff.vector_hit_count || 0)
      + ', graph=' + esc(handoff.graph_hit_count || 0)
      + ', chronicle=' + esc(handoff.chronicle_hit_count || 0) + '</p>'
      + '<p>Referenced IDs: ' + esc((handoff.referenced_record_ids || []).join(', ') || '(none)') + '</p>'
      + '<p>Downstream commands: ' + esc((handoff.downstream_commands || []).join(' | ')) + '</p>'
      + '<p>Notes: ' + esc((handoff.notes || []).join(' | ')) + '</p>'
      + '</div>';
  }}
  if (record.package_handoff_preview) {{
    const preview = record.package_handoff_preview;
    const packageReview = preview.package_review || {{}};
    const manifest = preview.package_manifest_preview || {{}};
    extra += '<div class="notice"><h3>Package Handoff Preview</h3>'
      + '<p>Status: ' + esc(preview.status || '') + '</p>'
      + '<p>' + esc(preview.message || '') + '</p>'
      + '<p>Eligible contexts: ' + esc((preview.eligible_context_ids || []).join(', ') || '(none)') + '</p>'
      + '<p>Skipped records: ' + esc((preview.skipped_record_ids || []).join(', ') || '(none)') + '</p>'
      + '<p>Package review status: ' + esc(packageReview.status || '(not available)') + '</p>'
      + '<p>Package warnings: ' + esc((packageReview.package_warnings || []).join(', ') || '(none)') + '</p>'
      + '<p>Manifest refs: ' + esc((manifest.referenced_records || []).join(', ') || '(none)') + '</p>'
      + '</div>';
  }}
  if (record.package_readiness) {{
    const readiness = record.package_readiness;
    const packageReview = readiness.package_review || {{}};
    const manifest = readiness.package_manifest_preview || {{}};
    extra += '<div class="notice"><h3>Review Package Readiness</h3>'
      + '<p>Status: ' + esc(readiness.status || '') + '</p>'
      + '<p>' + esc(readiness.message || '') + '</p>'
      + '<p>Eligible contexts: ' + esc((readiness.eligible_context_ids || []).join(', ') || '(none)') + '</p>'
      + '<p>Suggested commands: ' + esc((readiness.suggested_commands || []).join(' | ') || '(none)') + '</p>'
      + '<p>Package review status: ' + esc(packageReview.status || '(not available)') + '</p>'
      + '<p>Package warnings: ' + esc((packageReview.package_warnings || []).join(', ') || '(none)') + '</p>'
      + '<p>Manifest refs: ' + esc((manifest.referenced_records || []).join(', ') || '(none)') + '</p>'
      + '</div>';
  }}
  if (record.review_capability) {{
    const capability = record.review_capability;
    const warnList = Array.isArray(capability.warnings) ? capability.warnings : [];
    const warnDetails = Array.isArray(capability.warning_details) ? capability.warning_details : [];
    extra += '<div class="notice"><h3>Review Capability</h3>'
      + '<p>' + esc(capability.message || '') + '</p>'
      + '<p>Status: ' + esc(capability.status || '') + '</p>'
      + '<p>Warnings: ' + esc(warnDetails.map(item => item.message).join(' | ') || warnList.join(', ') || '(none)') + '</p></div>';
  }}
  if (record.latest_identity_assurance) {{
    const assurance = record.latest_identity_assurance;
    extra += '<div class="notice"><h3>Identity Assurance</h3>'
      + '<p>Status: ' + esc(assurance.status || '') + '</p>'
      + '<p>' + esc(assurance.message || '') + '</p></div>';
  }}
  if (Array.isArray(record.history) && record.history.length > 0) {{
    extra += '<div class="notice"><h3>Review Timeline</h3><ul>'
      + record.history.map(item => '<li>'
        + esc(item.reviewed_at || '') + ' — '
        + esc(item.disposition || '') + ' by '
        + esc((item.reviewer_identity && item.reviewer_identity.label) || item.reviewer || '')
        + ' (' + esc((item.identity_assurance && item.identity_assurance.status) || '') + ')'
        + '</li>').join('')
      + '</ul></div>';
  }}
  document.getElementById('detail').innerHTML =
    '<h2>' + esc(endpoint) + '</h2>' + extra + '<pre>' + esc(JSON.stringify(payload, null, 2)) + '</pre>';
}}
document.querySelectorAll('button[data-endpoint]').forEach(button => button.addEventListener('click', () => loadEndpoint(button.dataset.endpoint)));
document.getElementById('view').addEventListener('click', event => {{
  if (event.target.dataset.detail) loadDetail(event.target.dataset.detail);
  if (event.target.dataset.jump) loadEndpoint(event.target.dataset.jump);
}});
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
    auth_mode: str = UIAuthMode.NOT_ENABLED,
    authorization_mode: str = UIAuthorizationMode.NOT_ENABLED,
) -> type[BaseHTTPRequestHandler]:
    service = ChronicleUIDataService(
        root,
        host=host,
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

        def log_message(self, format: str, *args: object) -> None:
            return

        def _send_html(self, body: str) -> None:
            payload = body.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def _send_json(self, body: dict[str, Any]) -> None:
            payload = json.dumps(body, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(HTTPStatus.OK)
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
    auth_mode: str = UIAuthMode.NOT_ENABLED,
    authorization_mode: str = UIAuthorizationMode.NOT_ENABLED,
) -> ThreadingHTTPServer:
    return ThreadingHTTPServer(
        (host, port),
        create_handler(
            root,
            host=host,
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
        auth_mode=auth_mode,
        authorization_mode=authorization_mode,
    )
    server = make_server(
        host=host,
        port=port,
        root=root_path,
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
