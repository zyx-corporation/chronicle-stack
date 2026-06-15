"""Controlled integration package service."""

from datetime import datetime, timezone
from pathlib import Path

from chronicle.ids import generate_id
from chronicle.integration.context_package_builder import (
    ContextPackageRecordBuilder,
    ContextSelectionPolicy,
    PackageClassificationSummary,
)
from chronicle.models.integration_package import (
    IntegrationPackage,
    IntegrationPackageKind,
    IntegrationPackageManifest,
    IntegrationTargetEnvironment,
)
from chronicle.services.chronicle_service import ChronicleService


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
