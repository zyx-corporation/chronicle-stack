"""Tests for audit insertion on security-aware export profiles."""

import json
import os

from typer.testing import CliRunner

from chronicle.cli import app
from chronicle.cli_export import export_app
from chronicle.models.audit import AuditOperation
from chronicle.services.audit_service import AuditService


def _run_primary(tmp_path, *args):
    os.chdir(str(tmp_path))
    runner = CliRunner()
    return runner.invoke(app, list(args))


def _run_export(tmp_path, *args):
    os.chdir(str(tmp_path))
    runner = CliRunner()
    return runner.invoke(export_app, list(args))


def _setup_sensitive_context(tmp_path):
    assert _run_primary(tmp_path, "init", "--title", "Export Audit Test").exit_code == 0
    result = _run_primary(
        tmp_path,
        "add-context",
        "--title",
        "Sensitive Context Title",
        "--summary",
        "Sensitive Context Summary",
        "--visibility",
        "sensitive",
        "--scope",
        "task",
    )
    assert result.exit_code == 0


def test_profile_export_writes_audit_event(tmp_path):
    _setup_sensitive_context(tmp_path)
    output = tmp_path / "public-review.yaml"

    result = _run_export(
        tmp_path,
        "profile",
        "--profile",
        "public-review",
        "--format",
        "yaml",
        "--output",
        str(output),
        "--json",
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["audit_id"].startswith("aud_")

    events = AuditService(tmp_path).list_events()
    assert len(events) == 1
    event = events[0]
    assert event.operation == AuditOperation.EXPORT
    assert event.actor == "chronicle-export"
    assert event.target_environment == "file"
    assert event.metadata["format"] == "yaml"
    assert event.metadata["profile"] == "public-review"
    assert event.metadata["redact_sensitive"] == "true"
    assert event.metadata["exclude_sensitive"] == "false"
    assert event.metadata["output_path"] == str(output)


def test_profile_export_audit_does_not_copy_exported_body(tmp_path):
    _setup_sensitive_context(tmp_path)

    result = _run_export(
        tmp_path,
        "profile",
        "--profile",
        "public-review",
        "--format",
        "yaml",
    )

    assert result.exit_code == 0
    assert "[REDACTED:sensitive]" in result.stdout

    audit_text = (tmp_path / ".chronicle" / "audit.jsonl").read_text(encoding="utf-8")
    assert "Sensitive Context Title" not in audit_text
    assert "Sensitive Context Summary" not in audit_text
    assert "[REDACTED:sensitive]" not in audit_text
    assert "public-review" in audit_text
