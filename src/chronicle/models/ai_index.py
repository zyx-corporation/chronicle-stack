"""Local file-backed placeholder AI index models."""

from datetime import datetime

from pydantic import BaseModel, Field


class VectorIndexEntry(BaseModel):
    record_id: str
    record_type: str = "event"
    text: str
    metadata: dict[str, str] = Field(default_factory=dict)
    indexed_at: datetime
    embedding_provider: str = "disabled"
    embedding_model: str = "none"
    external_call_made: bool = False


class VectorSearchResult(BaseModel):
    record_id: str
    record_type: str
    score: float
    text: str
    metadata: dict[str, str] = Field(default_factory=dict)


class VectorIndexSnapshot(BaseModel):
    entries: list[VectorIndexEntry] = Field(default_factory=list)


class AiGraphNode(BaseModel):
    node_id: str
    labels: list[str] = Field(default_factory=list)
    properties: dict[str, str] = Field(default_factory=dict)


class AiGraphEdge(BaseModel):
    source_id: str
    target_id: str
    relation: str
    properties: dict[str, str] = Field(default_factory=dict)


class GraphIndexSnapshot(BaseModel):
    nodes: list[AiGraphNode] = Field(default_factory=list)
    edges: list[AiGraphEdge] = Field(default_factory=list)


class VectorIndexStatus(BaseModel):
    path: str
    entry_count: int = 0
    embedding_provider: str = "disabled"
    embedding_model: str = "none"
    external_call_made: bool = False


class GraphIndexStatus(BaseModel):
    path: str
    node_count: int = 0
    edge_count: int = 0
    external_call_made: bool = False


class AiIndexStatus(BaseModel):
    vector: VectorIndexStatus
    graph: GraphIndexStatus
    derived_surface: bool = True
    primary_record_authoritative: bool = True
    external_services: bool = False
    graphrag_runtime: bool = False
    correctness_proof: bool = False


class GraphNeighborsResult(BaseModel):
    node_id: str
    neighbors: list[AiGraphNode] = Field(default_factory=list)
    outgoing: list[AiGraphEdge] = Field(default_factory=list)
    incoming: list[AiGraphEdge] = Field(default_factory=list)
