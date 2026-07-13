"""Tests for the static capability registry."""

import json
import os

from typer.testing import CliRunner

from chronicle.cli import app
from chronicle.services.capability_registry_service import CapabilityRegistryService


runner = CliRunner()


def test_capability_registry_service_lists_unique_capabilities() -> None:
    service = CapabilityRegistryService()

    manifests = service.list_capabilities()

    assert any(manifest.capability_id == "runtime.summarize" for manifest in manifests)
    assert any(manifest.capability_id == "artifact.propose_update" for manifest in manifests)
    assert service.duplicate_ids() == []


def test_runtime_capability_list_json(tmp_path) -> None:
    os.chdir(str(tmp_path))
    result = runner.invoke(app, ["runtime", "capability", "list", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    ids = {item["capability_id"] for item in payload}
    assert "runtime.summarize" in ids
    assert "runtime.invoke" in ids
    assert "review.approve" in ids


def test_runtime_capability_show_json(tmp_path) -> None:
    os.chdir(str(tmp_path))
    result = runner.invoke(app, ["runtime", "capability", "show", "--id", "runtime.summarize", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["capability_id"] == "runtime.summarize"
    assert payload["operation_family"] == "runtime"
    assert payload["review_required"] is True
    assert payload["uses_network"] is True
