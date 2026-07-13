"""Scoped capability runtime for Stage 2 capability execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from chronicle.errors import (
    ArtifactNotFoundError,
    CapabilityAccessDeniedError,
    CapabilityNetworkAccessDeniedError,
    ContextNotFoundError,
)
from chronicle.models.capability import CapabilityManifest
from chronicle.models.context import Context
from chronicle.services.artifact_service import ArtifactService
from chronicle.services.capability_registry_service import CapabilityRegistryService
from chronicle.services.context_service import ContextService
from chronicle.services.proposal_service import ProposalService


@dataclass(frozen=True)
class ScopedContextProjection:
    """Read-only context view exposed to capability code."""

    context_id: str
    title: str
    summary: str
    scope: str
    tags: tuple[str, ...] = ()

    @classmethod
    def from_context(cls, context: Context) -> "ScopedContextProjection":
        return cls(
            context_id=context.context_id,
            title=context.title,
            summary=context.summary,
            scope=context.scope.value,
            tags=tuple(context.tags),
        )


@dataclass(frozen=True)
class CapabilityAuditMetadata:
    """Minimal audit context attached to scoped capability execution."""

    capability_id: str
    selected_context_ids: tuple[str, ...] = ()
    selected_artifact_ids: tuple[str, ...] = ()
    network_enabled: bool = False
    allowed_network_destinations: tuple[str, ...] = ()
    allowed_network_operations: tuple[str, ...] = ()


@dataclass(frozen=True)
class CapabilityNetworkPolicy:
    """Deny-by-default network policy for capability execution."""

    enabled: bool = False
    allowed_destinations: tuple[str, ...] = ()
    allowed_operations: tuple[str, ...] = ()

    def allows(self, *, destination: str, operation: str) -> bool:
        if not self.enabled:
            return False
        return destination in self.allowed_destinations and operation in self.allowed_operations


class ScopedContextReader:
    """Read-only access limited to preselected context IDs."""

    def __init__(self, service: ContextService, allowed_context_ids: set[str]) -> None:
        self._service = service
        self._allowed_context_ids = allowed_context_ids

    def get(self, context_id: str) -> ScopedContextProjection:
        if context_id not in self._allowed_context_ids:
            raise CapabilityAccessDeniedError(resource_kind="context", resource_id=context_id)
        context = self._service.get_context(context_id)
        return ScopedContextProjection.from_context(context)

    def list_selected(self) -> list[ScopedContextProjection]:
        return [self.get(context_id) for context_id in sorted(self._allowed_context_ids)]


class ScopedArtifactAccess:
    """Read-only artifact access limited to preselected artifact IDs."""

    def __init__(self, service: ArtifactService, allowed_artifact_ids: set[str]) -> None:
        self._service = service
        self._allowed_artifact_ids = allowed_artifact_ids

    def get(self, artifact_id: str):
        if artifact_id not in self._allowed_artifact_ids:
            raise CapabilityAccessDeniedError(resource_kind="artifact", resource_id=artifact_id)
        return self._service.get(artifact_id)

    def read_current(self, artifact_id: str) -> str:
        artifact = self.get(artifact_id)
        return self._service.chronicle.artifact_store.read_current(artifact.artifact_id)


class ScopedProposalWriter:
    """Proposal-only mutation surface for capability execution."""

    def __init__(self, service: ProposalService, allowed_artifact_ids: set[str], allowed_context_ids: set[str]) -> None:
        self._service = service
        self._allowed_artifact_ids = allowed_artifact_ids
        self._allowed_context_ids = allowed_context_ids

    def propose_artifact_update(self, **kwargs):
        artifact_id = str(kwargs["artifact_id"])
        if artifact_id not in self._allowed_artifact_ids:
            raise CapabilityAccessDeniedError(resource_kind="artifact", resource_id=artifact_id)
        return self._service.propose_artifact_update(**kwargs)

    def propose_context_update(self, **kwargs):
        context_id = str(kwargs["context_id"])
        if context_id not in self._allowed_context_ids:
            raise CapabilityAccessDeniedError(resource_kind="context", resource_id=context_id)
        return self._service.propose_context_update(**kwargs)


class PolicyBoundNetworkClient:
    """Policy-only network authorizer for capability runtime."""

    def __init__(self, *, capability_id: str, policy: CapabilityNetworkPolicy) -> None:
        self._capability_id = capability_id
        self._policy = policy

    def authorize(self, *, destination: str, operation: str) -> dict[str, str]:
        if not self._policy.allows(destination=destination, operation=operation):
            raise CapabilityNetworkAccessDeniedError(
                capability_id=self._capability_id,
                destination=destination,
                operation=operation,
            )
        return {"destination": destination, "operation": operation}


@dataclass(frozen=True)
class ScopedCapabilityRuntime:
    """Capability execution context with deny-by-default access surfaces."""

    manifest: CapabilityManifest
    contexts: ScopedContextReader
    artifacts: ScopedArtifactAccess
    proposals: ScopedProposalWriter
    network: PolicyBoundNetworkClient
    audit: CapabilityAuditMetadata


@dataclass
class ScopedCapabilityRuntimeFactory:
    """Build deny-by-default scoped runtimes from the static capability registry."""

    root: Path | None = None
    registry: CapabilityRegistryService = field(default_factory=CapabilityRegistryService)

    def create(
        self,
        *,
        capability_id: str,
        selected_context_ids: list[str] | None = None,
        selected_artifact_ids: list[str] | None = None,
        network_policy: CapabilityNetworkPolicy | None = None,
    ) -> ScopedCapabilityRuntime:
        manifest = self.registry.get_capability(capability_id)
        selected_context_ids = sorted(set(selected_context_ids or []))
        selected_artifact_ids = sorted(set(selected_artifact_ids or []))
        self._validate_selected_records(
            context_ids=selected_context_ids,
            artifact_ids=selected_artifact_ids,
        )

        effective_policy = network_policy or CapabilityNetworkPolicy()
        if not manifest.uses_network:
            effective_policy = CapabilityNetworkPolicy()

        return ScopedCapabilityRuntime(
            manifest=manifest,
            contexts=ScopedContextReader(ContextService(self.root), set(selected_context_ids)),
            artifacts=ScopedArtifactAccess(ArtifactService(self.root), set(selected_artifact_ids)),
            proposals=ScopedProposalWriter(
                ProposalService(self.root),
                set(selected_artifact_ids),
                set(selected_context_ids),
            ),
            network=PolicyBoundNetworkClient(
                capability_id=capability_id,
                policy=effective_policy,
            ),
            audit=CapabilityAuditMetadata(
                capability_id=capability_id,
                selected_context_ids=tuple(selected_context_ids),
                selected_artifact_ids=tuple(selected_artifact_ids),
                network_enabled=effective_policy.enabled,
                allowed_network_destinations=effective_policy.allowed_destinations,
                allowed_network_operations=effective_policy.allowed_operations,
            ),
        )

    def _validate_selected_records(self, *, context_ids: list[str], artifact_ids: list[str]) -> None:
        context_service = ContextService(self.root)
        artifact_service = ArtifactService(self.root)
        for context_id in context_ids:
            try:
                context_service.get_context(context_id)
            except ContextNotFoundError:
                raise
        for artifact_id in artifact_ids:
            try:
                artifact_service.get(artifact_id)
            except ArtifactNotFoundError:
                raise
