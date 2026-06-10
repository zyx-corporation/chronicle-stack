import pytest

from chronicle.errors import ArtifactNotFoundError, EmptyArtifactContentError
from chronicle.models.artifact import ArtifactType
from chronicle.services.artifact_service import ArtifactService
from chronicle.services.chronicle_service import ChronicleService


@pytest.fixture
def artifact_service(tmp_path):
    ChronicleService(tmp_path).init("Artifact Test")
    return ArtifactService(tmp_path)


def test_create_artifact(artifact_service, tmp_path):
    source = tmp_path / "spec.md"
    source.write_text("# Spec\n\nContent here.", encoding="utf-8")

    artifact, version = artifact_service.create(
        title="Test Spec",
        artifact_type=ArtifactType.SPECIFICATION,
        source_file=source,
    )

    assert artifact.artifact_id.startswith("art_")
    assert version.version_id.startswith("ver_")
    assert version.change_summary == "created"

    current = artifact_service.chronicle.artifact_store.read_current(
        artifact.artifact_id
    )
    assert "Content here" in current


def test_update_artifact_creates_version(artifact_service, tmp_path):
    source_v1 = tmp_path / "v1.md"
    source_v1.write_text("Version 1", encoding="utf-8")
    artifact, v1 = artifact_service.create(
        title="Doc",
        artifact_type=ArtifactType.DOCUMENT,
        source_file=source_v1,
    )

    source_v2 = tmp_path / "v2.md"
    source_v2.write_text("Version 2", encoding="utf-8")
    updated, v2 = artifact_service.update(
        artifact_id=artifact.artifact_id,
        source_file=source_v2,
        summary="Second version",
    )

    assert updated.current_version_id == v2.version_id
    assert v2.parent_version_id == v1.version_id

    art, versions = artifact_service.history(artifact.artifact_id)
    assert len(versions) == 2


def test_artifact_history(artifact_service, tmp_path):
    source = tmp_path / "doc.md"
    source.write_text("Hello", encoding="utf-8")
    artifact, _ = artifact_service.create(
        title="History Doc",
        artifact_type=ArtifactType.DOCUMENT,
        source_file=source,
    )

    art, versions = artifact_service.history(artifact.artifact_id)
    assert art.title == "History Doc"
    assert len(versions) == 1


def test_artifact_not_found(artifact_service):
    with pytest.raises(ArtifactNotFoundError):
        artifact_service.get("art_nonexistent")


# --- ADR-001 P0 regression: source_event_id integrity ---

def test_create_source_event_id_is_populated(artifact_service, tmp_path):
    """source_event_id must be a valid evt_ ID immediately after create."""
    source = tmp_path / "spec.md"
    source.write_text("Content", encoding="utf-8")
    _, version = artifact_service.create(
        title="Test",
        artifact_type=ArtifactType.SPECIFICATION,
        source_file=source,
    )
    assert version.source_event_id.startswith("evt_")


def test_update_source_event_id_is_populated(artifact_service, tmp_path):
    """source_event_id must be a valid evt_ ID immediately after update."""
    src = tmp_path / "v1.md"
    src.write_text("v1", encoding="utf-8")
    artifact, _ = artifact_service.create(
        title="Doc",
        artifact_type=ArtifactType.DOCUMENT,
        source_file=src,
    )
    src2 = tmp_path / "v2.md"
    src2.write_text("v2", encoding="utf-8")
    _, v2 = artifact_service.update(
        artifact_id=artifact.artifact_id,
        source_file=src2,
        summary="updated",
    )
    assert v2.source_event_id.startswith("evt_")


def test_source_event_id_survives_rebuild(artifact_service, tmp_path):
    """source_event_id stored in JSONL must survive index rebuild."""
    source = tmp_path / "spec.md"
    source.write_text("Content", encoding="utf-8")
    _, version = artifact_service.create(
        title="Test",
        artifact_type=ArtifactType.SPECIFICATION,
        source_file=source,
    )
    original_id = version.source_event_id

    artifact_service.chronicle.rebuild_indexes()
    _, versions = artifact_service.history(version.artifact_id)
    assert versions[0].source_event_id == original_id


# --- ADR-001 §4: empty body guard ---

def test_update_with_no_content_raises_error(artifact_service, tmp_path):
    """Artifact update without file or content must raise an error."""
    source = tmp_path / "doc.md"
    source.write_text("Content", encoding="utf-8")
    artifact, _ = artifact_service.create(
        title="Doc",
        artifact_type=ArtifactType.DOCUMENT,
        source_file=source,
    )
    with pytest.raises(EmptyArtifactContentError):
        artifact_service.update(artifact_id=artifact.artifact_id)
