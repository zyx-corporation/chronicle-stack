"""Node trust model for federation Phase 6."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class TrustLevel(StrEnum):
    OBSERVED = "observed"
    LIMITED = "limited"
    TRUSTED = "trusted"
    WITHDRAWN = "withdrawn"


class TrustRelationStatus(StrEnum):
    ACTIVE = "active"
    WITHDRAWN = "withdrawn"


class NodeProfile(BaseModel):
    node_id: str
    subject_id: str
    display_name: str = ""
    created_at: datetime
    public_key_ref: str = ""
    key_rotation_ref: str = ""
    delegated_actor_metadata: dict[str, str] = Field(default_factory=dict)
    ai_proxy_generation_metadata: dict[str, str] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class TrustRelation(BaseModel):
    relation_id: str
    source_node: str
    target_node: str
    target_subject_id: str = ""
    domain: str
    purpose: str
    level: TrustLevel
    capabilities: list[str] = Field(default_factory=list)
    context_scope: str = ""
    created_at: datetime
    expires_at: datetime | None = None
    status: TrustRelationStatus = TrustRelationStatus.ACTIVE
    created_from: str = "manual_assertion"
    delegated_actor_metadata: dict[str, str] = Field(default_factory=dict)
    ai_proxy_generation_metadata: dict[str, str] = Field(default_factory=dict)
    withdrawn_at: datetime | None = None
    withdrawal_reason: str = ""


class TrustSummary(BaseModel):
    target_node: str
    purpose: str
    relation_count: int = 0
    active_relation_count: int = 0
    dominant_level: str = "unknown"
    capability_counts: dict[str, int] = Field(default_factory=dict)
    domains: list[str] = Field(default_factory=list)
    preview_message: str = ""
