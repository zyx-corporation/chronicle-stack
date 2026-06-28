"""Local node trust registry service."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from chronicle.ids import generate_id
from chronicle.models.audit import AuditOperation, AuditSeverity, AuditTargetEnvironment
from chronicle.models.trust import (
    NodeProfile,
    TrustLevel,
    TrustRelation,
    TrustRelationStatus,
    TrustSummary,
)
from chronicle.services.audit_service import AuditService
from chronicle.services.chronicle_service import ChronicleService
from chronicle.store.trust_store import TrustStore


class TrustService:
    def __init__(self, root: Path | None = None) -> None:
        self.chronicle = ChronicleService(root)
        self.store = TrustStore(self.chronicle.paths)
        self.audit = AuditService(root)

    def add_node_profile(
        self,
        *,
        node_id: str,
        subject_id: str,
        display_name: str = "",
        public_key_ref: str = "",
        key_rotation_ref: str = "",
        delegated_actor_metadata: dict[str, str] | None = None,
        ai_proxy_generation_metadata: dict[str, str] | None = None,
        metadata: dict[str, str] | None = None,
    ) -> NodeProfile:
        self.chronicle.require_initialized()
        profile = NodeProfile(
            node_id=node_id,
            subject_id=subject_id,
            display_name=display_name,
            created_at=datetime.now(timezone.utc).astimezone(),
            public_key_ref=public_key_ref,
            key_rotation_ref=key_rotation_ref,
            delegated_actor_metadata=delegated_actor_metadata or {},
            ai_proxy_generation_metadata=ai_proxy_generation_metadata or {},
            metadata=metadata or {},
        )
        self.store.save_node_profile(profile)
        return profile

    def assert_relation(
        self,
        *,
        target_node: str,
        target_subject_id: str,
        domain: str,
        purpose: str,
        level: TrustLevel,
        capabilities: list[str] | None = None,
        context_scope: str = "",
        expires_at: datetime | None = None,
        created_from: str = "manual_assertion",
        delegated_actor_metadata: dict[str, str] | None = None,
        ai_proxy_generation_metadata: dict[str, str] | None = None,
    ) -> TrustRelation:
        metadata = self.chronicle.require_initialized()
        relation = TrustRelation(
            relation_id=generate_id("trust_relation"),
            source_node=self._local_node_id(metadata.chronicle_id),
            target_node=target_node,
            target_subject_id=target_subject_id,
            domain=domain,
            purpose=purpose,
            level=level,
            capabilities=capabilities or [],
            context_scope=context_scope,
            created_at=datetime.now(timezone.utc).astimezone(),
            expires_at=expires_at,
            created_from=created_from,
            delegated_actor_metadata=delegated_actor_metadata or {},
            ai_proxy_generation_metadata=ai_proxy_generation_metadata or {},
        )
        self.store.save_relation(relation)
        self._audit_relation(relation, action="asserted")
        return relation

    def withdraw_relation(
        self,
        *,
        relation_id: str,
        reason: str,
        delegated_actor_metadata: dict[str, str] | None = None,
        ai_proxy_generation_metadata: dict[str, str] | None = None,
    ) -> TrustRelation:
        relation = self.store.load_relation(relation_id)
        withdrawn = relation.model_copy(
            update={
                "status": TrustRelationStatus.WITHDRAWN,
                "level": TrustLevel.WITHDRAWN,
                "withdrawn_at": datetime.now(timezone.utc).astimezone(),
                "withdrawal_reason": reason,
                "delegated_actor_metadata": delegated_actor_metadata or relation.delegated_actor_metadata,
                "ai_proxy_generation_metadata": ai_proxy_generation_metadata or relation.ai_proxy_generation_metadata,
            }
        )
        self.store.save_relation(withdrawn)
        self._audit_relation(withdrawn, action="withdrawn")
        return withdrawn

    def list_node_profiles(self) -> list[NodeProfile]:
        self.chronicle.require_initialized()
        return sorted(self.store.list_node_profiles(), key=lambda item: item.created_at)

    def list_relations(self) -> list[TrustRelation]:
        self.chronicle.require_initialized()
        return sorted(self.store.list_relations(), key=lambda item: item.created_at, reverse=True)

    def summarize_for_target(self, *, target_node: str, purpose: str = "") -> TrustSummary:
        relations = [row for row in self.list_relations() if row.target_node == target_node]
        active = [row for row in relations if row.status == TrustRelationStatus.ACTIVE]
        capability_counts: dict[str, int] = {}
        domains = sorted({row.domain for row in active if row.domain})
        level_order = {
            TrustLevel.TRUSTED.value: 3,
            TrustLevel.LIMITED.value: 2,
            TrustLevel.OBSERVED.value: 1,
            TrustLevel.WITHDRAWN.value: 0,
        }
        dominant_level = "unknown"
        if active:
            dominant_level = max(active, key=lambda item: level_order.get(item.level.value, -1)).level.value
        for row in active:
            for capability in row.capabilities:
                capability_counts[capability] = capability_counts.get(capability, 0) + 1
        preview_message = (
            f"{len(active)} active trust relation(s) for {target_node}; dominant_level={dominant_level}."
            if active
            else f"No active trust relation for {target_node}; message/package handoff remains advisory only."
        )
        return TrustSummary(
            target_node=target_node,
            purpose=purpose,
            relation_count=len(relations),
            active_relation_count=len(active),
            dominant_level=dominant_level,
            capability_counts=capability_counts,
            domains=domains,
            preview_message=preview_message,
        )

    def _local_node_id(self, chronicle_id: str) -> str:
        return f"node:local:{chronicle_id}"

    def _audit_relation(self, relation: TrustRelation, *, action: str) -> None:
        self.audit.record(
            operation=AuditOperation.REINTERPRET,
            actor="trust-service",
            purpose=f"trust_{action}",
            target_environment=AuditTargetEnvironment.LOCAL,
            referenced_records=[relation.relation_id, relation.target_node],
            result=AuditSeverity.INFO,
            summary=f"Trust relation {action}: {relation.source_node} -> {relation.target_node}",
            metadata={
                "relation_id": relation.relation_id,
                "target_subject_id": relation.target_subject_id,
                "domain": relation.domain,
                "purpose": relation.purpose,
                "level": relation.level.value,
                "capabilities": ",".join(relation.capabilities),
                "status": relation.status.value,
                "delegated_actor_present": str(bool(relation.delegated_actor_metadata)).lower(),
                "ai_proxy_present": str(bool(relation.ai_proxy_generation_metadata)).lower(),
            },
        )
