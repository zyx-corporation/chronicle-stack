"""Tests for downstream query-engine adapter skeleton CLI output."""

import json
import os
from pathlib import Path

from typer.testing import CliRunner

from chronicle.cli import app


runner = CliRunner()


def test_package_query_engine_adapter_outputs_json_skeleton(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "Adapter CLI"])

    result = runner.invoke(
        app,
        ["package", "query-engine-adapter", "--query", "release planning context"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["skeleton_kind"] == "query_engine_import_adapter"
    assert payload["graph_export_format"] == "graph-json"
    assert payload["recommended_sequence"][0]["name"] == "inspect_handoff"


def test_package_query_engine_adapter_can_write_output_file(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "Adapter CLI Output"])
    output = tmp_path / "adapter-skeleton.json"

    result = runner.invoke(
        app,
        ["package", "query-engine-adapter", "--query", "graph context", "--output", str(output)],
    )

    assert result.exit_code == 0
    assert output.exists()
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["required_inputs"] == ["query_engine_handoff.json", ".chronicle/chronicle.jsonl", "graph.json"]
    assert "Adapter skeleton written to" in result.stdout


def test_package_query_engine_bundle_writes_bundle_files(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "Bundle CLI"])
    output_dir = tmp_path / "handoff-bundle"

    result = runner.invoke(
        app,
        ["package", "query-engine-bundle", "--query", "graph context", "--output-dir", str(output_dir)],
    )

    assert result.exit_code == 0
    assert (output_dir / "bundle_manifest.json").exists()
    assert (output_dir / "query_engine_handoff.json").exists()
    assert (output_dir / "query_engine_adapter_skeleton.json").exists()
    assert (output_dir / "graph.json").exists()
    assert (output_dir / "ACCEPTANCE_CHECKLIST.md").exists()
    assert (output_dir / "TRIAL_REPORT_TEMPLATE.md").exists()
    manifest = json.loads((output_dir / "bundle_manifest.json").read_text(encoding="utf-8"))
    assert manifest["bundle_kind"] == "query_engine_handoff_bundle"
    assert manifest["acceptance_checklist_included"] is True
    assert manifest["trial_report_template_included"] is True
    assert "downstream implementation repo is requested only if this bundle is insufficient" in (
        output_dir / "ACCEPTANCE_CHECKLIST.md"
    ).read_text(encoding="utf-8")
    assert "Bundle was sufficient for downstream trial" in (
        output_dir / "TRIAL_REPORT_TEMPLATE.md"
    ).read_text(encoding="utf-8")
    assert "Query-engine handoff bundle written to" in result.stdout
