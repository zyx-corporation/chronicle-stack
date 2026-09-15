"""Agent runtime integration contract models.

These models define how a future Kazane or agent runtime may describe its
Chronicle API access without owning the Chronicle record.
"""

from enum import StrEnum

from pydantic import BaseModel, Field, model_validator

from chronicle.api.contracts import ApiActorKind, ApiOriginMetadata


class AgentCapabilityScope(StrEnum):
    READ_CONTEXT = "read_context"
    READ_BOUNDARIES = "read_boundaries"
    WRITE_EVENTS = "write_events"
    WRITE_ASSERTIONS = "write_assertions"
    WRITE_DIFFS = "write_diffs"
    REQUEST_REVIEW = "request_review"


class AgentRecordOriginKind(StrEnum):
    HUMAN_JUDGMENT = "human_judgment"
    AI_PROPOSAL = "ai_proposal"
    AGENT_ACTION = "agent_action"
    BUSINESS_SYSTEM_FACT = "business_system_fact"
    DERIVED_INTERPRETATION = "derived_interpretation"


class AgentRuntimeMetadata(BaseModel):
    runtime_name: str = Field(min_length=1)
    actor_id: str = Field(min_length=1)
    origin_kind: AgentRecordOriginKind
    capability_scope: AgentCapabilityScope
    source_session: str | None = None
    human_supervisor_id: str | None = None
    review_required: bool = True

    @model_validator(mode="after")
    def _human_judgment_requires_supervisor(self) -> "AgentRuntimeMetadata":
        if (
            self.origin_kind == AgentRecordOriginKind.HUMAN_JUDGMENT
            and not self.human_supervisor_id
        ):
            raise ValueError("human_judgment records require human_supervisor_id")
        return self

    def to_api_origin(self) -> ApiOriginMetadata:
        return ApiOriginMetadata(
            source_tool=f"agent-runtime:{self.runtime_name}",
            actor_id=self.actor_id,
            actor_kind=(
                ApiActorKind.HUMAN
                if self.origin_kind == AgentRecordOriginKind.HUMAN_JUDGMENT
                else ApiActorKind.AGENT
            ),
            source_session=self.source_session,
            capability_id=f"agent.{self.capability_scope.value}",
        )


class AgentRuntimeContract(BaseModel):
    schema_version: str = "chronicle-agent-runtime/v0.1-draft"
    runtime_name: str
    allowed_scopes: list[AgentCapabilityScope]
    writes_through_chronicle_api: bool = True
    owns_primary_record: bool = False
    unbounded_memory_dump_allowed: bool = False
    review_required_for_ai_or_agent_output: bool = True
    replay_audit_required: bool = True
    notes: list[str] = Field(default_factory=list)


def default_agent_runtime_contract(runtime_name: str = "kazane-compatible-agent") -> AgentRuntimeContract:
    return AgentRuntimeContract(
        runtime_name=runtime_name,
        allowed_scopes=[
            AgentCapabilityScope.READ_CONTEXT,
            AgentCapabilityScope.READ_BOUNDARIES,
            AgentCapabilityScope.WRITE_EVENTS,
            AgentCapabilityScope.WRITE_ASSERTIONS,
            AgentCapabilityScope.WRITE_DIFFS,
            AgentCapabilityScope.REQUEST_REVIEW,
        ],
        notes=[
            "Agent runtime may read context and boundaries, but does not own the Chronicle.",
            "Agent-originated writes must preserve origin kind, scope, idempotency, and audit metadata.",
            "AI proposals and derived interpretations remain reviewable; they are not primary facts.",
        ],
    )
