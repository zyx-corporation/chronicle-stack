"""Contract tests for CLI --json output shape stability."""

import json
import os

from typer.testing import CliRunner

from chronicle.cli import app


def _setup_cli(tmp_path):
    os.chdir(str(tmp_path))
    runner = CliRunner()
    return runner


def test_show_json_shape(tmp_path):
    """chronicle show --json must have expected top-level keys."""
    runner = _setup_cli(tmp_path)
    runner.invoke(app, ["init", "--title", "Shape Test"])

    result = runner.invoke(app, ["show", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    # Contract: these top-level keys must exist
    for key in ["metadata", "event_count", "artifact_count", "context_count",
                "decision_count", "corrupt_lines"]:
        assert key in data, f"Missing key '{key}' in show --json output"


def test_search_json_shape(tmp_path):
    """chronicle search --json must produce a list with kind/identifier/summary."""
    runner = _setup_cli(tmp_path)
    runner.invoke(app, ["init", "--title", "Search Shape"])
    runner.invoke(app, ["record", "--type", "user_input", "--actor", "user",
                         "--summary", "SearchTermTest"])

    result = runner.invoke(app, ["search", "SearchTermTest", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert isinstance(data, list)
    if data:
        for key in ["kind", "identifier", "summary"]:
            assert key in data[0], f"Missing key '{key}' in search result"


def test_boundary_list_json_shape(tmp_path):
    """chronicle boundary list --json must produce a list with rule fields."""
    runner = _setup_cli(tmp_path)
    runner.invoke(app, ["init", "--title", "Boundary Shape"])
    runner.invoke(app, [
        "boundary", "add", "--type", "warn", "--field", "visibility",
        "--operator", "equals", "--value", "sensitive",
        "--reason", "Contract test",
    ])

    result = runner.invoke(app, ["boundary", "list", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert isinstance(data, list)
    if data:
        for key in ["rule_id", "rule_type", "field", "operator"]:
            assert key in data[0], f"Missing key '{key}' in boundary rule"


def test_boundary_check_json_shape(tmp_path):
    """chronicle boundary check --json must produce a list with matched field."""
    runner = _setup_cli(tmp_path)
    runner.invoke(app, ["init", "--title", "Check Shape"])
    runner.invoke(app, [
        "add-context", "--title", "Sensitive", "--scope", "project",
        "--visibility", "sensitive",
    ])
    runner.invoke(app, [
        "boundary", "add", "--type", "warn", "--field", "visibility",
        "--operator", "equals", "--value", "sensitive",
        "--reason", "Contract check",
    ])
    # Get context ID
    list_result = runner.invoke(app, ["search", "Sensitive", "--json"])
    ctx_data = json.loads(list_result.stdout)
    ctx_id = next((r["identifier"] for r in ctx_data if r["kind"] == "context"), None)
    assert ctx_id is not None

    result = runner.invoke(app, ["boundary", "check", "--context", ctx_id, "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert isinstance(data, list)
    if data:
        for key in ["rule_id", "rule_type", "matched"]:
            assert key in data[0], f"Missing key '{key}' in boundary check result"


def test_injection_plan_json_shape(tmp_path):
    """chronicle injection plan --json must have plan_id, selected/warned/excluded."""
    runner = _setup_cli(tmp_path)
    runner.invoke(app, ["init", "--title", "Plan Shape"])
    runner.invoke(app, [
        "add-context", "--title", "Plan Context", "--scope", "project",
    ])

    result = runner.invoke(app, ["injection", "plan", "--task", "Shape test", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert "plan" in data
    assert "recorded" in data
    assert "event_id" in data
    plan = data["plan"]
    for key in ["plan_id", "task", "selected", "warned", "excluded"]:
        assert key in plan, f"Missing key '{key}' in injection plan"
    assert plan["plan_id"].startswith("ip_")


def test_cli_invalid_enum_exits_nonzero(tmp_path):
    """Invalid enum value in CLI must result in non-zero exit code."""
    runner = _setup_cli(tmp_path)
    runner.invoke(app, ["init", "--title", "Enum Test"])

    result = runner.invoke(app, ["add-context", "--title", "Bad", "--scope", "invalid_scope"])
    assert result.exit_code != 0
