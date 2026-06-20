"""Tests for explicit local runtime CLI commands."""

import json
import os
import re
from pathlib import Path

from typer.testing import CliRunner

from chronicle.cli import app


runner = CliRunner()


def test_runtime_status_json(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))

    result = runner.invoke(app, ["runtime", "status", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["provider_kind"] == "local"
    assert payload["external_call_made"] is False
    assert payload["generated_output_requires_review"] is True


def test_runtime_summarize_json_without_record(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))

    result = runner.invoke(
        app,
        [
            "runtime",
            "summarize",
            "--text",
            "First sentence. Second sentence. Third sentence. Fourth sentence.",
            "--max-sentences",
            "2",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["provider_kind"] == "local"
    assert payload["external_call_made"] is False
    assert payload["recorded"] is False
    assert payload["generated_text"] == "First sentence. Second sentence."


def test_runtime_summarize_record_persists_event(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "Runtime Chronicle"])

    result = runner.invoke(
        app,
        [
            "runtime",
            "summarize",
            "--text",
            "A local explicit runtime summary should be reviewable. It must stay local.",
            "--record",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["recorded"] is True
    assert re.match(r"evt_[a-f0-9]+", payload["event_id"])

    show_result = runner.invoke(app, ["show", "--json"])
    show_payload = json.loads(show_result.stdout)
    assert show_payload["event_count"] == 2

    search_result = runner.invoke(app, ["search", "Runtime summary generated", "--json"])
    search_payload = json.loads(search_result.stdout)
    assert any(item["kind"] == "event" for item in search_payload)


def test_runtime_summarize_can_persist_draft_summary_job(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "Runtime Draft Chronicle"])

    result = runner.invoke(
        app,
        [
            "runtime",
            "summarize",
            "--text",
            "A runtime-produced draft should stay reviewable and explicit. It remains local.",
            "--draft-title",
            "Runtime Draft Summary",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["draft_summary_job_id"].startswith("sum_")
    assert payload["draft_artifact_id"].startswith("art_")
    assert payload["draft_version_id"].startswith("ver_")
    assert payload["external_call_made"] is False

    show_result = runner.invoke(app, ["summary", "show", "--id", payload["draft_summary_job_id"], "--json"])
    assert show_result.exit_code == 0
    job = json.loads(show_result.stdout)
    assert job["title"] == "Runtime Draft Summary"
    assert job["provenance"]["generated_by"] == "runtime_manual"
    assert job["provenance"]["invocation_mode"] == "explicit-manual"
    assert job["provenance"]["runtime"]["provider_kind"] == "local"


def test_runtime_retrieve_plan_json(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "Runtime Retrieve"])
    record_result = runner.invoke(
        app,
        ["record", "--type", "user_input", "--actor", "user", "--summary", "GraphRAG planning context"],
    )
    event_id_match = re.search(r"evt_[a-f0-9]+", record_result.stdout)
    assert event_id_match is not None
    event_id = event_id_match.group(0)
    runner.invoke(
        app,
        [
            "ai-index",
            "vector",
            "add",
            "--record",
            event_id,
            "--text",
            "GraphRAG planning context for local retrieval plan",
        ],
    )

    result = runner.invoke(
        app,
        ["runtime", "retrieve-plan", "--query", "GraphRAG planning", "--json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["provider_kind"] == "local"
    assert payload["external_call_made"] is False
    assert payload["query"] == "GraphRAG planning"
    assert payload["vector_hits"]
    assert payload["chronicle_hits"]


def test_runtime_retrieve_plan_record_persists_event(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "Runtime Retrieve Record"])
    runner.invoke(
        app,
        ["record", "--type", "user_input", "--actor", "user", "--summary", "Retrieval context event"],
    )

    result = runner.invoke(
        app,
        ["runtime", "retrieve-plan", "--query", "Retrieval context", "--record", "--json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["recorded"] is True
    assert re.match(r"evt_[a-f0-9]+", payload["event_id"])

    show_result = runner.invoke(app, ["show", "--json"])
    show_payload = json.loads(show_result.stdout)
    assert show_payload["event_count"] == 3

    search_result = runner.invoke(app, ["search", "Runtime retrieval plan generated", "--json"])
    search_payload = json.loads(search_result.stdout)
    assert any(item["kind"] == "event" for item in search_payload)
