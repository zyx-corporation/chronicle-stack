"""Tests for proposal-first editing records."""

import json
import os

import pytest
from typer.testing import CliRunner

from chronicle.cli import app
from chronicle.models.artifact import ArtifactType
from chronicle.services.artifact_service import ArtifactService
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.context_service import ContextService
from chronicle.services.proposal_service import ProposalService


@pytest.fixture
def chronicle_root(tmp_path):
    ChronicleService(tmp_path).init("Proposal Test")
    return tmp_path


def test_artifact_proposal_records_needs_review_event(chronicle_root, tmp_path):
    source = tmp_path / "artifact.md"
    source.write_text("artifact v1", encoding="utf-8")
    artifact, _version = ArtifactService(chronicle_root).create(
        title="Proposal Artifact",
        artifact_type=ArtifactType.DOCUMENT,
        source_file=source,
    )
    proposal = ProposalService(chronicle_root).propose_artifact_update(
        artifact_id=artifact.artifact_id,
        summary="Propose better body",
        content="artifact v2 proposal",
    )

    assert proposal.event_type.value == "proposal_recorded"
    assert proposal.review_status.value == "needs_review"
    assert proposal.payload["proposal"]["target_kind"] == "artifact"
    assert proposal.payload["proposal"]["proposed_content"]["length"] == len("artifact v2 proposal")


def test_context_proposal_records_target_context(chronicle_root):
    context = ContextService(chronicle_root).add_context(title="Proposal Context", summary="v1")
    proposal = ProposalService(chronicle_root).propose_context_update(
        context_id=context.context_id,
        summary="Clarify summary",
        proposed_summary="v2 summary proposal",
        proposed_tags=["review", "draft"],
    )

    assert proposal.event_type.value == "proposal_recorded"
    assert proposal.context_ids == [context.context_id]
    assert proposal.payload["proposal"]["proposed_fields"]["summary"] == "v2 summary proposal"
    assert proposal.payload["proposal"]["proposed_fields"]["tags"] == ["review", "draft"]


def test_artifact_propose_update_cli_json(tmp_path):
    os.chdir(tmp_path)
    runner = CliRunner()
    runner.invoke(app, ["init", "--title", "Artifact Proposal CLI"])
    source = tmp_path / "artifact.md"
    source.write_text("artifact v1", encoding="utf-8")
    create = runner.invoke(
        app,
        ["artifact", "create", "--title", "CLI Artifact", "--type", "document", "--file", str(source), "--json"],
    )
    artifact_id = json.loads(create.stdout)["artifact"]["artifact_id"]

    result = runner.invoke(
        app,
        [
            "artifact",
            "propose-update",
            "--artifact",
            artifact_id,
            "--summary",
            "Propose CLI update",
            "--content",
            "artifact v2 proposal",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["review_status"] == "needs_review"
    assert payload["payload"]["proposal"]["proposal_kind"] == "artifact_update"


def test_context_propose_update_cli_json(tmp_path):
    os.chdir(tmp_path)
    runner = CliRunner()
    runner.invoke(app, ["init", "--title", "Context Proposal CLI"])
    created = runner.invoke(
        app,
        ["add-context", "--title", "CLI Context", "--summary", "v1", "--json"],
    )
    context_id = json.loads(created.stdout)["context_id"]

    result = runner.invoke(
        app,
        [
            "context",
            "propose-update",
            "--context",
            context_id,
            "--summary",
            "Propose CLI context update",
            "--body",
            "v2 summary proposal",
            "--tag",
            "draft",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["payload"]["proposal"]["proposal_kind"] == "context_update"
    assert payload["payload"]["proposal"]["proposed_fields"]["summary"] == "v2 summary proposal"
