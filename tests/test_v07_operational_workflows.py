"""Tests for v0.7 operational hardening workflows."""

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


def test_context_classification_workflow_remediates_doctor_warning(tmp_path):
    assert _run(tmp_path, "init", "--title", "v0.7 classification").exit_code == 0
    add_result = _run(
        tmp_path,
        "add-context",
        "--title",
        "Classify Me",
        "--summary",
        "release smoke context",
        "--json",
    )
    assert add_result.exit_code == 0
    context_id = _json(add_result)["context_id"]

    missing = _run(tmp_path, "context", "classification", "missing", "--json")
    assert missing.exit_code == 0
    assert [context["context_id"] for context in _json(missing)] == [context_id]

    classify = _run(
        tmp_path,
        "context",
        "classification",
        "set",
        "--context",
        context_id,
        "--layer",
        "internal",
        "--sensitivity",
        "internal",
        "--owner",
        "release-smoke",
        "--reason",
        "v0.7 smoke",
        "--json",
    )
    assert classify.exit_code == 0
    classified = _json(classify)
    assert classified["classification"]["sensitivity"] == "internal"
    assert classified["classification"]["integrity"]["hash"]

    missing_after = _run(tmp_path, "context", "classification", "missing", "--json")
    assert missing_after.exit_code == 0
    assert _json(missing_after) == []

    doctor = _run(tmp_path, "doctor", "--json")
    checks = {check["check_id"]: check for check in _json(doctor)["checks"]}
    assert checks["security_context_classification_present"]["severity"] == "ok"
    assert checks["security_integrity_metadata_present"]["severity"] == "ok"


def test_audit_workflow_creates_parseable_audit_log(tmp_path):
    assert _run(tmp_path, "init", "--title", "v0.7 audit").exit_code == 0

    record = _run(
        tmp_path,
        "audit",
        "record",
        "--operation",
        "export",
        "--purpose",
        "v0.7 smoke",
        "--target",
        "local",
        "--summary",
        "audit smoke",
        "--json",
    )
    assert record.exit_code == 0
    audit_id = _json(record)["audit_id"]

    listed = _run(tmp_path, "audit", "list", "--json")
    assert listed.exit_code == 0
    assert [event["audit_id"] for event in _json(listed)] == [audit_id]

    shown = _run(tmp_path, "audit", "show", "--id", audit_id, "--json")
    assert shown.exit_code == 0
    assert _json(shown)["operation"] == "export"

    doctor = _run(tmp_path, "doctor", "--json")
    checks = {check["check_id"]: check for check in _json(doctor)["checks"]}
    assert checks["security_audit_log_parseable"]["severity"] == "ok"


def test_lifecycle_workflow_creates_parseable_lifecycle_log(tmp_path):
    assert _run(tmp_path, "init", "--title", "v0.7 lifecycle").exit_code == 0
    add_result = _run(
        tmp_path,
        "add-context",
        "--title",
        "Lifecycle Target",
        "--summary",
        "target context",
        "--json",
    )
    assert add_result.exit_code == 0
    context_id = _json(add_result)["context_id"]

    record = _run(
        tmp_path,
        "lifecycle",
        "record",
        "--target",
        context_id,
        "--target-kind",
        "context",
        "--action",
        "seal",
        "--reason",
        "v0.7 smoke",
        "--json",
    )
    assert record.exit_code == 0
    lifecycle_id = _json(record)["lifecycle_id"]

    listed = _run(tmp_path, "lifecycle", "list", "--json")
    assert listed.exit_code == 0
    assert [event["lifecycle_id"] for event in _json(listed)] == [lifecycle_id]

    shown = _run(tmp_path, "lifecycle", "show", "--id", lifecycle_id, "--json")
    assert shown.exit_code == 0
    assert _json(shown)["action"] == "seal"

    doctor = _run(tmp_path, "doctor", "--json")
    checks = {check["check_id"]: check for check in _json(doctor)["checks"]}
    assert checks["security_lifecycle_log_parseable"]["severity"] == "ok"


def test_v07_operational_smoke_reaches_warning_free_security_surfaces(tmp_path):
    assert _run(tmp_path, "init", "--title", "v0.7 smoke").exit_code == 0
    add_result = _run(
        tmp_path,
        "add-context",
        "--title",
        "Operational Context",
        "--summary",
        "context for v0.7 smoke",
        "--json",
    )
    context_id = _json(add_result)["context_id"]

    assert _run(
        tmp_path,
        "context",
        "classification",
        "set",
        "--context",
        context_id,
        "--layer",
        "internal",
        "--sensitivity",
        "internal",
    ).exit_code == 0
    assert _run(
        tmp_path,
        "audit",
        "record",
        "--operation",
        "export",
        "--purpose",
        "v0.7 smoke",
        "--target",
        "local",
    ).exit_code == 0
    assert _run(
        tmp_path,
        "lifecycle",
        "record",
        "--target",
        context_id,
        "--target-kind",
        "context",
        "--action",
        "seal",
    ).exit_code == 0

    doctor = _run(tmp_path, "doctor", "--json")
    payload = _json(doctor)
    checks = {check["check_id"]: check for check in payload["checks"]}
    assert checks["security_context_classification_present"]["severity"] == "ok"
    assert checks["security_audit_log_parseable"]["severity"] == "ok"
    assert checks["security_lifecycle_log_parseable"]["severity"] == "ok"
    assert checks["graph_export_available"]["severity"] == "ok"
    assert checks["html_export_available"]["severity"] == "ok"
