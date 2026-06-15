"""Security metadata doctor checks."""

from chronicle.doctor.check_factory import ok, warn
from chronicle.models.classification import AllowedOperation, ClassificationLayer
from chronicle.models.context import Context
from chronicle.models.doctor import DoctorCheck
from chronicle.models.event import ChronicleEvent
from chronicle.security.prompt_injection import scan_text_for_prompt_injection


def check_security_metadata(events: list[ChronicleEvent]) -> list[DoctorCheck]:
    """Run security metadata checks for stored Context records."""
    contexts = _contexts(events)
    return [
        check_context_classification(contexts),
        check_layer4_context_body_storage(contexts),
        check_context_use_policy_metadata(contexts),
        check_prompt_injection_markers(contexts),
        check_integrity_metadata_presence(contexts),
    ]


def _contexts(events: list[ChronicleEvent]) -> list[Context]:
    contexts: list[Context] = []
    for event in events:
        context = event.payload.get("context")
        if isinstance(context, dict):
            try:
                contexts.append(Context.model_validate(context))
            except ValueError:
                continue
    return contexts


def check_context_classification(contexts: list[Context]) -> DoctorCheck:
    unclassified = sorted(ctx.context_id for ctx in contexts if ctx.classification is None)
    if unclassified:
        return warn(
            "security_context_classification_present",
            "one or more Context records are missing classification metadata",
            detail=", ".join(unclassified),
            recommendation=(
                "run `chronicle context classification missing` and "
                "`chronicle context classification set --context <id> --layer internal --sensitivity internal`"
            ),
        )
    return ok("security_context_classification_present", "Context classification metadata is present")


def check_layer4_context_body_storage(contexts: list[Context]) -> DoctorCheck:
    layer4 = sorted(
        ctx.context_id
        for ctx in contexts
        if ctx.classification is not None and ctx.classification.layer == ClassificationLayer.RESTRICTED_SECRET
    )
    if layer4:
        return warn(
            "security_layer4_body_storage",
            "Layer 4 Context records are present in Chronicle body storage",
            detail=", ".join(layer4),
            recommendation="store Layer 4 secrets as references to a dedicated secret manager instead of body text",
        )
    return ok("security_layer4_body_storage", "no Layer 4 Context body storage detected")


def check_context_use_policy_metadata(contexts: list[Context]) -> DoctorCheck:
    risky = sorted(
        ctx.context_id
        for ctx in contexts
        if ctx.classification is not None
        and ctx.classification.layer >= ClassificationLayer.SENSITIVE_CONTEXT
        and (
            AllowedOperation.INJECT in ctx.classification.allowed_operations
            or ctx.classification.llm_policy.external_allowed
        )
    )
    if risky:
        return warn(
            "security_sensitive_context_use_policy",
            "sensitive Context records are marked for model-context or external use",
            detail=", ".join(risky),
            recommendation="review LlmPolicy and allowed_operations before context-use workflows",
        )
    return ok("security_sensitive_context_use_policy", "no sensitive external/model-context policy risk detected")


def check_prompt_injection_markers(contexts: list[Context]) -> DoctorCheck:
    findings: list[str] = []
    for ctx in contexts:
        text = f"{ctx.title}\n{ctx.summary}"
        report = scan_text_for_prompt_injection(text, source_id=ctx.context_id)
        if report.findings:
            findings.extend(f"{finding.source_id}:{finding.pattern_id}" for finding in report.findings)
    if findings:
        return warn(
            "security_prompt_injection_markers",
            "stored Context text contains instruction-like markers",
            detail="; ".join(sorted(findings)),
            recommendation="treat stored content as data and use Chronicle data block boundaries for model-facing workflows",
        )
    return ok("security_prompt_injection_markers", "no prompt-injection markers detected in Context text")


def check_integrity_metadata_presence(contexts: list[Context]) -> DoctorCheck:
    missing = sorted(
        ctx.context_id
        for ctx in contexts
        if ctx.classification is not None and not ctx.classification.integrity.hash
    )
    if missing:
        return warn(
            "security_integrity_metadata_present",
            "classified Context records are missing integrity metadata hashes",
            detail=", ".join(missing),
            recommendation="use the context classification workflow before packaging or controlled export workflows",
        )
    return ok(
        "security_integrity_metadata_present",
        "classified Context integrity metadata is present or no classified Contexts exist",
    )
