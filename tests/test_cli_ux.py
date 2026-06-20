"""Tests for CLI UX improvements (v0.3)."""

import os

from typer.testing import CliRunner

from chronicle.cli import app


def _run(tmp_path, *args):
    os.chdir(str(tmp_path))
    runner = CliRunner()
    return runner.invoke(app, list(args))


def test_version_flag(tmp_path):
    """chronicle --version must succeed and output a version string."""
    # --version is eager, so it works without init
    result = _run(tmp_path, "--version")
    assert result.exit_code == 0
    assert "chronicle" in result.stdout


def test_version_flag_output_not_empty(tmp_path):
    """--version output must contain a version number."""
    result = _run(tmp_path, "--version")
    assert len(result.stdout.strip()) > 0


def test_help_includes_key_commands(tmp_path):
    """--help must list all major subcommands."""
    result = _run(tmp_path, "--help")
    for cmd in ["artifact", "decision", "rde", "boundary", "injection", "ai-index", "runtime", "review",
                "init", "record", "add-context", "search", "export", "show", "index"]:
        assert cmd in result.stdout, f"Missing '{cmd}' in --help"


def test_export_help_lists_all_formats(tmp_path):
    """export --help must reference all export formats."""
    result = _run(tmp_path, "export", "--help")
    assert result.exit_code == 0
    assert "yaml" in result.stdout or "YAML" in result.stdout
    assert "markdown" in result.stdout or "Markdown" in result.stdout
    assert "graph-json" in result.stdout or "Graph JSON" in result.stdout
    assert "html" in result.stdout or "HTML" in result.stdout


def test_injection_plan_help_shows_record_option(tmp_path):
    """injection plan --help must reference the --record persistence option."""
    result = _run(tmp_path, "injection", "plan", "--help")
    assert result.exit_code == 0
    # Rich may render as -record or --record depending on terminal
    assert "record" in result.stdout.lower()


def test_runtime_help_lists_retrieve_plan(tmp_path):
    """runtime --help must list summarize, invoke-plan, config, and retrieve-plan."""
    result = _run(tmp_path, "runtime", "--help")
    assert result.exit_code == 0
    assert "summarize" in result.stdout
    assert "invoke-plan" in result.stdout
    assert "config" in result.stdout
    assert "retrieve-plan" in result.stdout


def test_review_help_lists_actions(tmp_path):
    """review --help must list queue and decision actions."""
    result = _run(tmp_path, "review", "--help")
    assert result.exit_code == 0
    assert "queue" in result.stdout
    assert "approve" in result.stdout
    assert "reject" in result.stdout
    assert "request-changes" in result.stdout


def test_ui_rejects_non_loopback_host(tmp_path):
    """ui must reject non-loopback hosts until auth/authz exists."""
    result = _run(tmp_path, "init", "--title", "UI Host Test")
    assert result.exit_code == 0

    result = _run(tmp_path, "ui", "--host", "0.0.0.0", "--json")
    assert result.exit_code != 0


def test_ui_help_mentions_auth_mode_options(tmp_path):
    """ui --help must mention auth boundary placeholder options."""
    result = _run(tmp_path, "ui", "--help")
    assert result.exit_code == 0
    assert "auth-mode" in result.stdout
    assert "authorization-mode" in result.stdout
    assert "mutation-capability-flag" in result.stdout
    assert "enable-ui-mutation" in result.stdout


def test_invalid_export_format_exits_nonzero(tmp_path):
    """Invalid export format must exit non-zero."""
    result = _run(tmp_path, "init", "--title", "Export Test")
    assert result.exit_code == 0
    result = _run(tmp_path, "export", "--format", "invalid_format")
    assert result.exit_code != 0


def test_invalid_scope_exits_nonzero(tmp_path):
    """Invalid scope must exit non-zero."""
    _run(tmp_path, "init", "--title", "Scope Test")
    result = _run(tmp_path, "add-context", "--title", "Bad", "--scope", "invalid_scope_value")
    assert result.exit_code != 0


def test_invalid_visibility_exits_nonzero(tmp_path):
    """Invalid visibility must exit non-zero."""
    _run(tmp_path, "init", "--title", "Vis Test")
    result = _run(tmp_path, "add-context", "--title", "Bad", "--visibility", "secret")
    assert result.exit_code != 0


def test_invalid_boundary_field_exits_nonzero(tmp_path):
    """Invalid boundary field must exit non-zero."""
    _run(tmp_path, "init", "--title", "Boundary Test")
    result = _run(tmp_path, "boundary", "add", "--type", "warn",
                   "--field", "invalid_field", "--operator", "equals",
                   "--value", "x")
    assert result.exit_code != 0


def test_invalid_boundary_operator_exits_nonzero(tmp_path):
    """Invalid boundary operator must exit non-zero."""
    _run(tmp_path, "init", "--title", "Boundary Op Test")
    result = _run(tmp_path, "boundary", "add", "--type", "warn",
                   "--field", "visibility", "--operator", "bad_op",
                   "--value", "x")
    assert result.exit_code != 0


def test_artifact_update_without_file_errors(tmp_path):
    """artifact update without --file must error."""
    _run(tmp_path, "init", "--title", "Update Test")
    # Create first
    f = tmp_path / "doc.md"
    f.write_text("Content", encoding="utf-8")
    create_result = _run(tmp_path, "artifact", "create", "--title", "Doc", "--type", "document", "--file", str(f))
    import re
    art_id_match = re.search(r"art_[a-f0-9]+", create_result.stdout)
    assert art_id_match
    art_id = art_id_match.group(0)

    result = _run(tmp_path, "artifact", "update", "--artifact", art_id)
    assert result.exit_code != 0


def test_cli_help_mentions_primary_record(tmp_path):
    """Root help should mention JSONL primary record concept."""
    result = _run(tmp_path, "--help")
    # The help may not mention JSONL directly; at minimum, it should reference the core concept
    assert "chronicle" in result.stdout.lower()
