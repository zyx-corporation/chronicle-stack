"""Controlled integration package models for CSG-RAG / Sayane workflows."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class IntegrationTargetEnvironment(StrEnum):
    """Target environment for a controlled package."""

    LOCAL = "local"
    EXTERNAL = "external"
    UNKNOWN = "unknown"


class IntegrationPackageKind(StrEnum):
    """Controlled package kind."""

    CONTEXT_PACKAGE = "context_package"
    REVIEW_PACKAGE = "review_package"


class PackageRecordBoundary(StrEnum):
    """How the record body is represented inside a package."""

    CHRONICLE_DATA = "chronicle_data"
    REFERENCE_ONLY = "reference_only"


class IntegrationPackageRecord(BaseModel):
    """One record included in a controlled integration package."""

    record_id: str
    record_kind: str
    title: str = ""
    classification_layer: int | None = None
    sensitivity: str = "unknown"
    allowed_operations: list[str] = Field(default_factory=list)
    content_boundary: PackageRecordBoundary = PackageRecordBoundary.CHRONICLE_DATA
    content: str | None = None
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)


class IntegrationPackageManifest(BaseModel):
    """Manifest for a controlled integration package."""

    schema_version: str = "0.5"
    package_id: str
    chronicle_id: str
    created_at: datetime
    package_kind: IntegrationPackageKind
    purpose: str = ""
    target_environment: IntegrationTargetEnvironment = IntegrationTargetEnvironment.UNKNOWN
    referenced_records: list[str] = Field(default_factory=list)
    output_classification: str = "unknown"
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)


class IntegrationPackage(BaseModel):
    """Controlled integration package payload.

    This is a transport contract, not a GraphRAG engine or model runtime.
    """

    manifest: IntegrationPackageManifest
    records: list[IntegrationPackageRecord] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
