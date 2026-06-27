"""Tests for read-only graph inspection commands (v0.4)."""

import json
import os

from typer.testing import CliRunner

from chronicle.cli_graph import graph_app
from chronicle.models.artifact import ArtifactType
from chronicle.services.artifact_service import ArtifactService
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.context_service import ContextService


def _run(tmp_path, *args):
    os.chdir(str(tmp_path))
    runner = CliRunner()
    return runner.invoke(graph_app, list(args))


def _setup_graph(tmp_path):
    ChronicleService(tmp_path).init("Graph Inspect")
    ContextService(tmp_path).add_context(title="Graph Context", summary="Context summary")
    source = tmp_path / "artifact.md"
    source.write_text("artifact body", encoding="utf-8")
    ArtifactService(tmp_path).create(
        title="Graph Artifact",
        artifact_type=ArtifactType.DOCUMENT,
        source_file=source,
    )


def test_graph_summary_json(tmp_path):
    _setup_graph(tmp_path)

    result = _run(tmp_path, "summary", "--json")
    payload = json.loads(result.stdout)

    assert result.exit_code == 0
    assert payload["chronicle_id"].startswith("chr_")
    assert payload["contract_version"] == "1.0"
    assert payload["incremental_mode"] == "event-driven_rebuildable"
    assert payload["incremental_expectations"]
    assert payload["node_count"] >= 1
    assert payload["edge_count"] >= 1
    assert "chronicle" in payload["node_types"]


def test_graph_nodes_human_filter(tmp_path):
    _setup_graph(tmp_path)

    result = _run(tmp_path, "nodes", "--type", "context")

    assert result.exit_code == 0
    assert "context" in result.stdout
    assert "Graph Context" in result.stdout
    assert "artifact_version" not in result.stdout


def test_graph_edges_json_filter(tmp_path):
    _setup_graph(tmp_path)

    result = _run(tmp_path, "edges", "--type", "chronicle_has_event", "--json")
    payload = json.loads(result.stdout)

    assert result.exit_code == 0
    assert payload
    assert all(edge["edge_type"] == "chronicle_has_event" for edge in payload)


def test_graph_inspection_does_not_mutate_jsonl(tmp_path):
    _setup_graph(tmp_path)
    events_file = tmp_path / ".chronicle" / "chronicle.jsonl"
    before = events_file.read_text(encoding="utf-8")

    assert _run(tmp_path, "summary").exit_code == 0
    assert _run(tmp_path, "nodes").exit_code == 0
    assert _run(tmp_path, "edges").exit_code == 0

    after = events_file.read_text(encoding="utf-8")
    assert after == before
