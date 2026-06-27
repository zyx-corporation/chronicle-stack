"""Graph node/edge models for deterministic graph export (v0.3).

These are derived views — they do NOT represent a primary record.
The JSONL remains the single source of truth.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from chronicle.models.export_manifest import ExportManifest


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


class GraphExportContract(BaseModel):
    contract_version: str = "1.0"
    export_family: str = "graph-json"
    primary_record: str = ".chronicle/chronicle.jsonl"
    derived_only: bool = True
    deterministic: bool = True
    mutates_primary_record: bool = False
    external_runtime_required: bool = False
    graph_runtime_included: bool = False
    incremental_source: str = "chronicle_events"
    incremental_mode: str = "event-driven_rebuildable"
    incremental_checkpoint_field: str = "event_id"
    incremental_ordering_field: str = "timestamp"
    incremental_expectations: list[str] = Field(default_factory=list)
    authority_note: str = (
        "Graph export remains derived and non-authoritative; Chronicle primary records stay authoritative."
    )


class GraphExport(BaseModel):
    schema_version: str = "0.3"
    generated_at: datetime
    chronicle_id: str
    export_manifest: ExportManifest | None = None
    export_contract: GraphExportContract | None = None
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)
