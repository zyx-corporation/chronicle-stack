"""Tests for v0.8 package review workflow."""

import json
import os

from typer.testing import CliRunner

from chronicle.cli import app


def _run(tmp_path, *args):
    os.chdir(str(tmp_path))
    runner = CliRunner()
    return runner.invoke(app, list(args))


def _json(result):
    return json.loads(result.stdout)


def _create_context(tmp_path, title="Review Context", summary="safe context"):
    result = _run(
        tmp_path,
        "add-context",
        "--title",
        title,
        "--summary",
        summary,
        "--json",
    )
    assert result.exit_code == 0
    return _json(result)["context_id"]


def _classify(tmp_path, context_id, layer="internal", sensitivity="internal"):
    result = _run(
        tmp_path,
        "context",
        "classification",
        "set",
        "--context",
        context_id,
        "--layer",
        layer,
        "--sensitivity",
        sensitivity,
        "--owner",
        "review-test",
        "--reason",
        "v0.8 review",
    )
    assert result.exit_code == 0


def test_package_review_passes_for_classified_local_context(tmp_path):
    assert _run(tmp_path, "init", "--title", "v0.8 review pass").exit_code == 0
    context_id = _create_context(tmp_path)
    _classify(tmp_path, context_id)

    result = _run(
        tmp_path,
        "package",
        "review",
        "--purpose",
        "v0.8 review",
        "--target",
        "local",
        "--context",
        context_id,
        "--json",
    )
    assert result.exit_code == 0
    payload = _json(result)
    assert payload["status"] == "pass"
    assert payload["record_count"] == 1
    assert payload["findings"] == []


def test_package_review_warns_for_unclassified_context(tmp_path):
    assert _run(tmp_path, "init", "--title", "v0.8 review warning").exit_code == 0
    context_id = _create_context(tmp_path)

    result = _run(
        tmp_path,
        "package",
        "review",
        "--purpose",
        "v0.8 review",
        "--target",
        "local",
        "--context",
        context_id,
        "--json",
    )
    assert result.exit_code == 0
    payload = _json(result)
    assert payload["status"] == "warning"
    assert payload["findings"][0]["code"] == "unclassified_context"
    assert payload["findings"][0]["record_id"] == context_id


def test_package_review_blocks_external_sensitive_context_not_allowed(tmp_path):
    assert _run(tmp_path, "init", "--title", "v0.8 review blocked").exit_code == 0
    context_id = _create_context(tmp_path)
    _classify(tmp_path, context_id, layer="sensitive_context", sensitivity="sensitive")

    result = _run(
        tmp_path,
        "package",
        "review",
        "--purpose",
        "v0.8 review",
        "--target",
        "external",
        "--context",
        context_id,
        "--json",
    )
    assert result.exit_code == 1
    payload = _json(result)
    assert payload["status"] == "blocked"
    assert any(finding["code"] == "external_sensitive_context_not_allowed" for finding in payload["findings"])


def test_package_review_can_review_persisted_package(tmp_path):
    assert _run(tmp_path, "init", "--title", "v0.8 persisted review").exit_code == 0
    context_id = _create_context(tmp_path)
    _classify(tmp_path, context_id)

    persist = _run(
        tmp_path,
        "package",
        "context",
        "--purpose",
        "persist review",
        "--target",
        "local",
        "--context",
        context_id,
        "--persist",
    )
    assert persist.exit_code == 0
    package_id = persist.stdout.splitlines()[0].split(": ", 1)[1]

    result = _run(tmp_path, "package", "review", "--package", package_id, "--json")
    assert result.exit_code == 0
    payload = _json(result)
    assert payload["status"] == "pass"
    assert payload["record_count"] == 1
