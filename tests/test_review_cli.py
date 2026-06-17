"""Review workflow CLI tests."""

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


def _create_summary_job(tmp_path: Path) -> str:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "Review Test"])
    result = runner.invoke(
        app,
        [
            "summary", "create",
            "--title", "Review target",
            "--text", "Draft summary body.",
        ],
    )
    assert result.exit_code == 0, result.stderr
    return _extract_summary_job_id(result.stdout)


def test_review_queue_lists_pending_summary_job(tmp_path: Path) -> None:
    summary_job_id = _create_summary_job(tmp_path)

    result = runner.invoke(app, ["review", "queue"])

    assert result.exit_code == 0
    assert summary_job_id in result.stdout
    assert "pending_review" in result.stdout


def test_review_approve_updates_summary_job_and_records_decision(tmp_path: Path) -> None:
    summary_job_id = _create_summary_job(tmp_path)

    approve_result = runner.invoke(
        app,
        ["review", "approve", "--id", summary_job_id, "--reason", "Looks good", "--json"],
    )

    assert approve_result.exit_code == 0, approve_result.stderr
    decision = json.loads(approve_result.stdout)
    assert decision["review_id"].startswith("rvw_")
    assert decision["target_id"] == summary_job_id
    assert decision["action"] == "approve"
    assert decision["resulting_status"] == "approved"

    show_result = runner.invoke(app, ["summary", "show", "--id", summary_job_id, "--json"])
    assert show_result.exit_code == 0
    summary = json.loads(show_result.stdout)
    assert summary["status"] == "approved"

    decisions_result = runner.invoke(app, ["review", "decisions", "--json"])
    assert decisions_result.exit_code == 0
    decisions = json.loads(decisions_result.stdout)
    assert decisions[0]["review_id"] == decision["review_id"]


def test_review_reject_updates_summary_job(tmp_path: Path) -> None:
    summary_job_id = _create_summary_job(tmp_path)

    reject_result = runner.invoke(
        app,
        ["review", "reject", "--id", summary_job_id, "--reason", "Incorrect", "--json"],
    )

    assert reject_result.exit_code == 0, reject_result.stderr
    decision = json.loads(reject_result.stdout)
    assert decision["action"] == "reject"
    assert decision["resulting_status"] == "rejected"

    show_result = runner.invoke(app, ["summary", "show", "--id", summary_job_id, "--json"])
    summary = json.loads(show_result.stdout)
    assert summary["status"] == "rejected"


def test_review_request_changes_keeps_item_in_queue(tmp_path: Path) -> None:
    summary_job_id = _create_summary_job(tmp_path)

    request_result = runner.invoke(
        app,
        ["review", "request-changes", "--id", summary_job_id, "--reason", "Need sources", "--json"],
    )

    assert request_result.exit_code == 0, request_result.stderr
    decision = json.loads(request_result.stdout)
    assert decision["action"] == "request_changes"
    assert decision["resulting_status"] == "request_changes"

    queue_result = runner.invoke(app, ["review", "queue", "--json"])
    queue = json.loads(queue_result.stdout)
    assert queue[0]["summary_job_id"] == summary_job_id
    assert queue[0]["status"] == "request_changes"
