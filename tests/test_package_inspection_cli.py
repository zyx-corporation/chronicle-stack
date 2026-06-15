"""Tests for persisted package inspection CLI."""

import json
import os
from datetime import datetime, timezone

from typer.testing import CliRunner

from chronicle.cli_package import package_app
from chronicle.models.context import Context, ContextScope
from chronicle.models.event import Actor, ChronicleEvent, EventType
from chronicle.services.chronicle_service import ChronicleService


def _run_package(tmp_path, *args):
    os.chdir(str(tmp_path))
    runner = CliRunner()
    return runner.invoke(package_app, list(args))


def _append_context(root, context: Context) -> None:
    service = ChronicleService(root)
    metadata = service.load_metadata()
    event = ChronicleEvent(
        event_id=f"evt_{context.context_id}",
        chronicle_id=metadata.chronicle_id,
        timestamp=datetime(2026, 6, 15, tzinfo=timezone.utc),
        event_type=EventType.CONTEXT_ADDED,
        actor=Actor.USER,
        summary=f"Add {context.title}",
        payload={"context": context.model_dump(mode="json")},
    )
    service.append_event(event)
    service.rebuild_indexes()


def _setup_package(tmp_path) -> str:
    ChronicleService(tmp_path).init("Package CLI Test")
    _append_context(
        tmp_path,
        Context(
            context_id="ctx_cli_pkg",
            title="CLI Package Context",
            summary="Body should not appear in record summary output",
            scope=ContextScope.TASK,
            created_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
        ),
    )

    result = _run_package(tmp_path, "context", "--purpose", "CLI inspection", "--persist")
    assert result.exit_code == 0
    for line in result.stdout.splitlines():
        if line.startswith("Package persisted:"):
            return line.split(":", 1)[1].strip()
    raise AssertionError(f"package id not found in output: {result.stdout}")


def test_package_inspection_list_show_and_records_json(tmp_path):
    package_id = _setup_package(tmp_path)

    list_result = _run_package(tmp_path, "list", "--json")
    assert list_result.exit_code == 0
    packages = json.loads(list_result.stdout)
    assert packages[0]["package_id"] == package_id
    assert packages[0]["referenced_records"] == ["ctx_cli_pkg"]

    show_result = _run_package(tmp_path, "show", "--package", package_id, "--json")
    assert show_result.exit_code == 0
    manifest = json.loads(show_result.stdout)
    assert manifest["package_id"] == package_id
    assert manifest["purpose"] == "CLI inspection"

    records_result = _run_package(tmp_path, "records", "--package", package_id, "--json")
    assert records_result.exit_code == 0
    records = json.loads(records_result.stdout)
    assert records[0]["record_id"] == "ctx_cli_pkg"
    assert records[0]["has_content"] is True
    assert "content" not in records[0]


def test_package_records_human_output_does_not_dump_body(tmp_path):
    package_id = _setup_package(tmp_path)

    result = _run_package(tmp_path, "records", "--package", package_id)

    assert result.exit_code == 0
    assert "ctx_cli_pkg" in result.stdout
    assert "has_content=True" in result.stdout
    assert "Body should not appear in record summary output" not in result.stdout
    assert "CLI Package Context" not in result.stdout
