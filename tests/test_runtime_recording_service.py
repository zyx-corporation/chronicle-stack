"""Tests for runtime-side Chronicle recording separation."""

import os
from pathlib import Path

from chronicle.models.artifact import ArtifactType
from chronicle.models.runtime import (
    RuntimeExecutionResult,
    RuntimeInvocationPlan,
    RuntimeProviderKind,
    RuntimeRetrievalPlan,
    RuntimeSummaryResult,
    default_local_runtime_config,
)
from chronicle.models.summary_job import SummarySourceRef
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.runtime_recording_service import RuntimeRecordingService
from chronicle.services.summary_job_service import SummaryJobService


def test_runtime_recording_service_persists_summary_result_event(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    ChronicleService(tmp_path).init("Runtime Recording Summary")
    service = RuntimeRecordingService(tmp_path)

    result = RuntimeSummaryResult(
        provider_kind=RuntimeProviderKind.LOCAL,
        provider_name="local-placeholder",
        model_name="local-placeholder",
        invocation_mode="explicit-manual",
        external_call_made=False,
        source_text_length=24,
        generated_text="Local runtime summary output.",
    )

    event_id = service.persist_summary_result(result)

    events = ChronicleService(tmp_path).jsonl.read_all()
    assert any(event.event_id == event_id for event in events)
    payload = next(event.payload for event in events if event.event_id == event_id)
    assert payload["runtime_summary"]["generated_text"] == "Local runtime summary output."


def test_runtime_recording_service_creates_execution_draft_summary(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    ChronicleService(tmp_path).init("Runtime Recording Draft")
    service = RuntimeRecordingService(tmp_path)

    result = RuntimeExecutionResult(
        provider_kind=RuntimeProviderKind.HTTP,
        provider_name="http-manual",
        model_name="http-model",
        operation="rewrite",
        invocation_mode="explicit-http-manual",
        external_call_made=True,
        source_text_length=18,
        output_text="Execution output for draft summary.",
        response_metadata={"response_id": "resp_1"},
        response_keys=["output_text", "response_id"],
    )

    draft = service.create_execution_draft_summary(
        title="Execution Draft",
        result=result,
        runtime_config=default_local_runtime_config().model_copy(
            update={
                "provider_kind": RuntimeProviderKind.HTTP,
                "provider_name": "http-manual",
                "model_name": "http-model",
                "allow_network": True,
            }
        ),
        prompt="Rewrite for operator handoff.",
        operator="runtime-invoke:rewrite",
        source_refs=[SummarySourceRef(record_id="evt_source", record_type="event")],
        tags=["runtime-invoke-summary", "rewrite", "http"],
    )

    stored = SummaryJobService(tmp_path).get(draft.summary_job_id)
    assert stored.summary_text == "Execution output for draft summary."
    assert stored.provenance.response_metadata["response_id"] == "resp_1"
    assert stored.provenance.external_call_made is True


def test_runtime_recording_service_persists_invocation_plan_event(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    ChronicleService(tmp_path).init("Runtime Recording Plan")
    service = RuntimeRecordingService(tmp_path)

    plan = RuntimeInvocationPlan(
        provider_kind=RuntimeProviderKind.LOCAL,
        provider_name="local-placeholder",
        model_name="local-placeholder",
        operation="summarize",
        source_text_length=12,
        request_preview={"operation": "summarize"},
        execution_request={"text": "hello", "operation": "summarize"},
        downstream_commands=["chronicle runtime summarize --text ..."],
        notes=["dry-run invocation contract only"],
        invocation_ready=True,
    )

    event_id = service.persist_invocation_plan(plan, summary_label="summary sum_123 summarize")

    events = ChronicleService(tmp_path).jsonl.read_all()
    payload = next(event.payload for event in events if event.event_id == event_id)
    assert payload["runtime_invocation_plan"]["operation"] == "summarize"


def test_runtime_recording_service_creates_execution_artifact(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    ChronicleService(tmp_path).init("Runtime Recording Artifact")
    service = RuntimeRecordingService(tmp_path)

    result = RuntimeExecutionResult(
        provider_kind=RuntimeProviderKind.HTTP,
        provider_name="http-manual",
        model_name="http-model",
        operation="rewrite",
        invocation_mode="explicit-http-manual",
        external_call_made=True,
        source_text_length=10,
        output_text="Artifact output body.",
    )

    artifact, version = service.create_execution_artifact(
        title="Runtime Artifact",
        artifact_type=ArtifactType.REPORT,
        result=result,
    )

    assert artifact.title == "Runtime Artifact"
    assert version.artifact_id == artifact.artifact_id
    current = service.artifacts.chronicle.artifact_store.read_current(artifact.artifact_id)
    assert current == "Artifact output body."


def test_runtime_recording_service_persists_retrieval_plan_event(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    ChronicleService(tmp_path).init("Runtime Recording Retrieval")
    service = RuntimeRecordingService(tmp_path)

    plan = RuntimeRetrievalPlan(query="graph context", notes=["dry-run retrieval plan only"])

    event_id = service.persist_retrieval_plan(plan)

    events = ChronicleService(tmp_path).jsonl.read_all()
    payload = next(event.payload for event in events if event.event_id == event_id)
    assert payload["runtime_retrieval_plan"]["query"] == "graph context"
