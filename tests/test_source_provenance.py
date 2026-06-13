"""Tests for v0.2 Source Provenance Metadata."""

import json

import pytest

from chronicle.models.artifact import ArtifactType
from chronicle.models.source import SourceProvenance
from chronicle.services.artifact_service import ArtifactService
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.context_service import ContextService


@pytest.fixture
def chronicle_svc(tmp_path):
    ChronicleService(tmp_path).init("Source Provenance Test")
    return ChronicleService(tmp_path)


def test_source_provenance_model_minimal(chronicle_svc):
    """SourceProvenance with minimal fields stores correctly."""
    sp = SourceProvenance(source_type="conversation", source_ref="abc")
    assert sp.source_type == "conversation"
    assert sp.source_ref == "abc"
    assert sp.source_tool is None


def test_record_event_with_source_provenance(chronicle_svc):
    """record_event with source metadata stores source in JSONL."""
    source = SourceProvenance(
        source_type="conversation",
        source_tool="chatgpt",
        source_session="session_001",
    )
    from chronicle.models.event import Actor, EventType
    event = chronicle_svc.record_event(
        event_type=EventType.USER_INPUT,
        actor=Actor.USER,
        summary="Test provenance",
        source=source,
    )
    assert event.source is not None
    assert event.source.source_tool == "chatgpt"
    assert event.source.source_session == "session_001"

    # Verify in JSONL
    events = chronicle_svc.jsonl.read_all()
    matching = [e for e in events if e.event_id == event.event_id]
    assert len(matching) == 1
    assert matching[0].source is not None
    assert matching[0].source.source_tool == "chatgpt"


def test_add_context_with_source_provenance(chronicle_svc):
    """ContextService.add_context with source stores it correctly."""
    from chronicle.models.source import SourceProvenance
    svc = ContextService(chronicle_svc.paths.root)
    source = SourceProvenance(
        source_type="conversation",
        source_tool="chatgpt",
        source_session="session_001",
    )
    ctx = svc.add_context(
        title="Provenance Context",
        source_type="conversation",
        source=source,
    )
    assert ctx.source is not None
    assert ctx.source.source_tool == "chatgpt"
    assert ctx.source.source_session == "session_001"
    # Legacy source_type/source_ref still populated
    assert ctx.source_type == "conversation"


def test_create_artifact_with_source_provenance(chronicle_svc):
    """ArtifactService.create with source stores it correctly."""
    svc = ArtifactService(chronicle_svc.paths.root)
    source_file = chronicle_svc.paths.root / "spec.md"
    source_file.write_text("# Spec", encoding="utf-8")
    source = SourceProvenance(
        source_type="file",
        source_tool="local-cli",
        source_file="spec.md",
    )
    artifact, _ = svc.create(
        title="Source Artifact",
        artifact_type=ArtifactType.SPECIFICATION,
        source_file=source_file,
        source=source,
    )
    assert artifact.source is not None
    assert artifact.source.source_tool == "local-cli"
    assert artifact.source.source_file == "spec.md"


def test_legacy_source_ref_still_loads(chronicle_svc):
    """Legacy source: {source_type, source_ref} payloads still load."""
    legacy_event = {
        "event_id": "evt_legacy_src",
        "chronicle_id": "chr_test",
        "timestamp": "2026-06-13T12:00:00+09:00",
        "event_type": "user_input",
        "actor": "user",
        "summary": "Legacy source",
        "source": {"source_type": "conversation", "source_ref": "ref123"},
        "payload": {},
    }
    with chronicle_svc.paths.events_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(legacy_event) + "\n")

    events = chronicle_svc.jsonl.read_all()
    matching = [e for e in events if e.event_id == "evt_legacy_src"]
    assert len(matching) == 1
    assert matching[0].source is not None
    assert matching[0].source.source_type == "conversation"
    assert matching[0].source.source_ref == "ref123"


def test_source_provenance_survives_index_rebuild(chronicle_svc):
    """Source provenance survives index rebuild."""
    svc = ContextService(chronicle_svc.paths.root)
    source = SourceProvenance(source_type="file", source_tool="local-cli")
    ctx = svc.add_context(title="Rebuild Source", source=source)

    art_svc = ArtifactService(chronicle_svc.paths.root)
    f = chronicle_svc.paths.root / "doc.md"
    f.write_text("Content", encoding="utf-8")
    art_source = SourceProvenance(source_type="file", source_tool="local-cli")
    artifact, _ = art_svc.create(
        title="Rebuild Artifact",
        artifact_type=ArtifactType.DOCUMENT,
        source_file=f,
        source=art_source,
    )

    chronicle_svc.rebuild_indexes()

    contexts = chronicle_svc.index.load_contexts()
    assert contexts[ctx.context_id].source.source_tool == "local-cli"

    artifacts, _ = chronicle_svc.index.load_artifacts()
    assert artifacts[artifact.artifact_id].source.source_tool == "local-cli"


def test_cli_record_with_source_metadata_json(tmp_path):
    """CLI record with --source-tool --source-session outputs source."""
    import os
    from typer.testing import CliRunner
    from chronicle.cli import app

    os.chdir(str(tmp_path))
    runner = CliRunner()
    runner.invoke(app, ["init", "--title", "CLI Source"])

    result = runner.invoke(app, [
        "record",
        "--type", "user_input",
        "--actor", "user",
        "--summary", "Test source",
        "--source-type", "conversation",
        "--source-tool", "chatgpt",
        "--source-session", "session_001",
        "--json",
    ])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["source"] is not None
    assert data["source"]["source_tool"] == "chatgpt"
    assert data["source"]["source_session"] == "session_001"


def test_cli_add_context_with_source_metadata_json(tmp_path):
    """CLI add-context with source options outputs source."""
    import os
    from typer.testing import CliRunner
    from chronicle.cli import app

    os.chdir(str(tmp_path))
    runner = CliRunner()
    runner.invoke(app, ["init", "--title", "CLI Source Context"])

    result = runner.invoke(app, [
        "add-context",
        "--title", "Source Context",
        "--scope", "task",
        "--source-type", "conversation",
        "--source-tool", "chatgpt",
        "--source-session", "session_001",
        "--json",
    ])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["source"] is not None
    assert data["source"]["source_tool"] == "chatgpt"


def test_cli_artifact_create_with_source_metadata_json(tmp_path):
    """CLI artifact create with source options outputs source."""
    import os
    from typer.testing import CliRunner
    from chronicle.cli import app

    os.chdir(str(tmp_path))
    runner = CliRunner()
    runner.invoke(app, ["init", "--title", "CLI Source Artifact"])

    source_file = tmp_path / "spec.md"
    source_file.write_text("# Spec", encoding="utf-8")

    result = runner.invoke(app, [
        "artifact", "create",
        "--title", "Source Artifact",
        "--type", "specification",
        "--file", str(source_file),
        "--source-type", "file",
        "--source-tool", "local-cli",
        "--json",
    ])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["artifact"]["source"] is not None
    assert data["artifact"]["source"]["source_tool"] == "local-cli"


def test_search_matches_source_metadata(chronicle_svc):
    """Search finds results by source_tool and source_session."""
    svc = ContextService(chronicle_svc.paths.root)
    source = SourceProvenance(source_type="conversation", source_tool="unique_tool_xyz")
    svc.add_context(title="Search Source", source_type="conversation", source=source)

    from chronicle.services.search_service import SearchService
    search = SearchService(chronicle_svc.paths.root)
    results = search.search("unique_tool_xyz")
    assert len(results) >= 1
    assert any(r.kind == "context" for r in results)


def test_export_includes_source_metadata(chronicle_svc):
    """YAML export includes source metadata."""
    svc = ContextService(chronicle_svc.paths.root)
    source = SourceProvenance(source_type="conversation", source_tool="export_test")
    svc.add_context(title="Export Source", source_type="conversation", source=source)

    from chronicle.exporters.yaml_exporter import YamlExporter
    yaml_content = YamlExporter(chronicle_svc.paths.root).export()
    assert "export_test" in yaml_content
