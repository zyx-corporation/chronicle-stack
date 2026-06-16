"""Tests for explicit local Chronicle UI server."""

import json
import threading
import urllib.request

from typer.testing import CliRunner

from chronicle.cli import app
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.context_service import ContextService
from chronicle.ui_server import ChronicleUIDataService, build_startup_metadata, make_server


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
    ChronicleService(tmp_path).init("UI Test")
    ContextService(tmp_path).add_context(title="UI Context")

    overview = ChronicleUIDataService(tmp_path).overview()

    assert overview["chronicle"]["title"] == "UI Test"
    assert overview["counts"]["contexts"] == 1
    assert overview["runtime_boundary"]["read_only"] is True
    assert overview["runtime_boundary"]["daemon"] is False
    assert overview["runtime_boundary"]["external_model_api"] is False
    assert overview["runtime_boundary"]["graphrag_runtime"] is False
    assert overview["runtime_boundary"]["vector_db"] is False
    assert overview["runtime_boundary"]["graph_db"] is False


def test_ui_shell_contains_review_console(tmp_path):
    ChronicleService(tmp_path).init("UI Shell")

    html = ChronicleUIDataService(tmp_path).html_shell()

    assert "Chronicle Stack Review Console" in html
    assert "Read-first review console" in html
    assert "does not write Chronicle records" in html


def test_http_root_and_overview_endpoint(tmp_path):
    ChronicleService(tmp_path).init("HTTP UI")
    server = make_server(host="127.0.0.1", port=0, root=tmp_path)
    host, port = server.server_address
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with urllib.request.urlopen(f"http://{host}:{port}/", timeout=5) as response:
            html = response.read().decode("utf-8")
        assert "Chronicle Stack Review Console" in html

        with urllib.request.urlopen(f"http://{host}:{port}/api/overview", timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        assert payload["chronicle"]["title"] == "HTTP UI"
        assert payload["runtime_boundary"]["read_only"] is True
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_chronicle_ui_help():
    runner = CliRunner()
    result = runner.invoke(app, ["ui", "--help"])
    assert result.exit_code == 0
    assert "Start an explicit foreground read-only local web UI" in result.stdout
    assert "--host" in result.stdout
    assert "--port" in result.stdout
    assert "--open" in result.stdout
    assert "--root" in result.stdout
    assert "--json" in result.stdout
