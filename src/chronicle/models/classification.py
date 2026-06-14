"""Security-aware classification metadata models.

These models are advisory metadata for v0.5 security-aware composition.
They do not implement access control, authentication, encryption, or policy enforcement.
"""

from datetime import datetime
from enum import IntEnum, StrEnum

from pydantic import BaseModel, Field, model_validator


class ClassificationLayer(IntEnum):
    """Security classification layer for context assets."""

    PUBLIC = 0
    SHAREABLE = 1
    INTERNAL = 2
    SENSITIVE_CONTEXT = 3
    RESTRICTED_SECRET = 4


class Sensitivity(StrEnum):
    """Human-readable sensitivity label."""

    PUBLIC = "public"
    SHAREABLE = "shareable"
    INTERNAL = "internal"
    SENSITIVE = "sensitive"
    RESTRICTED = "restricted"
    UNKNOWN = "unknown"


class AllowedOperation(StrEnum):
    """Operation categories used for advisory policy checks.

    These values describe what a caller intends to do with a record. They are
    not access-control enforcement by themselves.
    """

    VIEW = "view"
    CREATE = "create"
    EDIT = "edit"
    APPEND = "append"
    SUMMARIZE = "summarize"
    REINTERPRET = "reinterpret"
    REDACT = "redact"
    SEAL = "seal"
    EXPORT = "export"
    INJECT = "inject"
    PUBLISH = "publish"


READ_LIKE_OPERATIONS = frozenset({
    AllowedOperation.VIEW,
    AllowedOperation.SUMMARIZE,
})

MUTATION_LIKE_OPERATIONS = frozenset({
    AllowedOperation.CREATE,
    AllowedOperation.EDIT,
    AllowedOperation.APPEND,
    AllowedOperation.REDACT,
    AllowedOperation.SEAL,
})

DISCLOSURE_LIKE_OPERATIONS = frozenset({
    AllowedOperation.EXPORT,
    AllowedOperation.INJECT,
    AllowedOperation.PUBLISH,
})

DERIVED_MEANING_OPERATIONS = frozenset({
    AllowedOperation.REINTERPRET,
})


class RetentionMode(StrEnum):
    """Retention lifecycle mode for a classified record."""

    KEEP = "keep"
    REVIEW = "review"
    EXPIRE = "expire"
    SEAL = "seal"


class LlmPolicy(BaseModel):
    """Advisory policy for model-context use."""

    local_allowed: bool = True
    external_allowed: bool = False
    masking_required: bool = True


class RetentionPolicy(BaseModel):
    """Retention metadata for future review / sealing workflows."""

    mode: RetentionMode = RetentionMode.KEEP
    review_at: datetime | None = None


class IntegrityMetadata(BaseModel):
    """Optional integrity metadata preparation.

    This is metadata for future change detection. It is not a guarantee that
    a record is tamper-proof.
    """

    hash: str = ""
    previous_hash: str = ""
    signature: str = ""
    snapshot_id: str = ""


class ClassificationMetadata(BaseModel):
    """Advisory classification metadata for Chronicle context assets."""

    layer: ClassificationLayer = ClassificationLayer.INTERNAL
    sensitivity: Sensitivity = Sensitivity.INTERNAL
    owner: str = ""
    created_at: datetime | None = None
    source_type: str = ""
    source_refs: list[str] = Field(default_factory=list)
    allowed_operations: list[AllowedOperation] = Field(default_factory=lambda: [
        AllowedOperation.VIEW,
        AllowedOperation.SUMMARIZE,
        AllowedOperation.REINTERPRET,
    ])
    llm_policy: LlmPolicy = Field(default_factory=LlmPolicy)
    retention: RetentionPolicy = Field(default_factory=RetentionPolicy)
    integrity: IntegrityMetadata = Field(default_factory=IntegrityMetadata)

    @model_validator(mode="after")
    def _align_restricted_defaults(self) -> "ClassificationMetadata":
        """Keep Layer 4 conservative by default.

        The model remains advisory, but when a caller marks a record as Layer 4
        and leaves broad operations in place, we narrow the default list to view
        only. Explicit callers can still override this by passing operations.
        """
        if self.layer == ClassificationLayer.RESTRICTED_SECRET and self.allowed_operations == [
            AllowedOperation.VIEW,
            AllowedOperation.SUMMARIZE,
            AllowedOperation.REINTERPRET,
        ]:
            self.allowed_operations = [AllowedOperation.VIEW]
            self.llm_policy.local_allowed = False
            self.llm_policy.external_allowed = False
            self.llm_policy.masking_required = True
        return self
