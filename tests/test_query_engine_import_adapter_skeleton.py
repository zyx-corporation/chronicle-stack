import json
from pathlib import Path

from chronicle.integration.query_engine_adapter_skeleton import QueryEngineAdapterSkeletonBuilder
from chronicle.models.integration_adapter import QueryEngineAdapterSkeleton
from chronicle.models.runtime import RuntimeQueryEngineHandoff


ROOT = Path(__file__).resolve().parents[1]
HANDOFF_JSON = ROOT / "docs" / "examples" / "query-engine-handoff-example.json"
SKELETON_JSON = ROOT / "docs" / "examples" / "query-engine-import-adapter-skeleton.json"
SKELETON_DOC = ROOT / "docs" / "query-engine-import-adapter-skeleton.md"


def test_query_engine_import_adapter_skeleton_example_json_is_valid() -> None:
    payload = json.loads(SKELETON_JSON.read_text(encoding="utf-8"))
    skeleton = QueryEngineAdapterSkeleton.model_validate(payload)

    assert skeleton.contract_version == "1.0"
    assert skeleton.skeleton_kind == "query_engine_import_adapter"
    assert skeleton.graph_export_format == "graph-json"
    assert skeleton.recommended_sequence[0].name == "inspect_handoff"


def test_query_engine_import_adapter_skeleton_builder_matches_example() -> None:
    handoff_payload = json.loads(HANDOFF_JSON.read_text(encoding="utf-8"))
    handoff = RuntimeQueryEngineHandoff.model_validate(handoff_payload)

    skeleton = QueryEngineAdapterSkeletonBuilder().build(handoff)

    assert skeleton.handoff_contract_version == handoff.contract_version
    assert skeleton.import_validation_contract_version == handoff.import_validation.contract_version
    assert skeleton.graph_export_contract_version == handoff.graph_export_contract_version
    assert skeleton.required_inputs == ["query_engine_handoff.json", ".chronicle/chronicle.jsonl", "graph.json"]


def test_query_engine_import_adapter_skeleton_doc_preserves_boundary() -> None:
    text = SKELETON_DOC.read_text(encoding="utf-8")

    assert "not an executable adapter" in text
    assert "no hosted query engine" in text
    assert "no mutation of `.chronicle/chronicle.jsonl`" in text
