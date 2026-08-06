"""Tests for the SQLite/OpenAI GraphRAG runtime."""

from __future__ import annotations

import math

from chronicle.models.event import Actor, EventType
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.graphrag_runtime_service import GraphRagRuntimeService, OpenAIHttpClient


class FakeOpenAITransport:
    def __call__(self, path, payload):  # noqa: ANN001, ANN204
        if path == "embeddings":
            return {
                "data": [
                    {"index": index, "embedding": self._embedding(text)}
                    for index, text in enumerate(payload["input"])
                ]
            }
        if path == "responses":
            return {
                "id": "resp_test",
                "output_text": "GraphRAGの回答 [evt_test]",
                "usage": {"input_tokens": 10, "output_tokens": 5},
            }
        raise AssertionError(path)

    @staticmethod
    def _embedding(text: str) -> list[float]:
        value = text.lower()
        raw = [float(value.count("graph") + 1), float(value.count("decision") + 1), 1.0]
        length = math.sqrt(sum(item * item for item in raw))
        return [item / length for item in raw]


def test_rebuild_and_query_create_real_sqlite_projections(tmp_path):
    chronicle = ChronicleService(tmp_path)
    chronicle.init("GraphRAG test")
    event = chronicle.record_event(
        EventType.NOTE_ADDED,
        Actor.USER,
        "Graph decision",
        payload={"content": "Graph database decision and retrieval context"},
    )
    client = OpenAIHttpClient(tmp_path, transport=FakeOpenAITransport())
    runtime = GraphRagRuntimeService(tmp_path, client=client)

    rebuilt = runtime.rebuild()
    result = runtime.query("graph decision")

    assert rebuilt["document_count"] == 2
    assert rebuilt["node_count"] == 2
    assert rebuilt["edge_count"] == 1
    assert runtime.paths.vector_db_file.read_bytes().startswith(b"SQLite format 3")
    assert runtime.paths.graph_db_file.read_bytes().startswith(b"SQLite format 3")
    assert result["answer"] == "GraphRAGの回答 [evt_test]"
    assert result["sources"][0]["record_id"] == event.event_id
    assert result["external_call_made"] is True
    assert result["requires_review"] is True


def test_status_is_rebuildable_and_keeps_jsonl_authoritative(tmp_path):
    ChronicleService(tmp_path).init("Status test")
    runtime = GraphRagRuntimeService(
        tmp_path,
        client=OpenAIHttpClient(tmp_path, transport=FakeOpenAITransport()),
    )

    assert runtime.status()["status"] == "needs_rebuild"
    runtime.rebuild()
    status = runtime.status()

    assert status["status"] == "ready"
    assert status["primary_record_authoritative"] is True
    assert status["vector_db"]["documents"] == 1

    runtime.chronicle.record_event(EventType.NOTE_ADDED, Actor.USER, "New note")
    assert runtime.status()["status"] == "stale"
