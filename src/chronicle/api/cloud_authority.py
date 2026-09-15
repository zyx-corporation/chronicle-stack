"""Chronicle Cloud authority planning contracts.

These models describe future cloud authority labels without implementing cloud
sync, storage, tenancy, or remote authorization.
"""

from enum import StrEnum

from pydantic import BaseModel, Field


class CloudAuthoritySurface(StrEnum):
    LOCAL_PRIMARY_RECORD = "local_primary_record"
    CLOUD_REPLICA = "cloud_replica"
    CLOUD_INDEX = "cloud_index"
    CLOUD_CACHE = "cloud_cache"
    COLLABORATION_VIEW = "collaboration_view"
    SHARED_EXPORT = "shared_export"


class CloudAuthorityEntry(BaseModel):
    surface: CloudAuthoritySurface
    label: str
    can_be_source_authority: bool
    exportable_required: bool = True
    reconstructable_required: bool = True
    notes: list[str] = Field(default_factory=list)


class CloudAuthorityModel(BaseModel):
    schema_version: str = "chronicle-cloud-authority/v0.1-draft"
    cloud_owns_chronicle: bool = False
    cloud_ai_memory_positioning_allowed: bool = False
    local_recovery_required: bool = True
    backup_sync_is_publication: bool = False
    federation_distinct_from_cloud_sharing: bool = True
    entries: list[CloudAuthorityEntry]
    unresolved: list[str] = Field(default_factory=list)


class CloudFederationSurface(StrEnum):
    TEAM_SYNC = "team_sync"
    ORGANIZATION_SHARING = "organization_sharing"
    PARTNER_DISCLOSURE = "partner_disclosure"
    PUBLIC_MATERIAL = "public_material"
    FEDERATION_PACKAGE = "federation_package"
    FEDERATION_MESSAGE = "federation_message"


class CloudFederationBoundaryEntry(BaseModel):
    surface: CloudFederationSurface
    belongs_to_cloud: bool
    belongs_to_federation: bool
    consent_required: bool
    redaction_preview_required: bool
    trust_scope_required: bool
    notes: list[str] = Field(default_factory=list)


class CloudFederationBoundaryModel(BaseModel):
    schema_version: str = "chronicle-cloud-federation-boundary/v0.1-draft"
    cloud_bypasses_federation_consent: bool = False
    federation_is_trust_disclosure_layer: bool = True
    cloud_sync_is_not_publication: bool = True
    entries: list[CloudFederationBoundaryEntry]
    adr_required_for_cloud_federation_bridge: bool = True


def default_cloud_authority_model() -> CloudAuthorityModel:
    return CloudAuthorityModel(
        entries=[
            CloudAuthorityEntry(
                surface=CloudAuthoritySurface.LOCAL_PRIMARY_RECORD,
                label="Local primary Chronicle record",
                can_be_source_authority=True,
                notes=["Current Chronicle JSONL authority anchor."],
            ),
            CloudAuthorityEntry(
                surface=CloudAuthoritySurface.CLOUD_REPLICA,
                label="Cloud replica",
                can_be_source_authority=False,
                notes=["Future sync copy; must not silently replace local authority."],
            ),
            CloudAuthorityEntry(
                surface=CloudAuthoritySurface.CLOUD_INDEX,
                label="Cloud derived index",
                can_be_source_authority=False,
                notes=["Rebuildable search or collaboration index only."],
            ),
            CloudAuthorityEntry(
                surface=CloudAuthoritySurface.CLOUD_CACHE,
                label="Cloud cache",
                can_be_source_authority=False,
                notes=["Temporary service acceleration surface."],
            ),
            CloudAuthorityEntry(
                surface=CloudAuthoritySurface.COLLABORATION_VIEW,
                label="Collaboration view",
                can_be_source_authority=False,
                notes=["Team-facing view with explicit provenance back to Chronicle records."],
            ),
            CloudAuthorityEntry(
                surface=CloudAuthoritySurface.SHARED_EXPORT,
                label="Shared export",
                can_be_source_authority=False,
                notes=["Disclosure artifact, not automatic federation or publication."],
            ),
        ],
        unresolved=[
            "sync_conflict_resolution",
            "team_permission_model",
            "tenant_isolation",
            "offline_recovery_protocol",
        ],
    )


def default_cloud_federation_boundary_model() -> CloudFederationBoundaryModel:
    return CloudFederationBoundaryModel(
        entries=[
            CloudFederationBoundaryEntry(
                surface=CloudFederationSurface.TEAM_SYNC,
                belongs_to_cloud=True,
                belongs_to_federation=False,
                consent_required=False,
                redaction_preview_required=False,
                trust_scope_required=False,
                notes=["Same-organization service-layer sync; not partner disclosure."],
            ),
            CloudFederationBoundaryEntry(
                surface=CloudFederationSurface.ORGANIZATION_SHARING,
                belongs_to_cloud=True,
                belongs_to_federation=False,
                consent_required=True,
                redaction_preview_required=True,
                trust_scope_required=False,
                notes=["Team/organization sharing still preserves provenance and authority labels."],
            ),
            CloudFederationBoundaryEntry(
                surface=CloudFederationSurface.PARTNER_DISCLOSURE,
                belongs_to_cloud=False,
                belongs_to_federation=True,
                consent_required=True,
                redaction_preview_required=True,
                trust_scope_required=True,
                notes=["Cross-organization disclosure belongs to Federation by default."],
            ),
            CloudFederationBoundaryEntry(
                surface=CloudFederationSurface.PUBLIC_MATERIAL,
                belongs_to_cloud=False,
                belongs_to_federation=True,
                consent_required=True,
                redaction_preview_required=True,
                trust_scope_required=True,
                notes=["Public release is a disclosure act, not ordinary sync."],
            ),
            CloudFederationBoundaryEntry(
                surface=CloudFederationSurface.FEDERATION_PACKAGE,
                belongs_to_cloud=False,
                belongs_to_federation=True,
                consent_required=True,
                redaction_preview_required=True,
                trust_scope_required=True,
                notes=["Manual package surface with inspect/verify/preview boundaries."],
            ),
            CloudFederationBoundaryEntry(
                surface=CloudFederationSurface.FEDERATION_MESSAGE,
                belongs_to_cloud=False,
                belongs_to_federation=True,
                consent_required=True,
                redaction_preview_required=True,
                trust_scope_required=True,
                notes=["Message exchange is review-first and cannot auto-apply."],
            ),
        ]
    )
