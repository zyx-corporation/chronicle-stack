"""Tests for the primary `chronicle context` compatibility alias."""

import json
import os
from datetime import datetime, timezone

from typer.testing import CliRunner

from chronicle.cli import app
from chronicle.models.classification import AllowedOperation, ClassificationLayer, ClassificationMetadata, LlmPolicy
from chronicle.models.context import Context, ContextScope
from chronicle.models.event import Actor, ChronicleEvent, EventType
from chronicle.services.chronicle_service import ChronicleService


def _run_primary(tmp_path, *args):
    os.chdir(str(tmp_path))
    runner = CliRunner()
    return runner.invoke(app, list(args))


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


def _setup_local_allowed_context(tmp_path) -> None:
    ChronicleService(tmp_path).init("Primary Context CLI Alias Test")
    _append_context(
        tmp_path,
        Context(
            context_id="ctx_primary_context",
            title="Primary Context Alias",
            summary="Primary alias dry-run body",
            scope=ContextScope.TASK,
            created_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
            classification=ClassificationMetadata(
                layer=ClassificationLayer.INTERNAL,
                allowed_operations=[AllowedOperation.VIEW, AllowedOperation.INJECT],
                llm_policy=LlmPolicy(local_allowed=True, external_allowed=False, masking_required=True),
            ),
        ),
    )


def test_primary_context_alias_check_json(tmp_path):
    _setup_local_allowed_context(tmp_path)

    result = _run_primary(
        tmp_path,
        "context",
        "check",
        "--target",
        "local",
        "--purpose",
        "primary alias dry-run",
        "--json",
    )

    assert result.exit_code == 0
    report = json.loads(result.stdout)
    assert report["status"] == "ok"
    assert report["target"] == "local"
    assert report["purpose"] == "primary alias dry-run"
    assert report["context_count"] == 1
    assert report["findings"][0]["context_id"] == "ctx_primary_context"


def test_primary_context_alias_check_human_output(tmp_path):
    _setup_local_allowed_context(tmp_path)

    result = _run_primary(
        tmp_path,
        "context",
        "check",
        "--target",
        "local",
        "--purpose",
        "primary alias dry-run",
    )

    assert result.exit_code == 0
    assert "Chronicle Context Use Check" in result.stdout
    assert "Status: ok" in result.stdout
    assert "Target: local" in result.stdout
    assert "ctx_primary_context" in result.stdout
