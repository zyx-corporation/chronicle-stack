"""Tests for scoped capability runtime access controls."""

import os
from pathlib import Path

import pytest

from chronicle.errors import CapabilityAccessDeniedError, CapabilityNetworkAccessDeniedError
from chronicle.models.artifact import ArtifactType
from chronicle.models.context import ContextScope
from chronicle.services.artifact_service import ArtifactService
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.context_service import ContextService
from chronicle.runtime.scoped import CapabilityNetworkPolicy, ScopedCapabilityRuntimeFactory


def test_scoped_runtime_reads_only_selected_contexts(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    ChronicleService(tmp_path).init("Scoped Runtime")
    contexts = ContextService(tmp_path)
    selected = contexts.add_context("Selected", "Keep", scope=ContextScope.PROJECT)
    other = contexts.add_context("Other", "Deny", scope=ContextScope.SESSION)

    runtime = ScopedCapabilityRuntimeFactory(tmp_path).create(
        capability_id="runtime.summarize",
        selected_context_ids=[selected.context_id],
    )

    projection = runtime.contexts.get(selected.context_id)

    assert projection.context_id == selected.context_id
    assert projection.summary == "Keep"
    with pytest.raises(CapabilityAccessDeniedError):
        runtime.contexts.get(other.context_id)


def test_scoped_runtime_reads_only_selected_artifacts(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    ChronicleService(tmp_path).init("Scoped Runtime Artifact")
    artifacts = ArtifactService(tmp_path)
    selected, _ = artifacts.create("Selected", ArtifactType.OTHER, content="selected body")
    other, _ = artifacts.create("Other", ArtifactType.OTHER, content="other body")

    runtime = ScopedCapabilityRuntimeFactory(tmp_path).create(
        capability_id="artifact.propose_update",
        selected_artifact_ids=[selected.artifact_id],
    )

    assert runtime.artifacts.read_current(selected.artifact_id) == "selected body"
    with pytest.raises(CapabilityAccessDeniedError):
        runtime.artifacts.read_current(other.artifact_id)


def test_scoped_runtime_proposal_writer_restricts_mutation_targets(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    ChronicleService(tmp_path).init("Scoped Runtime Proposal")
    artifacts = ArtifactService(tmp_path)
    selected, _ = artifacts.create("Selected", ArtifactType.OTHER, content="selected body")
    other, _ = artifacts.create("Other", ArtifactType.OTHER, content="other body")

    runtime = ScopedCapabilityRuntimeFactory(tmp_path).create(
        capability_id="artifact.propose_update",
        selected_artifact_ids=[selected.artifact_id],
    )

    event = runtime.proposals.propose_artifact_update(
        artifact_id=selected.artifact_id,
        summary="Scoped proposal",
        content="revised body",
    )

    assert event.artifact_id == selected.artifact_id
    with pytest.raises(CapabilityAccessDeniedError):
        runtime.proposals.propose_artifact_update(
            artifact_id=other.artifact_id,
            summary="Denied",
            content="nope",
        )


def test_scoped_runtime_network_is_denied_by_default(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    ChronicleService(tmp_path).init("Scoped Runtime Network")

    runtime = ScopedCapabilityRuntimeFactory(tmp_path).create(capability_id="runtime.invoke")

    with pytest.raises(CapabilityNetworkAccessDeniedError):
        runtime.network.authorize(destination="api.example.test", operation="invoke")


def test_scoped_runtime_network_honors_manifest_and_policy(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    ChronicleService(tmp_path).init("Scoped Runtime Network Allow")

    runtime = ScopedCapabilityRuntimeFactory(tmp_path).create(
        capability_id="runtime.invoke",
        network_policy=CapabilityNetworkPolicy(
            enabled=True,
            allowed_destinations=("api.example.test",),
            allowed_operations=("invoke",),
        ),
    )

    allowed = runtime.network.authorize(destination="api.example.test", operation="invoke")

    assert allowed == {"destination": "api.example.test", "operation": "invoke"}
    assert runtime.audit.network_enabled is True


def test_scoped_runtime_disables_network_for_non_network_capability(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    ChronicleService(tmp_path).init("Scoped Runtime No Network")

    runtime = ScopedCapabilityRuntimeFactory(tmp_path).create(
        capability_id="artifact.propose_update",
        network_policy=CapabilityNetworkPolicy(
            enabled=True,
            allowed_destinations=("api.example.test",),
            allowed_operations=("invoke",),
        ),
    )

    with pytest.raises(CapabilityNetworkAccessDeniedError):
        runtime.network.authorize(destination="api.example.test", operation="invoke")
    assert runtime.audit.network_enabled is False
