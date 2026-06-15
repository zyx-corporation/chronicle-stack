"""Tests for the primary `chronicle graph` compatibility alias."""

import json
import os

from typer.testing import CliRunner

from chronicle.cli import app
from chronicle.services.chronicle_service import ChronicleService


def _run_primary(tmp_path, *args):
    os.chdir(str(tmp_path))
    runner = CliRunner()
    return runner.invoke(app, list(args))


def _init_chronicle(tmp_path) -> None:
    ChronicleService(tmp_path).init("Primary Graph CLI Alias Test")


def test_primary_graph_alias_summary_json(tmp_path):
    _init_chronicle(tmp_path)

    result = _run_primary(tmp_path, "graph", "summary", "--json")

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["schema_version"] == "0.3"
    assert payload["node_count"] >= 1
    assert "chronicle" in payload["node_types"]


def test_primary_graph_alias_nodes_json(tmp_path):
    _init_chronicle(tmp_path)

    result = _run_primary(tmp_path, "graph", "nodes", "--json")

    assert result.exit_code == 0
    nodes = json.loads(result.stdout)
    assert any(node["node_type"] == "chronicle" for node in nodes)


def test_primary_graph_alias_edges_json_is_local_and_parseable(tmp_path):
    _init_chronicle(tmp_path)

    result = _run_primary(tmp_path, "graph", "edges", "--json")

    assert result.exit_code == 0
    edges = json.loads(result.stdout)
    assert isinstance(edges, list)
