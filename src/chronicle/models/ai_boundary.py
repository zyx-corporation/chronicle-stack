"""AI boundary preview models for external adapter review."""

from datetime import datetime

from pydantic import BaseModel, Field


class AiBoundaryPersistencePolicy(BaseModel):
    persist_prompt: bool = False
    persist_response: bool = False
    persist_model_id: bool = True
    persist_runtime_label: bool = True
    persist_timestamp: bool = True


class SayaneAdapterContract(BaseModel):
    export_command: str
    import_command: str
    accepted_payloads: list[str] = Field(default_factory=list)
    boundaries: list[str] = Field(default_factory=list)


class AiBoundaryPreview(BaseModel):
    task: str
    model_id: str
    runtime_label: str
    source_chronicle_id: str
    target_environment: str = "external"
    requested_context_ids: list[str] = Field(default_factory=list)
    included_context_ids: list[str] = Field(default_factory=list)
    excluded_context_ids: list[str] = Field(default_factory=list)
    redaction_candidates: list[str] = Field(default_factory=list)
    package_warnings: list[str] = Field(default_factory=list)
    persistence_policy: AiBoundaryPersistencePolicy = Field(
        default_factory=AiBoundaryPersistencePolicy
    )
    prompt_text: str | None = None
    response_text: str | None = None
    occurred_at: datetime | None = None
    notes: list[str] = Field(default_factory=list)
    sayane_contract: SayaneAdapterContract
    recorded: bool = False
    event_id: str | None = None

