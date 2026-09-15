"""Chronicle-native API contract models.

These models describe the planned local API surface without implementing a
daemon, HTTP server, or hosted endpoint.
"""

from chronicle.api.contracts import (
    API_SCHEMA_VERSION,
    ApiEndpoint,
    AssertionWriteRequest,
    BoundariesQueryRequest,
    ContextQueryRequest,
    DiffWriteRequest,
    EndpointContract,
    EventWriteRequest,
    TimelineQueryRequest,
    list_endpoint_contracts,
)
from chronicle.api.agent_runtime import (
    AgentCapabilityScope,
    AgentRecordOriginKind,
    AgentRuntimeContract,
    AgentRuntimeMetadata,
    default_agent_runtime_contract,
)
from chronicle.api.cloud_authority import (
    CloudAuthorityEntry,
    CloudAuthorityModel,
    CloudAuthoritySurface,
    CloudFederationBoundaryEntry,
    CloudFederationBoundaryModel,
    CloudFederationSurface,
    default_cloud_federation_boundary_model,
    default_cloud_authority_model,
)

__all__ = [
    "API_SCHEMA_VERSION",
    "ApiEndpoint",
    "AssertionWriteRequest",
    "BoundariesQueryRequest",
    "ContextQueryRequest",
    "DiffWriteRequest",
    "EndpointContract",
    "EventWriteRequest",
    "TimelineQueryRequest",
    "list_endpoint_contracts",
    "AgentCapabilityScope",
    "AgentRecordOriginKind",
    "AgentRuntimeContract",
    "AgentRuntimeMetadata",
    "default_agent_runtime_contract",
    "CloudAuthorityEntry",
    "CloudAuthorityModel",
    "CloudAuthoritySurface",
    "CloudFederationBoundaryEntry",
    "CloudFederationBoundaryModel",
    "CloudFederationSurface",
    "default_cloud_federation_boundary_model",
    "default_cloud_authority_model",
]
