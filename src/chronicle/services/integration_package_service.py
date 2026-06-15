"""Controlled integration package service."""

from datetime import datetime, timezone
from pathlib import Path

from chronicle.ids import generate_id
from chronicle.integration.context_package_builder import (
    ContextPackageRecordBuilder,
    ContextSelectionPolicy,
    PackageClassificationSummary,
)
from chronicle.models.audit import AuditOperation, AuditSeverity, AuditTargetEnvironment
from chronicle.models.integration_package import (
    IntegrationPackage,
    IntegrationPackageKind,
    IntegrationPackageManifest,
    IntegrationTargetEnvironment,
)
from chronicle.services.audit_service import AuditService
from chronicle.services.chronicle_service import ChronicleService
from chronicle.store.integration_package_store import IntegrationPackageStore


class IntegrationPackageService:
    """Build controlled packages for future CSG-RAG / Sayane workflows.

    This service does not call models, vector databases, graph databases, or
    external runtimes.
    """

    def __init__(self, root: Path | None = None) -> None:
        self.chronicle = ChronicleService(root)
        self.selection_policy = ContextSelectionPolicy()
        self.record_builder = ContextPackageRecordBuilder()
        self.classification_summary = PackageClassificationSummary()
        self.store = IntegrationPackageStore(self.chronicle.paths)
        self.audit = AuditService(root)

    def build_context_package(
        self,
        *,
        purpose: str,
        target_environment: IntegrationTargetEnvironment = IntegrationTargetEnvironment.LOCAL,
        context_ids: list[str] | None = None,
    ) -> IntegrationPackage:
        metadata = self.chronicle.require_initialized()
        contexts = self.chronicle.index.load_contexts()
        selected = self.selection_policy.select(contexts, context_ids)
        records = [self.record_builder.build(context, target_environment) for context in selected]
        warnings = sorted({warning for record in records for warning in record.warnings})

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
            },
        )
        return IntegrationPackage(manifest=manifest, records=records)

    def save_package(self, package: IntegrationPackage) -> Path:
        """Persist a controlled integration package through the package store."""
        self.chronicle.require_initialized()
        package_dir = self.store.save(package)
        self._record_package_audit(package, package_dir)
        return package_dir

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
