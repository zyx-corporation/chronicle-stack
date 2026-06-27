import json
from pathlib import Path

from chronicle.models.runtime import RuntimeQueryEngineHandoff


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_JSON = ROOT / "docs" / "examples" / "query-engine-handoff-example.json"
EXAMPLE_DOC = ROOT / "docs" / "query-engine-handoff-consumer-example.md"


def test_query_engine_handoff_example_json_is_valid() -> None:
    payload = json.loads(EXAMPLE_JSON.read_text(encoding="utf-8"))
    handoff = RuntimeQueryEngineHandoff.model_validate(payload)

    assert handoff.contract_version == "1.0"
    assert handoff.graph_export_format == "graph-json"
    assert handoff.import_validation is not None
    assert handoff.import_validation.status == "contract_validated"
    assert handoff.import_validation.import_ready is True
    assert not handoff.graph_runtime_included
    assert not handoff.external_query_runtime_included


def test_query_engine_handoff_example_doc_preserves_boundary() -> None:
    text = EXAMPLE_DOC.read_text(encoding="utf-8")

    assert "docs/examples/query-engine-handoff-example.json" in text
    assert "hosted query engine" in text
    assert "does not certify semantic correctness" in text
    assert "chronicle export --format graph-json -o graph.json" in text
