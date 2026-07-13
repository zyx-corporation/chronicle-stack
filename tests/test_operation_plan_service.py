"""Tests for Stage 2 operation plan preview and proposal conversion."""

import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from chronicle.cli import app
from chronicle.errors import OperationPlanAlreadyConvertedError, OperationPlanStaleTargetError
from chronicle.models.artifact import ArtifactType
from chronicle.services.artifact_service import ArtifactService
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.operation_plan_service import OperationPlanService
from chronicle.services.proposal_service import ProposalService
from chronicle.services.review_service import ReviewService


runner = CliRunner()


def test_operation_plan_preview_builds_artifact_update_plan(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    ChronicleService(tmp_path).init("Operation Plan")
    artifact, _ = ArtifactService(tmp_path).create("Plan Artifact", ArtifactType.DOCUMENT, content="v1")

    plan = OperationPlanService(tmp_path).build_artifact_update_plan(
        artifact_id=artifact.artifact_id,
        summary="Plan update",
        content="v2",
        source_refs=["evt_source_1"],
    )

    assert plan.preview_only is True
    assert plan.operation == "artifact.propose_update"
    assert plan.target_refs[0].record_id == artifact.artifact_id
    assert plan.source_refs == ["evt_source_1"]


def test_operation_plan_conversion_records_proposal_with_plan_payload(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    ChronicleService(tmp_path).init("Operation Plan Proposal")
    artifact, _ = ArtifactService(tmp_path).create("Plan Artifact", ArtifactType.DOCUMENT, content="v1")
    service = OperationPlanService(tmp_path)
    plan = service.build_artifact_update_plan(
        artifact_id=artifact.artifact_id,
        summary="Plan update",
        content="v2",
    )

    event = service.convert_artifact_update_plan_to_proposal(
        plan=plan,
        summary="Plan update",
        content="v2",
    )

    proposal = event.payload["proposal"]
    assert proposal["operation_plan"]["plan_id"] == plan.plan_id
    assert proposal["target_id"] == artifact.artifact_id


def test_operation_plan_conversion_rejects_duplicate_conversion(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    ChronicleService(tmp_path).init("Operation Plan Duplicate")
    artifact, _ = ArtifactService(tmp_path).create("Plan Artifact", ArtifactType.DOCUMENT, content="v1")
    service = OperationPlanService(tmp_path)
    plan = service.build_artifact_update_plan(
        artifact_id=artifact.artifact_id,
        summary="Plan update",
        content="v2",
    )

    service.convert_artifact_update_plan_to_proposal(plan=plan, summary="Plan update", content="v2")

    with pytest.raises(OperationPlanAlreadyConvertedError):
        service.convert_artifact_update_plan_to_proposal(plan=plan, summary="Plan update", content="v2")


def test_operation_plan_conversion_rejects_stale_target(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    ChronicleService(tmp_path).init("Operation Plan Stale")
    artifacts = ArtifactService(tmp_path)
    artifact, _ = artifacts.create("Plan Artifact", ArtifactType.DOCUMENT, content="v1")
    service = OperationPlanService(tmp_path)
    plan = service.build_artifact_update_plan(
        artifact_id=artifact.artifact_id,
        summary="Plan update",
        content="v2",
    )
    artifacts.update(artifact.artifact_id, content="v1.1", summary="intervening update")

    with pytest.raises(OperationPlanStaleTargetError):
        service.convert_artifact_update_plan_to_proposal(plan=plan, summary="Plan update", content="v2")


def test_operation_plan_preview_cli_json(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    ChronicleService(tmp_path).init("Operation Plan CLI")
    artifact, _ = ArtifactService(tmp_path).create("Plan Artifact", ArtifactType.DOCUMENT, content="v1")

    result = runner.invoke(
        app,
        [
            "plan",
            "artifact-update-preview",
            "--artifact",
            artifact.artifact_id,
            "--summary",
            "Plan update",
            "--content",
            "v2",
            "--json",
        ],
    )

    assert result.exit_code == 0
    assert '"operation": "artifact.propose_update"' in result.stdout


def test_operation_plan_persist_and_get_recorded_preview(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    ChronicleService(tmp_path).init("Operation Plan Record")
    artifact, _ = ArtifactService(tmp_path).create("Plan Artifact", ArtifactType.DOCUMENT, content="v1")
    service = OperationPlanService(tmp_path)
    plan = service.build_artifact_update_plan(
        artifact_id=artifact.artifact_id,
        summary="Plan update",
        content="v2",
    )

    event_id = service.persist_plan(plan)
    stored = service.get_plan(plan.plan_id)

    assert stored["event_id"] == event_id
    assert stored["plan"].plan_id == plan.plan_id
    assert stored["preview_only"] is True
    assert stored["action_preview_summary"]["status"] == "preview_only"


def test_operation_plan_list_cli_json(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    ChronicleService(tmp_path).init("Operation Plan CLI List")
    artifact, _ = ArtifactService(tmp_path).create("Plan Artifact", ArtifactType.DOCUMENT, content="v1")

    result = runner.invoke(
        app,
        [
            "plan",
            "artifact-update-preview",
            "--artifact",
            artifact.artifact_id,
            "--summary",
            "Plan update",
            "--content",
            "v2",
            "--record",
        ],
    )
    assert result.exit_code == 0

    list_result = runner.invoke(app, ["plan", "list", "--json"])

    assert list_result.exit_code == 0
    assert '"preview_only": true' in list_result.stdout
    assert '"operation": "artifact.propose_update"' in list_result.stdout


def test_operation_plan_status_tracks_conversion_and_apply(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    ChronicleService(tmp_path).init("Operation Plan Status")
    artifact, _ = ArtifactService(tmp_path).create("Plan Artifact", ArtifactType.DOCUMENT, content="v1")
    service = OperationPlanService(tmp_path)
    plan = service.build_artifact_update_plan(
        artifact_id=artifact.artifact_id,
        summary="Plan update",
        content="v2",
    )
    service.persist_plan(plan)
    proposal = service.convert_artifact_update_plan_to_proposal(
        plan=plan,
        summary="Plan update",
        content="v2",
    )
    ReviewService(tmp_path).approve(event_id=proposal.event_id, reviewer="alice")
    ProposalService(tmp_path).apply_artifact_proposal(proposal_event_id=proposal.event_id)

    stored = service.get_plan(plan.plan_id)

    assert stored["converted"] is True
    assert stored["applied"] is True
    assert stored["proposal_event_id"] == proposal.event_id
    assert stored["applied_event_id"] is not None
    assert stored["action_preview_summary"]["status"] == "applied"


def test_operation_plan_status_reports_stale_preview(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    ChronicleService(tmp_path).init("Operation Plan Stale Preview")
    artifacts = ArtifactService(tmp_path)
    artifact, _ = artifacts.create("Plan Artifact", ArtifactType.DOCUMENT, content="v1")
    service = OperationPlanService(tmp_path)
    plan = service.build_artifact_update_plan(
        artifact_id=artifact.artifact_id,
        summary="Plan update",
        content="v2",
    )
    service.persist_plan(plan)
    artifacts.update(artifact.artifact_id, content="v1.1", summary="intervening update")

    stored = service.get_plan(plan.plan_id)

    assert stored["target_status"]["stale"] is True
    assert stored["action_preview_summary"]["status"] == "stale_preview"
    assert "artifact-update-preview" in stored["action_preview_summary"]["next_action_command"]
