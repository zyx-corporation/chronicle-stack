"""Local retrieval adapter over the derived graph export."""

import re
from pathlib import Path

from chronicle.models.runtime import LocalGraphRetrievalAdapterResult, RuntimeRetrievalHit
from chronicle.services.graph_export_service import GraphExportService


TOKEN_PATTERN = re.compile(r"[a-z0-9_]{2,}")


def _tokenize(value: str) -> set[str]:
    return {token for token in TOKEN_PATTERN.findall(value.lower()) if token}


class LocalGraphRetrievalAdapter:
    """Consume the derived graph export without becoming a GraphRAG runtime."""

    def __init__(self, root: Path | None = None) -> None:
        self.graph_export = GraphExportService(root)

    def retrieve(self, *, query: str, limit: int = 5) -> LocalGraphRetrievalAdapterResult:
        graph = self.graph_export.export_graph()
        query_tokens = _tokenize(query)
        adjacency: dict[str, set[str]] = {}
        for edge in graph.edges:
            adjacency.setdefault(edge.from_node_id, set()).add(edge.to_node_id)
            adjacency.setdefault(edge.to_node_id, set()).add(edge.from_node_id)

        ranked: list[tuple[float, object]] = []
        for node in graph.nodes:
            haystack = " ".join(
                [
                    node.node_type,
                    node.source_id,
                    node.title,
                    node.summary,
                    " ".join(f"{key} {value}" for key, value in sorted(node.metadata.items())),
                ]
            )
            node_tokens = _tokenize(haystack)
            overlap = query_tokens & node_tokens if query_tokens else set()
            substring_match = query.lower() in haystack.lower() if query else False
            if not overlap and not substring_match:
                continue
            score = len(overlap) / max(len(query_tokens), 1)
            score += min(len(adjacency.get(node.node_id, set())) * 0.05, 0.2)
            if substring_match:
                score += 0.1
            ranked.append((score, node))

        ranked.sort(key=lambda item: (-item[0], item[1].node_type, item[1].source_id))
        top_nodes = ranked[:limit]
        hits = [
            RuntimeRetrievalHit(
                source="graph_export_adapter",
                identifier=node.source_id,
                summary=node.title or node.summary or node.node_type,
                detail=node.node_type,
                score=round(score, 4),
            )
            for score, node in top_nodes
        ]
        expanded_edge_count = sum(len(adjacency.get(node.node_id, set())) for _score, node in top_nodes)
        return LocalGraphRetrievalAdapterResult(
            export_contract_version=(
                graph.export_contract.contract_version if graph.export_contract is not None else "unknown"
            ),
            query=query,
            incremental_mode=(
                graph.export_contract.incremental_mode
                if graph.export_contract is not None
                else "event-driven_rebuildable"
            ),
            candidate_node_count=len(graph.nodes),
            matched_node_count=len(ranked),
            expanded_edge_count=expanded_edge_count,
            hits=hits,
            notes=[
                "derived graph export consumed locally",
                "no graph runtime or external retrieval service invoked",
                "full graph remains rebuildable from Chronicle events",
            ],
        )
