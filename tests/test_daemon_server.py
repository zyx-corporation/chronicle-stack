"""Tests for the explicit loopback Chronicle API daemon MVP."""

import http.client
import json
import os
import threading

import pytest
from typer.testing import CliRunner

from chronicle.cli import app
from chronicle.daemon_server import (
    DAEMON_AUTH_HEADER,
    build_daemon_startup_metadata,
    make_daemon_server,
    run_daemon_smoke,
    validate_daemon_host,
)
from chronicle.models.artifact import ArtifactType
from chronicle.models.boundary import BoundaryConditionField, BoundaryOperator, BoundaryRuleType
from chronicle.services.artifact_service import ArtifactService
from chronicle.services.boundary_service import BoundaryService
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.context_service import ContextService


def _http_get(
    host: str,
    port: int,
    path: str,
    *,
    headers: dict[str, str] | None = None,
) -> tuple[int, str]:
    connection = http.client.HTTPConnection(host, port, timeout=5)
    try:
        connection.request("GET", path, headers=headers or {})
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
        connection.request("POST", path, body=payload, headers=request_headers)
        response = connection.getresponse()
        return response.status, response.read().decode("utf-8")
    finally:
        connection.close()


def _http_get_with_raw_host_headers(
    host: str,
    port: int,
    path: str,
    host_headers: list[str],
) -> tuple[int, str]:
    connection = http.client.HTTPConnection(host, port, timeout=5)
    try:
        connection.putrequest("GET", path, skip_host=True)
        for value in host_headers:
            connection.putheader("Host", value)
        connection.endheaders()
        response = connection.getresponse()
        return response.status, response.read().decode("utf-8")
    finally:
        connection.close()


def test_daemon_startup_metadata_shape(tmp_path) -> None:
    ChronicleService(tmp_path).init("Daemon Metadata")

    metadata = build_daemon_startup_metadata(
        host="127.0.0.1",
        port=8776,
        root=tmp_path,
        session_token="test-token",
    )
    payload = metadata.to_dict()

    assert payload["bind_scope"] == "loopback-only"
    assert payload["loopback_only"] is True
    assert payload["read_only"] is False
    assert payload["write_endpoints_enabled"] is True
    assert payload["auth_header"] == DAEMON_AUTH_HEADER
    assert "GET /health" in payload["endpoints"]
    assert payload["write_endpoints"] == ["POST /events", "POST /diffs", "POST /assertions"]


def test_daemon_rejects_non_loopback_host() -> None:
    with pytest.raises(Exception) as exc:
        validate_daemon_host("0.0.0.0")

    assert "loopback-only" in str(exc.value)


def test_daemon_cli_json_shape(tmp_path) -> None:
    os.chdir(str(tmp_path))
    runner = CliRunner()
    runner.invoke(app, ["init", "--title", "Daemon CLI Shape"])

    result = runner.invoke(
        app,
        ["daemon", "start", "--session-token", "shape-token", "--json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    for key in [
        "host",
        "port",
        "url",
        "root",
        "bind_scope",
        "read_only",
        "write_endpoints",
        "auth_header",
        "session_token",
        "endpoints",
        "primary_record_path",
    ]:
        assert key in payload
    assert payload["session_token"] == "shape-token"


def test_daemon_smoke_checks_without_starting_server(tmp_path) -> None:
    ChronicleService(tmp_path).init("Daemon Smoke")

    report = run_daemon_smoke(root=tmp_path)

    assert report.passed is True
    assert report.server_started is False
    assert report.external_runtime is False
    names = {check.name for check in report.checks}
    assert "root_initialized" in names
    assert "dry_run_write_no_primary_change" in names


def test_daemon_smoke_cli_json_shape(tmp_path) -> None:
    os.chdir(str(tmp_path))
    runner = CliRunner()
    runner.invoke(app, ["init", "--title", "Daemon Smoke CLI"])

    result = runner.invoke(app, ["daemon", "smoke", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["passed"] is True
    assert payload["server_started"] is False
    assert payload["external_runtime"] is False
    assert isinstance(payload["checks"], list)


def test_daemon_health_context_timeline_boundaries_and_write_event(tmp_path) -> None:
    ChronicleService(tmp_path).init("Daemon HTTP")
    context = ContextService(tmp_path).add_context(title="Daemon Context", summary="readable")
    artifact_file = tmp_path / "daemon-artifact.md"
    artifact_file.write_text("v1", encoding="utf-8")
    artifact, version_1 = ArtifactService(tmp_path).create(
        title="Daemon Artifact",
        artifact_type=ArtifactType.DOCUMENT,
        source_file=artifact_file,
    )
    artifact_file.write_text("v2", encoding="utf-8")
    _artifact, version_2 = ArtifactService(tmp_path).update(
        artifact_id=artifact.artifact_id,
        source_file=artifact_file,
        summary="daemon update",
    )
    BoundaryService(tmp_path).add_rule(
        rule_type=BoundaryRuleType.WARN,
        field=BoundaryConditionField.TAG,
        operator=BoundaryOperator.CONTAINS,
        value="external",
        reason="Review disclosure.",
    )
    try:
        server = make_daemon_server(
            host="127.0.0.1",
            port=0,
            root=tmp_path,
            session_token="daemon-test-token",
        )
    except OSError as exc:
        pytest.skip(f"local socket bind unavailable in this environment: {exc}")
    host, port = server.server_address
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        status, body = _http_get(host, port, "/health")
        assert status == 200
        assert json.loads(body) == {"status": "ok"}

        status, body = _http_get(host, port, f"/context?context_id={context.context_id}")
        assert status == 401
        assert json.loads(body)["error"] == "unauthorized"

        headers = {DAEMON_AUTH_HEADER: "daemon-test-token"}
        status, body = _http_get(
            host,
            port,
            f"/context?context_id={context.context_id}",
            headers=headers,
        )
        assert status == 200
        assert json.loads(body)["records"][0]["context_id"] == context.context_id

        status, body = _http_get(
            host,
            port,
            f"/timeline?context_id={context.context_id}",
            headers=headers,
        )
        assert status == 200
        assert json.loads(body)["records"]

        status, body = _http_get(host, port, "/boundaries?matter_ref=daemon", headers=headers)
        assert status == 200
        assert json.loads(body)["records"][0]["rule_type"] == "warn"

        before = len(ChronicleService(tmp_path).jsonl.read_all())
        status, body = _http_post(
            host,
            port,
            "/events",
            {
                "idempotency_key": "idem-daemon-event-1",
                "origin": {
                    "source_tool": "daemon-test",
                    "actor_id": "tool:daemon-test",
                    "actor_kind": "tool",
                },
                "dry_run": False,
                "event_type": "note_added",
                "actor": "tool",
                "summary": "Daemon write event",
                "payload": {"note": "structured event write"},
                "context_ids": [context.context_id],
            },
            headers=headers,
        )
        after = len(ChronicleService(tmp_path).jsonl.read_all())
        write_payload = json.loads(body)
        assert status == 200
        assert write_payload["accepted"] is True
        assert write_payload["dry_run"] is False
        assert write_payload["event_id"].startswith("evt_")
        assert after == before + 1

        status, body = _http_post(
            host,
            port,
            "/events",
            {
                "idempotency_key": "idem-daemon-event-1",
                "origin": {
                    "source_tool": "daemon-test",
                    "actor_id": "tool:daemon-test",
                    "actor_kind": "tool",
                },
                "dry_run": False,
                "event_type": "note_added",
                "actor": "tool",
                "summary": "Daemon write duplicate",
            },
            headers=headers,
        )
        duplicate_payload = json.loads(body)
        assert status == 200
        assert duplicate_payload["duplicate"] is True
        assert len(ChronicleService(tmp_path).jsonl.read_all()) == after

        status, body = _http_post(
            host,
            port,
            "/assertions",
            {
                "idempotency_key": "idem-daemon-assertion-1",
                "origin": {
                    "source_tool": "daemon-test",
                    "actor_id": "tool:daemon-test",
                    "actor_kind": "tool",
                },
                "dry_run": False,
                "assertion_kind": "claim",
                "statement": "Daemon assertion write",
                "verification_status": "unverified",
                "context_ids": [context.context_id],
            },
            headers=headers,
        )
        assertion_payload = json.loads(body)
        assert status == 200
        assert assertion_payload["accepted"] is True
        assert assertion_payload["assertion_id"].startswith("obj_")

        status, body = _http_post(
            host,
            port,
            "/diffs",
            {
                "idempotency_key": "idem-daemon-diff-1",
                "origin": {
                    "source_tool": "daemon-test",
                    "actor_id": "tool:daemon-test",
                    "actor_kind": "tool",
                },
                "dry_run": False,
                "artifact_id": artifact.artifact_id,
                "from_version_id": version_1.version_id,
                "to_version_id": version_2.version_id,
                "created_by": "tool",
                "summary": "Daemon API diff",
                "transformed": ["daemon body changed"],
            },
            headers=headers,
        )
        diff_payload = json.loads(body)
        assert status == 200
        assert diff_payload["accepted"] is True
        assert diff_payload["rde_record_id"].startswith("rde_")
    finally:
        server.shutdown()
        server.server_close()


def test_daemon_rejects_untrusted_host_and_browser_origin_before_route_logic(tmp_path) -> None:
    ChronicleService(tmp_path).init("Daemon Request Boundary")
    try:
        server = make_daemon_server(
            host="127.0.0.1",
            port=0,
            root=tmp_path,
            session_token="daemon-boundary-token",
        )
    except OSError as exc:
        pytest.skip(f"local socket bind unavailable in this environment: {exc}")
    host, port = server.server_address
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        status, body = _http_get(
            host,
            port,
            "/health",
            headers={"Host": f"localhost:{port}"},
        )
        assert status == 200
        assert json.loads(body) == {"status": "ok"}

        status, body = _http_get(
            host,
            port,
            "/health",
            headers={"Host": f"attacker.example:{port}"},
        )
        assert status == 421
        assert json.loads(body)["error"] == "invalid_host"

        status, body = _http_get_with_raw_host_headers(host, port, "/health", [])
        assert status == 421
        assert json.loads(body)["error"] == "invalid_host"

        status, body = _http_get_with_raw_host_headers(
            host,
            port,
            "/health",
            [f"127.0.0.1:{port}", f"attacker.example:{port}"],
        )
        assert status == 421
        assert json.loads(body)["error"] == "invalid_host"

        status, body = _http_get(
            host,
            port,
            "/health",
            headers={"Host": f"127.0.0.1:{port + 1}"},
        )
        assert status == 421
        assert json.loads(body)["error"] == "invalid_host"

        status, body = _http_get(
            host,
            port,
            "/health",
            headers={"Origin": "https://attacker.example"},
        )
        assert status == 403
        assert json.loads(body)["error"] == "origin_not_allowed"

        status, body = _http_get(
            host,
            port,
            "/context",
            headers={
                DAEMON_AUTH_HEADER: "daemon-boundary-token",
                "Origin": "https://attacker.example",
            },
        )
        assert status == 403
        assert json.loads(body)["error"] == "origin_not_allowed"

        before = len(ChronicleService(tmp_path).jsonl.read_all())
        status, body = _http_post(
            host,
            port,
            "/events",
            {
                "idempotency_key": "idem-origin-blocked-1",
                "origin": {
                    "source_tool": "browser-attack",
                    "actor_id": "tool:browser-attack",
                    "actor_kind": "tool",
                },
                "dry_run": False,
                "event_type": "note_added",
                "actor": "tool",
                "summary": "Must not be recorded",
            },
            headers={
                DAEMON_AUTH_HEADER: "daemon-boundary-token",
                "Origin": "https://attacker.example",
            },
        )
        assert status == 403
        assert json.loads(body)["error"] == "origin_not_allowed"
        assert len(ChronicleService(tmp_path).jsonl.read_all()) == before
    finally:
        server.shutdown()
        server.server_close()
