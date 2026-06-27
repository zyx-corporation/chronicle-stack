"""Controlled integration package service."""

from datetime import datetime, timezone
from pathlib import Path

from chronicle.ids import generate_id
from chronicle.integration.query_engine_adapter_skeleton import QueryEngineAdapterSkeletonBuilder
from chronicle.models.graph import GraphExport
from chronicle.models.integration_adapter import QueryEngineHandoffBundleManifest
from chronicle.models.runtime import RuntimeQueryEngineHandoff
from chronicle.integration.context_package_builder import (
    ContextPackageRecordBuilder,
    ContextSelectionPolicy,
    PackageClassificationSummary,
)
from chronicle.lifecycle.derived_output_policy import lifecycle_state_by_target
from chronicle.models.audit import AuditOperation, AuditSeverity, AuditTargetEnvironment
from chronicle.models.integration_package import (
    IntegrationPackage,
    IntegrationPackageKind,
    IntegrationPackageManifest,
    IntegrationPackageRecord,
    IntegrationTargetEnvironment,
)
from chronicle.services.audit_service import AuditService
from chronicle.services.chronicle_service import ChronicleService
from chronicle.store.integration_package_store import IntegrationPackageStore
from chronicle.store.lifecycle_store import LifecycleStore


class IntegrationPackageService:
    """Build controlled packages for future CSG-RAG / Sayane workflows.

    This service does not call models, vector databases, graph databases, or
    external runtimes.
    """

    def __init__(self, root: Path | None = None) -> None:
        self.chronicle = ChronicleService(root)
        self.selection_policy = ContextSelectionPolicy()
        self.query_engine_adapter_skeleton = QueryEngineAdapterSkeletonBuilder()
        self.record_builder = ContextPackageRecordBuilder()
        self.classification_summary = PackageClassificationSummary()
        self.store = IntegrationPackageStore(self.chronicle.paths)
        self.audit = AuditService(root)
        self.lifecycle_store = LifecycleStore(self.chronicle.paths.lifecycle_file)

    def build_context_package(
        self,
        *,
        purpose: str,
        target_environment: IntegrationTargetEnvironment = IntegrationTargetEnvironment.LOCAL,
        context_ids: list[str] | None = None,
    ) -> IntegrationPackage:
        metadata = self.chronicle.require_initialized()
        contexts = self.chronicle.index.load_contexts()
        lifecycle_states = lifecycle_state_by_target(self.lifecycle_store.read_all())
        selected = self.selection_policy.select(contexts, context_ids, lifecycle_states)
        records = [
            self.record_builder.build(context, target_environment, lifecycle_states.get(context.context_id))
            for context in selected
        ]
        warnings = sorted({warning for record in records for warning in record.warnings})
        excluded = sorted(
            context_id
            for context_id, state in lifecycle_states.items()
            if state.is_tombstoned and (context_ids is None or context_id in context_ids)
        )
        if excluded:
            warnings.append("lifecycle_tombstoned_records_excluded")

        manifest = IntegrationPackageManifest(
            package_id=generate_id("package"),
            chronicle_id=metadata.chronicle_id,
            created_at=datetime.now(timezone.utc).astimezone(),
            package_kind=IntegrationPackageKind.CONTEXT_PACKAGE,
            purpose=purpose,
            target_environment=target_environment,
            referenced_records=[record.record_id for record in records],
            output_classification=self.classification_summary.output_classification(records),
            warnings=warnings,
            metadata={
                "record_count": str(len(records)),
                "runtime": "none",
                "excluded_lifecycle_tombstone_count": str(len(excluded)),
            },
        )
        return IntegrationPackage(manifest=manifest, records=records)

    def build_query_engine_adapter_skeleton(
        self, handoff: RuntimeQueryEngineHandoff
    ):
        """Build a descriptive downstream adapter skeleton without executing it."""
        return self.query_engine_adapter_skeleton.build(handoff)

    def build_query_engine_handoff_bundle_manifest(
        self,
        handoff: RuntimeQueryEngineHandoff,
        graph_export: GraphExport,
    ) -> QueryEngineHandoffBundleManifest:
        """Build a descriptive manifest for a local downstream handoff bundle."""
        skeleton = self.query_engine_adapter_skeleton.build(handoff)
        import_validation = handoff.import_validation
        return QueryEngineHandoffBundleManifest(
            handoff_contract_version=handoff.contract_version,
            graph_export_contract_version=handoff.graph_export_contract_version,
            adapter_skeleton_contract_version=skeleton.contract_version,
            primary_record_path=handoff.primary_record_path,
            files=[
                "bundle_manifest.json",
                "query_engine_handoff.json",
                "query_engine_adapter_skeleton.json",
                "graph.json",
                "ACCEPTANCE_CHECKLIST.md",
            ],
            referenced_record_count=len(handoff.referenced_record_ids),
            eligible_context_count=len(handoff.eligible_context_ids),
            import_validation_status=(
                import_validation.status if import_validation is not None else "advisory_only"
            ),
            import_ready=bool(import_validation.import_ready) if import_validation is not None else False,
            notes=[
                "bundle remains local, read-only, and descriptive",
                "Chronicle primary records remain authoritative over derived bundle files",
                (
                    f"graph export contains {len(graph_export.nodes)} nodes and {len(graph_export.edges)} edges"
                ),
            ],
        )

    def save_package(self, package: IntegrationPackage) -> Path:
        """Persist a controlled integration package through the package store."""
        self.chronicle.require_initialized()
        package_dir = self.store.save(package)
        self._record_package_audit(package, package_dir)
        return package_dir

    def list_package_manifests(self) -> list[IntegrationPackageManifest]:
        """List persisted package manifests."""
        self.chronicle.require_initialized()
        return [self.store.load_manifest(package_id) for package_id in self.store.list_package_ids()]

    def load_package_manifest(self, package_id: str) -> IntegrationPackageManifest:
        """Load a persisted package manifest."""
        self.chronicle.require_initialized()
        return self.store.load_manifest(package_id)

    def load_package_records(self, package_id: str) -> list[IntegrationPackageRecord]:
        """Load persisted package records."""
        self.chronicle.require_initialized()
        return self.store.load_records(package_id)

    def load_package(self, package_id: str) -> IntegrationPackage:
        """Load a persisted controlled integration package."""
        self.chronicle.require_initialized()
        return self.store.load(package_id)

    def _record_package_audit(self, package: IntegrationPackage, package_dir: Path) -> None:
        """Record package persistence without copying record content."""
        manifest = package.manifest
        self.audit.record(
            operation=AuditOperation.EXPORT,
            actor="integration-package-service",
            purpose=manifest.purpose,
            target_environment=AuditTargetEnvironment.PACKAGE,
            output_classification=manifest.output_classification,
            referenced_records=manifest.referenced_records,
            result=AuditSeverity.INFO,
            summary=f"Persisted integration package {manifest.package_id}.",
            metadata={
                "package_id": manifest.package_id,
                "package_kind": manifest.package_kind.value,
                "record_count": str(len(package.records)),
                "package_path": str(package_dir),
            },
        )
