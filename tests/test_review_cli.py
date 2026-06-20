"""Tests for append-only review CLI workflow."""

import json

from typer.testing import CliRunner

from chronicle.cli import app
from chronicle.services.audit_service import AuditService
from chronicle.services.review_service import review_action_commands
from chronicle.services.runtime_service import RuntimeService


def _setup(tmp_path):
    runner = CliRunner()
    result = runner.invoke(app, ["init", "--title", "Review Test"], catch_exceptions=False)
    assert result.exit_code == 0
    runtime_record = RuntimeService(tmp_path).summarize(
        text="Review me locally.",
        record=True,
    )
    return runner, runtime_record.event_id


def test_review_queue_lists_needs_review_target(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner, event_id = _setup(tmp_path)

    result = runner.invoke(app, ["review", "queue", "--json"], catch_exceptions=False)

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload[0]["target_event_id"] == event_id
    assert payload[0]["pending"] is True
    assert payload[0]["available_actions"] == [
        item["command"] for item in review_action_commands(event_id)
    ]


def test_review_approve_records_reviewer_event_and_resolves_queue(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner, event_id = _setup(tmp_path)

    result = runner.invoke(
        app,
        ["review", "approve", "--event", event_id, "--reviewer", "alice", "--note", "looks good", "--json"],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["target_event_id"] == event_id
    assert payload["disposition"] == "approve"
    assert payload["audit_id"].startswith("aud_")
    assert payload["reviewer_identity"]["label"] == "alice"
    assert payload["reviewer_identity"]["kind"] == "user_declared"
    audit_events = AuditService(tmp_path).list_events()
    assert audit_events[-1].operation.value == "review_decision"
    assert audit_events[-1].source_event_id == payload["review_event_id"]
    queue_result = runner.invoke(app, ["review", "queue", "--json"], catch_exceptions=False)
    assert queue_result.exit_code == 0
    assert json.loads(queue_result.stdout) == []


def test_review_request_changes_keeps_target_in_queue(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner, event_id = _setup(tmp_path)

    result = runner.invoke(
        app,
        [
            "review",
            "request-changes",
            "--event",
            event_id,
            "--reviewer",
            "alice",
            "--reviewer-kind",
            "local_operator",
            "--session",
            "terminal-1",
            "--note",
            "revise wording",
            "--json",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    queue_result = runner.invoke(app, ["review", "queue", "--json"], catch_exceptions=False)
    payload = json.loads(queue_result.stdout)
    assert payload[0]["target_event_id"] == event_id
    assert payload[0]["pending"] is True
    assert payload[0]["latest_disposition"] == "request_changes"
    assert payload[0]["latest_audit_id"].startswith("aud_")
    assert payload[0]["history_count"] == 1
    assert payload[0]["latest_reviewer_identity"]["kind"] == "local_operator"


def test_review_history_tracks_multiple_decisions(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner, event_id = _setup(tmp_path)

    first = runner.invoke(
        app,
        ["review", "request-changes", "--event", event_id, "--reviewer", "alice", "--note", "revise wording", "--json"],
        catch_exceptions=False,
    )
    assert first.exit_code == 0
    second = runner.invoke(
        app,
        ["review", "approve", "--event", event_id, "--reviewer", "bob", "--note", "fixed", "--json"],
        catch_exceptions=False,
    )
    assert second.exit_code == 0

    queue_result = runner.invoke(app, ["review", "queue", "--include-resolved", "--json"], catch_exceptions=False)
    payload = json.loads(queue_result.stdout)
    assert payload[0]["history_count"] == 2
    assert payload[0]["latest_disposition"] == "approve"


def test_review_approve_reports_audit_failure_as_chronicle_error(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner, event_id = _setup(tmp_path)

    def _broken_audit_record(self, *args, **kwargs):
        raise RuntimeError("audit insert boom")

    monkeypatch.setattr(AuditService, "record", _broken_audit_record)

    result = runner.invoke(
        app,
        ["review", "approve", "--event", event_id, "--reviewer", "alice", "--json"],
        catch_exceptions=False,
    )

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["error"]["code"] == "REVIEW_AUDIT_INSERTION_FAILED"
