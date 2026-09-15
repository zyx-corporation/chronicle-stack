"""Explicit loopback Chronicle API daemon MVP.

The daemon is a small HTTP surface over the transport-free API adapter.  It is
not autostarted, not hosted, and not a second source of truth.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import secrets
from typing import Any
from urllib.parse import parse_qs, urlparse

from chronicle.api.contracts import (
    API_SCHEMA_VERSION,
    ApiActorKind,
    ApiOriginMetadata,
    AssertionWriteRequest,
    BoundariesQueryRequest,
    ContextQueryRequest,
    DiffWriteRequest,
    EventWriteRequest,
    TimelineQueryRequest,
)
from chronicle.http_boundary import LoopbackRequestHandler
from chronicle.models.event import Actor, EventType
from chronicle.errors import UIHostNotLoopbackError
from chronicle.services.api_adapter_service import ApiAdapterService
from chronicle.services.chronicle_service import ChronicleService
from chronicle.ui_server import DEFAULT_UI_HOST, _is_loopback_host

DEFAULT_DAEMON_HOST = DEFAULT_UI_HOST
DEFAULT_DAEMON_PORT = 8776
DAEMON_AUTH_HEADER = "X-Chronicle-Daemon-Token"
DAEMON_ALLOWED_REQUEST_HOSTS = frozenset({"127.0.0.1", "localhost"})


@dataclass(frozen=True)
class DaemonStartupMetadata:
    host: str
    port: int
    url: str
    root: str
    bind_scope: str
    loopback_only: bool
    read_only: bool
    auth_mode: str
    auth_header: str
    session_token: str
    schema_version: str
    endpoints: list[str]
    write_endpoints: list[str]
    primary_record_path: str
    primary_record_authoritative: bool = True
    write_endpoints_enabled: bool = True
    autostart: bool = False
    hosted_api: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


@dataclass(frozen=True)
class DaemonSmokeCheck:
    name: str
    passed: bool
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DaemonSmokeReport:
    root: str
    passed: bool
    server_started: bool
    external_runtime: bool
    checks: list[DaemonSmokeCheck]

    def to_dict(self) -> dict[str, Any]:
        return {
            "root": self.root,
            "passed": self.passed,
            "server_started": self.server_started,
            "external_runtime": self.external_runtime,
            "checks": [check.to_dict() for check in self.checks],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


def build_daemon_startup_metadata(
    *,
    host: str = DEFAULT_DAEMON_HOST,
    port: int = DEFAULT_DAEMON_PORT,
    root: Path | None = None,
    session_token: str | None = None,
) -> DaemonStartupMetadata:
    root_path = (root or Path.cwd()).resolve()
    token = session_token or secrets.token_urlsafe(24)
    return DaemonStartupMetadata(
        host=host,
        port=port,
        url=f"http://{host}:{port}",
        root=str(root_path),
        bind_scope="loopback-only" if _is_loopback_host(host) else "non-loopback",
        loopback_only=_is_loopback_host(host),
        read_only=False,
        auth_mode="loopback_session_token",
        auth_header=DAEMON_AUTH_HEADER,
        session_token=token,
        schema_version=API_SCHEMA_VERSION,
        endpoints=[
            "GET /health",
            "GET /context",
            "GET /timeline",
            "GET /boundaries",
            "POST /events",
            "POST /diffs",
            "POST /assertions",
        ],
        write_endpoints=["POST /events", "POST /diffs", "POST /assertions"],
        primary_record_path=str(root_path / ".chronicle" / "chronicle.jsonl"),
    )


def validate_daemon_root(root: Path | None = None) -> None:
    ChronicleService(root).require_initialized()


def validate_daemon_host(host: str) -> None:
    if _is_loopback_host(host):
        return
    raise UIHostNotLoopbackError(host)


def create_daemon_handler(
    root: Path | None = None,
    *,
    host: str = DEFAULT_DAEMON_HOST,
    port: int = DEFAULT_DAEMON_PORT,
    session_token: str | None = None,
) -> type[BaseHTTPRequestHandler]:
    root_path = root or Path.cwd()
    metadata = build_daemon_startup_metadata(
        host=host,
        port=port,
        root=root_path,
        session_token=session_token,
    )
    adapter = ApiAdapterService(root_path)

    class ChronicleDaemonRequestHandler(LoopbackRequestHandler):
        server_version = "ChronicleDaemonLocal/0.1"

        def log_message(self, format: str, *args: object) -> None:  # noqa: A002
            return

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            query = parse_qs(parsed.query)
            if parsed.path == "/health":
                self._send_json({"status": "ok"})
                return
            if parsed.path not in {"/context", "/timeline", "/boundaries"}:
                self._send_json(
                    {"ok": False, "error": "not_found", "detail": "Unknown daemon endpoint."},
                    status=HTTPStatus.NOT_FOUND,
                )
                return
            if not self._authorized():
                self._send_json(
                    {
                        "ok": False,
                        "error": "unauthorized",
                        "detail": f"Pass {DAEMON_AUTH_HEADER} for daemon read endpoints.",
                    },
                    status=HTTPStatus.UNAUTHORIZED,
                )
                return
            try:
                if parsed.path == "/context":
                    request = ContextQueryRequest(
                        context_ids=query.get("context_id", []),
                        artifact_id=_first(query, "artifact_id"),
                        decision_id=_first(query, "decision_id"),
                        subject_ref=_first(query, "subject_ref"),
                        matter_ref=_first(query, "matter_ref"),
                        stakeholder_ref=_first(query, "stakeholder_ref"),
                        include_payload=_bool(query, "include_payload"),
                    )
                    self._send_json(adapter.get_context(request).model_dump(mode="json"))
                elif parsed.path == "/timeline":
                    request = TimelineQueryRequest(
                        context_ids=query.get("context_id", []),
                        artifact_id=_first(query, "artifact_id"),
                        decision_id=_first(query, "decision_id"),
                        subject_ref=_first(query, "subject_ref"),
                        include_payload=_bool(query, "include_payload"),
                    )
                    self._send_json(adapter.get_timeline(request).model_dump(mode="json"))
                else:
                    request = BoundariesQueryRequest(
                        company_ref=_first(query, "company_ref"),
                        matter_ref=_first(query, "matter_ref"),
                        context_ids=query.get("context_id", []),
                    )
                    self._send_json(adapter.get_boundaries(request).model_dump(mode="json"))
            except Exception as exc:  # pydantic validation plus Chronicle errors
                self._send_json(
                    {"ok": False, "error": "validation_error", "detail": str(exc)},
                    status=HTTPStatus.BAD_REQUEST,
                )

        def do_POST(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path not in {"/events", "/diffs", "/assertions"}:
                self._send_json(
                    {
                        "ok": False,
                        "error": "write_endpoint_not_implemented",
                        "detail": "Only POST /events, POST /diffs, and POST /assertions are enabled in this API write MVP.",
                    },
                    status=HTTPStatus.METHOD_NOT_ALLOWED,
                )
                return
            if not self._authorized():
                self._send_json(
                    {
                        "ok": False,
                        "error": "unauthorized",
                        "detail": f"Pass {DAEMON_AUTH_HEADER} for daemon write endpoints.",
                    },
                    status=HTTPStatus.UNAUTHORIZED,
                )
                return
            try:
                body = self._read_json_body()
                if parsed.path == "/events":
                    event_request = EventWriteRequest.model_validate(body)
                    response = (
                        adapter.preview_event_write(event_request)
                        if event_request.dry_run
                        else adapter.commit_event_write(event_request)
                    )
                elif parsed.path == "/diffs":
                    diff_request = DiffWriteRequest.model_validate(body)
                    response = (
                        adapter.preview_diff_write(diff_request)
                        if diff_request.dry_run
                        else adapter.commit_diff_write(diff_request)
                    )
                else:
                    assertion_request = AssertionWriteRequest.model_validate(body)
                    response = (
                        adapter.preview_assertion_write(assertion_request)
                        if assertion_request.dry_run
                        else adapter.commit_assertion_write(assertion_request)
                    )
                self._send_json(response.model_dump(mode="json"))
            except Exception as exc:
                self._send_json(
                    {"ok": False, "error": "validation_error", "detail": str(exc)},
                    status=HTTPStatus.BAD_REQUEST,
                )

        def _authorized(self) -> bool:
            supplied_token = str(self.headers.get(DAEMON_AUTH_HEADER, "") or "")
            return secrets.compare_digest(supplied_token, metadata.session_token)

        def _send_json(self, body: dict[str, Any], *, status: HTTPStatus = HTTPStatus.OK) -> None:
            payload = json.dumps(body, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def _read_json_body(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length", "0") or "0")
            raw = self.rfile.read(length).decode("utf-8") if length else "{}"
            payload = json.loads(raw or "{}")
            if not isinstance(payload, dict):
                raise ValueError("JSON body must be an object")
            return payload

    return ChronicleDaemonRequestHandler


def make_daemon_server(
    *,
    host: str = DEFAULT_DAEMON_HOST,
    port: int = DEFAULT_DAEMON_PORT,
    root: Path | None = None,
    session_token: str | None = None,
) -> ThreadingHTTPServer:
    return ThreadingHTTPServer(
        (host, port),
        create_daemon_handler(root, host=host, port=port, session_token=session_token),
    )


def serve_daemon(
    *,
    host: str = DEFAULT_DAEMON_HOST,
    port: int = DEFAULT_DAEMON_PORT,
    root: Path | None = None,
    session_token: str | None = None,
) -> DaemonStartupMetadata:
    root_path = root or Path.cwd()
    validate_daemon_root(root_path)
    validate_daemon_host(host)
    metadata = build_daemon_startup_metadata(
        host=host,
        port=port,
        root=root_path,
        session_token=session_token,
    )
    server = make_daemon_server(host=host, port=port, root=root_path, session_token=metadata.session_token)
    try:
        server.serve_forever()
    except KeyboardInterrupt:  # pragma: no cover - interactive shutdown path
        pass
    finally:
        server.server_close()
    return metadata


def run_daemon_smoke(
    *,
    root: Path | None = None,
    host: str = DEFAULT_DAEMON_HOST,
    port: int = DEFAULT_DAEMON_PORT,
) -> DaemonSmokeReport:
    root_path = root or Path.cwd()
    checks: list[DaemonSmokeCheck] = []
    try:
        validate_daemon_root(root_path)
        checks.append(DaemonSmokeCheck("root_initialized", True, "ok"))
    except Exception as exc:
        checks.append(DaemonSmokeCheck("root_initialized", False, str(exc)))
        return DaemonSmokeReport(
            root=str(root_path.resolve()),
            passed=False,
            server_started=False,
            external_runtime=False,
            checks=checks,
        )

    try:
        validate_daemon_host(host)
        metadata = build_daemon_startup_metadata(
            host=host,
            port=port,
            root=root_path,
            session_token="smoke-token",
        )
        checks.append(
            DaemonSmokeCheck(
                "loopback_bind_metadata",
                metadata.loopback_only and metadata.bind_scope == "loopback-only",
                metadata.bind_scope,
            )
        )
        checks.append(
            DaemonSmokeCheck(
                "write_endpoint_contract",
                set(metadata.write_endpoints)
                == {"POST /events", "POST /diffs", "POST /assertions"},
                ", ".join(metadata.write_endpoints),
            )
        )
    except Exception as exc:
        checks.append(DaemonSmokeCheck("loopback_bind_metadata", False, str(exc)))

    adapter = ApiAdapterService(root_path)
    try:
        context_response = adapter.get_context(ContextQueryRequest(subject_ref="daemon-smoke"))
        checks.append(
            DaemonSmokeCheck(
                "context_read_adapter",
                context_response.boundary_preview is True,
                "ok",
            )
        )
    except Exception as exc:
        checks.append(DaemonSmokeCheck("context_read_adapter", False, str(exc)))

    try:
        before = len(ChronicleService(root_path).jsonl.read_all())
        response = adapter.preview_event_write(
            EventWriteRequest(
                idempotency_key="daemon-smoke-dry-run",
                origin=ApiOriginMetadata(
                    source_tool="daemon-smoke",
                    actor_id="tool:daemon-smoke",
                    actor_kind=ApiActorKind.TOOL,
                ),
                event_type=EventType.NOTE_ADDED,
                actor=Actor.TOOL,
                summary="Daemon smoke dry-run",
            )
        )
        after = len(ChronicleService(root_path).jsonl.read_all())
        checks.append(
            DaemonSmokeCheck(
                "dry_run_write_no_primary_change",
                response.accepted and response.dry_run and before == after,
                "ok" if before == after else "primary record changed",
            )
        )
    except Exception as exc:
        checks.append(DaemonSmokeCheck("dry_run_write_no_primary_change", False, str(exc)))

    return DaemonSmokeReport(
        root=str(root_path.resolve()),
        passed=all(check.passed for check in checks),
        server_started=False,
        external_runtime=False,
        checks=checks,
    )


def _first(query: dict[str, list[str]], key: str) -> str | None:
    values = query.get(key, [])
    if not values:
        return None
    return values[0]


def _bool(query: dict[str, list[str]], key: str) -> bool:
    value = (_first(query, key) or "").strip().lower()
    return value in {"1", "true", "yes", "on"}
