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


def test_ai_index_status_json_shape(tmp_path):
    """chronicle ai-index status --json must expose stable status keys."""
    runner = _setup_cli(tmp_path)
    runner.invoke(app, ["init", "--title", "AI Index Shape"])

    result = runner.invoke(app, ["ai-index", "status", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    for key in ["vector", "graph", "derived_surface", "primary_record_authoritative"]:
        assert key in payload, f"Missing key '{key}' in ai-index status"
    for key in ["path", "entry_count", "embedding_provider", "embedding_model"]:
        assert key in payload["vector"], f"Missing key '{key}' in vector ai-index status"
    for key in ["path", "node_count", "edge_count"]:
        assert key in payload["graph"], f"Missing key '{key}' in graph ai-index status"


def test_runtime_status_json_shape(tmp_path):
    """chronicle runtime status --json must expose stable runtime keys."""
    runner = _setup_cli(tmp_path)

    result = runner.invoke(app, ["runtime", "status", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    for key in ["provider_kind", "model_name", "capabilities", "external_call_made"]:
        assert key in payload, f"Missing key '{key}' in runtime status"


def test_runtime_retrieve_plan_json_shape(tmp_path):
    """chronicle runtime retrieve-plan --json must expose stable retrieval plan keys."""
    runner = _setup_cli(tmp_path)
    runner.invoke(app, ["init", "--title", "Runtime Plan Shape"])

    result = runner.invoke(app, ["runtime", "retrieve-plan", "--query", "shape", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    for key in ["provider_kind", "query", "vector_hits", "graph_hits", "chronicle_hits", "query_engine_handoff", "notes"]:
        assert key in payload, f"Missing key '{key}' in runtime retrieve-plan"
    assert "import_validation" in payload["query_engine_handoff"]


def test_package_query_engine_adapter_json_shape(tmp_path):
    """chronicle package query-engine-adapter must expose stable skeleton keys."""
    runner = _setup_cli(tmp_path)
    runner.invoke(app, ["init", "--title", "Adapter Shape"])

    result = runner.invoke(app, ["package", "query-engine-adapter", "--query", "shape"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    for key in [
        "contract_version",
        "skeleton_kind",
        "handoff_contract_version",
        "required_inputs",
        "recommended_sequence",
        "prohibited_capabilities",
        "non_goals",
        "notes",
    ]:
        assert key in payload, f"Missing key '{key}' in package query-engine-adapter"


def test_package_query_engine_bundle_manifest_json_shape(tmp_path):
    """chronicle package query-engine-bundle must write stable bundle manifest keys."""
    runner = _setup_cli(tmp_path)
    runner.invoke(app, ["init", "--title", "Bundle Shape"])
    output_dir = tmp_path / "bundle"

    result = runner.invoke(
        app,
        ["package", "query-engine-bundle", "--query", "shape", "--output-dir", str(output_dir)],
    )

    assert result.exit_code == 0
    payload = json.loads((output_dir / "bundle_manifest.json").read_text(encoding="utf-8"))
    for key in [
        "contract_version",
        "bundle_kind",
        "query",
        "handoff_contract_version",
        "graph_export_contract_version",
        "adapter_skeleton_contract_version",
        "files",
        "acceptance_checklist_included",
        "trial_report_template_included",
        "referenced_record_count",
        "eligible_context_count",
        "import_validation_status",
        "import_ready",
        "notes",
    ]:
        assert key in payload, f"Missing key '{key}' in package query-engine-bundle manifest"


def test_package_query_engine_trial_record_json_shape(tmp_path):
    """chronicle package query-engine-trial-record --json must expose stable event and payload keys."""
    runner = _setup_cli(tmp_path)
    runner.invoke(app, ["init", "--title", "Trial Record Shape"])
    output_dir = tmp_path / "bundle"
    runner.invoke(
        app,
        ["package", "query-engine-bundle", "--query", "shape", "--output-dir", str(output_dir)],
    )

    result = runner.invoke(
        app,
        [
            "package",
            "query-engine-trial-record",
            "--bundle-dir",
            str(output_dir),
            "--reviewer",
            "shape-tester",
            "--consumer",
            "shape-demo",
            "--insufficient",
            "--missing-behavior",
            "external runtime belongs downstream",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    for key in ["event_id", "event_type", "actor", "summary", "payload"]:
        assert key in payload, f"Missing key '{key}' in package query-engine-trial-record event"
    trial_payload = payload["payload"]["query_engine_trial_record"]
    for key in [
        "contract_version",
        "record_kind",
        "query",
        "bundle_dir",
        "reviewer",
        "downstream_consumer",
        "sufficient",
        "files_reviewed",
        "import_validation_status",
        "import_ready",
        "missing_behavior",
        "notes",
    ]:
        assert key in trial_payload, f"Missing key '{key}' in query-engine trial payload"


def test_runtime_invoke_plan_json_shape(tmp_path):
    """chronicle runtime invoke-plan --json must expose stable invocation-plan keys."""
    runner = _setup_cli(tmp_path)
    runner.invoke(app, ["init", "--title", "Runtime Invoke Shape"])

    result = runner.invoke(app, ["runtime", "invoke-plan", "--text", "shape", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    for key in ["provider_kind", "provider_name", "model_name", "operation", "invocation_ready", "blocking_reasons", "execution_request", "notes"]:
        assert key in payload, f"Missing key '{key}' in runtime invoke-plan"


def test_ui_startup_metadata_json_shape(tmp_path):
    """chronicle ui startup metadata builder must expose stable boundary keys."""
    from pathlib import Path

    from chronicle.ui_server import build_startup_metadata

    payload = json.loads(
        build_startup_metadata(host="127.0.0.1", port=8765, root=Path(tmp_path)).to_json()
    )
    for key in ["host", "port", "url", "root", "bind_scope", "mutation_enabled", "mutation_capability_flag", "ui_boundary"]:
        assert key in payload, f"Missing key '{key}' in ui startup metadata"
    for key in [
        "bind_scope",
        "loopback_only",
        "mutation_enabled",
        "auth_mode",
        "authorization_mode",
        "session_gating",
        "mutation_readiness_status",
        "mutation_readiness_message",
        "mutation_blockers",
    ]:
        assert key in payload["ui_boundary"], f"Missing key '{key}' in ui boundary metadata"


def test_review_queue_json_shape(tmp_path):
    """chronicle review queue --json must expose stable review queue keys."""
    from chronicle.services.runtime_service import RuntimeService

    runner = _setup_cli(tmp_path)
    runner.invoke(app, ["init", "--title", "Review Queue Shape"])
    runtime_record = RuntimeService(tmp_path).summarize(text="Needs review", record=True)

    result = runner.invoke(app, ["review", "queue", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload[0]["target_event_id"] == runtime_record.event_id
    for key in ["target_event_id", "target_summary", "pending", "review_kind", "available_actions"]:
        assert key in payload[0], f"Missing key '{key}' in review queue payload"


def test_ui_review_capability_shape(tmp_path):
    """UI review queue derived payload must expose capability warning details."""
    from chronicle.services.runtime_service import RuntimeService
    from chronicle.ui_server import ChronicleUIDataService

    runner = _setup_cli(tmp_path)
    runner.invoke(app, ["init", "--title", "UI Review Capability Shape"])
    RuntimeService(tmp_path).summarize(text="Needs review", record=True)

    payload = ChronicleUIDataService(tmp_path).review_queue()["review_queue"][0]

    for key in ["status", "can_review_now", "warnings", "warning_details", "message"]:
        assert key in payload["review_capability"], f"Missing key '{key}' in review capability payload"
    for key in ["status", "expected_actions", "expected_commands", "message"]:
        assert key in payload["cli_parity_summary"], f"Missing key '{key}' in review parity payload"
