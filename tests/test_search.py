import pytest

from chronicle.models.artifact import ArtifactType
from chronicle.models.event import Actor, EventType
from chronicle.services.artifact_service import ArtifactService
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.search_service import SearchService
from chronicle.exporters.markdown_exporter import MarkdownExporter
from chronicle.exporters.yaml_exporter import YamlExporter


@pytest.fixture
def populated_chronicle(tmp_path):
    service = ChronicleService(tmp_path)
    service.init("Search Test")
    service.record_event(
        event_type=EventType.USER_INPUT,
        actor=Actor.USER,
        summary="Create Decision Model specification",
    )

    artifacts = ArtifactService(tmp_path)
    source = tmp_path / "spec.md"
    source.write_text("# Decision Model\n\nDetails here.", encoding="utf-8")
    artifacts.create(
        title="Decision Model Spec",
        artifact_type=ArtifactType.SPECIFICATION,
        source_file=source,
    )
    return tmp_path


def test_search_events_and_artifacts(populated_chronicle):
    search = SearchService(populated_chronicle)
    results = search.search("Decision Model")
    assert len(results) >= 2
    kinds = {r.kind for r in results}
    assert "event" in kinds or "artifact" in kinds


def test_index_rebuild(populated_chronicle):
    service = ChronicleService(populated_chronicle)
    service.paths.artifact_index_file.unlink()
    service.rebuild_indexes()
    artifacts, _ = service.index.load_artifacts()
    assert len(artifacts) == 1


def test_yaml_export(populated_chronicle):
    content = YamlExporter(populated_chronicle).export()
    assert "Search Test" in content
    assert "events:" in content


def test_markdown_export(populated_chronicle):
    content = MarkdownExporter(populated_chronicle).export()
    assert "# Chronicle: Search Test" in content
    assert "Decision Model Spec" in content
