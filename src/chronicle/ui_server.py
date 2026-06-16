"""Explicit foreground local web UI for Chronicle Stack.

This module intentionally uses Python stdlib only. It serves read-only views over
local Chronicle files and must not be confused with a daemon, hosted service,
access-control layer, model runtime, GraphRAG engine, vector DB, or graph DB.
"""

from __future__ import annotations

import html
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


def _dump_model(model: object) -> dict[str, Any]:
    return model.model_dump(mode="json")  # type: ignore[attr-defined]


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
            "package_review": self.package_review_snapshot(),
            "graph_summary": self.graph_summary(),
            "runtime_boundary": self.runtime_boundary(),
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
        rde_records = sorted(self.chronicle.index.load_rde_records().values(), key=lambda item: item.created_at)
        return {"rde_records": [_dump_model(record) for record in rde_records]}

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

    def package_review_snapshot(self) -> dict[str, Any]:
        try:
            review_report = self.package_review.review_context_package(purpose="chronicle ui overview")
            return review_report.model_dump(mode="json")
        except Exception as exc:  # pragma: no cover - defensive UI degradation
            return {"status": "unavailable", "error": str(exc)}

    def graph_summary(self) -> dict[str, Any]:
        try:
            graph = GraphExportService(self.root).export_graph()
            return {"nodes": len(graph.nodes), "edges": len(graph.edges)}
        except Exception as exc:  # pragma: no cover - defensive UI degradation
            return {"nodes": 0, "edges": 0, "error": str(exc)}

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
            "access_control": False,
            "correctness_proof": False,
        }

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
            "/api/package-review": lambda: {"package_review": self.package_review_snapshot()},
            "/api/graph-summary": lambda: {"graph_summary": self.graph_summary()},
        }
        handler = routes.get(path)
        return handler() if handler else None

    def html_shell(self) -> str:
        """Return the interactive local UI shell."""
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
h1 {{ border-bottom: 2px solid #2563eb; padding-bottom: 8px; }}
nav {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 16px 0; }}
button {{ border: 1px solid #d1d5db; background: #fff; border-radius: 6px; padding: 8px 10px; cursor: pointer; }}
button:hover {{ background: #f9fafb; }}
.panel {{ border: 1px solid #e5e7eb; border-radius: 8px; padding: 14px; margin: 12px 0; background: #fff; }}
.warning {{ background: #fefce8; border-left: 4px solid #eab308; padding: 10px 12px; border-radius: 0 4px 4px 0; }}
.cards {{ display: flex; flex-wrap: wrap; gap: 12px; }}
.card {{ border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px; min-width: 120px; }}
.count {{ font-size: 1.8em; font-weight: bold; color: #2563eb; }}
.label {{ color: #6b7280; font-size: 0.85em; }}
pre {{ white-space: pre-wrap; word-break: break-word; background: #f9fafb; padding: 12px; border-radius: 8px; border: 1px solid #e5e7eb; }}
table {{ width: 100%; border-collapse: collapse; }}
th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #e5e7eb; vertical-align: top; }}
th {{ background: #f9fafb; }}
.id {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.85em; }}
</style>
</head>
<body>
<h1>Chronicle Stack Local UI</h1>
<p><strong>{title}</strong></p>
<p>Root: <span class="id">{root}</span></p>
<div class="warning">
  <p><strong>Read-only foreground local UI.</strong> This UI reads local Chronicle files and does not write records.</p>
  <p>No daemon, no autostart, no external model API, no GraphRAG runtime, no vector DB, no graph DB. UI visibility is not access control or correctness proof.</p>
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
  <button data-endpoint="/api/package-review">Package Review</button>
  <button data-endpoint="/api/graph-summary">Graph Summary</button>
</nav>
<section id="summary" class="panel"></section>
<section id="view" class="panel"><p>Loading overview...</p></section>
<script>
function escapeHtml(value) {{
  return String(value).replace(/[&<>\"']/g, function(ch) {{
    return {{'&': '&amp;', '<': '&lt;', '>': '&gt;', '\"': '&quot;', "'": '&#39;'}}[ch];
  }});
}}
function renderCards(counts) {{
  return '<div class="cards">' + Object.keys(counts).map(function(key) {{
    return '<div class="card"><div class="count">' + escapeHtml(counts[key]) + '</div><div class="label">' + escapeHtml(key) + '</div></div>';
  }}).join('') + '</div>';
}}
function renderTable(rows) {{
  if (!Array.isArray(rows) || rows.length === 0) return '<p>No records.</p>';
  const keys = Object.keys(rows[0]).slice(0, 8);
  return '<table><thead><tr>' + keys.map(k => '<th>' + escapeHtml(k) + '</th>').join('') + '</tr></thead><tbody>' +
    rows.map(row => '<tr>' + keys.map(k => '<td>' + escapeHtml(typeof row[k] === 'object' ? JSON.stringify(row[k]) : row[k] ?? '') + '</td>').join('') + '</tr>').join('') +
    '</tbody></table>';
}}
function firstArray(payload) {{
  for (const key of Object.keys(payload)) if (Array.isArray(payload[key])) return payload[key];
  return null;
}}
async function loadEndpoint(endpoint) {{
  const response = await fetch(endpoint);
  const payload = await response.json();
  if (payload.counts) document.getElementById('summary').innerHTML = '<h2>Summary</h2>' + renderCards(payload.counts);
  const rows = firstArray(payload);
  let body = rows ? renderTable(rows) : '<pre>' + escapeHtml(JSON.stringify(payload, null, 2)) + '</pre>';
  document.getElementById('view').innerHTML = '<h2>' + escapeHtml(endpoint) + '</h2>' + body;
}}
document.querySelectorAll('button[data-endpoint]').forEach(button => {{
  button.addEventListener('click', () => loadEndpoint(button.dataset.endpoint));
}});
loadEndpoint('/api/overview');
</script>
</body>
</html>"""

    def static_review_console(self) -> str:
        return HtmlDashboardExporter(self.root).export()


def create_handler(root: Path | None = None) -> type[BaseHTTPRequestHandler]:
    """Create a request handler class bound to a Chronicle root."""
    service = ChronicleUIDataService(root)

    class ChronicleUIRequestHandler(BaseHTTPRequestHandler):
        server_version = "ChronicleUILocal/0.2"

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
