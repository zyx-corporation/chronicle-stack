"""Tests for local placeholder ai-index CLI commands."""

import json
import os
import re
from pathlib import Path

from typer.testing import CliRunner

from chronicle.cli import app


runner = CliRunner()


def _extract_prefixed_id(text: str, prefix: str) -> str:
    match = re.search(rf"{prefix}[a-f0-9]+", text)
    assert match is not None, text
    return match.group(0)


def test_ai_index_status_json(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "AI Index Status"])

    result = runner.invoke(app, ["ai-index", "status", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["vector"]["entry_count"] == 0
    assert payload["graph"]["node_count"] == 0
    assert payload["external_services"] is False
    assert payload["primary_record_authoritative"] is True


def test_ai_index_vector_add_and_search_json(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "AI Vector"])
    record = runner.invoke(
        app,
        ["record", "--type", "user_input", "--actor", "user", "--summary", "Anchor event"],
    )
    event_id = _extract_prefixed_id(record.stdout, "evt_")

    add_result = runner.invoke(
        app,
        [
            "ai-index",
            "vector",
            "add",
            "--record",
            event_id,
            "--text",
            "GraphRAG placeholder search for local runtime boundary",
            "--metadata",
            "source=manual",
            "--json",
        ],
    )

    assert add_result.exit_code == 0
    add_payload = json.loads(add_result.stdout)
    assert add_payload["record_id"] == event_id
    assert add_payload["embedding_provider"] == "disabled"
    assert (tmp_path / ".chronicle" / "ai_indexes" / "vector_index.json").exists()

    search_result = runner.invoke(
        app,
        ["ai-index", "vector", "search", "--query", "placeholder boundary", "--json"],
    )

    assert search_result.exit_code == 0
    search_payload = json.loads(search_result.stdout)
    assert len(search_payload) == 1
    assert search_payload[0]["record_id"] == event_id
    assert search_payload[0]["score"] > 0


def test_ai_index_graph_neighbors_json(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "AI Graph"])
    event_result = runner.invoke(
        app,
        ["record", "--type", "user_input", "--actor", "user", "--summary", "Graph event"],
    )
    event_id = _extract_prefixed_id(event_result.stdout, "evt_")
    runner.invoke(
        app,
        ["add-context", "--title", "Graph Context", "--scope", "task"],
    )
    context_search = runner.invoke(app, ["search", "Graph Context", "--json"])
    context_id = next(
        item["identifier"]
        for item in json.loads(context_search.stdout)
        if item["kind"] == "context"
    )

    node_result = runner.invoke(
        app,
        [
            "ai-index",
            "graph",
            "add-node",
            "--id",
            event_id,
            "--label",
            "event",
            "--property",
            "title=Graph event",
            "--json",
        ],
    )
    assert node_result.exit_code == 0
    runner.invoke(
        app,
        [
            "ai-index",
            "graph",
            "add-node",
            "--id",
            context_id,
            "--label",
            "context",
        ],
    )
    edge_result = runner.invoke(
        app,
        [
            "ai-index",
            "graph",
            "add-edge",
            "--source",
            event_id,
            "--target",
            context_id,
            "--relation",
            "references",
            "--json",
        ],
    )

    assert edge_result.exit_code == 0
    neighbors_result = runner.invoke(
        app,
        ["ai-index", "graph", "neighbors", "--id", event_id, "--json"],
    )

    assert neighbors_result.exit_code == 0
    payload = json.loads(neighbors_result.stdout)
    assert payload["node_id"] == event_id
    assert payload["outgoing"][0]["relation"] == "references"
    assert payload["neighbors"][0]["node_id"] == context_id
    assert (tmp_path / ".chronicle" / "ai_indexes" / "graph_index.json").exists()


def test_ai_index_invalid_metadata_exits_nonzero(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "AI Invalid"])
    record = runner.invoke(
        app,
        ["record", "--type", "user_input", "--actor", "user", "--summary", "Anchor event"],
    )
    event_id = _extract_prefixed_id(record.stdout, "evt_")

    result = runner.invoke(
        app,
        [
            "ai-index",
            "vector",
            "add",
            "--record",
            event_id,
            "--text",
            "Invalid metadata",
            "--metadata",
            "not-a-pair",
        ],
    )

    assert result.exit_code != 0
