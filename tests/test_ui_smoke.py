"""Tests for read-only UI smoke command."""

import json

from typer.testing import CliRunner

from chronicle.cli import app
from chronicle.models.artifact import ArtifactType
from chronicle.models.audit import AuditOperation, AuditSeverity, AuditTargetEnvironment
from chronicle.models.boundary import BoundaryConditionField, BoundaryOperator, BoundaryRuleType
from chronicle.models.lifecycle import LifecycleAction, LifecycleReasonClass
from chronicle.models.visibility import VisibilityHint
from chronicle.services.artifact_service import ArtifactService
from chronicle.services.audit_service import AuditService
from chronicle.services.boundary_service import BoundaryService
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.context_service import ContextService
from chronicle.services.lifecycle_service import LifecycleService
from chronicle.services.runtime_config_service import RuntimeConfigService
from chronicle.services.runtime_service import RuntimeService
from chronicle.services.summary_job_service import SummaryJobService
from chronicle.ui_smoke import run_ui_smoke


def _populate(root):
    ChronicleService(root).init("UI Smoke")
    context = ContextService(root).add_context(title="Smoke Context", visibility_hint=VisibilityHint.PUBLIC)
    artifact_file = root / "artifact.md"
    artifact_file.write_text("artifact body", encoding="utf-8")
    ArtifactService(root).create(
        title="Smoke Artifact",
        artifact_type=ArtifactType.DOCUMENT,
        source_file=artifact_file,
        visibility_hint=VisibilityHint.PRIVATE,
    )
    BoundaryService(root).add_rule(
        rule_type=BoundaryRuleType.WARN,
        field=BoundaryConditionField.VISIBILITY,
        operator=BoundaryOperator.EQUALS,
        value="private",
        reason="Smoke boundary",
    )
    AuditService(root).record(
        operation=AuditOperation.EXPORT,
        actor="test",
        purpose="ui smoke",
        target_environment=AuditTargetEnvironment.LOCAL,
        result=AuditSeverity.INFO,
        summary="Smoke audit",
    )
    LifecycleService(root).record(
        action=LifecycleAction.SEAL,
        target_id=context.context_id,
        target_kind="context",
        actor="test",
        reason_class=LifecycleReasonClass.PRIVACY,
        reason="Smoke lifecycle",
    )
    RuntimeService(root).summarize(
        text="Smoke runtime summary. It stays local.",
        record=True,
    )
    RuntimeConfigService(root).set_local(model_name="smoke-local-model", provider_name="smoke-local")
    SummaryJobService(root).create_manual_draft(
        title="Smoke Summary Draft",
        summary_text="Smoke summary draft body.",
        prompt="Smoke summary prompt.",
    )


def test_run_ui_smoke_success(tmp_path):
    _populate(tmp_path)

    report = run_ui_smoke(tmp_path)

    assert report.passed is True
    payload = report.to_dict()
    assert payload["read_only"] is True
    assert payload["server_started"] is False
    assert payload["browser_required"] is False
    assert payload["external_runtime"] is False
    check_names = {check["name"] for check in payload["checks"]}
    assert "/api/overview" in check_names
    assert "/api/review-queue" in check_names
    assert "/api/summary-jobs" in check_names
    assert "/api/ui-boundary" in check_names
    assert "/api/runtime-config" in check_names
    assert "html-shell" in check_names
    assert any(name.startswith("/api/review-queue/") for name in check_names)
    assert any(name.endswith("#cli-parity") for name in check_names)
    assert any(name.endswith("#auth-readiness") for name in check_names)
    assert "/api/overview#runtime-auth-readiness" in check_names
    assert "/api/overview#summary-auth-readiness" in check_names
    assert any(name.startswith("/api/contexts/") for name in check_names)
    assert "/api/contexts/__chronicle_missing_context__" in check_names


def test_ui_smoke_command_text_success(tmp_path):
    _populate(tmp_path)
    runner = CliRunner()

    result = runner.invoke(app, ["ui-smoke", "--root", str(tmp_path)])

    assert result.exit_code == 0
    assert "Chronicle UI smoke" in result.stdout
    assert "Mode: read-only, no server, no browser, no external runtime" in result.stdout
    assert "[PASS] /api/overview" in result.stdout
    assert "[PASS] html-shell" in result.stdout


def test_ui_smoke_command_json_success(tmp_path):
    _populate(tmp_path)
    runner = CliRunner()

    result = runner.invoke(app, ["ui-smoke", "--root", str(tmp_path), "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["passed"] is True
    assert payload["server_started"] is False
    assert payload["external_runtime"] is False
    assert any(check["name"] == "/api/overview" for check in payload["checks"])
    assert any(check["name"] == "html-shell" for check in payload["checks"])


def test_ui_smoke_command_missing_root_fails(tmp_path):
    runner = CliRunner()

    result = runner.invoke(app, ["ui-smoke", "--root", str(tmp_path)])

    assert result.exit_code != 0


def test_ui_smoke_help():
    runner = CliRunner()

    result = runner.invoke(app, ["ui-smoke", "--help"])

    assert result.exit_code == 0
    assert "read-only" in result.stdout.lower()
    assert "json" in result.stdout.lower()
    assert "root" in result.stdout.lower()
