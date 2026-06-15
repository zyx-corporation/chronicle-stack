"""Tests for the primary `chronicle export profile` compatibility alias."""

import json
import os

import yaml
from typer.testing import CliRunner

from chronicle.cli import app


def _run_primary(tmp_path, *args):
    os.chdir(str(tmp_path))
    runner = CliRunner()
    return runner.invoke(app, list(args))


def _setup_sensitive_context(tmp_path):
    assert _run_primary(tmp_path, "init", "--title", "Primary Export Profile Alias Test").exit_code == 0
    result = _run_primary(
        tmp_path,
        "add-context",
        "--title",
        "Sensitive Alias Context Title",
        "--summary",
        "Sensitive Alias Context Summary",
        "--visibility",
        "sensitive",
        "--scope",
        "task",
    )
    assert result.exit_code == 0


def test_primary_export_format_yaml_remains_compatible(tmp_path):
    _setup_sensitive_context(tmp_path)

    result = _run_primary(tmp_path, "export", "--format", "yaml", "--redact-sensitive")

    assert result.exit_code == 0
    payload = yaml.safe_load(result.stdout)
    assert payload["export_manifest"]["export_options"]["redact_sensitive"] is True
    assert "Sensitive Alias Context Title" not in result.stdout
    assert "[REDACTED:sensitive]" in result.stdout


def test_primary_export_profile_public_review_redacts_sensitive_context(tmp_path):
    _setup_sensitive_context(tmp_path)

    result = _run_primary(
        tmp_path,
        "export",
        "profile",
        "--format",
        "yaml",
        "--profile",
        "public-review",
    )

    assert result.exit_code == 0
    payload = yaml.safe_load(result.stdout)
    assert payload["export_manifest"]["export_options"]["profile"] == "public-review"
    assert payload["export_manifest"]["export_options"]["redact_sensitive"] is True
    assert "Sensitive Alias Context Title" not in result.stdout
    assert "[REDACTED:sensitive]" in result.stdout


def test_primary_export_profile_output_json_reports_audit_without_body(tmp_path):
    _setup_sensitive_context(tmp_path)
    output = tmp_path / "profile.yaml"

    result = _run_primary(
        tmp_path,
        "export",
        "profile",
        "--format",
        "yaml",
        "--profile",
        "restricted-summary",
        "--output",
        str(output),
        "--json",
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["output"] == str(output)
    assert payload["format"] == "yaml"
    assert payload["profile"] == "restricted-summary"
    assert payload["exclude_sensitive"] is True
    assert payload["audit_id"]
    content = output.read_text(encoding="utf-8")
    assert "Sensitive Alias Context Title" not in content
    assert "Sensitive Alias Context Summary" not in content
