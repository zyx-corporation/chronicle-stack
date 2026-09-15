"""Contract tests for the planned Chronicle-native API surface."""

import pytest
from pydantic import ValidationError

from chronicle.api.contracts import (
    API_SCHEMA_VERSION,
    ApiActorKind,
    ApiEndpoint,
    ApiOriginMetadata,
    AssertionKind,
    AssertionWriteRequest,
    BoundariesQueryRequest,
    ContextQueryRequest,
    DiffWriteRequest,
    EventWriteRequest,
    TimelineQueryRequest,
    list_endpoint_contracts,
)
from chronicle.models.artifact import ArtifactType
from chronicle.models.boundary import BoundaryConditionField, BoundaryOperator, BoundaryRuleType
from chronicle.services.api_adapter_service import ApiAdapterService
from chronicle.services.artifact_service import ArtifactService
from chronicle.services.audit_service import AuditService
from chronicle.services.boundary_service import BoundaryService
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.chronicle_object_service import ChronicleObjectService
from chronicle.services.context_service import ContextService


def _origin() -> ApiOriginMetadata:
    return ApiOriginMetadata(
        source_tool="contract-test",
        actor_id="tool:contract-test",
        actor_kind=ApiActorKind.TOOL,
    )


def test_minimum_api_surface_is_contract_only() -> None:
    contracts = list_endpoint_contracts()

    assert [contract.endpoint for contract in contracts] == [
        ApiEndpoint.POST_EVENTS,
        ApiEndpoint.GET_CONTEXT,
        ApiEndpoint.POST_DIFFS,
        ApiEndpoint.GET_TIMELINE,
        ApiEndpoint.POST_ASSERTIONS,
        ApiEndpoint.GET_BOUNDARIES,
    ]
    assert all(contract.opens_network_socket is False for contract in contracts)
    assert {contract.endpoint for contract in contracts if contract.write} == {
        ApiEndpoint.POST_EVENTS,
        ApiEndpoint.POST_DIFFS,
        ApiEndpoint.POST_ASSERTIONS,
    }
    assert all(contract.idempotency_required for contract in contracts if contract.write)


def test_event_write_requires_idempotency_and_origin_metadata() -> None:
    with pytest.raises(ValidationError):
        EventWriteRequest(event_type="user_input", actor="tool", summary="Captured note")

    request = EventWriteRequest(
        idempotency_key="idem-event-1",
        origin=_origin(),
        event_type="user_input",
        actor="tool",
        summary="Captured note",
        payload={"note": "structured, not generic log ingestion"},
    )

    payload = request.model_dump(mode="json")
    assert payload["schema_version"] == API_SCHEMA_VERSION
    assert payload["dry_run"] is True
    assert payload["review_status"] == "needs_review"
    assert payload["origin"]["source_tool"] == "contract-test"


def test_context_and_timeline_reads_require_selectors() -> None:
    with pytest.raises(ValidationError):
        ContextQueryRequest()
    with pytest.raises(ValidationError):
        TimelineQueryRequest()

    context_request = ContextQueryRequest(context_ids=["ctx_api"], operation="view")
    timeline_request = TimelineQueryRequest(artifact_id="art_api")

    assert context_request.boundary_preview is True
    assert timeline_request.include_payload is False


def test_assertions_capture_reviewable_claims_not_truth_proofs() -> None:
    request = AssertionWriteRequest(
        idempotency_key="idem-assertion-1",
        origin=_origin(),
        assertion_kind=AssertionKind.CAVEAT,
        statement="Evidence is incomplete until the partner review arrives.",
        evidence_refs=["src_partner_review_request"],
        caveats=["Do not promote to primary fact without review."],
    )

    payload = request.model_dump(mode="json")
    assert payload["assertion_kind"] == "caveat"
    assert payload["verification_status"] == "unverified"
    assert payload["confidence"] == "unknown"


def test_boundary_query_contract_is_advisory() -> None:
    request = BoundariesQueryRequest(
        matter_ref="matter:api-contract",
        operation="inject",
        target_use="agent_context_preview",
    )

    assert request.include_rules is True
    assert request.operation == "inject"


def test_request_models_export_json_schema_without_server_dependency() -> None:
    schema = EventWriteRequest.model_json_schema()

    assert schema["title"] == "EventWriteRequest"
    assert "idempotency_key" in schema["properties"]
    assert "origin" in schema["properties"]


def test_api_adapter_dry_run_write_does_not_change_primary_record(tmp_path) -> None:
    ChronicleService(tmp_path).init("API Adapter Dry Run")
    service = ApiAdapterService(tmp_path)
    before = len(service.chronicle.jsonl.read_all())

    response = service.preview_event_write(
        EventWriteRequest(
            idempotency_key="idem-event-dry-run",
            origin=_origin(),
            event_type="user_input",
            actor="tool",
            summary="Preview only",
        )
    )

    after = len(service.chronicle.jsonl.read_all())
    assert response.accepted is True
    assert response.dry_run is True
    assert response.idempotency_key == "idem-event-dry-run"
    assert before == after


def test_api_adapter_blocks_committed_writes_until_persistence_contract(tmp_path) -> None:
    ChronicleService(tmp_path).init("API Adapter Commit Block")
    service = ApiAdapterService(tmp_path)
    before = len(service.chronicle.jsonl.read_all())

    response = service.preview_event_write(
        EventWriteRequest(
            idempotency_key="idem-event-commit",
            origin=_origin(),
            dry_run=False,
            event_type="user_input",
            actor="tool",
            summary="Should not commit",
        )
    )

    after = len(service.chronicle.jsonl.read_all())
    assert response.accepted is False
    assert response.errors[0].code == "partial_persistence_blocked"
    assert before == after


def test_api_adapter_commits_event_write_with_idempotency_and_audit(tmp_path) -> None:
    ChronicleService(tmp_path).init("API Adapter Commit")
    service = ApiAdapterService(tmp_path)
    before = len(service.chronicle.jsonl.read_all())
    request = EventWriteRequest(
        idempotency_key="idem-event-commit-1",
        origin=_origin(),
        dry_run=False,
        event_type="note_added",
        actor="tool",
        summary="Committed API note",
        payload={"note": "structured event write"},
        audit_reason="contract test",
    )

    response = service.commit_event_write(request)
    duplicate = service.commit_event_write(request)
    after = len(service.chronicle.jsonl.read_all())
    audits = AuditService(tmp_path).list_events()

    assert response.accepted is True
    assert response.dry_run is False
    assert response.event_id is not None
    assert duplicate.duplicate is True
    assert duplicate.event_id == response.event_id
    assert after == before + 1
    assert audits[-1].operation == "api_write"
    assert audits[-1].source_event_id == response.event_id


def test_api_adapter_commits_assertion_as_reviewable_chronicle_object(tmp_path) -> None:
    ChronicleService(tmp_path).init("API Adapter Assertion Commit")
    context = ContextService(tmp_path).add_context(title="Assertion Context")
    service = ApiAdapterService(tmp_path)
    before = len(service.chronicle.jsonl.read_all())
    request = AssertionWriteRequest(
        idempotency_key="idem-assertion-commit-1",
        origin=_origin(),
        dry_run=False,
        assertion_kind="caveat",
        statement="This claim needs partner confirmation.",
        verification_status="unverified",
        evidence_refs=["src_partner_request"],
        caveats=["Do not treat as primary fact."],
        context_ids=[context.context_id],
    )

    response = service.commit_assertion_write(request)
    duplicate = service.commit_assertion_write(request)
    objects = ChronicleObjectService(tmp_path).list_objects()
    after = len(service.chronicle.jsonl.read_all())

    assert response.accepted is True
    assert response.assertion_id is not None
    assert duplicate.duplicate is True
    assert duplicate.assertion_id == response.assertion_id
    assert after == before + 1
    assertion = next(item for item in objects if item.object_id == response.assertion_id)
    assert assertion.object_type == "objection"
    assert assertion.context_id == context.context_id
    assert assertion.evidence == ["src_partner_request"]


def test_api_adapter_commits_diff_write_with_idempotency_and_audit(tmp_path) -> None:
    ChronicleService(tmp_path).init("API Adapter Diff Commit")
    artifact_file = tmp_path / "artifact.md"
    artifact_file.write_text("v1", encoding="utf-8")
    artifact, version_1 = ArtifactService(tmp_path).create(
        title="API Diff Artifact",
        artifact_type=ArtifactType.DOCUMENT,
        source_file=artifact_file,
    )
    artifact_file.write_text("v2", encoding="utf-8")
    _artifact, version_2 = ArtifactService(tmp_path).update(
        artifact_id=artifact.artifact_id,
        source_file=artifact_file,
        summary="api diff update",
    )
    service = ApiAdapterService(tmp_path)
    before = len(service.chronicle.jsonl.read_all())
    request = DiffWriteRequest(
        idempotency_key="idem-diff-commit-1",
        origin=_origin(),
        dry_run=False,
        artifact_id=artifact.artifact_id,
        from_version_id=version_1.version_id,
        to_version_id=version_2.version_id,
        created_by="tool",
        summary="API diff",
        transformed=["body changed"],
    )

    response = service.commit_diff_write(request)
    duplicate = service.commit_diff_write(request)
    after = len(service.chronicle.jsonl.read_all())

    assert response.accepted is True
    assert response.rde_record_id is not None
    assert duplicate.duplicate is True
    assert duplicate.rde_record_id == response.rde_record_id
    assert after == before + 1
    assert service.chronicle.paths.rde_report_path(response.rde_record_id).exists()


def test_api_adapter_reads_context_and_timeline_without_payload_by_default(tmp_path) -> None:
    ChronicleService(tmp_path).init("API Adapter Read")
    context = ContextService(tmp_path).add_context(title="API Context", source_ref="private-ref")
    service = ApiAdapterService(tmp_path)

    context_response = service.get_context(ContextQueryRequest(context_ids=[context.context_id]))
    timeline_response = service.get_timeline(TimelineQueryRequest(context_ids=[context.context_id]))

    assert context_response.records[0]["context_id"] == context.context_id
    assert "source_ref" not in context_response.records[0]
    assert timeline_response.records
    assert "payload" not in timeline_response.records[0]


def test_api_adapter_reads_advisory_boundaries(tmp_path) -> None:
    ChronicleService(tmp_path).init("API Adapter Boundary")
    BoundaryService(tmp_path).add_rule(
        rule_type=BoundaryRuleType.WARN,
        field=BoundaryConditionField.TAG,
        operator=BoundaryOperator.CONTAINS,
        value="external",
        reason="External disclosure needs review.",
    )

    response = ApiAdapterService(tmp_path).get_boundaries(
        BoundariesQueryRequest(matter_ref="matter:api")
    )

    assert response.records[0]["rule_type"] == "warn"
    assert response.warnings[0].code == "advisory_boundary_rules"
