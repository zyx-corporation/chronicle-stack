"""Rebuildable local GraphRAG runtime backed by SQLite and OpenAI."""

from __future__ import annotations

import json
import math
import os
import sqlite3
import ssl
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable
from urllib import error as urllib_error
from urllib import request as urllib_request

import certifi

from chronicle.errors import ChronicleError
from chronicle.services.chronicle_service import ChronicleService


class GraphRagRuntimeError(ChronicleError):
    """Raised when the derived GraphRAG runtime cannot complete a request."""

    def __init__(self, message: str) -> None:
        super().__init__(
            code="GRAPHRAG_RUNTIME_ERROR",
            message=message,
            hint="Check OPENAI_API_KEY, network access, and rebuild the runtime.",
        )


@dataclass(frozen=True)
class OpenAIModels:
    response: str = "gpt-5.4-mini"
    embedding: str = "text-embedding-3-small"


class OpenAIHttpClient:
    """Small dependency-free client for Responses and Embeddings APIs."""

    def __init__(self, root: Path, *, transport: Callable[..., dict[str, Any]] | None = None) -> None:
        self.root = root
        self.transport = transport or self._post
        self.base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        self.models = OpenAIModels(
            response=os.environ.get("CHRONICLE_OPENAI_MODEL", "gpt-5.4-mini"),
            embedding=os.environ.get("CHRONICLE_EMBEDDING_MODEL", "text-embedding-3-small"),
        )

    def _api_key(self) -> str:
        key = os.environ.get("OPENAI_API_KEY", "").strip()
        if key:
            return key
        env_path = self.root / ".env"
        if env_path.is_file() and not env_path.is_symlink():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                if line.startswith("OPENAI_API_KEY="):
                    return line.partition("=")[2].strip().strip('"').strip("'")
        raise GraphRagRuntimeError("OPENAI_API_KEY is not configured")

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        request = urllib_request.Request(
            f"{self.base_url}/{path.lstrip('/')}",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self._api_key()}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            context = ssl.create_default_context(cafile=certifi.where())
            with urllib_request.urlopen(request, timeout=60, context=context) as response:
                result = json.loads(response.read().decode("utf-8"))
        except urllib_error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            raise GraphRagRuntimeError(f"OpenAI API returned HTTP {exc.code}: {detail}") from exc
        except (urllib_error.URLError, OSError, json.JSONDecodeError) as exc:
            raise GraphRagRuntimeError(f"OpenAI API request failed: {exc}") from exc
        if not isinstance(result, dict):
            raise GraphRagRuntimeError("OpenAI API returned an invalid response")
        return result

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        result = self.transport(
            "embeddings",
            {"model": self.models.embedding, "input": texts, "encoding_format": "float"},
        )
        rows = result.get("data", [])
        if not isinstance(rows, list) or len(rows) != len(texts):
            raise GraphRagRuntimeError("Embedding response did not match the requested inputs")
        rows = sorted(rows, key=lambda item: int(item.get("index", 0)))
        return [[float(value) for value in item.get("embedding", [])] for item in rows]

    def answer(self, *, question: str, context: str) -> tuple[str, dict[str, Any]]:
        result = self.transport(
            "responses",
            {
                "model": self.models.response,
                "instructions": (
                    "You are Chronicle's research assistant. Answer in the user's language. "
                    "Use only the supplied Chronicle context, distinguish facts from inference, "
                    "and cite record ids in square brackets."
                ),
                "input": f"Question:\n{question}\n\nChronicle context:\n{context}",
                "max_output_tokens": 900,
            },
        )
        text = result.get("output_text")
        if not isinstance(text, str) or not text.strip():
            parts: list[str] = []
            for item in result.get("output", []):
                if not isinstance(item, dict):
                    continue
                for content in item.get("content", []):
                    if isinstance(content, dict) and isinstance(content.get("text"), str):
                        parts.append(content["text"])
            text = "\n".join(parts)
        if not text.strip():
            raise GraphRagRuntimeError("Responses API returned no text")
        usage = result.get("usage") if isinstance(result.get("usage"), dict) else {}
        return text.strip(), {"response_id": result.get("id", ""), "usage": usage}


class GraphRagRuntimeService:
    """Build and query SQLite vector/graph projections of Chronicle JSONL."""

    def __init__(self, root: Path | None = None, *, client: OpenAIHttpClient | None = None) -> None:
        self.root = (root or Path.cwd()).resolve()
        self.chronicle = ChronicleService(self.root)
        self.paths = self.chronicle.paths
        self.client = client or OpenAIHttpClient(self.root)

    def rebuild(self) -> dict[str, Any]:
        self.chronicle.require_initialized()
        events = self.chronicle.jsonl.read_all(skip_corrupt=True)
        documents = [(event.event_id, event.event_type.value, self._event_text(event)) for event in events]
        embeddings: list[list[float]] = []
        for start in range(0, len(documents), 64):
            embeddings.extend(self.client.embed([text for _, _, text in documents[start : start + 64]]))
        self.paths.runtime_dir.mkdir(parents=True, exist_ok=True)
        self._replace_vector_db(documents, embeddings)
        node_count, edge_count = self._replace_graph_db(events)
        return {
            "status": "ready",
            "vector_db": str(self.paths.vector_db_file),
            "graph_db": str(self.paths.graph_db_file),
            "document_count": len(documents),
            "node_count": node_count,
            "edge_count": edge_count,
            "embedding_model": self.client.models.embedding,
            "primary_record_authoritative": True,
        }

    def status(self) -> dict[str, Any]:
        vector_count = self._count(self.paths.vector_db_file, "documents")
        node_count = self._count(self.paths.graph_db_file, "nodes")
        edge_count = self._count(self.paths.graph_db_file, "edges")
        event_count = len(self.chronicle.jsonl.read_all(skip_corrupt=True)) if self.paths.events_file.exists() else 0
        ready = vector_count > 0 and node_count > 0 and vector_count == event_count
        return {
            "status": "ready" if ready else ("stale" if vector_count else "needs_rebuild"),
            "vector_db": {"path": str(self.paths.vector_db_file), "documents": vector_count},
            "graph_db": {"path": str(self.paths.graph_db_file), "nodes": node_count, "edges": edge_count},
            "response_model": self.client.models.response,
            "embedding_model": self.client.models.embedding,
            "primary_record_authoritative": True,
        }

    def query(self, question: str, *, limit: int = 8) -> dict[str, Any]:
        question = question.strip()
        if not question:
            raise GraphRagRuntimeError("Question is required")
        if self.status()["status"] != "ready":
            self.rebuild()
        query_vector = self.client.embed([question])[0]
        hits = self._vector_hits(query_vector, limit=limit)
        expanded_ids = self._expand_graph([hit[0] for hit in hits])
        records = self._record_context(dict.fromkeys([*(hit[0] for hit in hits), *expanded_ids]))
        context = "\n\n".join(f"[{record_id}] {text}" for record_id, text in records)
        answer, metadata = self.client.answer(question=question, context=context)
        return {
            "answer": answer,
            "sources": [
                {"record_id": record_id, "score": round(score, 6), "text": text}
                for record_id, score, text in hits
            ],
            "graph_expanded_record_ids": expanded_ids,
            "model": self.client.models.response,
            "embedding_model": self.client.models.embedding,
            "response_metadata": metadata,
            "external_call_made": True,
            "requires_review": True,
        }

    def _replace_vector_db(self, documents: list[tuple[str, str, str]], embeddings: list[list[float]]) -> None:
        with sqlite3.connect(self.paths.vector_db_file) as db:
            db.executescript(
                "DROP TABLE IF EXISTS documents;"
                "CREATE TABLE documents (record_id TEXT PRIMARY KEY, record_type TEXT NOT NULL, "
                "text TEXT NOT NULL, embedding TEXT NOT NULL);"
            )
            db.executemany(
                "INSERT INTO documents VALUES (?, ?, ?, ?)",
                [(record_id, kind, text, json.dumps(vector)) for (record_id, kind, text), vector in zip(documents, embeddings, strict=True)],
            )

    def _replace_graph_db(self, events: list[Any]) -> tuple[int, int]:
        nodes: dict[str, tuple[str, str]] = {}
        edges: set[tuple[str, str, str]] = set()
        previous_event_id: str | None = None
        for event in sorted(events, key=lambda item: (item.timestamp, item.event_id)):
            nodes[event.event_id] = ("event", event.summary)
            if previous_event_id:
                edges.add((previous_event_id, event.event_id, "next_event"))
            previous_event_id = event.event_id
            refs = {
                "parent": event.parent_event_id,
                "artifact": event.artifact_id,
                "decision": event.decision_id,
                "rde": event.rde_record_id,
            }
            for relation, target in refs.items():
                if target:
                    nodes.setdefault(target, (relation, target))
                    edges.add((event.event_id, target, relation))
            for context_id in event.context_ids:
                nodes.setdefault(context_id, ("context", context_id))
                edges.add((event.event_id, context_id, "context"))
        with sqlite3.connect(self.paths.graph_db_file) as db:
            db.executescript(
                "DROP TABLE IF EXISTS nodes; DROP TABLE IF EXISTS edges;"
                "CREATE TABLE nodes (node_id TEXT PRIMARY KEY, kind TEXT NOT NULL, label TEXT NOT NULL);"
                "CREATE TABLE edges (source_id TEXT NOT NULL, target_id TEXT NOT NULL, relation TEXT NOT NULL, "
                "PRIMARY KEY (source_id, target_id, relation));"
            )
            db.executemany("INSERT INTO nodes VALUES (?, ?, ?)", [(key, *value) for key, value in nodes.items()])
            db.executemany("INSERT INTO edges VALUES (?, ?, ?)", list(edges))
        return len(nodes), len(edges)

    def _vector_hits(self, query_vector: list[float], *, limit: int) -> list[tuple[str, float, str]]:
        with sqlite3.connect(self.paths.vector_db_file) as db:
            rows = db.execute("SELECT record_id, text, embedding FROM documents").fetchall()
        scored = [(record_id, self._cosine(query_vector, json.loads(vector)), text) for record_id, text, vector in rows]
        return sorted(scored, key=lambda row: (-row[1], row[0]))[:limit]

    def _expand_graph(self, record_ids: list[str]) -> list[str]:
        if not record_ids:
            return []
        placeholders = ",".join("?" for _ in record_ids)
        with sqlite3.connect(self.paths.graph_db_file) as db:
            rows = db.execute(
                f"SELECT source_id, target_id FROM edges WHERE source_id IN ({placeholders}) OR target_id IN ({placeholders})",  # noqa: S608
                [*record_ids, *record_ids],
            ).fetchall()
        selected = set(record_ids)
        return sorted({value for row in rows for value in row if value not in selected})

    def _record_context(self, record_ids: Any) -> list[tuple[str, str]]:
        lookup = {event.event_id: self._event_text(event) for event in self.chronicle.jsonl.read_all(skip_corrupt=True)}
        return [(record_id, lookup[record_id]) for record_id in record_ids if record_id in lookup]

    @staticmethod
    def _event_text(event: Any) -> str:
        payload = json.dumps(event.payload, ensure_ascii=False, sort_keys=True)
        return f"{event.event_type.value}: {event.summary}\n{payload}"[:12000]

    @staticmethod
    def _cosine(left: list[float], right: list[float]) -> float:
        if not left or len(left) != len(right):
            return 0.0
        dot = sum(a * b for a, b in zip(left, right, strict=True))
        denom = math.sqrt(sum(a * a for a in left)) * math.sqrt(sum(b * b for b in right))
        return dot / denom if denom else 0.0

    @staticmethod
    def _count(path: Path, table: str) -> int:
        if not path.exists():
            return 0
        try:
            with sqlite3.connect(path) as db:
                return int(db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])  # noqa: S608
        except sqlite3.Error:
            return 0
