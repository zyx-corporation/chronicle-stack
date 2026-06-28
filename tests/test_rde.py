import pytest

from chronicle.errors import RdeVersionNotFoundError
from chronicle.models.artifact import ArtifactType
from chronicle.services.artifact_service import ArtifactService
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.rde_service import RdeService
from chronicle.services.search_service import SearchService


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
    report_path = rde_service.chronicle.paths.rde_report_path(
        record.rde_record_id
    )
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


# --- ADR-001 T-RDE: empty sections must show (none), not imply reviewed ---

def test_rde_empty_sections_show_none(rde_service, tmp_path):
    """Empty RDE fields must render as '(none)', not as reviewed."""
    artifacts = ArtifactService(tmp_path)
    src1 = tmp_path / "v1.md"
    src1.write_text("v1", encoding="utf-8")
    artifact, v1 = artifacts.create(
        title="Doc",
        artifact_type=ArtifactType.DOCUMENT,
        source_file=src1,
    )
    src2 = tmp_path / "v2.md"
    src2.write_text("v2", encoding="utf-8")
    _, v2 = artifacts.update(
        artifact_id=artifact.artifact_id,
        source_file=src2,
        summary="updated",
    )

    record = rde_service.record(
        artifact_id=artifact.artifact_id,
        from_version_id=v1.version_id,
        to_version_id=v2.version_id,
        summary="minor update",
        # No preserved / transformed / etc. provided
    )

    report_path = rde_service.chronicle.paths.rde_report_path(
        record.rde_record_id
    )
    report_text = report_path.read_text(encoding="utf-8")
    # Empty sections must show "(none)" — not imply completeness
    assert "(none)" in report_text
    # Must not claim complete validation
    assert "RDE complete" not in report_text


def test_rde_record_links_to_target_version(rde_service, tmp_path):
    artifacts = ArtifactService(tmp_path)
    source_v1 = tmp_path / "v1.md"
    source_v1.write_text("Original", encoding="utf-8")
    artifact, v1 = artifacts.create(
        title="RDE Link Test",
        artifact_type=ArtifactType.SPECIFICATION,
        source_file=source_v1,
    )

    source_v2 = tmp_path / "v2.md"
    source_v2.write_text("Updated", encoding="utf-8")
    _, v2 = artifacts.update(
        artifact_id=artifact.artifact_id,
        source_file=source_v2,
        summary="Updated spec",
    )

    record = rde_service.record(
        artifact_id=artifact.artifact_id,
        from_version_id=v1.version_id,
        to_version_id=v2.version_id,
        summary="Test RDE linkage",
        preserved=["Original intent"],
    )

    # Rebuild indexes to trigger rde_record_id enrichment
    rde_service.chronicle.rebuild_indexes()

    # Load artifact history and verify rde_record_id on target version
    art, versions = artifacts.history(artifact.artifact_id)
    v2_from_history = [v for v in versions if v.version_id == v2.version_id][0]
    assert v2_from_history.rde_record_id == record.rde_record_id


def test_rde_record_is_searchable(rde_service, tmp_path):
    artifacts = ArtifactService(tmp_path)
    source_v1 = tmp_path / "v1.md"
    source_v1.write_text("Original", encoding="utf-8")
    artifact, v1 = artifacts.create(
        title="RDE Search Test",
        artifact_type=ArtifactType.SPECIFICATION,
        source_file=source_v1,
    )

    source_v2 = tmp_path / "v2.md"
    source_v2.write_text("Updated", encoding="utf-8")
    _, v2 = artifacts.update(
        artifact_id=artifact.artifact_id,
        source_file=source_v2,
        summary="Updated spec",
    )

    rde_service.record(
        artifact_id=artifact.artifact_id,
        from_version_id=v1.version_id,
        to_version_id=v2.version_id,
        summary="Searchable RDE",
        preserved=["UniqueSearchTermXYZ"],
    )

    search = SearchService(tmp_path)
    results = search.search("UniqueSearchTermXYZ")
    assert len(results) >= 1
    kinds = {r.kind for r in results}
    assert "rde" in kinds or "event" in kinds


def test_rde_draft_can_record_ai_assisted_hypothesis(tmp_path):
    ChronicleService(tmp_path).init("RDE Draft Test")
    artifacts = ArtifactService(tmp_path)
    source_v1 = tmp_path / "draft-v1.md"
    source_v1.write_text("Original", encoding="utf-8")
    artifact, v1 = artifacts.create(
        title="AI Draft Target",
        artifact_type=ArtifactType.SPECIFICATION,
        source_file=source_v1,
    )

    source_v2 = tmp_path / "draft-v2.md"
    source_v2.write_text("Updated with AI-assisted delta", encoding="utf-8")
    _, v2 = artifacts.update(
        artifact_id=artifact.artifact_id,
        source_file=source_v2,
        summary="Updated",
    )

    memo = RdeService(tmp_path).draft(
        artifact_id=artifact.artifact_id,
        from_version_id=v1.version_id,
        to_version_id=v2.version_id,
        summary="AI-assisted draft",
        mode="ai-assisted",
        ai_summary="AI summary separated from source.",
        ai_response="AI raw response.",
        ai_model="external:test-model",
        interpretation="This AI interpretation should remain a hypothesis.",
        record=True,
    )

    assert memo.recorded_rde_id is not None
    assert memo.linked_delta_object_id == f"obj_delta_{memo.recorded_rde_id}"
    assert memo.linked_hypothesis_object_id is not None
