"""Tests for agent runtime contract models."""

import json
import os

import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from chronicle.api.agent_runtime import (
    AgentCapabilityScope,
    AgentRecordOriginKind,
    AgentRuntimeMetadata,
    default_agent_runtime_contract,
)
from chronicle.cli import app


def test_default_agent_runtime_contract_keeps_chronicle_authority() -> None:
    contract = default_agent_runtime_contract("kazane-test")

    assert contract.runtime_name == "kazane-test"
    assert AgentCapabilityScope.READ_CONTEXT in contract.allowed_scopes
    assert AgentCapabilityScope.WRITE_ASSERTIONS in contract.allowed_scopes
    assert contract.writes_through_chronicle_api is True
    assert contract.owns_primary_record is False
    assert contract.unbounded_memory_dump_allowed is False
    assert contract.review_required_for_ai_or_agent_output is True


def test_agent_runtime_metadata_converts_to_api_origin() -> None:
    metadata = AgentRuntimeMetadata(
        runtime_name="kazane-test",
        actor_id="agent:kazane-test",
        origin_kind=AgentRecordOriginKind.AGENT_ACTION,
        capability_scope=AgentCapabilityScope.WRITE_EVENTS,
        source_session="session-1",
    )

    origin = metadata.to_api_origin()

    assert origin.source_tool == "agent-runtime:kazane-test"
    assert origin.actor_id == "agent:kazane-test"
    assert origin.actor_kind == "agent"
    assert origin.capability_id == "agent.write_events"


def test_human_judgment_agent_metadata_requires_supervisor() -> None:
    with pytest.raises(ValidationError):
        AgentRuntimeMetadata(
            runtime_name="kazane-test",
            actor_id="human:operator",
            origin_kind=AgentRecordOriginKind.HUMAN_JUDGMENT,
            capability_scope=AgentCapabilityScope.WRITE_ASSERTIONS,
        )

    metadata = AgentRuntimeMetadata(
        runtime_name="kazane-test",
        actor_id="human:operator",
        origin_kind=AgentRecordOriginKind.HUMAN_JUDGMENT,
        capability_scope=AgentCapabilityScope.WRITE_ASSERTIONS,
        human_supervisor_id="human:operator",
    )
    assert metadata.to_api_origin().actor_kind == "human"


def test_daemon_agent_contract_cli_json_shape(tmp_path) -> None:
    os.chdir(str(tmp_path))
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "daemon",
            "agent",
            "contract",
            "--runtime-name",
            "kazane-test",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    for key in [
        "schema_version",
        "runtime_name",
        "allowed_scopes",
        "writes_through_chronicle_api",
        "owns_primary_record",
        "unbounded_memory_dump_allowed",
        "review_required_for_ai_or_agent_output",
        "replay_audit_required",
        "notes",
    ]:
        assert key in payload
    assert payload["runtime_name"] == "kazane-test"
    assert payload["owns_primary_record"] is False
