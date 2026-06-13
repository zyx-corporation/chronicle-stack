"""Tests for v0.2 visibility_hint on Context and Artifact."""

import json

import pytest

from chronicle.models.artifact import ArtifactType
from chronicle.models.visibility import VisibilityHint
from chronicle.services.artifact_service import ArtifactService
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.context_service import ContextService


@pytest.fixture
def chronicle_svc(tmp_path):
    ChronicleService(tmp_path).init("Visibility Test")
    return ChronicleService(tmp_path)


def test_add_context_with_visibility_hint(chronicle_svc):
    """ContextService.add_context with visibility_hint sets it correctly."""
    svc = ContextService(chronicle_svc.paths.root)
    ctx = svc.add_context(
        title="Private Context",
        summary="Private note",
        visibility_hint=VisibilityHint.PRIVATE,
    )
    assert ctx.visibility_hint == VisibilityHint.PRIVATE


def test_create_artifact_with_visibility_hint(chronicle_svc):
    """ArtifactService.create with visibility_hint sets it correctly."""
    svc = ArtifactService(chronicle_svc.paths.root)
    source = chronicle_svc.paths.root / "spec.md"
    source.write_text("# Sensitive Spec", encoding="utf-8")
    artifact, _ = svc.create(
        title="Sensitive Spec",
        artifact_type=ArtifactType.SPECIFICATION,
        source_file=source,
        visibility_hint=VisibilityHint.SENSITIVE,
    )
    assert artifact.visibility_hint == VisibilityHint.SENSITIVE


def test_visibility_hint_defaults_to_unknown(chronicle_svc):
    """Context/Artifact without explicit visibility_hint defaults to UNKNOWN."""
    ctx_svc = ContextService(chronicle_svc.paths.root)
    ctx = ctx_svc.add_context(title="Default Context")
    assert ctx.visibility_hint == VisibilityHint.UNKNOWN

    art_svc = ArtifactService(chronicle_svc.paths.root)
    source = chronicle_svc.paths.root / "doc.md"
    source.write_text("Content", encoding="utf-8")
    artifact, _ = art_svc.create(
        title="Default Artifact",
        artifact_type=ArtifactType.DOCUMENT,
        source_file=source,
    )
    assert artifact.visibility_hint == VisibilityHint.UNKNOWN


def test_visibility_hint_survives_index_rebuild(chronicle_svc):
    """visibility_hint is preserved after index rebuild for both Context and Artifact."""
    ctx_svc = ContextService(chronicle_svc.paths.root)
    ctx = ctx_svc.add_context(
        title="Rebuild Context",
        visibility_hint=VisibilityHint.PRIVATE,
    )

    art_svc = ArtifactService(chronicle_svc.paths.root)
    source = chronicle_svc.paths.root / "doc.md"
    source.write_text("Content", encoding="utf-8")
    artifact, _ = art_svc.create(
        title="Rebuild Artifact",
        artifact_type=ArtifactType.DOCUMENT,
        source_file=source,
        visibility_hint=VisibilityHint.SENSITIVE,
    )

    chronicle_svc.rebuild_indexes()

    contexts = chronicle_svc.index.load_contexts()
    assert contexts[ctx.context_id].visibility_hint == VisibilityHint.PRIVATE

    artifacts, _ = chronicle_svc.index.load_artifacts()
    assert artifacts[artifact.artifact_id].visibility_hint == VisibilityHint.SENSITIVE


def test_legacy_payload_without_visibility_defaults_unknown(chronicle_svc):
    """Legacy payloads without visibility_hint default to UNKNOWN."""
    # Context without visibility_hint
    ctx_payload = {
        "context_id": "ctx_legacy",
        "title": "Legacy Context",
        "summary": "No visibility",
        "source_type": "conversation",
        "source_ref": "",
        "scope": "task",
        "confidence": "medium",
        "created_at": "2026-06-13T12:00:00+09:00",
        "tags": [],
    }
    with chronicle_svc.paths.events_file.open("a", encoding="utf-8") as f:
        event = {
            "event_id": "evt_legacy_ctx",
            "chronicle_id": "chr_test",
            "timestamp": "2026-06-13T12:00:00+09:00",
            "event_type": "context_added",
            "actor": "user",
            "summary": "Legacy context",
            "payload": {"context": ctx_payload},
        }
        f.write(json.dumps(event) + "\n")

    # Artifact without visibility_hint
    art_payload = {
        "artifact_id": "art_legacy",
        "chronicle_id": "chr_test",
        "title": "Legacy Artifact",
        "artifact_type": "document",
        "current_version_id": "ver_legacy",
        "created_at": "2026-06-13T12:00:00+09:00",
        "updated_at": "2026-06-13T12:00:00+09:00",
        "status": "draft",
        "path": "artifacts/art_legacy/current.md",
        "tags": [],
    }
    with chronicle_svc.paths.events_file.open("a", encoding="utf-8") as f:
        event = {
            "event_id": "evt_legacy_art",
            "chronicle_id": "chr_test",
            "timestamp": "2026-06-13T12:00:00+09:00",
            "event_type": "artifact_created",
            "actor": "user",
            "summary": "Legacy artifact",
            "payload": {
                "artifact": art_payload,
                "version": {
                    "version_id": "ver_legacy",
                    "artifact_id": "art_legacy",
                    "created_at": "2026-06-13T12:00:00+09:00",
                    "created_by": "user",
                    "source_event_id": "evt_legacy_art",
                    "path": "artifacts/art_legacy/versions/ver_legacy.md",
                    "change_summary": "created",
                },
            },
        }
        f.write(json.dumps(event) + "\n")

    chronicle_svc.rebuild_indexes()

    contexts = chronicle_svc.index.load_contexts()
    assert contexts["ctx_legacy"].visibility_hint == VisibilityHint.UNKNOWN

    artifacts, _ = chronicle_svc.index.load_artifacts()
    assert artifacts["art_legacy"].visibility_hint == VisibilityHint.UNKNOWN


def test_cli_add_context_with_visibility_json(tmp_path):
    """CLI add-context --visibility private --json includes visibility_hint."""
    import os
    from typer.testing import CliRunner
    from chronicle.cli import app

    os.chdir(str(tmp_path))
    runner = CliRunner()
    runner.invoke(app, ["init", "--title", "CLI Visibility"])

    result = runner.invoke(app, [
        "add-context",
        "--title", "Private Context",
        "--scope", "task",
        "--visibility", "private",
        "--json",
    ])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["visibility_hint"] == "private"


def test_cli_artifact_create_with_visibility_json(tmp_path):
    """CLI artifact create --visibility sensitive --json includes visibility_hint."""
    import os
    from typer.testing import CliRunner
    from chronicle.cli import app

    os.chdir(str(tmp_path))
    runner = CliRunner()
    runner.invoke(app, ["init", "--title", "CLI Visibility"])

    source = tmp_path / "spec.md"
    source.write_text("# Sensitive Spec", encoding="utf-8")

    result = runner.invoke(app, [
        "artifact", "create",
        "--title", "Sensitive Spec",
        "--type", "specification",
        "--file", str(source),
        "--visibility", "sensitive",
        "--json",
    ])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["artifact"]["visibility_hint"] == "sensitive"


def test_cli_invalid_visibility_fails(tmp_path):
    """CLI with invalid visibility value exits non-zero."""
    import os
    from typer.testing import CliRunner
    from chronicle.cli import app

    os.chdir(str(tmp_path))
    runner = CliRunner()
    runner.invoke(app, ["init", "--title", "CLI Invalid Visibility"])

    result = runner.invoke(app, [
        "add-context",
        "--title", "Bad Visibility",
        "--visibility", "classified",
    ])
    assert result.exit_code != 0
