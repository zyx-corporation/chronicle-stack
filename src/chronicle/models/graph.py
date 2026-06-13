"""Graph node/edge models for deterministic graph export (v0.3).

These are derived views — they do NOT represent a primary record.
The JSONL remains the single source of truth.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class GraphNode(BaseModel):
    node_id: str
    node_type: str
    source_id: str
    title: str = ""
    summary: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    edge_id: str
    edge_type: str
    from_node_id: str
    to_node_id: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class GraphExport(BaseModel):
    schema_version: str = "0.3"
    generated_at: datetime
    chronicle_id: str
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)
