"""Runtime CLI tests."""

import json

from typer.testing import CliRunner

from chronicle.cli import app

runner = CliRunner()


def test_runtime_status_text_defaults_to_disabled() -> None:
    result = runner.invoke(app, ["runtime", "status"])

    assert result.exit_code == 0
    assert "Chronicle AI Runtime Status" in result.stdout
    assert "Status: disabled" in result.stdout
    assert "Provider: disabled" in result.stdout
    assert "network calls by default: False" in result.stdout
    assert "model calls by default: False" in result.stdout
    assert "generated output requires review: True" in result.stdout


def test_runtime_status_json_defaults_to_disabled() -> None:
    result = runner.invoke(app, ["runtime", "status", "--json"])

    assert result.exit_code == 0
    data = json.loads(result.stdout)

    assert data["status"] == "disabled"
    assert data["config"]["provider_kind"] == "disabled"
    assert data["config"]["allow_network"] is False
    assert data["config"]["allow_external_context"] is False
    assert data["config"]["review_required"] is True
    assert data["boundary"]["network_calls_default"] is False
    assert data["boundary"]["model_calls_default"] is False
    assert data["boundary"]["vector_db_default"] is False
    assert data["boundary"]["graph_db_default"] is False
    assert data["boundary"]["generated_output_requires_review"] is True
    assert data["boundary"]["indexes_are_derived"] is True
