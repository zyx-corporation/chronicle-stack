"""Dry-run checks for model-context use."""

from pathlib import Path

from chronicle.models.classification import AllowedOperation, ClassificationLayer
from chronicle.models.context import Context
from chronicle.models.context_use import (
    ContextUseCheckReport,
    ContextUseFinding,
    ContextUseSeverity,
    ContextUseTarget,
)
from chronicle.services.chronicle_service import ChronicleService


class ContextUseService:
    """Evaluate whether selected Context records are suitable for model-context use.

    This service is read-only. It does not submit context to any model service.
    """

    def __init__(self, root: Path | None = None) -> None:
        self.chronicle = ChronicleService(root)

    def check(
        self,
        *,
        target: ContextUseTarget,
        purpose: str,
        context_ids: list[str] | None = None,
    ) -> ContextUseCheckReport:
        self.chronicle.require_initialized()
        contexts = self.chronicle.index.load_contexts()
        selected = self._select_contexts(contexts, context_ids)

        findings: list[ContextUseFinding] = []
        for ctx in selected:
            findings.extend(self._evaluate_context(ctx, target))

        status = self._overall_status(findings)
        return ContextUseCheckReport(
            status=status,
            target=target,
            purpose=purpose,
            context_count=len(selected),
            findings=findings,
        )

    def _select_contexts(
        self,
        contexts: dict[str, Context],
        context_ids: list[str] | None,
    ) -> list[Context]:
        if not context_ids:
            return list(contexts.values())
        return [contexts[cid] for cid in context_ids if cid in contexts]

    def _evaluate_context(
        self,
        context: Context,
        target: ContextUseTarget,
    ) -> list[ContextUseFinding]:
        classification = context.classification
        if classification is None:
            return [
                ContextUseFinding(
                    context_id=context.context_id,
                    title=context.title,
                    severity=ContextUseSeverity.WARNING,
                    summary="Context is unclassified.",
                    detail="No ClassificationMetadata is attached to this Context.",
                    recommendation="Add classification metadata before relying on this context-use check.",
                )
            ]

        findings: list[ContextUseFinding] = []

        if classification.layer == ClassificationLayer.RESTRICTED_SECRET:
            findings.append(
                ContextUseFinding(
                    context_id=context.context_id,
                    title=context.title,
                    severity=ContextUseSeverity.BLOCKED,
                    summary="Layer 4 context is not allowed for model-context use.",
                    detail="Restricted Secret records should not be placed in model context by default.",
                    recommendation="Keep secrets outside Chronicle body text and use references to a dedicated secret manager.",
                )
            )
            return findings

        if AllowedOperation.INJECT not in classification.allowed_operations:
            findings.append(
                ContextUseFinding(
                    context_id=context.context_id,
                    title=context.title,
                    severity=ContextUseSeverity.WARNING,
                    summary="Context does not list inject as an allowed operation.",
                    detail="The operation model is advisory, but this context is not marked for model-context use.",
                    recommendation="Add inject to allowed_operations only when this context is intended for model-context use.",
                )
            )

        if target == ContextUseTarget.EXTERNAL:
            if classification.layer >= ClassificationLayer.SENSITIVE_CONTEXT and not classification.llm_policy.external_allowed:
                findings.append(
                    ContextUseFinding(
                        context_id=context.context_id,
                        title=context.title,
                        severity=ContextUseSeverity.WARNING,
                        summary="Sensitive context is not explicitly allowed for external model-context use.",
                        detail="Layer 3+ context requires explicit review before external use.",
                        recommendation="Use local model context, mask the context, or add explicit external allowance only after review.",
                    )
                )
            elif not classification.llm_policy.external_allowed:
                findings.append(
                    ContextUseFinding(
                        context_id=context.context_id,
                        title=context.title,
                        severity=ContextUseSeverity.WARNING,
                        summary="External model-context use is not explicitly allowed.",
                        detail="ClassificationMetadata.llm_policy.external_allowed is false.",
                        recommendation="Use local model context or explicitly allow external use after review.",
                    )
                )

            if classification.llm_policy.masking_required:
                findings.append(
                    ContextUseFinding(
                        context_id=context.context_id,
                        title=context.title,
                        severity=ContextUseSeverity.WARNING,
                        summary="Masking is required before external model-context use.",
                        detail="ClassificationMetadata.llm_policy.masking_required is true.",
                        recommendation="Mask personal, customer, organizational, or strategic details before external use.",
                    )
                )

        if target == ContextUseTarget.LOCAL and not classification.llm_policy.local_allowed:
            findings.append(
                ContextUseFinding(
                    context_id=context.context_id,
                    title=context.title,
                    severity=ContextUseSeverity.WARNING,
                    summary="Local model-context use is not explicitly allowed.",
                    detail="ClassificationMetadata.llm_policy.local_allowed is false.",
                    recommendation="Review this context before local model-context use.",
                )
            )

        if not findings:
            findings.append(
                ContextUseFinding(
                    context_id=context.context_id,
                    title=context.title,
                    severity=ContextUseSeverity.OK,
                    summary="No model-context use warning detected.",
                )
            )

        return findings

    def _overall_status(self, findings: list[ContextUseFinding]) -> ContextUseSeverity:
        if any(f.severity == ContextUseSeverity.BLOCKED for f in findings):
            return ContextUseSeverity.BLOCKED
        if any(f.severity == ContextUseSeverity.WARNING for f in findings):
            return ContextUseSeverity.WARNING
        return ContextUseSeverity.OK
