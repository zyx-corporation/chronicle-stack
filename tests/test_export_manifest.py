"""Tests for export manifest metadata (v0.4)."""

import json
import os

import yaml
from typer.testing import CliRunner

from chronicle.cli import app


def _run(tmp_path, *args):
    os.chdir(str(tmp_path))
    runner = CliRunner()
    return runner.invoke(app, list(args))


def test_yaml_export_contains_manifest(tmp_path):
    assert _run(tmp_path, "init", "--title", "Manifest YAML").exit_code == 0

    result = _run(tmp_path, "export", "--format", "yaml")
    payload = yaml.safe_load(result.stdout)

    assert result.exit_code == 0
    assert "export_manifest" in payload
    manifest = payload["export_manifest"]
    assert manifest["export_format"] == "yaml"
    assert manifest["chronicle_id"].startswith("chr_")
    assert manifest["tool_name"] == "chronicle-stack"
    assert manifest["event_count"] >= 1


def test_graph_json_export_contains_manifest(tmp_path):
    assert _run(tmp_path, "init", "--title", "Manifest Graph").exit_code == 0

    result = _run(tmp_path, "export", "--format", "graph-json")
    payload = json.loads(result.stdout)

    assert result.exit_code == 0
    assert "export_manifest" in payload
    assert payload["export_manifest"]["export_format"] == "graph-json"
    assert payload["export_manifest"]["chronicle_id"] == payload["chronicle_id"]


def test_html_export_contains_manifest_section(tmp_path):
    assert _run(tmp_path, "init", "--title", "Manifest HTML").exit_code == 0

    result = _run(tmp_path, "export", "--format", "html")

    assert result.exit_code == 0
    assert "Export Manifest" in result.stdout
    assert "html" in result.stdout
    assert "Export Manifest は出力の来歴メタデータ" in result.stdout


def test_manifest_exports_do_not_mutate_jsonl(tmp_path):
    assert _run(tmp_path, "init", "--title", "Manifest No Mutation").exit_code == 0
    events_file = tmp_path / ".chronicle" / "chronicle.jsonl"
    before = events_file.read_text(encoding="utf-8")

    assert _run(tmp_path, "export", "--format", "yaml").exit_code == 0
    assert _run(tmp_path, "export", "--format", "graph-json").exit_code == 0
    assert _run(tmp_path, "export", "--format", "html").exit_code == 0

    after = events_file.read_text(encoding="utf-8")
    assert after == before
