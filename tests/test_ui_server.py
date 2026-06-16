"""Tests for explicit local Chronicle UI server."""

import http.client
import json
import threading

from typer.testing import CliRunner

from chronicle.cli import app
from chronicle.models.artifact import ArtifactType
from chronicle.models.audit import AuditOperation, AuditSeverity, AuditTargetEnvironment
from chronicle.models.boundary import BoundaryConditionField, BoundaryOperator, BoundaryRuleType
from chronicle.models.decision import DecisionType
from chronicle.models.lifecycle import LifecycleAction, LifecycleReasonClass
from chronicle.models.visibility import VisibilityHint
from chronicle.services.artifact_service import ArtifactService
from chronicle.services.audit_service import AuditService
from chronicle.services.boundary_service import BoundaryService
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.context_service import ContextService
from chronicle.services.decision_service import DecisionService
from chronicle.services.lifecycle_service import LifecycleService
from chronicle.ui_server import ChronicleUIDataService, build_startup_metadata, make_server


def _http_get(host: str, port: int, path: str) -> tuple[int, str]:
    connection = http.client.HTTPConnection(host, port, timeout=5)
    try:
        connection.request("GET", path)
        response = connection.getresponse()
        return response.status, response.read().decode("utf-8")
    finally:
        connection.close()


def _populate(root):
    ChronicleService(root).init("UI Test")
    context = ContextService(root).add_context(title="UI Context", visibility_hint=VisibilityHint.PUBLIC)
    artifact_file = root / "artifact.md"
    artifact_file.write_text("artifact body", encoding="utf-8")
    artifact, _version = ArtifactService(root).create(
        title="UI Artifact",
        artifact_type=ArtifactType.DOCUMENT,
        source_file=artifact_file,
        visibility_hint=VisibilityHint.PRIVATE,
    )
    DecisionService(root).record(
        decision_type=DecisionType.ACCEPTED,
        reason="UI decision",
        artifact_id=artifact.artifact_id,
    )
    BoundaryService(root).add_rule(
        rule_type=BoundaryRuleType.WARN,
        field=BoundaryConditionField.VISIBILITY,
        operator=BoundaryOperator.EQUALS,
        value="private",
        reason="UI boundary",
    )
    AuditService(root).record(
        operation=AuditOperation.EXPORT,
        actor="test",
        purpose="ui audit",
        target_environment=AuditTargetEnvironment.LOCAL,
        result=AuditSeverity.INFO,
        summary="UI audit event",
    )
    LifecycleService(root).record(
        action=LifecycleAction.SEAL,
        target_id=context.context_id,
        target_kind="context",
        actor="test",
        reason_class=LifecycleReasonClass.PRIVACY,
        reason="UI lifecycle marker",
    )


def test_startup_metadata(tmp_path):
    metadata = build_startup_metadata(host="127.0.0.1", port=8765, root=tmp_path)
    payload = json.loads(metadata.to_json())
    assert payload["host"] == "127.0.0.1"
    assert payload["port"] == 8765
    assert payload["url"] == "http://127.0.0.1:8765"
    assert payload["root"] == str(tmp_path.resolve())
    assert payload["read_only"] is True
    assert payload["runtime"] == "foreground-local-ui"
    assert payload["external_runtime"] is False


def test_ui_overview_data(tmp_path):
    _populate(tmp_path)

    overview = ChronicleUIDataService(tmp_path).overview()

    assert overview["chronicle"]["title"] == "UI Test"
    assert overview["counts"]["contexts"] == 1
    assert overview["counts"]["artifacts"] == 1
    assert overview["counts"]["decisions"] == 1
    assert overview["counts"]["boundary_rules"] == 1
    assert overview["counts"]["audit_events"] == 1
    assert overview["counts"]["lifecycle_markers"] == 1
    assert overview["runtime_boundary"]["read_only"] is True
    assert overview["runtime_boundary"]["daemon"] is False
    assert overview["runtime_boundary"]["external_model_api"] is False
    assert overview["runtime_boundary"]["graphrag_runtime"] is False
    assert overview["runtime_boundary"]["vector_db"] is False
    assert overview["runtime_boundary"]["graph_db"] is False


def test_ui_data_service_read_endpoints(tmp_path):
    _populate(tmp_path)
    service = ChronicleUIDataService(tmp_path)

    assert service.contexts()["contexts"][0]["title"] == "UI Context"
    assert service.artifacts()["artifacts"][0]["title"] == "UI Artifact"
    assert service.decisions()["decisions"][0]["reason"] == "UI decision"
    assert service.boundary_rules()["boundary_rules"][0]["reason"] == "UI boundary"
    assert service.audit_events()["audit_events"][0]["summary"] == "UI audit event"
    assert service.lifecycle_markers()["lifecycle_markers"][0]["reason"] == "UI lifecycle marker"
    assert "events" in service.events()
    assert "rde_records" in service.rde_records()
    assert "status" in service.package_review_snapshot()
    assert "nodes" in service.graph_summary()


def test_ui_shell_contains_interactive_local_ui(tmp_path):
    ChronicleService(tmp_path).init("UI Shell")

    html = ChronicleUIDataService(tmp_path).html_shell()

    assert "Chronicle Stack Local UI" in html
    assert "Read-only foreground local UI" in html
    assert "fetch(endpoint)" in html
    assert "/api/events" in html
    assert "/api/package-review" in html
    assert "does not write records" in html


def test_http_root_and_read_only_endpoints(tmp_path):
    _populate(tmp_path)
    server = make_server(host="127.0.0.1", port=0, root=tmp_path)
    host, port = server.server_address
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        status, html = _http_get(host, port, "/")
        assert status == 200
        assert "Chronicle Stack Local UI" in html

        expected_keys = {
            "/api/overview": "counts",
            "/api/events": "events",
            "/api/contexts": "contexts",
            "/api/artifacts": "artifacts",
            "/api/decisions": "decisions",
            "/api/rde": "rde_records",
            "/api/boundary": "boundary_rules",
            "/api/audit": "audit_events",
            "/api/lifecycle": "lifecycle_markers",
            "/api/package-review": "package_review",
            "/api/graph-summary": "graph_summary",
        }
        for endpoint, key in expected_keys.items():
            status, body = _http_get(host, port, endpoint)
            assert status == 200, endpoint
            payload = json.loads(body)
            assert key in payload, endpoint

        status, review_console = _http_get(host, port, "/review-console")
        assert status == 200
        assert "Chronicle Stack Review Console" in review_console
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_chronicle_ui_help():
    runner = CliRunner()
    result = runner.invoke(app, ["ui", "--help"])
    assert result.exit_code == 0
    for option in ("host", "port", "open", "root", "json"):
        assert option in result.stdout.lower()
