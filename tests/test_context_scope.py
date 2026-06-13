"""Tests for v0.2 Context Scope Model."""

import json

import pytest

from chronicle.models.context import ContextScope
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.context_service import ContextService


@pytest.fixture
def context_service(tmp_path):
    ChronicleService(tmp_path).init("Context Scope Test")
    return ContextService(tmp_path)


def test_add_context_with_formal_scope(context_service):
    """add_context with ContextScope.TASK produces correct scope."""
    ctx = context_service.add_context(
        title="Task Context",
        summary="Only for this task",
        scope=ContextScope.TASK,
    )
    assert ctx.scope == ContextScope.TASK
    assert ctx.scope_hint is not None
    assert ctx.scope_hint.value == "task"


def test_context_scope_survives_index_rebuild(context_service):
    """Context scope is preserved after index rebuild."""
    ctx = context_service.add_context(
        title="Rebuild Test",
        summary="Test scope persistence",
        scope=ContextScope.SESSION,
    )
    context_service.chronicle.rebuild_indexes()
    contexts = context_service.chronicle.index.load_contexts()
    loaded = contexts[ctx.context_id]
    assert loaded.scope == ContextScope.SESSION


def test_context_scope_backward_compat_from_scope_hint(context_service):
    """v0.1 payload with only scope_hint is read back with correct scope."""
    # Simulate a v0.1 event: scope_hint but no scope
    v01_payload = {
        "context_id": "ctx_v01test",
        "title": "Legacy Context",
        "summary": "From v0.1",
        "source_type": "conversation",
        "source_ref": "",
        "scope_hint": "artifact",
        "confidence": "medium",
        "created_at": "2026-06-13T12:00:00+09:00",
        "tags": [],
    }

    # Write it directly into JSONL
    with context_service.chronicle.paths.events_file.open("a", encoding="utf-8") as f:
        event = {
            "event_id": "evt_manual_test",
            "chronicle_id": "chr_test",
            "timestamp": "2026-06-13T12:00:00+09:00",
            "event_type": "context_added",
            "actor": "user",
            "summary": "Legacy context",
            "payload": {"context": v01_payload},
        }
        f.write(json.dumps(event) + "\n")

    context_service.chronicle.rebuild_indexes()
    contexts = context_service.chronicle.index.load_contexts()
    assert "ctx_v01test" in contexts
    loaded = contexts["ctx_v01test"]
    assert loaded.scope == ContextScope.ARTIFACT


def test_context_unknown_scope_defaults_to_unknown(context_service):
    """Missing scope and scope_hint defaults to UNKNOWN."""
    v01_payload = {
        "context_id": "ctx_noscope",
        "title": "No Scope Context",
        "summary": "No scope hint",
        "source_type": "conversation",
        "source_ref": "",
        "confidence": "medium",
        "created_at": "2026-06-13T12:00:00+09:00",
        "tags": [],
    }

    with context_service.chronicle.paths.events_file.open("a", encoding="utf-8") as f:
        event = {
            "event_id": "evt_manual_noscope",
            "chronicle_id": "chr_test",
            "timestamp": "2026-06-13T12:00:00+09:00",
            "event_type": "context_added",
            "actor": "user",
            "summary": "No scope context",
            "payload": {"context": v01_payload},
        }
        f.write(json.dumps(event) + "\n")

    context_service.chronicle.rebuild_indexes()
    contexts = context_service.chronicle.index.load_contexts()
    loaded = contexts["ctx_noscope"]
    assert loaded.scope == ContextScope.UNKNOWN


def test_cli_add_context_with_scope_json(tmp_path):
    """CLI add-context --scope task produces JSON with scope field."""
    import os
    from typer.testing import CliRunner
    from chronicle.cli import app

    os.chdir(str(tmp_path))
    runner = CliRunner()
    runner.invoke(app, ["init", "--title", "CLI Scope Test"])

    result = runner.invoke(app, [
        "add-context",
        "--title", "Task Context",
        "--summary", "Only for this task",
        "--scope", "task",
        "--json",
    ])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["scope"] == "task"


def test_cli_add_context_invalid_scope_fails(tmp_path):
    """CLI add-context with invalid scope value exits non-zero."""
    import os
    from typer.testing import CliRunner
    from chronicle.cli import app

    os.chdir(str(tmp_path))
    runner = CliRunner()
    runner.invoke(app, ["init", "--title", "CLI Invalid Scope"])

    result = runner.invoke(app, [
        "add-context",
        "--title", "Bad Scope",
        "--scope", "invalid_value",
    ])
    assert result.exit_code != 0
