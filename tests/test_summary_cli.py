"""Summary job CLI tests."""

import json
import os
import re
from pathlib import Path

from typer.testing import CliRunner

from chronicle.cli import app

runner = CliRunner()


def _extract_summary_job_id(text: str) -> str:
    match = re.search(r"\b(sum_[a-f0-9]+)\b", text)
    assert match is not None, text
    return match.group(1)


def test_summary_create_records_pending_review_job_without_runtime(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "Summary Test"])

    result = runner.invoke(
        app,
        [
            "summary", "create",
            "--title", "Draft summary",
            "--text", "This is a manually supplied draft summary.",
            "--source", "event:evt_source",
            "--prompt", "Summarize the source event.",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.stderr
    data = json.loads(result.stdout)

    assert data["summary_job_id"].startswith("sum_")
    assert data["status"] == "pending_review"
    assert data["artifact_id"].startswith("art_")
    assert data["version_id"].startswith("ver_")
    assert data["event_id"].startswith("evt_")
    assert data["provenance"]["generated_by"] == "manual"
    assert data["provenance"]["invocation_mode"] == "explicit-manual"
    assert data["provenance"]["external_call_made"] is False
    assert data["provenance"]["runtime"]["provider_kind"] == "disabled"
    assert data["source_refs"][0]["record_type"] == "event"
    assert data["source_refs"][0]["record_id"] == "evt_source"

    job_path = tmp_path / ".chronicle" / "summary_jobs" / f"{data['summary_job_id']}.json"
    assert job_path.exists()


def test_summary_list_and_show(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "Summary Test"])

    create_result = runner.invoke(
        app,
        [
            "summary", "create",
            "--title", "Draft summary",
            "--text", "Draft body.",
        ],
    )
    assert create_result.exit_code == 0, create_result.stderr
    summary_job_id = _extract_summary_job_id(create_result.stdout)

    list_result = runner.invoke(app, ["summary", "list"])
    assert list_result.exit_code == 0
    assert summary_job_id in list_result.stdout
    assert "pending_review" in list_result.stdout

    show_result = runner.invoke(app, ["summary", "show", "--id", summary_job_id, "--json"])
    assert show_result.exit_code == 0
    data = json.loads(show_result.stdout)
    assert data["summary_job_id"] == summary_job_id
    assert data["status"] == "pending_review"
    assert data["provenance"]["external_call_made"] is False


def test_summary_run_creates_runtime_backed_draft(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "Summary Run Test"])

    create_result = runner.invoke(
        app,
        [
            "summary", "create",
            "--title", "Source Draft",
            "--text", "First sentence. Second sentence. Third sentence.",
            "--source", "event:evt_source",
            "--prompt", "Condense the source draft.",
            "--json",
        ],
    )
    assert create_result.exit_code == 0, create_result.stderr
    source_job = json.loads(create_result.stdout)

    run_result = runner.invoke(
        app,
        [
            "summary", "run",
            "--id", source_job["summary_job_id"],
            "--max-sentences", "2",
            "--json",
        ],
    )
    assert run_result.exit_code == 0, run_result.stderr
    result = json.loads(run_result.stdout)
    assert result["draft_summary_job_id"].startswith("sum_")
    assert result["generated_text"] == "First sentence. Second sentence."

    show_result = runner.invoke(app, ["summary", "show", "--id", result["draft_summary_job_id"], "--json"])
    assert show_result.exit_code == 0
    draft_job = json.loads(show_result.stdout)
    assert draft_job["provenance"]["generated_by"] == "runtime_manual"
    assert draft_job["provenance"]["operator"] == "summary-run"
    assert draft_job["provenance"]["prompt"] == "Condense the source draft."
    assert draft_job["source_refs"][0]["record_id"] == "evt_source"
