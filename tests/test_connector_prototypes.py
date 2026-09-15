"""Tests for local connector prototype simulation."""

import json
import os

from typer.testing import CliRunner

from chronicle.api.connector_prototypes import (
    ConnectorPrototypeKind,
    ConnectorPrototypeSimulator,
)
from chronicle.cli import app
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.chronicle_object_service import ChronicleObjectService
from chronicle.services.context_service import ContextService


def test_connector_prototype_dry_run_does_not_change_primary_record(tmp_path) -> None:
    ChronicleService(tmp_path).init("Connector Prototype Dry Run")
    before = len(ChronicleService(tmp_path).jsonl.read_all())

    simulation = ConnectorPrototypeSimulator(tmp_path).simulate(
        connector=ConnectorPrototypeKind.OBSIDIAN_CAPTURE,
        title="Obsidian note",
        body="A structured note capture.",
        idempotency_key="idem-prototype-dry-run",
        source_ref="vault/note.md",
    )

    after = len(ChronicleService(tmp_path).jsonl.read_all())
    assert simulation.production_surface is False
    assert simulation.request_model == "EventWriteRequest"
    assert simulation.response is not None
    assert simulation.response["dry_run"] is True
    assert "prototype_only_not_production_connector" in simulation.warnings
    assert before == after


def test_connector_prototype_commit_records_event_with_origin_metadata(tmp_path) -> None:
    ChronicleService(tmp_path).init("Connector Prototype Commit")
    context = ContextService(tmp_path).add_context(title="Prototype Context")
    before = len(ChronicleService(tmp_path).jsonl.read_all())

    simulation = ConnectorPrototypeSimulator(tmp_path).simulate(
        connector=ConnectorPrototypeKind.BROWSER_CAPTURE,
        title="Browser capture",
        body="Captured page note.",
        idempotency_key="idem-prototype-browser-commit",
        commit=True,
        context_ids=[context.context_id],
        source_url="https://example.test/source",
    )

    after = len(ChronicleService(tmp_path).jsonl.read_all())
    event = ChronicleService(tmp_path).jsonl.read_all()[-1]
    assert simulation.response is not None
    assert simulation.response["accepted"] is True
    assert after == before + 1
    assert event.payload["api"]["origin"]["source_tool"] == "prototype:browser_capture"
    assert event.payload["connector_prototype"] == "browser_capture"


def test_connector_prototype_agent_assertion_records_reviewable_object(tmp_path) -> None:
    ChronicleService(tmp_path).init("Connector Prototype Assertion")

    simulation = ConnectorPrototypeSimulator(tmp_path).simulate(
        connector=ConnectorPrototypeKind.AGENT_ASSERTION,
        title="agent:claim",
        body="Agent says partner evidence is still missing.",
        idempotency_key="idem-prototype-agent-assertion",
        commit=True,
        subject_ref="subject:partner-evidence",
    )

    assert simulation.response is not None
    assertion_id = simulation.response["assertion_id"]
    assert assertion_id is not None
    record = ChronicleObjectService(tmp_path).get(assertion_id)
    assert record.object_type == "objection"
    assert record.created_by == "prototype:agent_assertion"
    assert "review_required_for_agent_claims" in simulation.carry_forward


def test_connector_prototype_cli_json_shape(tmp_path) -> None:
    os.chdir(str(tmp_path))
    runner = CliRunner()
    runner.invoke(app, ["init", "--title", "Connector Prototype CLI"])

    result = runner.invoke(
        app,
        [
            "daemon",
            "prototype",
            "simulate",
            "--connector",
            "business_fact",
            "--title",
            "account:alpha",
            "--body",
            "Contract signed status was reported by CRM simulator.",
            "--idempotency-key",
            "idem-prototype-business-cli",
            "--subject-ref",
            "account:alpha",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.stderr
    payload = json.loads(result.stdout)
    for key in [
        "connector",
        "production_surface",
        "request_model",
        "request_payload",
        "response",
        "carry_forward",
        "do_not_carry_forward",
        "warnings",
    ]:
        assert key in payload
    assert payload["connector"] == "business_fact"
    assert payload["production_surface"] is False
    assert payload["request_model"] == "AssertionWriteRequest"
    assert "no_generic_log_ingestion" in payload["do_not_carry_forward"]
