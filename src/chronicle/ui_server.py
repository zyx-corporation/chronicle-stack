"""Explicit foreground local web UI for Chronicle Stack.

This module intentionally uses Python stdlib only. It serves read-only views over
local Chronicle files and must not be confused with a daemon, hosted service,
access-control layer, model runtime, GraphRAG engine, vector DB, or graph DB.
"""

from __future__ import annotations

import json
import webbrowser
from dataclasses import asdict, dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from chronicle.errors import ChronicleError
from chronicle.exporters.html_exporter import HtmlDashboardExporter
from chronicle.services.audit_service import AuditService
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.graph_export_service import GraphExportService
from chronicle.services.lifecycle_service import LifecycleService
from chronicle.services.package_review_service import PackageReviewService

DEFAULT_UI_HOST = "127.0.0.1"
DEFAULT_UI_PORT = 8765


@dataclass(frozen=True)
class UIStartupMetadata:
    """Startup metadata printed by `chronicle ui --json`."""

    host: str
    port: int
    url: str
    root: str
    read_only: bool = True
    runtime: str = "foreground-local-ui"
    external_runtime: bool = False

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)


def build_startup_metadata(*, host: str, port: int, root: Path) -> UIStartupMetadata:
    """Build local UI startup metadata without starting the server."""
    return UIStartupMetadata(
        host=host,
        port=port,
        url=f"http://{host}:{port}",
        root=str(root.resolve()),
    )


class ChronicleUIDataService:
    """Read-only data provider for the local UI."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path.cwd()
        self.chronicle = ChronicleService(self.root)
        self.audit = AuditService(self.root)
        self.lifecycle = LifecycleService(self.root)
        self.package_review = PackageReviewService(self.root)

    def overview(self) -> dict[str, Any]:
        """Return a minimal local UI overview document."""
        metadata = self.chronicle.require_initialized()
        events = self.chronicle.jsonl.read_all()
        artifacts, _ = self.chronicle.index.load_artifacts()
        contexts = self.chronicle.index.load_contexts()
        decisions = self.chronicle.index.load_decisions()
        rde_records = self.chronicle.index.load_rde_records()
        boundary_rules = self.chronicle.index.load_boundary_rules()
        audit_events = self.audit.list_events()
        lifecycle_events = self.lifecycle.list_events()
        try:
            review_report = self.package_review.review_context_package(purpose="chronicle ui overview")
            package_review = review_report.model_dump(mode="json")
        except Exception as exc:  # pragma: no cover - defensive UI degradation
            package_review = {"status": "unavailable", "error": str(exc)}
        try:
            graph = GraphExportService(self.root).export_graph()
            graph_summary = {"nodes": len(graph.nodes), "edges": len(graph.edges)}
        except Exception as exc:  # pragma: no cover - defensive UI degradation
            graph_summary = {"nodes": 0, "edges": 0, "error": str(exc)}

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
            },
            "package_review": package_review,
            "graph_summary": graph_summary,
            "runtime_boundary": {
                "read_only": True,
                "foreground_process": True,
                "daemon": False,
                "server_default_host": DEFAULT_UI_HOST,
                "external_model_api": False,
                "graphrag_runtime": False,
                "vector_db": False,
                "graph_db": False,
                "access_control": False,
                "correctness_proof": False,
            },
        }

    def html_shell(self) -> str:
        """Return the initial UI shell.

        The first implementation reuses the static Review Console body to avoid a
        second UI language. Later phases can add client-side drill-downs.
        """
        return HtmlDashboardExporter(self.root).export()


def create_handler(root: Path | None = None) -> type[BaseHTTPRequestHandler]:
    """Create a request handler class bound to a Chronicle root."""
    service = ChronicleUIDataService(root)

    class ChronicleUIRequestHandler(BaseHTTPRequestHandler):
        server_version = "ChronicleUILocal/0.1"

        def do_GET(self) -> None:  # noqa: N802 - stdlib API
            parsed = urlparse(self.path)
            if parsed.path in ("/", "/index.html"):
                self._send_html(service.html_shell())
                return
            if parsed.path == "/api/overview":
                self._send_json(service.overview())
                return
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")

        def log_message(self, format: str, *args: object) -> None:
            """Suppress default request logs for cleaner foreground CLI output."""
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


def make_server(*, host: str = DEFAULT_UI_HOST, port: int = DEFAULT_UI_PORT, root: Path | None = None) -> ThreadingHTTPServer:
    """Create the local UI server without starting it."""
    return ThreadingHTTPServer((host, port), create_handler(root))


def serve_ui(
    *,
    host: str = DEFAULT_UI_HOST,
    port: int = DEFAULT_UI_PORT,
    root: Path | None = None,
    open_browser: bool = False,
) -> UIStartupMetadata:
    """Start the foreground local UI server.

    This function blocks until interrupted by the user. It returns only if the
    server exits normally, which is mainly useful for tests around setup failure.
    """
    root_path = root or Path.cwd()
    service = ChronicleService(root_path)
    service.require_initialized()
    metadata = build_startup_metadata(host=host, port=port, root=root_path)
    server = make_server(host=host, port=port, root=root_path)
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
    """Validate that the target root is an initialized Chronicle."""
    try:
        ChronicleService(root).require_initialized()
    except ChronicleError:
        raise
