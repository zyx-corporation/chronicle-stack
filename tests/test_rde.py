import pytest

from chronicle.errors import RdeVersionNotFoundError
from chronicle.models.artifact import ArtifactType
from chronicle.services.artifact_service import ArtifactService
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.rde_service import RdeService


@pytest.fixture
def rde_service(tmp_path):
    ChronicleService(tmp_path).init("RDE Test")
    return RdeService(tmp_path)


def test_rde_record(rde_service, tmp_path):
    artifacts = ArtifactService(tmp_path)
    source_v1 = tmp_path / "v1.md"
    source_v1.write_text("Original intent preserved", encoding="utf-8")
    artifact, v1 = artifacts.create(
        title="RDE Target",
        artifact_type=ArtifactType.SPECIFICATION,
        source_file=source_v1,
    )

    source_v2 = tmp_path / "v2.md"
    source_v2.write_text("Transformed content added", encoding="utf-8")
    _, v2 = artifacts.update(
        artifact_id=artifact.artifact_id,
        source_file=source_v2,
        summary="Detailed spec",
    )

    record = rde_service.record(
        artifact_id=artifact.artifact_id,
        from_version_id=v1.version_id,
        to_version_id=v2.version_id,
        summary="Spec detailed",
        preserved=["Original intent"],
        transformed=["Added detail sections"],
    )

    assert record.rde_record_id.startswith("rde_")
    report_path = rde_service.chronicle.paths.rde_report_path(record.rde_record_id)
    assert report_path.exists()
    assert "Preserved" in report_path.read_text(encoding="utf-8")


def test_rde_version_not_found(rde_service, tmp_path):
    artifacts = ArtifactService(tmp_path)
    source = tmp_path / "doc.md"
    source.write_text("Content", encoding="utf-8")
    artifact, v1 = artifacts.create(
        title="Doc",
        artifact_type=ArtifactType.DOCUMENT,
        source_file=source,
    )

    with pytest.raises(RdeVersionNotFoundError):
        rde_service.record(
            artifact_id=artifact.artifact_id,
            from_version_id=v1.version_id,
            to_version_id="ver_nonexistent",
        )
