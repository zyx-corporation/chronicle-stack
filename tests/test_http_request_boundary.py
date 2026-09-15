"""Socket-level rejection before routing, including unsupported HTTP methods."""

import http.client
import threading
from contextlib import contextmanager
from unittest.mock import patch

import pytest

from chronicle.daemon_server import make_daemon_server
from chronicle.services.chronicle_service import ChronicleService
from chronicle.ui_server import (
    ChronicleUIDataService,
    UIAuthMode,
    UIAuthorizationMode,
    make_server,
)


@contextmanager
def running_server(root, surface):
    ChronicleService(root).init("Boundary regression")
    if surface == "daemon":
        server = make_daemon_server(root=root, port=0)
    else:
        server = make_server(
            root=root, port=0, workspace_enabled=surface == "workspace",
            mutation_capability_flag=True, enable_ui_mutation=True,
            auth_mode=UIAuthMode.LOOPBACK_LOCAL,
            authorization_mode=UIAuthorizationMode.REVIEWER_DECLARED,
        )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def request(server, method, path, headers):
    connection = http.client.HTTPConnection(*server.server_address, timeout=5)
    try:
        connection.request(method, path, headers=headers)
        response = connection.getresponse()
        return response.status, dict(response.getheaders()), response.read()
    finally:
        connection.close()


@pytest.mark.parametrize("surface", ["daemon", "ui", "workspace"])
def test_every_method_passes_boundary_before_dispatch(tmp_path, surface):
    with running_server(tmp_path, surface) as server:
        port = server.server_address[1]
        origin = {"Origin": f"http://127.0.0.1:{port}"} if surface != "daemon" else {}
        primary = tmp_path / ".chronicle/chronicle.jsonl"
        before = primary.read_bytes()
        for method in ["GET", "POST", "OPTIONS", "HEAD", "PUT", "PATCH", "DELETE", "TRACE",
                       "CONNECT", "CUSTOM"]:
            for path in ["/", "/health", "/api/capture", "/unknown"]:
                status, headers, _ = request(server, method, path, {"Host": "attacker.invalid"})
                assert status == 421, (surface, method, path, status)
                assert not any(key.lower().startswith("access-control-") for key in headers)
                status, _, _ = request(server, method, path, {"Origin": "https://attacker.invalid"})
                assert status == 403, (surface, method, path, status)
            if method not in {"GET", "POST"}:
                status, headers, body = request(server, method, "/", origin)
                assert status == 405, (surface, method, status)
                assert headers["Allow"] == "GET, POST"
                if method == "HEAD":
                    assert body == b""
        assert primary.read_bytes() == before


def test_workspace_denials_never_reach_services(tmp_path):
    with running_server(tmp_path, "workspace") as server:
        primary = tmp_path / ".chronicle/chronicle.jsonl"
        before = primary.read_bytes()
        origin = {"Origin": f"http://127.0.0.1:{server.server_address[1]}"}
        with (
            patch.object(ChronicleUIDataService, "capture_response") as capture,
            patch.object(ChronicleUIDataService, "graphrag_response") as graphrag,
            patch.object(ChronicleUIDataService, "review_action_response") as review,
        ):
            for path in ["/api/capture", "/api/graphrag/query", "/api/graphrag/rebuild",
                         "/api/review-actions/evt_test/approve",
                         "/api/review-actions/evt_test/reject",
                         "/api/review-actions/evt_test/request-changes"]:
                status, _, _ = request(server, "POST", path, origin)
                assert status == 401
            capture.assert_not_called()
            graphrag.assert_not_called()
            review.assert_not_called()
        assert primary.read_bytes() == before
