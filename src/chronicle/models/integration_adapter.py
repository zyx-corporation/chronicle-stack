"""Descriptive downstream adapter skeleton models."""

from pydantic import BaseModel, Field


class AdapterSkeletonStep(BaseModel):
    name: str
    required: bool = True
    command_hint: str = ""
    notes: list[str] = Field(default_factory=list)


class QueryEngineAdapterSkeleton(BaseModel):
    contract_version: str = "1.0"
    skeleton_kind: str = "query_engine_import_adapter"
    handoff_contract_version: str = "1.0"
    import_validation_contract_version: str = "1.0"
    primary_record_path: str = ".chronicle/chronicle.jsonl"
    graph_export_format: str = "graph-json"
    graph_export_contract_version: str = "1.0"
    required_inputs: list[str] = Field(default_factory=list)
    recommended_sequence: list[AdapterSkeletonStep] = Field(default_factory=list)
    prohibited_capabilities: list[str] = Field(default_factory=list)
    non_goals: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class QueryEngineHandoffBundleManifest(BaseModel):
    contract_version: str = "1.0"
    bundle_kind: str = "query_engine_handoff_bundle"
    handoff_contract_version: str = "1.0"
    graph_export_contract_version: str = "1.0"
    adapter_skeleton_contract_version: str = "1.0"
    primary_record_path: str = ".chronicle/chronicle.jsonl"
    files: list[str] = Field(default_factory=list)
    referenced_record_count: int = 0
    eligible_context_count: int = 0
    import_validation_status: str = "advisory_only"
    import_ready: bool = False
    notes: list[str] = Field(default_factory=list)
