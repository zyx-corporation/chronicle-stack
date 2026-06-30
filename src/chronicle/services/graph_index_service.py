"""Local file-backed placeholder graph index service."""

import json
from pathlib import Path

from chronicle.errors import AiIndexRecordNotFoundError
from chronicle.models.ai_index import AiGraphEdge, AiGraphNode, GraphIndexSnapshot, GraphNeighborsResult
from chronicle.services.chronicle_service import ChronicleService


class GraphIndexService:
    """Manage a local placeholder graph index without an external graph database."""

    def __init__(self, root: Path | None = None) -> None:
        self.chronicle = ChronicleService(root)
        self.paths = self.chronicle.paths

    def add_node(
        self,
        *,
        node_id: str,
        labels: list[str] | None = None,
        properties: dict[str, str] | None = None,
    ) -> AiGraphNode:
        self.chronicle.require_initialized()
        self._require_record(node_id)
        snapshot = self._load_snapshot()
        node = AiGraphNode(node_id=node_id, labels=labels or [], properties=properties or {})
        updated = False
        for index, existing in enumerate(snapshot.nodes):
            if existing.node_id == node_id:
                merged_labels = list(dict.fromkeys([*existing.labels, *node.labels]))
                snapshot.nodes[index] = AiGraphNode(
                    node_id=node_id,
                    labels=merged_labels,
                    properties={**existing.properties, **node.properties},
                )
                node = snapshot.nodes[index]
                updated = True
                break
        if not updated:
            snapshot.nodes.append(node)
        self._save_snapshot(snapshot)
        return node

    def add_edge(
        self,
        *,
        source_id: str,
        target_id: str,
        relation: str,
        properties: dict[str, str] | None = None,
    ) -> AiGraphEdge:
        self.chronicle.require_initialized()
        self._require_record(source_id)
        self._require_record(target_id)
        snapshot = self._load_snapshot()
        edge = AiGraphEdge(
            source_id=source_id,
            target_id=target_id,
            relation=relation,
            properties=properties or {},
        )
        snapshot.edges = [
            existing
            for existing in snapshot.edges
            if not (
                existing.source_id == source_id
                and existing.target_id == target_id
                and existing.relation == relation
            )
        ]
        snapshot.edges.append(edge)
        self._save_snapshot(snapshot)
        return edge

    def neighbors(self, *, node_id: str) -> GraphNeighborsResult:
        self.chronicle.require_initialized()
        self._require_record(node_id)
        snapshot = self._load_snapshot()
        outgoing = [edge for edge in snapshot.edges if edge.source_id == node_id]
        incoming = [edge for edge in snapshot.edges if edge.target_id == node_id]
        neighbor_ids = {edge.target_id for edge in outgoing} | {edge.source_id for edge in incoming}
        neighbors = [node for node in snapshot.nodes if node.node_id in neighbor_ids]
        neighbors.sort(key=lambda node: node.node_id)
        return GraphNeighborsResult(
            node_id=node_id,
            neighbors=neighbors,
            outgoing=outgoing,
            incoming=incoming,
        )

    def snapshot(self) -> GraphIndexSnapshot:
        self.chronicle.require_initialized()
        return self._load_snapshot()

    def get_node(self, node_id: str) -> AiGraphNode | None:
        self.chronicle.require_initialized()
        snapshot = self._load_snapshot()
        return next((node for node in snapshot.nodes if node.node_id == node_id), None)

    def get_edge(self, *, source_id: str, relation: str, target_id: str) -> AiGraphEdge | None:
        self.chronicle.require_initialized()
        snapshot = self._load_snapshot()
        return next(
            (
                edge
                for edge in snapshot.edges
                if edge.source_id == source_id
                and edge.relation == relation
                and edge.target_id == target_id
            ),
            None,
        )

    def _load_snapshot(self) -> GraphIndexSnapshot:
        if not self.paths.graph_index_file.exists():
            return GraphIndexSnapshot()
        raw = json.loads(self.paths.graph_index_file.read_text(encoding="utf-8"))
        return GraphIndexSnapshot.model_validate(raw)

    def _save_snapshot(self, snapshot: GraphIndexSnapshot) -> None:
        self.paths.ai_indexes_dir.mkdir(parents=True, exist_ok=True)
        self.paths.graph_index_file.write_text(
            json.dumps(snapshot.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _require_record(self, record_id: str) -> None:
        metadata = self.chronicle.load_metadata()
        events = self.chronicle.jsonl.read_all(skip_corrupt=True)
        artifacts, _ = self.chronicle.index.load_artifacts()
        contexts = self.chronicle.index.load_contexts()
        decisions = self.chronicle.index.load_decisions()
        rde_records = self.chronicle.index.load_rde_records()
        boundary_rules = self.chronicle.index.load_boundary_rules()
        known_ids = {
            metadata.chronicle_id,
            *(event.event_id for event in events),
            *artifacts.keys(),
            *contexts.keys(),
            *decisions.keys(),
            *rde_records.keys(),
            *boundary_rules.keys(),
        }
        if record_id not in known_ids:
            raise AiIndexRecordNotFoundError(record_id)
