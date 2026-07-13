"""Static capability registry service."""

from __future__ import annotations

from collections import Counter

from chronicle.models.capability import CapabilityExposure, CapabilityManifest


class CapabilityNotFoundError(ValueError):
    """Requested capability manifest was not found."""


class CapabilityRegistryService:
    """Expose a static Stage 2 capability registry."""

    def list_capabilities(self) -> list[CapabilityManifest]:
        return [CapabilityManifest.model_validate(item) for item in _CAPABILITY_MANIFESTS]

    def get_capability(self, capability_id: str) -> CapabilityManifest:
        for manifest in self.list_capabilities():
            if manifest.capability_id == capability_id:
                return manifest
        raise CapabilityNotFoundError(capability_id)

    def duplicate_ids(self) -> list[str]:
        counts = Counter(manifest.capability_id for manifest in self.list_capabilities())
        return sorted(capability_id for capability_id, count in counts.items() if count > 1)


_CAPABILITY_MANIFESTS = [
    {
        "capability_id": "runtime.summarize",
        "title": "Runtime Summarize",
        "summary": "Generate an explicit local or configured-provider summary through the runtime boundary.",
        "operation_family": "runtime",
        "exposure": CapabilityExposure.CLI.value,
        "input_schema_ref": "chronicle.models.runtime.RuntimeSummaryResult.request",
        "output_schema_ref": "chronicle.models.runtime.RuntimeSummaryResult",
        "context_scope": "selected_or_none",
        "reads_record_kinds": ["summary_source_ref"],
        "uses_network": True,
        "review_required": True,
        "notes": [
            "Configured provider execution remains explicit/manual only.",
            "Chronicle primary record remains authoritative.",
        ],
    },
    {
        "capability_id": "runtime.invoke",
        "title": "Runtime Invoke",
        "summary": "Execute an explicit configured-provider operation through the runtime boundary.",
        "operation_family": "runtime",
        "exposure": CapabilityExposure.CLI.value,
        "input_schema_ref": "chronicle.models.runtime.RuntimeExecutionResult.request",
        "output_schema_ref": "chronicle.models.runtime.RuntimeExecutionResult",
        "context_scope": "selected_or_none",
        "reads_record_kinds": ["summary_source_ref"],
        "uses_network": True,
        "review_required": True,
        "notes": [
            "Configured provider execution is blocked unless explicit execution is enabled.",
        ],
    },
    {
        "capability_id": "runtime.retrieve_plan",
        "title": "Runtime Retrieve Plan",
        "summary": "Assemble a dry-run retrieval plan without invoking an external runtime.",
        "operation_family": "runtime",
        "exposure": CapabilityExposure.CLI.value,
        "input_schema_ref": "chronicle.models.runtime.RuntimeRetrievalPlan.request",
        "output_schema_ref": "chronicle.models.runtime.RuntimeRetrievalPlan",
        "context_scope": "derived_read_only",
        "reads_record_kinds": ["vector_index", "graph_export", "chronicle_search"],
        "uses_network": False,
        "review_required": True,
        "notes": [
            "Dry-run retrieval only.",
            "No GraphRAG runtime is implied.",
        ],
    },
    {
        "capability_id": "artifact.propose_update",
        "title": "Artifact Proposal Update",
        "summary": "Create an append-only proposal event for a later artifact update review/apply flow.",
        "operation_family": "proposal",
        "exposure": CapabilityExposure.CLI.value,
        "input_schema_ref": "chronicle.services.proposal_service.ProposalService.propose_artifact_update",
        "output_schema_ref": "chronicle.models.event.EventType.PROPOSAL_RECORDED",
        "context_scope": "targeted_artifact",
        "reads_record_kinds": ["artifact"],
        "emits_proposal_kinds": ["artifact_update"],
        "uses_network": False,
        "mutates_primary_record": True,
        "review_required": True,
    },
    {
        "capability_id": "context.propose_update",
        "title": "Context Proposal Update",
        "summary": "Create an append-only proposal event for a later context update review/apply flow.",
        "operation_family": "proposal",
        "exposure": CapabilityExposure.CLI.value,
        "input_schema_ref": "chronicle.services.proposal_service.ProposalService.propose_context_update",
        "output_schema_ref": "chronicle.models.event.EventType.PROPOSAL_RECORDED",
        "context_scope": "targeted_context",
        "reads_record_kinds": ["context"],
        "emits_proposal_kinds": ["context_update"],
        "uses_network": False,
        "mutates_primary_record": True,
        "review_required": True,
    },
    {
        "capability_id": "review.approve",
        "title": "Review Approve",
        "summary": "Record an append-only approval decision for a reviewable Chronicle event.",
        "operation_family": "review",
        "exposure": CapabilityExposure.CLI.value,
        "input_schema_ref": "chronicle.services.review_service.ReviewService.approve",
        "output_schema_ref": "chronicle.models.review.ReviewDecisionResult",
        "context_scope": "review_target",
        "reads_record_kinds": ["event", "audit"],
        "uses_network": False,
        "mutates_primary_record": True,
        "review_required": False,
    },
    {
        "capability_id": "review.request_changes",
        "title": "Review Request Changes",
        "summary": "Record an append-only request-changes decision for a reviewable Chronicle event.",
        "operation_family": "review",
        "exposure": CapabilityExposure.CLI.value,
        "input_schema_ref": "chronicle.services.review_service.ReviewService.request_changes",
        "output_schema_ref": "chronicle.models.review.ReviewDecisionResult",
        "context_scope": "review_target",
        "reads_record_kinds": ["event", "audit"],
        "uses_network": False,
        "mutates_primary_record": True,
        "review_required": False,
    },
    {
        "capability_id": "review.reject",
        "title": "Review Reject",
        "summary": "Record an append-only rejection decision for a reviewable Chronicle event.",
        "operation_family": "review",
        "exposure": CapabilityExposure.CLI.value,
        "input_schema_ref": "chronicle.services.review_service.ReviewService.reject",
        "output_schema_ref": "chronicle.models.review.ReviewDecisionResult",
        "context_scope": "review_target",
        "reads_record_kinds": ["event", "audit"],
        "uses_network": False,
        "mutates_primary_record": True,
        "review_required": False,
    },
]
