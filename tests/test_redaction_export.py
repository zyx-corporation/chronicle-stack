"""Tests for redaction-aware export options (v0.4)."""

import os

import yaml
from typer.testing import CliRunner

from chronicle.cli import app


def _run(tmp_path, *args):
    os.chdir(str(tmp_path))
    runner = CliRunner()
    return runner.invoke(app, list(args))


def _setup_sensitive_context(tmp_path):
    assert _run(tmp_path, "init", "--title", "Redaction Test").exit_code == 0
    result = _run(
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


def _setup_sensitive_artifact(tmp_path):
    assert _run(tmp_path, "init", "--title", "Redaction Artifact").exit_code == 0
    source = tmp_path / "secret.md"
    source.write_text("secret body", encoding="utf-8")
    result = _run(
        tmp_path,
        "artifact",
        "create",
        "--title",
        "Sensitive Artifact Title",
        "--type",
        "document",
        "--file",
        str(source),
        "--visibility",
        "sensitive",
    )
    assert result.exit_code == 0


def test_yaml_redact_sensitive_context(tmp_path):
    _setup_sensitive_context(tmp_path)

    result = _run(tmp_path, "export", "--format", "yaml", "--redact-sensitive")
    payload = yaml.safe_load(result.stdout)

    assert result.exit_code == 0
    assert payload["export_manifest"]["export_options"]["redact_sensitive"] is True
    assert "Sensitive Context Title" not in result.stdout
    assert "Sensitive Context Summary" not in result.stdout
    assert "[REDACTED:sensitive]" in result.stdout


def test_yaml_exclude_sensitive_context(tmp_path):
    _setup_sensitive_context(tmp_path)

    result = _run(tmp_path, "export", "--format", "yaml", "--exclude-sensitive")
    payload = yaml.safe_load(result.stdout)

    assert result.exit_code == 0
    assert payload["export_manifest"]["export_options"]["exclude_sensitive"] is True
    assert payload["contexts"] == {}
    assert "Sensitive Context Title" not in result.stdout


def test_html_redact_sensitive_artifact(tmp_path):
    _setup_sensitive_artifact(tmp_path)

    result = _run(tmp_path, "export", "--format", "html", "--redact-sensitive")

    assert result.exit_code == 0
    assert "Sensitive Artifact Title" not in result.stdout
    assert "[REDACTED:sensitive]" in result.stdout
    assert "Redaction-aware export" in result.stdout


def test_redaction_options_are_mutually_exclusive(tmp_path):
    _setup_sensitive_context(tmp_path)

    result = _run(
        tmp_path,
        "export",
        "--format",
        "yaml",
        "--redact-sensitive",
        "--exclude-sensitive",
    )

    assert result.exit_code != 0
    assert "Use either --redact-sensitive or --exclude-sensitive" in result.stdout


def test_redaction_options_only_support_yaml_and_html(tmp_path):
    _setup_sensitive_context(tmp_path)

    result = _run(tmp_path, "export", "--format", "graph-json", "--redact-sensitive")

    assert result.exit_code != 0
    assert "supports yaml and html only" in result.stdout


def test_redaction_export_does_not_mutate_jsonl(tmp_path):
    _setup_sensitive_context(tmp_path)
    events_file = tmp_path / ".chronicle" / "chronicle.jsonl"
    before = events_file.read_text(encoding="utf-8")

    assert _run(tmp_path, "export", "--format", "yaml", "--redact-sensitive").exit_code == 0
    assert _run(tmp_path, "export", "--format", "html", "--exclude-sensitive").exit_code == 0

    after = events_file.read_text(encoding="utf-8")
    assert after == before
