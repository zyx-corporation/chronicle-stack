"""Federation package models for local-first handoff bundles."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class FederationPackageVisibility(StrEnum):
    PRIVATE = "private"
    TRUSTED = "trusted"
    PROJECT = "project"
    ORGANIZATION = "organization"
    COMMUNITY = "community"
    FEDERATED = "federated"
    PUBLIC = "public"


class FederationPackageSignatureMode(StrEnum):
    UNSIGNED = "unsigned"
    LOCAL_DEV = "local_dev"


class FederationPackageSignatureStatus(StrEnum):
    UNSIGNED = "unsigned"
    SIGNED = "signed"
    MISMATCH = "mismatch"
    EXPIRED = "expired"
    REVOKED = "revoked"


class FederationPackageFileEntry(BaseModel):
    path: str
    sha256: str


class FederationPackageSignature(BaseModel):
    algorithm: str = "placeholder"
    key_id: str = "local-dev-key"
    value: str = ""
    status: FederationPackageSignatureStatus = FederationPackageSignatureStatus.UNSIGNED
    signed_at: datetime | None = None
    expires_at: datetime | None = None
    revoked_at: datetime | None = None
    revocation_reason: str | None = None


class FederationPackageRetentionPolicy(BaseModel):
    expires_at: str | None = None
    revocable: bool = True


class FederationPackageManifest(BaseModel):
    schema_version: str = "federation-manifest/v0.1"
    package_id: str
    chronicle_id: str
    created_at: datetime
    created_by_node: str
    target_node: str
    purpose: str
    visibility: FederationPackageVisibility = FederationPackageVisibility.FEDERATED
    source_root: str
    tool_version: str
    referenced_records: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    files: list[FederationPackageFileEntry] = Field(default_factory=list)
    retention_policy: FederationPackageRetentionPolicy = Field(
        default_factory=FederationPackageRetentionPolicy
    )
    signature: FederationPackageSignature = Field(default_factory=FederationPackageSignature)
    notes: list[str] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)


class FederationPackageRedactionReport(BaseModel):
    advisory_only: bool = True
    record_count: int = 0
    reference_only_record_ids: list[str] = Field(default_factory=list)
    warning_codes: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class FederationPackageVerificationEntry(BaseModel):
    path: str
    expected_sha256: str
    actual_sha256: str | None = None
    exists: bool = False
    matches: bool = False


class FederationPackageVerificationReport(BaseModel):
    package_path: str
    manifest_path: str
    signature_status: FederationPackageSignatureStatus
    valid: bool
    files_checked: list[FederationPackageVerificationEntry] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
