"""Context integration package construction helpers."""

from chronicle.lifecycle.derived_output_policy import LifecycleTargetState, package_warnings_for_lifecycle
from chronicle.models.classification import ClassificationLayer
from chronicle.models.context import Context
from chronicle.models.integration_package import (
    IntegrationPackageRecord,
    IntegrationTargetEnvironment,
    PackageRecordBoundary,
)
from chronicle.security.prompt_injection import format_as_chronicle_data_block, scan_text_for_prompt_injection


class ContextSelectionPolicy:
    """Select Context records for controlled integration packages."""

    def select(
        self,
        contexts: dict[str, Context],
        context_ids: list[str] | None,
        lifecycle_states: dict[str, LifecycleTargetState] | None = None,
    ) -> list[Context]:
        selected_contexts = list(contexts.values()) if not context_ids else [contexts[context_id] for context_id in context_ids if context_id in contexts]
        if not lifecycle_states:
            return selected_contexts
        return [context for context in selected_contexts if not lifecycle_states.get(context.context_id, LifecycleTargetState(context.context_id)).is_tombstoned]


class ContextPackageRecordBuilder:
    """Build package records from Context models."""

    def build(
        self,
        context: Context,
        target_environment: IntegrationTargetEnvironment,
        lifecycle_state: LifecycleTargetState | None = None,
    ) -> IntegrationPackageRecord:
        classification = context.classification
        warnings: list[str] = []
        layer: int | None = None
        sensitivity = "unknown"
        allowed_operations: list[str] = []
        boundary = PackageRecordBoundary.CHRONICLE_DATA
        body = f"{context.title}\n{context.summary}"

        warnings.extend(package_warnings_for_lifecycle(lifecycle_state))

        if classification is None:
            warnings.append("unclassified_context")
        else:
            layer = int(classification.layer)
            sensitivity = classification.sensitivity.value
            allowed_operations = [operation.value for operation in classification.allowed_operations]
            if classification.layer == ClassificationLayer.RESTRICTED_SECRET:
                warnings.append("layer4_reference_only")
                boundary = PackageRecordBoundary.REFERENCE_ONLY
            if (
                target_environment == IntegrationTargetEnvironment.EXTERNAL
                and classification.layer >= ClassificationLayer.SENSITIVE_CONTEXT
                and not classification.llm_policy.external_allowed
            ):
                warnings.append("external_sensitive_context_not_allowed")

        scan = scan_text_for_prompt_injection(body, source_id=context.context_id)
        warnings.extend(f"prompt_marker:{finding.pattern_id}" for finding in scan.findings)

        content = None
        if boundary == PackageRecordBoundary.CHRONICLE_DATA:
            content = format_as_chronicle_data_block(
                source_id=context.context_id,
                title=context.title,
                body=context.summary,
            )

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


class PackageClassificationSummary:
    """Summarize output classification from package records."""

    def output_classification(self, records: list[IntegrationPackageRecord]) -> str:
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
