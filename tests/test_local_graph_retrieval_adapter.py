"""Tests for the local graph retrieval adapter."""

from chronicle.models.artifact import ArtifactType
from chronicle.services.artifact_service import ArtifactService
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.context_service import ContextService
from chronicle.services.local_graph_retrieval_adapter import LocalGraphRetrievalAdapter


def test_local_graph_retrieval_adapter_returns_contract_and_hits(tmp_path):
    ChronicleService(tmp_path).init("Local Graph Adapter")
    ContextService(tmp_path).add_context(title="Graph Planning Context", summary="Graph retrieval planning notes")
    source = tmp_path / "artifact.md"
    source.write_text("graph retrieval artifact body", encoding="utf-8")
    ArtifactService(tmp_path).create(
        title="Graph Retrieval Artifact",
        artifact_type=ArtifactType.DOCUMENT,
        source_file=source,
    )

    result = LocalGraphRetrievalAdapter(tmp_path).retrieve(query="graph retrieval planning", limit=5)

    assert result.contract_version == "1.0"
    assert result.incremental_mode == "event-driven_rebuildable"
    assert result.candidate_node_count >= 1
    assert result.matched_node_count >= 1
    assert result.hits
    assert result.hits[0].source == "graph_export_adapter"

