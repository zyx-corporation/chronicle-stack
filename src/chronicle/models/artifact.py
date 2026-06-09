"""Artifact and version models."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ArtifactType(StrEnum):
    DOCUMENT = "document"
    SPECIFICATION = "specification"
    ROADMAP = "roadmap"
    ESSAY = "essay"
    SUMMARY = "summary"
    TRANSLATION = "translation"
    CODE = "code"
    PROMPT = "prompt"
    REVIEW = "review"
    REPORT = "report"
    CONFIGURATION = "configuration"
    OTHER = "other"


class ArtifactStatus(StrEnum):
    DRAFT = "draft"
    REVIEWING = "reviewing"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"
    UNKNOWN = "unknown"


class Artifact(BaseModel):
    artifact_id: str
    chronicle_id: str
    title: str
    artifact_type: ArtifactType
    current_version_id: str
    created_at: datetime
    updated_at: datetime
    status: ArtifactStatus = ArtifactStatus.DRAFT
    path: str
    tags: list[str] = Field(default_factory=list)


class ArtifactVersion(BaseModel):
    version_id: str
    artifact_id: str
    created_at: datetime
    created_by: str
    source_event_id: str
    parent_version_id: str | None = None
    path: str
    change_summary: str = ""
    rde_record_id: str | None = None
