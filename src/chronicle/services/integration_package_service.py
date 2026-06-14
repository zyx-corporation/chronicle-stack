"""Controlled integration package service."""

from datetime import datetime, timezone
from pathlib import Path

from chronicle.ids import generate_id
from chronicle.models.classification import ClassificationLayer
from chronicle.models.context import Context
from chronicle.models.integration_package import (
    IntegrationPackage,
    IntegrationPackageKind,
    IntegrationPackageManifest,
    IntegrationPackageRecord,
    IntegrationTargetEnvironment,
    PackageRecordBoundary,
)
from chronicle.security.prompt_injection import format_as_chronicle_data_block, scan_text_for_prompt_injection
from chronicle.services.chronicle_service import ChronicleService


class IntegrationPackageService:
    """Build controlled packages for future CSG-RAG / Sayane workflows.

    This service does not call models, vector databases, graph databases, or
    external runtimes.
    """

    def __init__(self, root: Path | None = None) -> None:
        self.chronicle = ChronicleService(root)

    def build_context_package(
        self,
        *,
        purpose: str,
        target_environment: IntegrationTargetEnvironment = IntegrationTargetEnvironment.LOCAL,
        context_ids: list[str] | None = None,
    ) -> IntegrationPackage:
        metadata = self.chronicle.require_initialized()
        contexts = self.chronicle.index.load_contexts()
        selected = self._select_contexts(contexts, context_ids)
        records = [self._context_record(ctx, target_environment) for ctx in selected]
        warnings = sorted({warning for record in records for warning in record.warnings})

        manifest = IntegrationPackageManifest(
            package_id=generate_id("package"),
            chronicle_id=metadata.chronicle_id,
            created_at=datetime.now(timezone.utc).astimezone(),
            package_kind=IntegrationPackageKind.CONTEXT_PACKAGE,
            purpose=purpose,
            target_environment=target_environment,
            referenced_records=[record.record_id for record in records],
            output_classification=self._output_classification(records),
            warnings=warnings,
            metadata={
                "record_count": str(len(records)),
                "runtime": "none",
            },
        )
        return IntegrationPackage(manifest=manifest, records=records)

    def _select_contexts(
        self,
        contexts: dict[str, Context],
        context_ids: list[str] | None,
    ) -> list[Context]:
        if not context_ids:
            return list(contexts.values())
        return [contexts[cid] for cid in context_ids if cid in contexts]

    def _context_record(
        self,
        context: Context,
        target_environment: IntegrationTargetEnvironment,
    ) -> IntegrationPackageRecord:
        classification = context.classification
        warnings: list[str] = []
        layer: int | None = None
        sensitivity = "unknown"
        allowed_operations: list[str] = []
        boundary = PackageRecordBoundary.CHRONICLE_DATA
        body = f"{context.title}\n{context.summary}"

        if classification is None:
            warnings.append("unclassified_context")
        else:
            layer = int(classification.layer)
            sensitivity = classification.sensitivity.value
            allowed_operations = [op.value for op in classification.allowed_operations]
            if classification.layer == ClassificationLayer.RESTRICTED_SECRET:
                warnings.append("layer4_reference_only")
                boundary = PackageRecordBoundary.REFERENCE_ONLY
            if target_environment == IntegrationTargetEnvironment.EXTERNAL and classification.layer >= ClassificationLayer.SENSITIVE_CONTEXT and not classification.llm_policy.external_allowed:
                warnings.append("external_sensitive_context_not_allowed")

        scan = scan_text_for_prompt_injection(body, source_id=context.context_id)
        warnings.extend(f"prompt_marker:{finding.pattern_id}" for finding in scan.findings)

        content = None
        if boundary == PackageRecordBoundary.CHRONICLE_DATA:
            content = format_as_chronicle_data_block(source_id=context.context_id, title=context.title, body=context.summary)

        return IntegrationPackageRecord(
            record_id=context.context_id,
            record_kind="context",
            title=context.title,
            classification_layer=layer,
            sensitivity=sensitivity,
            allowed_operations=allowed_operations,
            content_boundary=boundary,
            content=content,
            warnings=sorted(set(warnings)),
            metadata={
                "scope": context.scope.value,
                "visibility_hint": context.visibility_hint.value,
            },
        )

    def _output_classification(self, records: list[IntegrationPackageRecord]) -> str:
        layers = [record.classification_layer for record in records if record.classification_layer is not None]
        if not layers:
            return "unknown"
        highest = max(layers)
        if highest >= 4:
            return "restricted"
        if highest >= 3:
            return "sensitive"
        if highest == 2:
            return "internal"
        if highest == 1:
            return "shareable"
        return "public"
