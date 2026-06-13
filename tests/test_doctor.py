"""Tests for chronicle doctor health checks (v0.4)."""

import json
import os
import shutil
from datetime import datetime, timezone

from typer.testing import CliRunner

from chronicle.cli import app


def _run(tmp_path, *args):
    os.chdir(str(tmp_path))
    runner = CliRunner()
    return runner.invoke(app, list(args))


def test_doctor_healthy_chronicle_human_output(tmp_path):
    """Healthy Chronicle should produce ok doctor output."""
    assert _run(tmp_path, "init", "--title", "Doctor Test").exit_code == 0

    result = _run(tmp_path, "doctor")

    assert result.exit_code == 0
    assert "Chronicle Doctor" in result.stdout
    assert "Status: ok" in result.stdout
    assert "chronicle_jsonl_exists" in result.stdout


def test_doctor_healthy_chronicle_json_output(tmp_path):
    """doctor --json should produce a stable parseable report."""
    assert _run(tmp_path, "init", "--title", "Doctor JSON").exit_code == 0

    result = _run(tmp_path, "doctor", "--json")
    payload = json.loads(result.stdout)

    assert result.exit_code == 0
    assert payload["status"] == "ok"
    assert payload["chronicle_id"].startswith("chr_")
    assert isinstance(payload["checks"], list)
    assert {check["check_id"] for check in payload["checks"]} >= {
        "chronicle_dir_exists",
        "chronicle_jsonl_exists",
        "metadata_exists",
        "jsonl_parseable",
    }


def test_doctor_missing_chronicle_errors(tmp_path):
    """doctor should fail when no Chronicle exists."""
    result = _run(tmp_path, "doctor", "--json")
    payload = json.loads(result.stdout)

    assert result.exit_code != 0
    assert payload["status"] == "error"
    checks = {check["check_id"]: check for check in payload["checks"]}
    assert checks["chronicle_dir_exists"]["severity"] == "error"
    assert checks["chronicle_jsonl_exists"]["severity"] == "error"


def test_doctor_corrupt_jsonl_errors(tmp_path):
    """doctor should report corrupt JSONL lines as errors."""
    assert _run(tmp_path, "init", "--title", "Corrupt").exit_code == 0
    events_file = tmp_path / ".chronicle" / "chronicle.jsonl"
    events_file.write_text(events_file.read_text(encoding="utf-8") + "{bad json\n", encoding="utf-8")

    result = _run(tmp_path, "doctor", "--json")
    payload = json.loads(result.stdout)

    assert result.exit_code != 0
    assert payload["status"] == "error"
    checks = {check["check_id"]: check for check in payload["checks"]}
    assert checks["jsonl_parseable"]["severity"] == "error"
    assert "line" in checks["jsonl_parseable"]["detail"]


def test_doctor_missing_indexes_warning_does_not_rebuild(tmp_path):
    """Missing derived indexes should warn but not trigger automatic rebuild."""
    assert _run(tmp_path, "init", "--title", "Indexes").exit_code == 0
    indexes_dir = tmp_path / ".chronicle" / "indexes"
    shutil.rmtree(indexes_dir)

    result = _run(tmp_path, "doctor", "--json")
    payload = json.loads(result.stdout)

    assert result.exit_code == 0
    assert payload["status"] == "warning"
    assert not indexes_dir.exists()
    checks = {check["check_id"]: check for check in payload["checks"]}
    assert checks["indexes_present"]["severity"] == "warning"


def test_doctor_does_not_mutate_jsonl(tmp_path):
    """doctor must not change chronicle.jsonl."""
    assert _run(tmp_path, "init", "--title", "No Mutation").exit_code == 0
    events_file = tmp_path / ".chronicle" / "chronicle.jsonl"
    before = events_file.read_text(encoding="utf-8")

    assert _run(tmp_path, "doctor").exit_code == 0

    after = events_file.read_text(encoding="utf-8")
    assert after == before


def test_doctor_recorded_injection_plan_missing_context_warning(tmp_path):
    """Recorded InjectionPlans that reference missing Contexts should warn."""
    assert _run(tmp_path, "init", "--title", "Bad IP").exit_code == 0
    events_file = tmp_path / ".chronicle" / "chronicle.jsonl"
    event = {
        "event_id": "evt_bad_ip",
        "chronicle_id": "chr_test",
        "timestamp": datetime.now(timezone.utc).astimezone().isoformat(),
        "event_type": "injection_plan_recorded",
        "actor": "user",
        "summary": "bad injection plan",
        "payload": {
            "injection_plan": {
                "plan_id": "ip_bad",
                "task": "bad refs",
                "created_at": datetime.now(timezone.utc).astimezone().isoformat(),
                "selected": [{"context_id": "ctx_missing", "title": "Missing"}],
                "warned": [],
                "excluded": [],
                "notes": [],
            }
        },
    }
    with events_file.open("a", encoding="utf-8") as file:
        file.write(json.dumps(event) + "\n")

    result = _run(tmp_path, "doctor", "--json")
    payload = json.loads(result.stdout)

    assert result.exit_code == 0
    assert payload["status"] == "warning"
    checks = {check["check_id"]: check for check in payload["checks"]}
    assert checks["recorded_injection_plan_context_refs"]["severity"] == "warning"
    assert "ctx_missing" in checks["recorded_injection_plan_context_refs"]["detail"]
