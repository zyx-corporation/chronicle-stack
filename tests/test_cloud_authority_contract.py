"""Tests for Chronicle Cloud authority planning contracts."""

import json
import os

from typer.testing import CliRunner

from chronicle.api.cloud_authority import (
    CloudAuthoritySurface,
    CloudFederationSurface,
    default_cloud_authority_model,
    default_cloud_federation_boundary_model,
)
from chronicle.cli import app


def test_cloud_authority_model_preserves_local_authority() -> None:
    model = default_cloud_authority_model()
    by_surface = {entry.surface: entry for entry in model.entries}

    assert model.cloud_owns_chronicle is False
    assert model.cloud_ai_memory_positioning_allowed is False
    assert model.local_recovery_required is True
    assert model.backup_sync_is_publication is False
    assert model.federation_distinct_from_cloud_sharing is True
    assert by_surface[CloudAuthoritySurface.LOCAL_PRIMARY_RECORD].can_be_source_authority is True
    assert by_surface[CloudAuthoritySurface.CLOUD_REPLICA].can_be_source_authority is False
    assert by_surface[CloudAuthoritySurface.CLOUD_INDEX].can_be_source_authority is False


def test_daemon_cloud_authority_cli_json_shape(tmp_path) -> None:
    os.chdir(str(tmp_path))
    runner = CliRunner()

    result = runner.invoke(app, ["daemon", "cloud", "authority", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    for key in [
        "schema_version",
        "cloud_owns_chronicle",
        "cloud_ai_memory_positioning_allowed",
        "local_recovery_required",
        "backup_sync_is_publication",
        "federation_distinct_from_cloud_sharing",
        "entries",
        "unresolved",
    ]:
        assert key in payload
    assert payload["cloud_owns_chronicle"] is False
    assert payload["entries"][0]["surface"] == "local_primary_record"


def test_cloud_federation_boundary_separates_sync_and_disclosure() -> None:
    model = default_cloud_federation_boundary_model()
    by_surface = {entry.surface: entry for entry in model.entries}

    assert model.cloud_bypasses_federation_consent is False
    assert model.federation_is_trust_disclosure_layer is True
    assert model.cloud_sync_is_not_publication is True
    assert by_surface[CloudFederationSurface.TEAM_SYNC].belongs_to_cloud is True
    assert by_surface[CloudFederationSurface.TEAM_SYNC].belongs_to_federation is False
    assert by_surface[CloudFederationSurface.PARTNER_DISCLOSURE].belongs_to_cloud is False
    assert by_surface[CloudFederationSurface.PARTNER_DISCLOSURE].belongs_to_federation is True
    assert by_surface[CloudFederationSurface.PARTNER_DISCLOSURE].trust_scope_required is True


def test_daemon_cloud_federation_boundary_cli_json_shape(tmp_path) -> None:
    os.chdir(str(tmp_path))
    runner = CliRunner()

    result = runner.invoke(app, ["daemon", "cloud", "federation-boundary", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    for key in [
        "schema_version",
        "cloud_bypasses_federation_consent",
        "federation_is_trust_disclosure_layer",
        "cloud_sync_is_not_publication",
        "entries",
        "adr_required_for_cloud_federation_bridge",
    ]:
        assert key in payload
    assert payload["cloud_bypasses_federation_consent"] is False
